#include <stdint.h>
#include "../common/tvm_harness.h"

// Full-model entrypoint exported from quick_start.ll.
extern int __tvm_ffi_fused_transpose_extern_fmatmul32_0_add_relu_transpose1_extern_fmatmul32_1_add1(
    void *self_handle, TVMArg *args, int num_args, void *result);

// quick_start.ll declares these as null global pointers; FuseTIR calls them for
// intermediate buffer allocation (~816 KB total across 3 allocations).
extern void *(*__TVMBackendAllocWorkspace)(int, int, uint64_t, int, int);
extern int   (*__TVMBackendFreeWorkspace)(int, int, void *);

#define TVM_WORKSPACE_SIZE (1024 * 1024)
static char _tvm_ws[TVM_WORKSPACE_SIZE] __attribute__((aligned(64), section(".l2")));
static uint64_t _tvm_ws_top = 0;

static void *_tvm_alloc(int dt, int did, uint64_t n, int dc, int db) {
    (void)dt; (void)did; (void)dc; (void)db;
    uintptr_t base = (uintptr_t)(_tvm_ws + _tvm_ws_top);
    uintptr_t aligned = (base + 63) & ~(uintptr_t)63;
    _tvm_ws_top = (aligned - (uintptr_t)_tvm_ws) + n;
    return (void *)aligned;
}
static int _tvm_free(int dt, int did, void *p) { (void)dt; (void)did; (void)p; return 0; }

static float x_data[1 * 784] __attribute__((aligned(64), section(".l2")));
static float fc1_w_data[256 * 784] __attribute__((aligned(64), section(".l2")));
static float fc1_b_data[256] __attribute__((aligned(64), section(".l2")));
static float fc2_w_data[10 * 256] __attribute__((aligned(64), section(".l2")));
static float fc2_b_data[10] __attribute__((aligned(64), section(".l2")));
static float out_data[1 * 10] __attribute__((aligned(64), section(".l2")));

static int64_t shape_x[2] __attribute__((aligned(64), section(".l2"))) = {1, 784};
static int64_t shape_fc1_w[2] __attribute__((aligned(64), section(".l2"))) = {256, 784};
static int64_t shape_fc1_b[1] __attribute__((aligned(64), section(".l2"))) = {256};
static int64_t shape_fc2_w[2] __attribute__((aligned(64), section(".l2"))) = {10, 256};
static int64_t shape_fc2_b[1] __attribute__((aligned(64), section(".l2"))) = {10};
static int64_t shape_out[2] __attribute__((aligned(64), section(".l2"))) = {1, 10};

static DLTensor make_tensor_nd(float *data, int ndim, int64_t *shape) {
  DLTensor t;
  t.data = data;
  t.device.device_type = TVM_DEVICE_CPU;
  t.device.device_id = 0;
  t.ndim = ndim;
  t.dtype.code = 2;   // float
  t.dtype.bits = 32;  // float32
  t.dtype.lanes = 1;
  t.shape = shape;
  t.strides = 0;
  t.byte_offset = 0;
  return t;
}

int main(void) {
  // Example initialization for a deterministic smoke test.
  for (int i = 0; i < 784; ++i) x_data[i] = 1.0f;
  for (int i = 0; i < 256 * 784; ++i) fc1_w_data[i] = 0.01f;
  for (int i = 0; i < 256; ++i) fc1_b_data[i] = 0.0f;
  for (int i = 0; i < 10 * 256; ++i) fc2_w_data[i] = 0.01f;
  for (int i = 0; i < 10; ++i) fc2_b_data[i] = 0.0f;
  for (int i = 0; i < 10; ++i) out_data[i] = 0.0f;

  DLTensor x = make_tensor_nd(x_data, 2, shape_x);
  DLTensor fc1_w = make_tensor_nd(fc1_w_data, 2, shape_fc1_w);
  DLTensor fc1_b = make_tensor_nd(fc1_b_data, 1, shape_fc1_b);
  DLTensor fc2_w = make_tensor_nd(fc2_w_data, 2, shape_fc2_w);
  DLTensor fc2_b = make_tensor_nd(fc2_b_data, 1, shape_fc2_b);
  DLTensor out = make_tensor_nd(out_data, 2, shape_out);

  // Fused function argument order in quick_start.ll:
  // (fc1_weight, x, fc1_bias, fc2_weight, fc2_bias, out)
  TVMArg args[6];
  args[0].type_index = TVM_ARG_HANDLE; args[0].padding = 0; args[0].value.v_handle = &fc1_w;
  args[1].type_index = TVM_ARG_HANDLE; args[1].padding = 0; args[1].value.v_handle = &x;
  args[2].type_index = TVM_ARG_HANDLE; args[2].padding = 0; args[2].value.v_handle = &fc1_b;
  args[3].type_index = TVM_ARG_HANDLE; args[3].padding = 0; args[3].value.v_handle = &fc2_w;
  args[4].type_index = TVM_ARG_HANDLE; args[4].padding = 0; args[4].value.v_handle = &fc2_b;
  args[5].type_index = TVM_ARG_HANDLE; args[5].padding = 0; args[5].value.v_handle = &out;

  __TVMBackendAllocWorkspace = _tvm_alloc;
  __TVMBackendFreeWorkspace  = _tvm_free;

  // Returns 0 on success (TVM convention)
  return __tvm_ffi_fused_transpose_extern_fmatmul32_0_add_relu_transpose1_extern_fmatmul32_1_add1(
      0, args, 6, 0);
}