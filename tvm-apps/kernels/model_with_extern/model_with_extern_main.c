#include "../common/tvm_harness.h"

extern int __tvm_ffi_extern_fmatmul32_0(void *self_handle, TVMArg *args,
                                         int num_args, void *result);

static float x_data[1 * 784] __attribute__((aligned(64), section(".l2")));
static float w_data[784 * 256] __attribute__((aligned(64), section(".l2")));
static float out_data[1 * 256] __attribute__((aligned(64), section(".l2")));

static int64_t shape_x[2] __attribute__((aligned(64), section(".l2"))) = {1, 784};
static int64_t shape_w[2] __attribute__((aligned(64), section(".l2"))) = {784, 256};
static int64_t shape_out[2] __attribute__((aligned(64), section(".l2"))) = {1, 256};

static DLTensor make_tensor2d(float *data, int64_t *shape) {
  DLTensor tensor;
  tensor.data = data;
  tensor.device.device_type = TVM_DEVICE_CPU;
  tensor.device.device_id = 0;
  tensor.ndim = 2;
  tensor.dtype.code = 2;   // float
  tensor.dtype.bits = 32;  // float32
  tensor.dtype.lanes = 1;
  tensor.shape = shape;
  tensor.strides = 0;
  tensor.byte_offset = 0;
  return tensor;
}

int main(void) {
  for (int i = 0; i < 784; ++i) {
    x_data[i] = 1.0f;
  }
  for (int i = 0; i < 784 * 256; ++i) {
    w_data[i] = 1.0f;
  }
  for (int i = 0; i < 256; ++i) {
    out_data[i] = 0.0f;
  }

  DLTensor x = make_tensor2d(x_data, shape_x);
  DLTensor w = make_tensor2d(w_data, shape_w);
  DLTensor out = make_tensor2d(out_data, shape_out);

  TVMArg args[3];
  args[0].type_index = TVM_ARG_HANDLE;
  args[0].padding = 0;
  args[0].value.v_handle = &x;
  args[1].type_index = TVM_ARG_HANDLE;
  args[1].padding = 0;
  args[1].value.v_handle = &w;
  args[2].type_index = TVM_ARG_HANDLE;
  args[2].padding = 0;
  args[2].value.v_handle = &out;

  return __tvm_ffi_extern_fmatmul32_0(0, args, 3, 0);
}
