#include <stdint.h>

#define TVM_ARG_HANDLE 7
#define TVM_DEVICE_CPU 1

typedef union {
  void *v_handle;
  int64_t v_int64;
  double v_float64;
} TVMValue;

typedef struct {
  int32_t type_index;
  int32_t padding;
  TVMValue value;
} TVMArg;

typedef struct {
  int32_t device_type;
  int32_t device_id;
} DLDevice;

typedef struct {
  uint8_t code;
  uint8_t bits;
  uint16_t lanes;
} DLDataType;

typedef struct {
  void *data;
  DLDevice device;
  int32_t ndim;
  DLDataType dtype;
  int64_t *shape;
  int64_t *strides;
  uint64_t byte_offset;
} DLTensor;

void TVMFFIErrorSetRaisedFromCStrParts(const char *kind, const char **parts,
                                       int num_parts) {
  (void)kind;
  (void)parts;
  (void)num_parts;
}

static DLTensor make_tensor(float *data, int64_t *shape) {
  DLTensor tensor;
  tensor.data = data;
  tensor.device.device_type = TVM_DEVICE_CPU;
  tensor.device.device_id = 0;
  tensor.ndim = 1;
  tensor.dtype.code = 2;
  tensor.dtype.bits = 32;
  tensor.dtype.lanes = 1;
  tensor.shape = shape;
  tensor.strides = 0;
  tensor.byte_offset = 0;
  return tensor;
}
