#include "../common/tvm_harness.h"

extern int __tvm_ffi_main(void *self_handle, TVMArg *args, int num_args,
                          void *result);

static float a_data[64] __attribute__((aligned(64), section(".l2"))) = {
    0.0f,  1.0f,  2.0f,  3.0f,  4.0f,  5.0f,  6.0f,  7.0f,
    8.0f,  9.0f,  10.0f, 11.0f, 12.0f, 13.0f, 14.0f, 15.0f,
    16.0f, 17.0f, 18.0f, 19.0f, 20.0f, 21.0f, 22.0f, 23.0f,
    24.0f, 25.0f, 26.0f, 27.0f, 28.0f, 29.0f, 30.0f, 31.0f,
    32.0f, 33.0f, 34.0f, 35.0f, 36.0f, 37.0f, 38.0f, 39.0f,
    40.0f, 41.0f, 42.0f, 43.0f, 44.0f, 45.0f, 46.0f, 47.0f,
    48.0f, 49.0f, 50.0f, 51.0f, 52.0f, 53.0f, 54.0f, 55.0f,
    56.0f, 57.0f, 58.0f, 59.0f, 60.0f, 61.0f, 62.0f, 63.0f,
};

static float b_data[64] __attribute__((aligned(64), section(".l2"))) = {
    1.0f, 1.0f, 1.0f, 1.0f, 1.0f, 1.0f, 1.0f, 1.0f,
    1.0f, 1.0f, 1.0f, 1.0f, 1.0f, 1.0f, 1.0f, 1.0f,
    1.0f, 1.0f, 1.0f, 1.0f, 1.0f, 1.0f, 1.0f, 1.0f,
    1.0f, 1.0f, 1.0f, 1.0f, 1.0f, 1.0f, 1.0f, 1.0f,
    1.0f, 1.0f, 1.0f, 1.0f, 1.0f, 1.0f, 1.0f, 1.0f,
    1.0f, 1.0f, 1.0f, 1.0f, 1.0f, 1.0f, 1.0f, 1.0f,
    1.0f, 1.0f, 1.0f, 1.0f, 1.0f, 1.0f, 1.0f, 1.0f,
    1.0f, 1.0f, 1.0f, 1.0f, 1.0f, 1.0f, 1.0f, 1.0f,
};

static float c_data[1] __attribute__((aligned(64), section(".l2"))) = {0.0f};

static int64_t shape_64[1] __attribute__((aligned(64), section(".l2"))) = {64};
static int64_t shape_1[1] __attribute__((aligned(64), section(".l2"))) = {1};

int main(void) {
  DLTensor a = make_tensor(a_data, shape_64);
  DLTensor b = make_tensor(b_data, shape_64);
  DLTensor c = make_tensor(c_data, shape_1);

  TVMArg args[3];
  args[0].type_index = TVM_ARG_HANDLE;
  args[0].padding = 0;
  args[0].value.v_handle = &a;
  args[1].type_index = TVM_ARG_HANDLE;
  args[1].padding = 0;
  args[1].value.v_handle = &b;
  args[2].type_index = TVM_ARG_HANDLE;
  args[2].padding = 0;
  args[2].value.v_handle = &c;

  int status = __tvm_ffi_main(0, args, 3, 0);
  if (status != 0) {
    return status;
  }

  return c_data[0] == 2016.0f ? 0 : 1;
}
