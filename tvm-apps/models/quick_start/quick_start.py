# from tvm.script import ir as I
# from tvm.script import tirx as T
# from tvm.script import relax as R

@I.ir_module
class Module:
    @T.prim_func
    def extern_fmatmul32_0(in0: T.Buffer((T.int64(1), T.int64(784)), "float32"), in1: T.Buffer((T.int64(784), T.int64(256)), "float32"), out: T.Buffer((T.int64(1), T.int64(256)), "float32")):
        T.func_attr({"op_pattern": 0, "tir.noalias": True})
        with T.sblock("root"):
            T.reads()
            T.writes()
            T.call_extern("int32", "fmatmul32", out.data, in0.data, in1.data, T.int64(1), T.int64(784), T.int64(256))

    @T.prim_func
    def extern_fmatmul32_1(in0: T.Buffer((T.int64(1), T.int64(256)), "float32"), in1: T.Buffer((T.int64(256), T.int64(10)), "float32"), out: T.Buffer((T.int64(1), T.int64(10)), "float32")):
        T.func_attr({"op_pattern": 0, "tir.noalias": True})
        with T.sblock("root"):
            T.reads()
            T.writes()
            T.call_extern("int32", "fmatmul32", out.data, in0.data, in1.data, T.int64(1), T.int64(256), T.int64(10))

    @T.prim_func(private=True)
    def fused_transpose_extern_fmatmul32_0_add_relu_transpose1_extern_fmatmul32_1_add1(fc1_weight: T.Buffer((T.int64(256), T.int64(784)), "float32"), x: T.Buffer((T.int64(1), T.int64(784)), "float32"), fc1_bias: T.Buffer((T.int64(256),), "float32"), fc2_weight: T.Buffer((T.int64(10), T.int64(256)), "float32"), fc2_bias: T.Buffer((T.int64(10),), "float32"), T_add_intermediate_1: T.Buffer((T.int64(1), T.int64(10)), "float32")):
        T.func_attr({"tirx.noalias": True})
        # with T.sblock("root"):
        T_transpose_intermediate = T.sblock_alloc_buffer((T.int64(784), T.int64(256)))
        out_intermediate = T.sblock_alloc_buffer((T.int64(1), T.int64(256)))
        T_add_intermediate = T.sblock_alloc_buffer((T.int64(1), T.int64(256)))
        compute_intermediate = T.sblock_alloc_buffer((T.int64(1), T.int64(256)))
        T_transpose_intermediate_1 = T.sblock_alloc_buffer((T.int64(256), T.int64(10)))
        out_intermediate_1 = T.sblock_alloc_buffer((T.int64(1), T.int64(10)))
        for ax0, ax1 in T.grid(T.int64(784), T.int64(256)):
            with T.sblock("T_transpose"):
                v_ax0, v_ax1 = T.axis.remap("SS", [ax0, ax1])
                T.reads(fc1_weight[v_ax1, v_ax0])
                T.writes(T_transpose_intermediate[v_ax0, v_ax1])
                T_transpose_intermediate[v_ax0, v_ax1] = fc1_weight[v_ax1, v_ax0]
        T.call_extern("int32", "fmatmul32", out_intermediate.data, x.data, T_transpose_intermediate.data, T.int64(1), T.int64(784), T.int64(256))
        for ax0, ax1 in T.grid(T.int64(1), T.int64(256)):
            with T.sblock("T_add"):
                v_ax0, v_ax1 = T.axis.remap("SS", [ax0, ax1])
                T.reads(out_intermediate[v_ax0, v_ax1], fc1_bias[v_ax1])
                T.writes(T_add_intermediate[v_ax0, v_ax1])
                T_add_intermediate[v_ax0, v_ax1] = out_intermediate[v_ax0, v_ax1] + fc1_bias[v_ax1]
        for i0, i1 in T.grid(T.int64(1), T.int64(256)):
            with T.sblock("compute"):
                v_i0, v_i1 = T.axis.remap("SS", [i0, i1])
                T.reads(T_add_intermediate[v_i0, v_i1])
                T.writes(compute_intermediate[v_i0, v_i1])
                compute_intermediate[v_i0, v_i1] = T.max(T_add_intermediate[v_i0, v_i1], T.float32(0.0))
        for ax0, ax1 in T.grid(T.int64(256), T.int64(10)):
            with T.sblock("T_transpose1"):
                v_ax0, v_ax1 = T.axis.remap("SS", [ax0, ax1])
                T.reads(fc2_weight[v_ax1, v_ax0])
                T.writes(T_transpose_intermediate_1[v_ax0, v_ax1])
                T_transpose_intermediate_1[v_ax0, v_ax1] = fc2_weight[v_ax1, v_ax0]
        T.call_extern("int32", "fmatmul32", out_intermediate_1.data, compute_intermediate.data, T_transpose_intermediate_1.data, T.int64(1), T.int64(256), T.int64(10))
        for ax0, ax1 in T.grid(T.int64(1), T.int64(10)):
            with T.sblock("T_add1"):
                v_ax0, v_ax1 = T.axis.remap("SS", [ax0, ax1])
                T.reads(out_intermediate_1[v_ax0, v_ax1], fc2_bias[v_ax1])
                T.writes(T_add_intermediate_1[v_ax0, v_ax1])
                T_add_intermediate_1[v_ax0, v_ax1] = out_intermediate_1[v_ax0, v_ax1] + fc2_bias[v_ax1]

    @R.function
    def forward(x: R.Tensor((1, 784), dtype="float32"), fc1_weight: R.Tensor((256, 784), dtype="float32"), fc1_bias: R.Tensor((256,), dtype="float32"), fc2_weight: R.Tensor((10, 256), dtype="float32"), fc2_bias: R.Tensor((10,), dtype="float32")) -> R.Tensor((1, 10), dtype="float32"):
        R.func_attr({"num_input": 1})
        cls = Module
        with R.dataflow():
            gv = R.call_tir(cls.fused_transpose_extern_fmatmul32_0_add_relu_transpose1_extern_fmatmul32_1_add1, (fc1_weight, x, fc1_bias, fc2_weight, fc2_bias), out_sinfo=R.Tensor((1, 10), dtype="float32"))
            R.output(gv)
        return gv