# custom_pipeline

Bypass Relax's native kernel selection for selected ops by routing them to
hand-written C kernels via `T.call_extern`.

## Files

- `kernels.json` — registry of (Relax op -> C function -> source file).
- `kernels_config.py` — typed loader for the JSON.
- `custom_pass.py` — Relax `module_pass` + `PyExprMutator` that rewrites
  matched `R.Call(op, ...)` into `R.call_tir(extern_fn, args, out_sinfo)`,
  and synthesizes the TIR `PrimFunc` whose body is a single
  `T.call_extern("int32", "<c_fn>", buf0.data, buf1.data, ..., out.data)`.
- `build.py` — driver that builds a small Relax model, runs the pass,
  lowers with the `"zero"` pipeline, and either:
  - exports a host shared library (`fcompile` links `kernels.json` C files), or
  - emits `.ll` for the existing AraXL `tvm-apps/Makefile`.

## Quickstart

Host shared library:

```bash
python -m tvm-apps.models.custom_pipeline.build
```

AraXL / RISC-V LLVM IR:

```bash
python -m tvm-apps.models.custom_pipeline.build --araxl --app model_with_extern
```

The `.ll` lands in `tvm-apps/models/custom_pipeline/build/`.
To consume it through the existing `tvm-apps/Makefile`, either:

1. Copy/symlink it to `tvm-apps/artifacts/output/<app>/<app>.ll`, **and**
2. Extend the `ELF` recipe to compile each `source_file` listed in
   `kernels.json` and pass the resulting `.o` files into the linker step.

A minimal Makefile patch (sketch):

```makefile
EXTERN_C_SRCS := $(ARA_DIR)/tvm-apps/apps/custom_conv2d.c
EXTERN_C_OBJS := $(patsubst %.c,$(APP_BUILD_DIR)/%.o,$(notdir $(EXTERN_C_SRCS)))

$(APP_BUILD_DIR)/%.o: $(ARA_DIR)/tvm-apps/apps/%.c | $(APP_BUILD_DIR)
	$(RISCV_CC) $(RISCV_CCFLAGS) -c $< -o $@

$(ELF): $(TVM_OBJ) $(MAIN_OBJ) $(EXTERN_C_OBJS) $(LINK_LD) | $(BIN_DIR)
	$(RISCV_CC) $(RISCV_CCFLAGS) $(RISCV_LDFLAGS) \
	    $(TVM_OBJ) $(MAIN_OBJ) $(EXTERN_C_OBJS) $(RUNTIME_LLVM) \
	    -o $@ -T$(LINK_LD)
```

## Buffer-pointer flow (Relax -> TIR -> C)

1. Relax `Call` operands are `Tensor`s with a DLTensor backing store.
2. The rewrite replaces the `Call` with `R.call_tir(gv, args, out_sinfo)`.
   `call_tir` allocates the output buffer (according to `out_sinfo`) and
   passes all tensor handles into the TIR PrimFunc.
3. Inside the PrimFunc, each parameter is a TIR `handle` `Var`; the
   `buffer_map` matches it to a typed `tir.Buffer`. `buf.data` is a raw
   pointer (TIR handle var) suitable for C-ABI.
4. `T.call_extern("int32", c_fn, buf0.data, buf1.data, ..., bufN.data)`
   emits a direct C-ABI call. The handwritten C function receives those
   pointers as ordinary `float*` arguments.

## Notes / limitations

- Shapes must be static at pass time (we read `arg.struct_info.shape`).
- The pass assumes one custom kernel per Relax op (extend `specs_by_op`
  if you want shape-based dispatch).
- For host builds, `fcompile` invokes the system C compiler; for AraXL,
  use the Makefile path so the RISC-V toolchain compiles the C sources.
