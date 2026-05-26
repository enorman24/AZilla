#include <stdint.h>
#include "printf.h"
#include "../common/tvm_harness.h"

// ----------------------------------------------------------------
// TVM workspace allocator — FuseTIR allocates the (16,32) transpose
// scratch buffer through this pointer rather than on the stack.
// ----------------------------------------------------------------
extern void *(*__TVMBackendAllocWorkspace)(int, int, uint64_t, int, int);
extern int   (*__TVMBackendFreeWorkspace)(int, int, void *);

#define TVM_WORKSPACE_SIZE (64 * 1024)
static char _tvm_ws[TVM_WORKSPACE_SIZE] __attribute__((aligned(64), section(".l2")));
static uint64_t _tvm_ws_top = 0;

static void *_tvm_alloc(int dt, int did, uint64_t n, int dc, int db) {
    (void)dt; (void)did; (void)dc; (void)db;
    uintptr_t base    = (uintptr_t)(_tvm_ws + _tvm_ws_top);
    uintptr_t aligned = (base + 63) & ~(uintptr_t)63;
    _tvm_ws_top = (aligned - (uintptr_t)_tvm_ws) + n;
    return (void *)aligned;
}
static int _tvm_free(int dt, int did, void *p) { (void)dt; (void)did; (void)p; return 0; }

// ----------------------------------------------------------------
// Single fused kernel emitted by FuseTIR:
//   transpose(W1) -> fmatmul32 -> fbiasadd32 -> relu
//                 -> transpose(W2) -> fmatmul32 -> fbiasadd32
//
// Args (6 DLTensors):  fc1_weight, x, fc1_bias, fc2_weight, fc2_bias, out
// ----------------------------------------------------------------
extern int __tvm_ffi_fused_transpose_extern_fmatmul32_0_extern_fbiasadd32_2_relu_transpose1_extern_fmatmul32_1_extern_fbiasadd32_3(
    void*, TVMArg*, int, void*);

// ----------------------------------------------------------------
// Data buffers in L2 (aligned for RVV)
// nn.Linear stores weights transposed: fc1=(32,16), fc2=(8,32)
// ----------------------------------------------------------------
static float x_data      [4 * 16]  __attribute__((aligned(64), section(".l2")));
static float W1_data     [32 * 16] __attribute__((aligned(64), section(".l2"))); // (32,16)
static float b1_data     [32]      __attribute__((aligned(64), section(".l2")));
static float W2_data     [8 * 32]  __attribute__((aligned(64), section(".l2"))); // (8,32)
static float b2_data     [8]       __attribute__((aligned(64), section(".l2")));
static float out_data    [4 * 8]   __attribute__((aligned(64), section(".l2")));

// Shape arrays for DLTensor
static int64_t sh_4x16[2]  = {4, 16};
static int64_t sh_32x16[2] = {32, 16};  // fc1_weight transposed
static int64_t sh_32[1]    = {32};
static int64_t sh_8x32[2]  = {8, 32};   // fc2_weight transposed
static int64_t sh_8[1]     = {8};
static int64_t sh_4x8[2]   = {4, 8};

static DLTensor make_tensor2d(float *data, int64_t *shape) {
    DLTensor t;
    t.data               = data;
    t.device.device_type = TVM_DEVICE_CPU;
    t.device.device_id   = 0;
    t.ndim               = 2;
    t.dtype.code         = 2;   // float
    t.dtype.bits         = 32;
    t.dtype.lanes        = 1;
    t.shape              = shape;
    t.strides            = 0;
    t.byte_offset        = 0;
    return t;
}

static DLTensor make_tensor1d(float *data, int64_t *shape) {
    DLTensor t = make_tensor2d(data, shape);
    t.ndim = 1;
    return t;
}

static TVMArg handle(DLTensor *t) {
    TVMArg a;
    a.type_index      = TVM_ARG_HANDLE;
    a.padding         = 0;
    a.value.v_handle  = t;
    return a;
}

#define CALL(fn, args, n) do {                          \
    int _r = fn(0, args, n, 0);                         \
    if (_r != 0) { printf("  ERROR ret=%d\n", _r); return _r; } \
} while(0)

int main(void) {
    printf("[tiny_mlp] start\n");
    printf("  model: (4,16) -> Linear(32) -> ReLU -> Linear(8)\n");
    printf("  kernels: fmatmul32 + fbiasadd32 (AraXL RVV)\n");

    // --- [1] Initialise weights and input ----------------------
    printf("[1/3] init weights\n");
    // x: batch of 4 sensor vectors, each 16 features
    for (int i = 0; i < 4 * 16; ++i)  x_data[i]  = 0.1f * (float)(i % 16);
    // W1 stored (32,16) — nn.Linear layout; small init keeps activations in [0,1]
    for (int i = 0; i < 32 * 16; ++i) W1_data[i] = 0.05f * (float)(i % 7 - 3);
    for (int i = 0; i < 32;      ++i) b1_data[i] = 0.01f;
    // W2 stored (8,32)
    for (int i = 0; i < 8 * 32;  ++i) W2_data[i] = 0.05f * (float)(i % 5 - 2);
    for (int i = 0; i < 8;       ++i) b2_data[i] = 0.0f;
    printf("[1/3] done\n");

    // --- [2] Build DLTensors and call fused kernel -------------
    printf("[2/3] build tensors\n");
    DLTensor t_W1  = make_tensor2d(W1_data,  sh_32x16);
    DLTensor t_x   = make_tensor2d(x_data,   sh_4x16);
    DLTensor t_b1  = make_tensor1d(b1_data,  sh_32);
    DLTensor t_W2  = make_tensor2d(W2_data,  sh_8x32);
    DLTensor t_b2  = make_tensor1d(b2_data,  sh_8);
    DLTensor t_out = make_tensor2d(out_data, sh_4x8);

    __TVMBackendAllocWorkspace = _tvm_alloc;
    __TVMBackendFreeWorkspace  = _tvm_free;

    printf("[3/3] run fused kernel (transpose->matmul->biasadd->relu->transpose->matmul->biasadd)\n");
    TVMArg fused_args[6] = {
        handle(&t_W1),
        handle(&t_x),
        handle(&t_b1),
        handle(&t_W2),
        handle(&t_b2),
        handle(&t_out),
    };
    CALL(__tvm_ffi_fused_transpose_extern_fmatmul32_0_extern_fbiasadd32_2_relu_transpose1_extern_fmatmul32_1_extern_fbiasadd32_3,
         fused_args, 6);
    printf("[3/3] done  out[0]=%f\n", out_data[0]);

    // --- Print logits for all 4 samples -------------------------
    printf("[done] logits (4 samples x 8 classes):\n");
    for (int i = 0; i < 4; ++i) {
        printf("  sample %d: ", i);
        for (int j = 0; j < 8; ++j)
            printf("%6.3f ", out_data[i * 8 + j]);
        printf("\n");
    }

    return 0;
}
