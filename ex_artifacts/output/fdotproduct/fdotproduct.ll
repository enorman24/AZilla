; ModuleID = 'TVMMod'
source_filename = "TVMMod"
target datalayout = "e-m:e-p:64:64-i64:64-i128:128-n32:64-S128"
target triple = "riscv64-unknown-elf"

%0 = type { i32, i32, double }
%1 = type { ptr, %2, i32, %3, ptr, ptr, i64 }
%2 = type { i32, i32 }
%3 = type { i8, i8, i16 }

@.str = private constant [10 x i8] c"TypeError\00", align 1
@.str.1 = private constant [10 x i8] c"Expected \00", align 1
@.str.2 = private constant [2 x i8] c"3\00", align 1
@.str.3 = private constant [11 x i8] c" arguments\00", align 1
@.str.4 = private constant [19 x i8] c" when calling:\0A  `\00", align 1
@.str.5 = private constant [89 x i8] c"fdotproduct(a: Tensor([64], float32), b: Tensor([64], float32), c: Tensor([1], float32))\00", align 1
@.str.6 = private constant [2 x i8] c"`\00", align 1
@.str.7 = private constant [21 x i8] c"args pointer is NULL\00", align 1
@.str.8 = private constant [30 x i8] c"Mismatched type on argument #\00", align 1
@.str.9 = private constant [2 x i8] c"0\00", align 1
@.str.10 = private constant [15 x i8] c"`,\0A  expected \00", align 1
@.str.11 = private constant [7 x i8] c"Tensor\00", align 1
@.str.12 = private constant [2 x i8] c"1\00", align 1
@.str.13 = private constant [2 x i8] c"2\00", align 1
@.str.14 = private constant [11 x i8] c"ValueError\00", align 1
@.str.15 = private constant [12 x i8] c"Mismatched \00", align 1
@.str.16 = private constant [2 x i8] c"a\00", align 1
@.str.17 = private constant [20 x i8] c".ndim on argument #\00", align 1
@.str.18 = private constant [21 x i8] c".dtype on argument #\00", align 1
@.str.19 = private constant [8 x i8] c"float32\00", align 1
@.str.20 = private constant [27 x i8] c".device_type on argument #\00", align 1
@.str.21 = private constant [4 x i8] c"cpu\00", align 1
@.str.22 = private constant [2 x i8] c"b\00", align 1
@.str.23 = private constant [2 x i8] c"c\00", align 1
@.str.24 = private constant [23 x i8] c".strides on argument #\00", align 1
@.str.25 = private constant [34 x i8] c"`,\0A  expected to be compact array\00", align 1
@.str.26 = private constant [36 x i8] c" data pointer is NULL on argument #\00", align 1
@.str.27 = private constant [36 x i8] c"`,\0A  expected non-NULL data pointer\00", align 1
@.str.28 = private constant [12 x i8] c"b.device_id\00", align 1
@.str.29 = private constant [15 x i8] c" on argument #\00", align 1
@.str.30 = private constant [24 x i8] c"`,\0A  expected to match \00", align 1
@.str.31 = private constant [12 x i8] c"a.device_id\00", align 1
@.str.32 = private constant [12 x i8] c"c.device_id\00", align 1
@.str.33 = private constant [9 x i8] c"Invalid \00", align 1
@.str.34 = private constant [11 x i8] c"a.shape[0]\00", align 1
@.str.35 = private constant [3 x i8] c"64\00", align 1
@.str.36 = private constant [14 x i8] c"a.byte_offset\00", align 1
@.str.37 = private constant [11 x i8] c"b.shape[0]\00", align 1
@.str.38 = private constant [14 x i8] c"b.byte_offset\00", align 1
@.str.39 = private constant [11 x i8] c"c.shape[0]\00", align 1
@.str.40 = private constant [14 x i8] c"c.byte_offset\00", align 1
@llvm.global_ctors = appending global [0 x { i32, ptr, ptr }] zeroinitializer

define dllexport noundef i32 @__tvm_ffi_fdotproduct(ptr noalias nocapture readnone %self_handle, ptr noalias readonly %args, i32 %num_args, ptr noalias nocapture readnone %result) local_unnamed_addr #0 !dbg !5 {
entry:
  tail call void @llvm.dbg.value(metadata ptr poison, metadata !11, metadata !DIExpression()), !dbg !15
  tail call void @llvm.dbg.value(metadata ptr %args, metadata !12, metadata !DIExpression()), !dbg !15
  tail call void @llvm.dbg.value(metadata i32 %num_args, metadata !13, metadata !DIExpression()), !dbg !15
  tail call void @llvm.dbg.value(metadata ptr poison, metadata !14, metadata !DIExpression()), !dbg !15
  %0 = icmp eq i32 %num_args, 3, !dbg !15
  br i1 %0, label %assert_end, label %assert_fail, !dbg !15, !prof !16

common.ret:                                       ; preds = %assert_end64, %assert_fail63, %assert_fail61, %assert_fail59, %assert_fail57, %assert_fail55, %assert_fail53, %assert_fail51, %assert_fail49, %assert_fail43, %assert_fail41, %assert_fail39, %assert_fail35, %assert_fail33, %assert_fail31, %assert_fail29, %assert_fail27, %assert_fail25, %assert_fail23, %assert_fail21, %assert_fail19, %assert_fail17, %assert_fail15, %assert_fail13, %assert_fail11, %assert_fail9, %assert_fail7, %assert_fail5, %assert_fail3, %assert_fail1, %assert_fail
  %common.ret.op = phi i32 [ -1, %assert_fail ], [ -1, %assert_fail1 ], [ -1, %assert_fail3 ], [ -1, %assert_fail5 ], [ -1, %assert_fail7 ], [ -1, %assert_fail9 ], [ -1, %assert_fail11 ], [ -1, %assert_fail13 ], [ -1, %assert_fail15 ], [ -1, %assert_fail17 ], [ -1, %assert_fail19 ], [ -1, %assert_fail21 ], [ -1, %assert_fail23 ], [ -1, %assert_fail25 ], [ -1, %assert_fail27 ], [ -1, %assert_fail29 ], [ -1, %assert_fail31 ], [ -1, %assert_fail33 ], [ -1, %assert_fail35 ], [ -1, %assert_fail39 ], [ -1, %assert_fail41 ], [ -1, %assert_fail43 ], [ -1, %assert_fail49 ], [ -1, %assert_fail51 ], [ -1, %assert_fail53 ], [ -1, %assert_fail55 ], [ -1, %assert_fail57 ], [ -1, %assert_fail59 ], [ -1, %assert_fail61 ], [ -1, %assert_fail63 ], [ 0, %assert_end64 ]
  ret i32 %common.ret.op, !dbg !15

assert_fail:                                      ; preds = %entry
  tail call fastcc void @__tvm_set_raised_6(ptr nonnull @.str, i32 6, ptr nonnull @.str.1, ptr nonnull @.str.2, ptr nonnull @.str.3, ptr nonnull @.str.4, ptr nonnull @.str.5, ptr nonnull @.str.6), !dbg !15
  br label %common.ret

assert_end:                                       ; preds = %entry
  %.not = icmp eq ptr %args, null, !dbg !15
  br i1 %.not, label %assert_fail1, label %assert_end2, !dbg !15, !prof !17

assert_fail1:                                     ; preds = %assert_end
  tail call fastcc void @__tvm_set_raised_6(ptr nonnull @.str, i32 4, ptr nonnull @.str.7, ptr nonnull @.str.4, ptr nonnull @.str.5, ptr nonnull @.str.6, ptr null, ptr null), !dbg !15
  br label %common.ret

assert_end2:                                      ; preds = %assert_end
  %a_handle.type_index = load i32, ptr %args, align 4, !dbg !15
  call void @llvm.dbg.value(metadata i32 %a_handle.type_index, metadata !18, metadata !DIExpression()), !dbg !15
  call void @llvm.dbg.value(metadata i32 %a_handle.type_index, metadata !18, metadata !DIExpression()), !dbg !15
  %a_handle.type_index.fr = freeze i32 %a_handle.type_index, !dbg !15
  %1 = icmp sgt i32 %a_handle.type_index.fr, 63, !dbg !15
  br i1 %1, label %assert_end4, label %switch.early.test, !dbg !15

switch.early.test:                                ; preds = %assert_end2
  switch i32 %a_handle.type_index.fr, label %assert_fail3 [
    i32 7, label %assert_end4
    i32 4, label %assert_end4
    i32 0, label %assert_end4
  ], !dbg !15

assert_fail3:                                     ; preds = %switch.early.test
  tail call fastcc void @__tvm_set_raised_6(ptr nonnull @.str, i32 6, ptr nonnull @.str.8, ptr nonnull @.str.9, ptr nonnull @.str.4, ptr nonnull @.str.5, ptr nonnull @.str.10, ptr nonnull @.str.11), !dbg !15
  br label %common.ret

assert_end4:                                      ; preds = %switch.early.test, %switch.early.test, %switch.early.test, %assert_end2
  %2 = getelementptr inbounds %0, ptr %args, i64 0, i32 2, !dbg !15
  %3 = load ptr, ptr %2, align 8, !dbg !15
  %4 = icmp eq i32 %a_handle.type_index.fr, 70, !dbg !15
  %a_handle.idx = select i1 %4, i64 24, i64 0, !dbg !15
  %a_handle = getelementptr inbounds i8, ptr %3, i64 %a_handle.idx, !dbg !15
  call void @llvm.dbg.declare(metadata ptr %a_handle, metadata !19, metadata !DIExpression()), !dbg !15
  call void @llvm.dbg.declare(metadata ptr %a_handle, metadata !19, metadata !DIExpression()), !dbg !15
  %5 = getelementptr inbounds %0, ptr %args, i64 1, i32 0, !dbg !15
  %b_handle.type_index = load i32, ptr %5, align 4, !dbg !15
  call void @llvm.dbg.value(metadata i32 %b_handle.type_index, metadata !20, metadata !DIExpression()), !dbg !15
  call void @llvm.dbg.value(metadata i32 %b_handle.type_index, metadata !20, metadata !DIExpression()), !dbg !15
  %b_handle.type_index.fr = freeze i32 %b_handle.type_index, !dbg !15
  %6 = icmp sgt i32 %b_handle.type_index.fr, 63, !dbg !15
  br i1 %6, label %assert_end6, label %switch.early.test65, !dbg !15

switch.early.test65:                              ; preds = %assert_end4
  switch i32 %b_handle.type_index.fr, label %assert_fail5 [
    i32 7, label %assert_end6
    i32 4, label %assert_end6
    i32 0, label %assert_end6
  ], !dbg !15

assert_fail5:                                     ; preds = %switch.early.test65
  tail call fastcc void @__tvm_set_raised_6(ptr nonnull @.str, i32 6, ptr nonnull @.str.8, ptr nonnull @.str.12, ptr nonnull @.str.4, ptr nonnull @.str.5, ptr nonnull @.str.10, ptr nonnull @.str.11), !dbg !15
  br label %common.ret

assert_end6:                                      ; preds = %switch.early.test65, %switch.early.test65, %switch.early.test65, %assert_end4
  %7 = getelementptr inbounds %0, ptr %args, i64 1, i32 2, !dbg !15
  %8 = load ptr, ptr %7, align 8, !dbg !15
  %9 = icmp eq i32 %b_handle.type_index.fr, 70, !dbg !15
  %b_handle.idx = select i1 %9, i64 24, i64 0, !dbg !15
  %b_handle = getelementptr inbounds i8, ptr %8, i64 %b_handle.idx, !dbg !15
  call void @llvm.dbg.declare(metadata ptr %b_handle, metadata !21, metadata !DIExpression()), !dbg !15
  call void @llvm.dbg.declare(metadata ptr %b_handle, metadata !21, metadata !DIExpression()), !dbg !15
  %10 = getelementptr inbounds %0, ptr %args, i64 2, i32 0, !dbg !15
  %c_handle.type_index = load i32, ptr %10, align 4, !dbg !15
  call void @llvm.dbg.value(metadata i32 %c_handle.type_index, metadata !22, metadata !DIExpression()), !dbg !15
  call void @llvm.dbg.value(metadata i32 %c_handle.type_index, metadata !22, metadata !DIExpression()), !dbg !15
  %c_handle.type_index.fr = freeze i32 %c_handle.type_index, !dbg !15
  %11 = icmp sgt i32 %c_handle.type_index.fr, 63, !dbg !15
  br i1 %11, label %assert_end8, label %switch.early.test66, !dbg !15

switch.early.test66:                              ; preds = %assert_end6
  switch i32 %c_handle.type_index.fr, label %assert_fail7 [
    i32 7, label %assert_end8
    i32 4, label %assert_end8
    i32 0, label %assert_end8
  ], !dbg !15

assert_fail7:                                     ; preds = %switch.early.test66
  tail call fastcc void @__tvm_set_raised_6(ptr nonnull @.str, i32 6, ptr nonnull @.str.8, ptr nonnull @.str.13, ptr nonnull @.str.4, ptr nonnull @.str.5, ptr nonnull @.str.10, ptr nonnull @.str.11), !dbg !15
  br label %common.ret

assert_end8:                                      ; preds = %switch.early.test66, %switch.early.test66, %switch.early.test66, %assert_end6
  %12 = getelementptr inbounds %0, ptr %args, i64 2, i32 2, !dbg !15
  %13 = load ptr, ptr %12, align 8, !dbg !15
  %14 = icmp eq i32 %c_handle.type_index.fr, 70, !dbg !15
  %c_handle.idx = select i1 %14, i64 24, i64 0, !dbg !15
  %c_handle = getelementptr inbounds i8, ptr %13, i64 %c_handle.idx, !dbg !15
  call void @llvm.dbg.declare(metadata ptr %c_handle, metadata !23, metadata !DIExpression()), !dbg !15
  call void @llvm.dbg.declare(metadata ptr %c_handle, metadata !23, metadata !DIExpression()), !dbg !15
  %.not67 = icmp eq ptr %3, null, !dbg !15
  br i1 %.not67, label %assert_fail9, label %assert_end10, !dbg !15, !prof !17

assert_fail9:                                     ; preds = %assert_end8
  tail call fastcc void @__tvm_set_raised_6(ptr nonnull @.str, i32 6, ptr nonnull @.str.8, ptr nonnull @.str.9, ptr nonnull @.str.4, ptr nonnull @.str.5, ptr nonnull @.str.10, ptr nonnull @.str.11), !dbg !15
  br label %common.ret

assert_end10:                                     ; preds = %assert_end8
  %15 = getelementptr inbounds %1, ptr %a_handle, i64 0, i32 2, !dbg !15
  %16 = load i32, ptr %15, align 4, !dbg !15
  %17 = icmp eq i32 %16, 1, !dbg !15
  br i1 %17, label %assert_end12, label %assert_fail11, !dbg !15, !prof !16

assert_fail11:                                    ; preds = %assert_end10
  tail call fastcc void @__tvm_set_raised_12(ptr nonnull @.str.14, i32 8, ptr nonnull @.str.15, ptr nonnull @.str.16, ptr nonnull @.str.17, ptr nonnull @.str.9, ptr nonnull @.str.10, ptr nonnull @.str.12), !dbg !15
  br label %common.ret

assert_end12:                                     ; preds = %assert_end10
  %18 = getelementptr inbounds %1, ptr %a_handle, i64 0, i32 3, i32 2, !dbg !15
  %19 = load i16, ptr %18, align 2, !dbg !15
  %20 = icmp eq i16 %19, 1, !dbg !15
  %21 = getelementptr inbounds %1, ptr %a_handle, i64 0, i32 3, i32 1, !dbg !15
  %22 = load i8, ptr %21, align 1, !dbg !15
  %23 = icmp eq i8 %22, 32, !dbg !15
  %24 = getelementptr inbounds %1, ptr %a_handle, i64 0, i32 3, i32 0, !dbg !15
  %25 = load i8, ptr %24, align 1, !dbg !15
  %26 = icmp eq i8 %25, 2, !dbg !15
  %27 = and i1 %23, %26, !dbg !15
  %28 = and i1 %20, %27, !dbg !15
  br i1 %28, label %assert_end14, label %assert_fail13, !dbg !15, !prof !16

assert_fail13:                                    ; preds = %assert_end12
  tail call fastcc void @__tvm_set_raised_12(ptr nonnull @.str, i32 8, ptr nonnull @.str.15, ptr nonnull @.str.16, ptr nonnull @.str.18, ptr nonnull @.str.9, ptr nonnull @.str.10, ptr nonnull @.str.19), !dbg !15
  br label %common.ret

assert_end14:                                     ; preds = %assert_end12
  %29 = getelementptr inbounds %1, ptr %a_handle, i64 0, i32 4, !dbg !15
  %fdotproduct.a_handle_shape = load ptr, ptr %29, align 8, !dbg !15
  call void @llvm.dbg.declare(metadata ptr %fdotproduct.a_handle_shape, metadata !24, metadata !DIExpression()), !dbg !15
  call void @llvm.dbg.declare(metadata ptr %fdotproduct.a_handle_shape, metadata !24, metadata !DIExpression()), !dbg !15
  %30 = getelementptr inbounds %1, ptr %a_handle, i64 0, i32 5, !dbg !15
  %fdotproduct.a_handle_strides = load ptr, ptr %30, align 8, !dbg !15
  call void @llvm.dbg.declare(metadata ptr %fdotproduct.a_handle_strides, metadata !25, metadata !DIExpression()), !dbg !15
  call void @llvm.dbg.declare(metadata ptr %fdotproduct.a_handle_strides, metadata !25, metadata !DIExpression()), !dbg !15
  %31 = getelementptr inbounds %1, ptr %a_handle, i64 0, i32 1, i32 0, !dbg !15
  %32 = load i32, ptr %31, align 4, !dbg !15
  %33 = icmp eq i32 %32, 1, !dbg !15
  br i1 %33, label %assert_end16, label %assert_fail15, !dbg !15, !prof !16

assert_fail15:                                    ; preds = %assert_end14
  tail call fastcc void @__tvm_set_raised_12(ptr nonnull @.str.14, i32 8, ptr nonnull @.str.15, ptr nonnull @.str.16, ptr nonnull @.str.20, ptr nonnull @.str.9, ptr nonnull @.str.10, ptr nonnull @.str.21), !dbg !15
  br label %common.ret

assert_end16:                                     ; preds = %assert_end14
  %34 = getelementptr inbounds %1, ptr %a_handle, i64 0, i32 1, i32 1, !dbg !15
  %dev_id = load i32, ptr %34, align 4, !dbg !15
  call void @llvm.dbg.value(metadata i32 %dev_id, metadata !26, metadata !DIExpression()), !dbg !15
  call void @llvm.dbg.value(metadata i32 %dev_id, metadata !26, metadata !DIExpression()), !dbg !15
  %a = load ptr, ptr %a_handle, align 8, !dbg !15
  call void @llvm.dbg.declare(metadata ptr %a, metadata !27, metadata !DIExpression()), !dbg !15
  call void @llvm.dbg.declare(metadata ptr %a, metadata !27, metadata !DIExpression()), !dbg !15
  call void @llvm.assume(i1 true) [ "align"(ptr %a, i64 64) ], !dbg !15
  %.not68 = icmp eq ptr %8, null, !dbg !15
  br i1 %.not68, label %assert_fail17, label %assert_end18, !dbg !15, !prof !17

assert_fail17:                                    ; preds = %assert_end16
  tail call fastcc void @__tvm_set_raised_6(ptr nonnull @.str, i32 6, ptr nonnull @.str.8, ptr nonnull @.str.12, ptr nonnull @.str.4, ptr nonnull @.str.5, ptr nonnull @.str.10, ptr nonnull @.str.11), !dbg !15
  br label %common.ret

assert_end18:                                     ; preds = %assert_end16
  %35 = getelementptr inbounds %1, ptr %b_handle, i64 0, i32 2, !dbg !15
  %36 = load i32, ptr %35, align 4, !dbg !15
  %37 = icmp eq i32 %36, 1, !dbg !15
  br i1 %37, label %assert_end20, label %assert_fail19, !dbg !15, !prof !16

assert_fail19:                                    ; preds = %assert_end18
  tail call fastcc void @__tvm_set_raised_12(ptr nonnull @.str.14, i32 8, ptr nonnull @.str.15, ptr nonnull @.str.22, ptr nonnull @.str.17, ptr nonnull @.str.12, ptr nonnull @.str.10, ptr nonnull @.str.12), !dbg !15
  br label %common.ret

assert_end20:                                     ; preds = %assert_end18
  %38 = getelementptr inbounds %1, ptr %b_handle, i64 0, i32 3, i32 2, !dbg !15
  %39 = load i16, ptr %38, align 2, !dbg !15
  %40 = icmp eq i16 %39, 1, !dbg !15
  %41 = getelementptr inbounds %1, ptr %b_handle, i64 0, i32 3, i32 1, !dbg !15
  %42 = load i8, ptr %41, align 1, !dbg !15
  %43 = icmp eq i8 %42, 32, !dbg !15
  %44 = getelementptr inbounds %1, ptr %b_handle, i64 0, i32 3, i32 0, !dbg !15
  %45 = load i8, ptr %44, align 1, !dbg !15
  %46 = icmp eq i8 %45, 2, !dbg !15
  %47 = and i1 %43, %46, !dbg !15
  %48 = and i1 %40, %47, !dbg !15
  br i1 %48, label %assert_end22, label %assert_fail21, !dbg !15, !prof !16

assert_fail21:                                    ; preds = %assert_end20
  tail call fastcc void @__tvm_set_raised_12(ptr nonnull @.str, i32 8, ptr nonnull @.str.15, ptr nonnull @.str.22, ptr nonnull @.str.18, ptr nonnull @.str.12, ptr nonnull @.str.10, ptr nonnull @.str.19), !dbg !15
  br label %common.ret

assert_end22:                                     ; preds = %assert_end20
  %49 = getelementptr inbounds %1, ptr %b_handle, i64 0, i32 4, !dbg !15
  %fdotproduct.b_handle_shape = load ptr, ptr %49, align 8, !dbg !15
  call void @llvm.dbg.declare(metadata ptr %fdotproduct.b_handle_shape, metadata !30, metadata !DIExpression()), !dbg !15
  call void @llvm.dbg.declare(metadata ptr %fdotproduct.b_handle_shape, metadata !30, metadata !DIExpression()), !dbg !15
  %50 = getelementptr inbounds %1, ptr %b_handle, i64 0, i32 5, !dbg !15
  %fdotproduct.b_handle_strides = load ptr, ptr %50, align 8, !dbg !15
  call void @llvm.dbg.declare(metadata ptr %fdotproduct.b_handle_strides, metadata !31, metadata !DIExpression()), !dbg !15
  call void @llvm.dbg.declare(metadata ptr %fdotproduct.b_handle_strides, metadata !31, metadata !DIExpression()), !dbg !15
  %51 = getelementptr inbounds %1, ptr %b_handle, i64 0, i32 1, i32 0, !dbg !15
  %52 = load i32, ptr %51, align 4, !dbg !15
  %53 = icmp eq i32 %52, 1, !dbg !15
  br i1 %53, label %assert_end24, label %assert_fail23, !dbg !15, !prof !16

assert_fail23:                                    ; preds = %assert_end22
  tail call fastcc void @__tvm_set_raised_12(ptr nonnull @.str.14, i32 8, ptr nonnull @.str.15, ptr nonnull @.str.22, ptr nonnull @.str.20, ptr nonnull @.str.12, ptr nonnull @.str.10, ptr nonnull @.str.21), !dbg !15
  br label %common.ret

assert_end24:                                     ; preds = %assert_end22
  %b = load ptr, ptr %b_handle, align 8, !dbg !15
  call void @llvm.dbg.declare(metadata ptr %b, metadata !32, metadata !DIExpression()), !dbg !15
  call void @llvm.dbg.declare(metadata ptr %b, metadata !32, metadata !DIExpression()), !dbg !15
  call void @llvm.assume(i1 true) [ "align"(ptr %b, i64 64) ], !dbg !15
  %.not69 = icmp eq ptr %13, null, !dbg !15
  br i1 %.not69, label %assert_fail25, label %assert_end26, !dbg !15, !prof !17

assert_fail25:                                    ; preds = %assert_end24
  tail call fastcc void @__tvm_set_raised_6(ptr nonnull @.str, i32 6, ptr nonnull @.str.8, ptr nonnull @.str.13, ptr nonnull @.str.4, ptr nonnull @.str.5, ptr nonnull @.str.10, ptr nonnull @.str.11), !dbg !15
  br label %common.ret

assert_end26:                                     ; preds = %assert_end24
  %54 = getelementptr inbounds %1, ptr %c_handle, i64 0, i32 2, !dbg !15
  %55 = load i32, ptr %54, align 4, !dbg !15
  %56 = icmp eq i32 %55, 1, !dbg !15
  br i1 %56, label %assert_end28, label %assert_fail27, !dbg !15, !prof !16

assert_fail27:                                    ; preds = %assert_end26
  tail call fastcc void @__tvm_set_raised_12(ptr nonnull @.str.14, i32 8, ptr nonnull @.str.15, ptr nonnull @.str.23, ptr nonnull @.str.17, ptr nonnull @.str.13, ptr nonnull @.str.10, ptr nonnull @.str.12), !dbg !15
  br label %common.ret

assert_end28:                                     ; preds = %assert_end26
  %57 = getelementptr inbounds %1, ptr %c_handle, i64 0, i32 3, i32 2, !dbg !15
  %58 = load i16, ptr %57, align 2, !dbg !15
  %59 = icmp eq i16 %58, 1, !dbg !15
  %60 = getelementptr inbounds %1, ptr %c_handle, i64 0, i32 3, i32 1, !dbg !15
  %61 = load i8, ptr %60, align 1, !dbg !15
  %62 = icmp eq i8 %61, 32, !dbg !15
  %63 = getelementptr inbounds %1, ptr %c_handle, i64 0, i32 3, i32 0, !dbg !15
  %64 = load i8, ptr %63, align 1, !dbg !15
  %65 = icmp eq i8 %64, 2, !dbg !15
  %66 = and i1 %62, %65, !dbg !15
  %67 = and i1 %59, %66, !dbg !15
  br i1 %67, label %assert_end30, label %assert_fail29, !dbg !15, !prof !16

assert_fail29:                                    ; preds = %assert_end28
  tail call fastcc void @__tvm_set_raised_12(ptr nonnull @.str, i32 8, ptr nonnull @.str.15, ptr nonnull @.str.23, ptr nonnull @.str.18, ptr nonnull @.str.13, ptr nonnull @.str.10, ptr nonnull @.str.19), !dbg !15
  br label %common.ret

assert_end30:                                     ; preds = %assert_end28
  %68 = getelementptr inbounds %1, ptr %c_handle, i64 0, i32 4, !dbg !15
  %fdotproduct.c_handle_shape = load ptr, ptr %68, align 8, !dbg !15
  call void @llvm.dbg.declare(metadata ptr %fdotproduct.c_handle_shape, metadata !33, metadata !DIExpression()), !dbg !15
  call void @llvm.dbg.declare(metadata ptr %fdotproduct.c_handle_shape, metadata !33, metadata !DIExpression()), !dbg !15
  call void @llvm.dbg.declare(metadata ptr poison, metadata !34, metadata !DIExpression()), !dbg !15
  call void @llvm.dbg.declare(metadata ptr poison, metadata !34, metadata !DIExpression()), !dbg !15
  %69 = getelementptr inbounds %1, ptr %c_handle, i64 0, i32 1, i32 0, !dbg !15
  %70 = load i32, ptr %69, align 4, !dbg !15
  %71 = icmp eq i32 %70, 1, !dbg !15
  br i1 %71, label %assert_end32, label %assert_fail31, !dbg !15, !prof !16

assert_fail31:                                    ; preds = %assert_end30
  tail call fastcc void @__tvm_set_raised_12(ptr nonnull @.str.14, i32 8, ptr nonnull @.str.15, ptr nonnull @.str.23, ptr nonnull @.str.20, ptr nonnull @.str.13, ptr nonnull @.str.10, ptr nonnull @.str.21), !dbg !15
  br label %common.ret

assert_end32:                                     ; preds = %assert_end30
  %c = load ptr, ptr %c_handle, align 8, !dbg !15
  call void @llvm.dbg.declare(metadata ptr %c, metadata !35, metadata !DIExpression()), !dbg !15
  call void @llvm.dbg.declare(metadata ptr %c, metadata !35, metadata !DIExpression()), !dbg !15
  call void @llvm.assume(i1 true) [ "align"(ptr %c, i64 64) ], !dbg !15
  %.not70 = icmp eq ptr %fdotproduct.a_handle_strides, null, !dbg !15
  br i1 %.not70, label %if_end, label %if_then, !dbg !15, !prof !17

if_then:                                          ; preds = %assert_end32
  %72 = load i64, ptr %fdotproduct.a_handle_strides, align 8, !dbg !15
  %73 = and i64 %72, 4294967295, !dbg !15
  %74 = icmp eq i64 %73, 1, !dbg !15
  br i1 %74, label %if_end, label %assert_fail33, !dbg !15, !prof !16

if_end:                                           ; preds = %if_then, %assert_end32
  %.not71 = icmp eq ptr %a, null, !dbg !15
  br i1 %.not71, label %assert_fail35, label %assert_end36, !dbg !15, !prof !17

assert_fail33:                                    ; preds = %if_then
  tail call fastcc void @__tvm_set_raised_12(ptr nonnull @.str.14, i32 7, ptr nonnull @.str.15, ptr nonnull @.str.16, ptr nonnull @.str.24, ptr nonnull @.str.9, ptr nonnull @.str.25, ptr null), !dbg !15
  br label %common.ret

assert_fail35:                                    ; preds = %if_end
  tail call fastcc void @__tvm_set_raised_6(ptr nonnull @.str.14, i32 6, ptr nonnull @.str.16, ptr nonnull @.str.26, ptr nonnull @.str.9, ptr nonnull @.str.4, ptr nonnull @.str.5, ptr nonnull @.str.27), !dbg !15
  br label %common.ret

assert_end36:                                     ; preds = %if_end
  %.not72 = icmp eq ptr %fdotproduct.b_handle_strides, null, !dbg !15
  br i1 %.not72, label %if_end38, label %if_then37, !dbg !15, !prof !17

if_then37:                                        ; preds = %assert_end36
  %75 = load i64, ptr %fdotproduct.b_handle_strides, align 8, !dbg !15
  %76 = and i64 %75, 4294967295, !dbg !15
  %77 = icmp eq i64 %76, 1, !dbg !15
  br i1 %77, label %if_end38, label %assert_fail39, !dbg !15, !prof !16

if_end38:                                         ; preds = %if_then37, %assert_end36
  %78 = getelementptr inbounds %1, ptr %b_handle, i64 0, i32 1, i32 1, !dbg !15
  %79 = load i32, ptr %78, align 4, !dbg !15
  %80 = icmp eq i32 %dev_id, %79, !dbg !15
  br i1 %80, label %assert_end42, label %assert_fail41, !dbg !15, !prof !16

assert_fail39:                                    ; preds = %if_then37
  tail call fastcc void @__tvm_set_raised_12(ptr nonnull @.str.14, i32 7, ptr nonnull @.str.15, ptr nonnull @.str.22, ptr nonnull @.str.24, ptr nonnull @.str.12, ptr nonnull @.str.25, ptr null), !dbg !15
  br label %common.ret

assert_fail41:                                    ; preds = %if_end38
  tail call fastcc void @__tvm_set_raised_12(ptr nonnull @.str.14, i32 8, ptr nonnull @.str.15, ptr nonnull @.str.28, ptr nonnull @.str.29, ptr nonnull @.str.12, ptr nonnull @.str.30, ptr nonnull @.str.31), !dbg !15
  br label %common.ret

assert_end42:                                     ; preds = %if_end38
  %.not73 = icmp eq ptr %b, null, !dbg !15
  br i1 %.not73, label %assert_fail43, label %if_end46, !dbg !15, !prof !17

assert_fail43:                                    ; preds = %assert_end42
  tail call fastcc void @__tvm_set_raised_6(ptr nonnull @.str.14, i32 6, ptr nonnull @.str.22, ptr nonnull @.str.26, ptr nonnull @.str.12, ptr nonnull @.str.4, ptr nonnull @.str.5, ptr nonnull @.str.27), !dbg !15
  br label %common.ret

if_end46:                                         ; preds = %assert_end42
  %81 = getelementptr inbounds %1, ptr %c_handle, i64 0, i32 1, i32 1, !dbg !15
  %82 = load i32, ptr %81, align 4, !dbg !15
  %83 = icmp eq i32 %dev_id, %82, !dbg !15
  br i1 %83, label %assert_end50, label %assert_fail49, !dbg !15, !prof !16

assert_fail49:                                    ; preds = %if_end46
  tail call fastcc void @__tvm_set_raised_12(ptr nonnull @.str.14, i32 8, ptr nonnull @.str.15, ptr nonnull @.str.32, ptr nonnull @.str.29, ptr nonnull @.str.13, ptr nonnull @.str.30, ptr nonnull @.str.31), !dbg !15
  br label %common.ret

assert_end50:                                     ; preds = %if_end46
  %.not74 = icmp eq ptr %c, null, !dbg !15
  br i1 %.not74, label %assert_fail51, label %assert_end52, !dbg !15, !prof !17

assert_fail51:                                    ; preds = %assert_end50
  tail call fastcc void @__tvm_set_raised_6(ptr nonnull @.str.14, i32 6, ptr nonnull @.str.23, ptr nonnull @.str.26, ptr nonnull @.str.13, ptr nonnull @.str.4, ptr nonnull @.str.5, ptr nonnull @.str.27), !dbg !15
  br label %common.ret

assert_end52:                                     ; preds = %assert_end50
  %84 = load i64, ptr %fdotproduct.a_handle_shape, align 8, !dbg !15
  %85 = and i64 %84, 4294967295, !dbg !15
  %86 = icmp eq i64 %85, 64, !dbg !15
  br i1 %86, label %assert_end54, label %assert_fail53, !dbg !15, !prof !16

assert_fail53:                                    ; preds = %assert_end52
  tail call fastcc void @__tvm_set_raised_12(ptr nonnull @.str.14, i32 8, ptr nonnull @.str.33, ptr nonnull @.str.34, ptr nonnull @.str.29, ptr nonnull @.str.9, ptr nonnull @.str.10, ptr nonnull @.str.35), !dbg !15
  br label %common.ret

assert_end54:                                     ; preds = %assert_end52
  %87 = getelementptr inbounds %1, ptr %a_handle, i64 0, i32 6, !dbg !15
  %88 = load i64, ptr %87, align 8, !dbg !15
  %89 = icmp eq i64 %88, 0, !dbg !15
  br i1 %89, label %assert_end56, label %assert_fail55, !dbg !15, !prof !16

assert_fail55:                                    ; preds = %assert_end54
  tail call fastcc void @__tvm_set_raised_12(ptr nonnull @.str.14, i32 8, ptr nonnull @.str.33, ptr nonnull @.str.36, ptr nonnull @.str.29, ptr nonnull @.str.9, ptr nonnull @.str.10, ptr nonnull @.str.9), !dbg !15
  br label %common.ret

assert_end56:                                     ; preds = %assert_end54
  %90 = load i64, ptr %fdotproduct.b_handle_shape, align 8, !dbg !15
  %91 = and i64 %90, 4294967295, !dbg !15
  %92 = icmp eq i64 %91, 64, !dbg !15
  br i1 %92, label %assert_end58, label %assert_fail57, !dbg !15, !prof !16

assert_fail57:                                    ; preds = %assert_end56
  tail call fastcc void @__tvm_set_raised_12(ptr nonnull @.str.14, i32 8, ptr nonnull @.str.33, ptr nonnull @.str.37, ptr nonnull @.str.29, ptr nonnull @.str.12, ptr nonnull @.str.10, ptr nonnull @.str.35), !dbg !15
  br label %common.ret

assert_end58:                                     ; preds = %assert_end56
  %93 = getelementptr inbounds %1, ptr %b_handle, i64 0, i32 6, !dbg !15
  %94 = load i64, ptr %93, align 8, !dbg !15
  %95 = icmp eq i64 %94, 0, !dbg !15
  br i1 %95, label %assert_end60, label %assert_fail59, !dbg !15, !prof !16

assert_fail59:                                    ; preds = %assert_end58
  tail call fastcc void @__tvm_set_raised_12(ptr nonnull @.str.14, i32 8, ptr nonnull @.str.33, ptr nonnull @.str.38, ptr nonnull @.str.29, ptr nonnull @.str.12, ptr nonnull @.str.10, ptr nonnull @.str.9), !dbg !15
  br label %common.ret

assert_end60:                                     ; preds = %assert_end58
  %96 = load i64, ptr %fdotproduct.c_handle_shape, align 8, !dbg !15
  %97 = and i64 %96, 4294967295, !dbg !15
  %98 = icmp eq i64 %97, 1, !dbg !15
  br i1 %98, label %assert_end62, label %assert_fail61, !dbg !15, !prof !16

assert_fail61:                                    ; preds = %assert_end60
  tail call fastcc void @__tvm_set_raised_12(ptr nonnull @.str.14, i32 8, ptr nonnull @.str.33, ptr nonnull @.str.39, ptr nonnull @.str.29, ptr nonnull @.str.13, ptr nonnull @.str.10, ptr nonnull @.str.12), !dbg !15
  br label %common.ret

assert_end62:                                     ; preds = %assert_end60
  %99 = getelementptr inbounds %1, ptr %c_handle, i64 0, i32 6, !dbg !15
  %100 = load i64, ptr %99, align 8, !dbg !15
  %101 = icmp eq i64 %100, 0, !dbg !15
  br i1 %101, label %assert_end64, label %assert_fail63, !dbg !15, !prof !16

assert_fail63:                                    ; preds = %assert_end62
  tail call fastcc void @__tvm_set_raised_12(ptr nonnull @.str.14, i32 8, ptr nonnull @.str.33, ptr nonnull @.str.40, ptr nonnull @.str.29, ptr nonnull @.str.13, ptr nonnull @.str.10, ptr nonnull @.str.9), !dbg !15
  br label %common.ret

assert_end64:                                     ; preds = %assert_end62
  tail call fastcc void @fdotproduct_compute_(ptr nonnull %c, ptr nonnull %a, ptr nonnull %b), !dbg !15
  br label %common.ret
}

; Function Attrs: noinline
define internal fastcc void @__tvm_set_raised_6(ptr %0, i32 %1, ptr %2, ptr %3, ptr %4, ptr %5, ptr %6, ptr %7) unnamed_addr #1 {
entry:
  %8 = alloca [6 x ptr], align 8
  store ptr %2, ptr %8, align 8
  %9 = getelementptr inbounds [6 x ptr], ptr %8, i64 0, i64 1
  store ptr %3, ptr %9, align 8
  %10 = getelementptr inbounds [6 x ptr], ptr %8, i64 0, i64 2
  store ptr %4, ptr %10, align 8
  %11 = getelementptr inbounds [6 x ptr], ptr %8, i64 0, i64 3
  store ptr %5, ptr %11, align 8
  %12 = getelementptr inbounds [6 x ptr], ptr %8, i64 0, i64 4
  store ptr %6, ptr %12, align 8
  %13 = getelementptr inbounds [6 x ptr], ptr %8, i64 0, i64 5
  store ptr %7, ptr %13, align 8
  call void @TVMFFIErrorSetRaisedFromCStrParts(ptr %0, ptr nonnull %8, i32 %1)
  ret void
}

declare void @TVMFFIErrorSetRaisedFromCStrParts(ptr, ptr, i32) local_unnamed_addr

; Function Attrs: mustprogress nocallback nofree nosync nounwind speculatable willreturn memory(none)
declare void @llvm.dbg.value(metadata, metadata, metadata) #2

; Function Attrs: mustprogress nocallback nofree nosync nounwind speculatable willreturn memory(none)
declare void @llvm.dbg.declare(metadata, metadata, metadata) #2

; Function Attrs: noinline
define internal fastcc void @__tvm_set_raised_12(ptr %0, i32 %1, ptr %2, ptr %3, ptr %4, ptr %5, ptr %6, ptr %7) unnamed_addr #1 {
entry:
  %8 = alloca [12 x ptr], align 8
  store ptr %2, ptr %8, align 8
  %9 = getelementptr inbounds [12 x ptr], ptr %8, i64 0, i64 1
  store ptr %3, ptr %9, align 8
  %10 = getelementptr inbounds [12 x ptr], ptr %8, i64 0, i64 2
  store ptr %4, ptr %10, align 8
  %11 = getelementptr inbounds [12 x ptr], ptr %8, i64 0, i64 3
  store ptr %5, ptr %11, align 8
  %12 = getelementptr inbounds [12 x ptr], ptr %8, i64 0, i64 4
  store ptr @.str.4, ptr %12, align 8
  %13 = getelementptr inbounds [12 x ptr], ptr %8, i64 0, i64 5
  store ptr @.str.5, ptr %13, align 8
  %14 = getelementptr inbounds [12 x ptr], ptr %8, i64 0, i64 6
  store ptr %6, ptr %14, align 8
  %15 = getelementptr inbounds [12 x ptr], ptr %8, i64 0, i64 7
  store ptr %7, ptr %15, align 8
  %16 = getelementptr inbounds [12 x ptr], ptr %8, i64 0, i64 8
  call void @llvm.memset.p0.i64(ptr noundef nonnull align 8 dereferenceable(32) %16, i8 0, i64 32, i1 false)
  call void @TVMFFIErrorSetRaisedFromCStrParts(ptr %0, ptr nonnull %8, i32 %1)
  ret void
}

; Function Attrs: mustprogress nocallback nofree nosync nounwind willreturn memory(inaccessiblemem: write)
declare void @llvm.assume(i1 noundef) #3

; Function Attrs: noinline
define internal fastcc void @fdotproduct_compute_(ptr noalias nocapture writeonly align 64 %c, ptr noalias align 64 %a, ptr noalias align 64 %b) unnamed_addr #4 !dbg !36 {
entry:
  tail call void @llvm.dbg.value(metadata ptr %c, metadata !40, metadata !DIExpression()), !dbg !43
  tail call void @llvm.dbg.value(metadata ptr %a, metadata !41, metadata !DIExpression()), !dbg !43
  tail call void @llvm.dbg.value(metadata ptr %b, metadata !42, metadata !DIExpression()), !dbg !43
  %0 = tail call float @fdotp_v32b(ptr %a, ptr %b, i64 64), !dbg !43
  store float %0, ptr %c, align 64, !dbg !43, !tbaa !44
  ret void, !dbg !43
}

declare float @fdotp_v32b(ptr, ptr, i64) local_unnamed_addr

define weak dllexport i32 @__tvm_ffi_main(ptr %0, ptr %1, i32 %2, ptr %3) local_unnamed_addr {
entry:
  %4 = tail call i32 @__tvm_ffi_fdotproduct(ptr poison, ptr %1, i32 %2, ptr poison), !dbg !15, !range !56
  ret i32 %4, !dbg !15
}

; Function Attrs: nofree nosync nounwind memory(none)
define weak dso_local i16 @__truncsfhf2(float %a0) local_unnamed_addr #5 section ".text.tvm.fp16.conv" {
b0:
  %v0 = bitcast float %a0 to i32
  %0 = tail call float @llvm.fabs.f32(float %a0)
  %v1 = bitcast float %0 to i32
  %v2 = add nsw i32 %v1, -947912704
  %v3 = add nsw i32 %v1, -1199570944
  %v4 = icmp ult i32 %v2, %v3
  br i1 %v4, label %b1, label %b5

b1:                                               ; preds = %b0
  %v5 = lshr i32 %v0, 13
  %v6 = and i32 %v5, 65535
  %v7 = add nuw nsw i32 %v6, -114688
  %v8 = and i32 %v0, 8191
  %v9 = icmp ugt i32 %v8, 4096
  br i1 %v9, label %b2, label %b3

b2:                                               ; preds = %b1
  %v10 = add nuw nsw i32 %v6, -114687
  br label %b13

b3:                                               ; preds = %b1
  %v11 = icmp eq i32 %v8, 4096
  br i1 %v11, label %b4, label %b13

b4:                                               ; preds = %b3
  %v12 = and i32 %v7, 65535
  %v13 = and i32 %v5, 1
  %v14 = add nuw nsw i32 %v12, %v13
  br label %b13

b5:                                               ; preds = %b0
  %v15 = icmp ugt i32 %v1, 2139095040
  br i1 %v15, label %b6, label %b7

b6:                                               ; preds = %b5
  %v16 = lshr i32 %v0, 13
  %v17 = and i32 %v16, 511
  %v18 = or disjoint i32 %v17, 32256
  br label %b13

b7:                                               ; preds = %b5
  %v19 = icmp ugt i32 %v1, 1199570943
  br i1 %v19, label %b13, label %b8

b8:                                               ; preds = %b7
  %v20 = icmp ult i32 %v1, 754974720
  br i1 %v20, label %b13, label %b9

b9:                                               ; preds = %b8
  %v21 = lshr i32 %v1, 23
  %v22 = sub nsw i32 113, %v21
  %v23 = and i32 %v0, 8388607
  %v24 = or disjoint i32 %v23, 8388608
  %v25 = add nsw i32 %v21, -81
  %v26 = shl i32 %v24, %v25
  %v27 = icmp ne i32 %v26, 0
  %v28 = lshr i32 %v24, %v22
  %v29 = zext i1 %v27 to i32
  %v30 = lshr i32 %v28, 13
  %v31 = and i32 %v28, 8191
  %v32 = or i32 %v31, %v29
  %v33 = icmp ugt i32 %v32, 4096
  br i1 %v33, label %b10, label %b11

b10:                                              ; preds = %b9
  %v34 = add nuw nsw i32 %v30, 1
  br label %b13

b11:                                              ; preds = %b9
  %v35 = icmp eq i32 %v32, 4096
  br i1 %v35, label %b12, label %b13

b12:                                              ; preds = %b11
  %v36 = and i32 %v30, 1
  %v37 = add nuw nsw i32 %v36, %v30
  br label %b13

b13:                                              ; preds = %b12, %b11, %b10, %b8, %b7, %b6, %b4, %b3, %b2
  %v38 = phi i32 [ %v18, %b6 ], [ %v10, %b2 ], [ %v14, %b4 ], [ %v7, %b3 ], [ 31744, %b7 ], [ 0, %b8 ], [ %v34, %b10 ], [ %v37, %b12 ], [ %v30, %b11 ]
  %v39 = lshr i32 %v0, 16
  %v40 = and i32 %v39, 32768
  %v41 = or i32 %v38, %v40
  %vlast = trunc i32 %v41 to i16
  ret i16 %vlast
}

; Function Attrs: nofree nosync nounwind memory(none)
define weak dso_local float @__extendhfsf2(i16 %a0) local_unnamed_addr #5 section ".text.tvm.fp16.conv" {
b0:
  %v1 = and i16 %a0, 32767
  %v2 = zext nneg i16 %v1 to i32
  %v3 = add nsw i16 %v1, -1024
  %v4 = icmp ult i16 %v3, 30720
  br i1 %v4, label %b1, label %b2

b1:                                               ; preds = %b0
  %v5 = shl nuw nsw i32 %v2, 13
  %v6 = add nuw nsw i32 %v5, 939524096
  br label %b6

b2:                                               ; preds = %b0
  %v7 = icmp ugt i16 %v1, 31743
  br i1 %v7, label %b3, label %b4

b3:                                               ; preds = %b2
  %v8 = shl nuw nsw i32 %v2, 13
  %v9 = or i32 %v8, 2139095040
  br label %b6

b4:                                               ; preds = %b2
  %v10 = icmp eq i16 %v1, 0
  br i1 %v10, label %b6, label %b5

b5:                                               ; preds = %b4
  %v11 = icmp ult i16 %v1, 256
  %v12 = lshr i32 %v2, 8
  %v13 = select i1 %v11, i32 %v2, i32 %v12
  %v14 = select i1 %v11, i32 32, i32 24
  %v15 = icmp ult i32 %v13, 16
  %v16 = lshr i32 %v13, 4
  %v17 = add nsw i32 %v14, -4
  %v18 = select i1 %v15, i32 %v13, i32 %v16
  %v19 = select i1 %v15, i32 %v14, i32 %v17
  %v20 = icmp ult i32 %v18, 4
  %v21 = lshr i32 %v18, 2
  %v22 = add nsw i32 %v19, -2
  %v23 = select i1 %v20, i32 %v18, i32 %v21
  %v24 = select i1 %v20, i32 %v19, i32 %v22
  %v25 = icmp ult i32 %v23, 2
  %v26 = sub nsw i32 0, %v23
  %v27 = select i1 %v25, i32 %v26, i32 -2
  %v28 = add nsw i32 %v27, %v24
  %v29 = add nsw i32 %v28, -8
  %v30 = shl i32 %v2, %v29
  %v31 = xor i32 %v30, 8388608
  %v32 = shl i32 %v28, 23
  %v33 = sub i32 1124073472, %v32
  %v34 = or i32 %v31, %v33
  br label %b6

b6:                                               ; preds = %b5, %b4, %b3, %b1
  %v35 = phi i32 [ %v6, %b1 ], [ %v9, %b3 ], [ %v34, %b5 ], [ 0, %b4 ]
  %v36 = and i16 %a0, -32768
  %v37 = zext i16 %v36 to i32
  %v38 = shl nuw i32 %v37, 16
  %v39 = or i32 %v35, %v38
  %v40 = bitcast i32 %v39 to float
  ret float %v40
}

; Function Attrs: nocallback nofree nosync nounwind speculatable willreturn memory(none)
declare float @llvm.fabs.f32(float) #6

; Function Attrs: nocallback nofree nounwind willreturn memory(argmem: write)
declare void @llvm.memset.p0.i64(ptr nocapture writeonly, i8, i64, i1 immarg) #7

attributes #0 = { "target-cpu"="generic" "target-features"="+v,+m,+f,+d" }
attributes #1 = { noinline }
attributes #2 = { mustprogress nocallback nofree nosync nounwind speculatable willreturn memory(none) }
attributes #3 = { mustprogress nocallback nofree nosync nounwind willreturn memory(inaccessiblemem: write) }
attributes #4 = { noinline "target-cpu"="generic" "target-features"="+v,+m,+f,+d" }
attributes #5 = { nofree nosync nounwind memory(none) "target-cpu"="generic" "target-features"="+v,+m,+f,+d" }
attributes #6 = { nocallback nofree nosync nounwind speculatable willreturn memory(none) }
attributes #7 = { nocallback nofree nounwind willreturn memory(argmem: write) }

!llvm.dbg.cu = !{!0}
!llvm.module.flags = !{!2, !3, !4}

!0 = distinct !DICompileUnit(language: DW_LANG_C, file: !1, producer: "TVM", isOptimized: false, runtimeVersion: 0, emissionKind: FullDebug)
!1 = !DIFile(filename: "IRModule.CodeGenLLVM", directory: ".")
!2 = !{i32 2, !"tvm_target", !"{\22kind\22:\22llvm\22,\22mtriple\22:\22riscv64-unknown-elf\22,\22mattr\22:[\22+v\22,\22+m\22,\22+f\22,\22+d\22],\22mabi\22:\22lp64d\22}"}
!3 = !{i32 4, !"Debug Info Version", i32 3}
!4 = !{i32 4, !"Dwarf Version", i32 4}
!5 = distinct !DISubprogram(name: "__tvm_ffi_fdotproduct", scope: !1, file: !1, type: !6, flags: DIFlagPrototyped, spFlags: DISPFlagLocalToUnit | DISPFlagDefinition | DISPFlagOptimized, unit: !0, retainedNodes: !10)
!6 = !DISubroutineType(types: !7)
!7 = !{!8, !9, !9, !8, !9}
!8 = !DIBasicType(name: "int32", size: 32, encoding: DW_ATE_signed)
!9 = !DIDerivedType(tag: DW_TAG_pointer_type, baseType: null)
!10 = !{!11, !12, !13, !14}
!11 = !DILocalVariable(name: "self_handle", arg: 1, scope: !5, file: !1, type: !9)
!12 = !DILocalVariable(name: "args", arg: 2, scope: !5, file: !1, type: !9)
!13 = !DILocalVariable(name: "num_args", arg: 3, scope: !5, file: !1, type: !8)
!14 = !DILocalVariable(name: "result", arg: 4, scope: !5, file: !1, type: !9)
!15 = !DILocation(line: 0, scope: !5)
!16 = !{!"branch_weights", i32 1048576, i32 1}
!17 = !{!"branch_weights", i32 1, i32 1048576}
!18 = !DILocalVariable(name: "a_handle.type_index", scope: !5, file: !1, type: !8)
!19 = !DILocalVariable(name: "a_handle", scope: !5, file: !1, type: !9)
!20 = !DILocalVariable(name: "b_handle.type_index", scope: !5, file: !1, type: !8)
!21 = !DILocalVariable(name: "b_handle", scope: !5, file: !1, type: !9)
!22 = !DILocalVariable(name: "c_handle.type_index", scope: !5, file: !1, type: !8)
!23 = !DILocalVariable(name: "c_handle", scope: !5, file: !1, type: !9)
!24 = !DILocalVariable(name: "fdotproduct.a_handle_shape", scope: !5, file: !1, type: !9)
!25 = !DILocalVariable(name: "fdotproduct.a_handle_strides", scope: !5, file: !1, type: !9)
!26 = !DILocalVariable(name: "dev_id", scope: !5, file: !1, type: !8)
!27 = !DILocalVariable(name: "a", scope: !5, file: !1, type: !28)
!28 = !DIDerivedType(tag: DW_TAG_pointer_type, baseType: !29)
!29 = !DIBasicType(name: "float32", size: 32, encoding: DW_ATE_float)
!30 = !DILocalVariable(name: "fdotproduct.b_handle_shape", scope: !5, file: !1, type: !9)
!31 = !DILocalVariable(name: "fdotproduct.b_handle_strides", scope: !5, file: !1, type: !9)
!32 = !DILocalVariable(name: "b", scope: !5, file: !1, type: !28)
!33 = !DILocalVariable(name: "fdotproduct.c_handle_shape", scope: !5, file: !1, type: !9)
!34 = !DILocalVariable(name: "fdotproduct.c_handle_strides", scope: !5, file: !1, type: !9)
!35 = !DILocalVariable(name: "c", scope: !5, file: !1, type: !28)
!36 = distinct !DISubprogram(name: "fdotproduct_compute_", scope: !1, file: !1, type: !37, flags: DIFlagPrototyped, spFlags: DISPFlagLocalToUnit | DISPFlagDefinition | DISPFlagOptimized, unit: !0, retainedNodes: !39)
!37 = !DISubroutineType(cc: DW_CC_nocall, types: !38)
!38 = !{!8, !28, !28, !28}
!39 = !{!40, !41, !42}
!40 = !DILocalVariable(name: "c", arg: 1, scope: !36, file: !1, type: !28)
!41 = !DILocalVariable(name: "a", arg: 2, scope: !36, file: !1, type: !28)
!42 = !DILocalVariable(name: "b", arg: 3, scope: !36, file: !1, type: !28)
!43 = !DILocation(line: 0, scope: !36)
!44 = !{!45, !45, i64 0}
!45 = !{!"0x18abb60.w4.b0", !46, i64 0}
!46 = !{!"0x18abb60.w8.b0", !47, i64 0}
!47 = !{!"0x18abb60.w16.b0", !48, i64 0}
!48 = !{!"0x18abb60.w32.b0", !49, i64 0}
!49 = !{!"0x18abb60.w64.b0", !50, i64 0}
!50 = !{!"0x18abb60.w128.b0", !51, i64 0}
!51 = !{!"0x18abb60.w256.b0", !52, i64 0}
!52 = !{!"0x18abb60.w512.b0", !53, i64 0}
!53 = !{!"0x18abb60.w1024.b0", !54, i64 0}
!54 = !{!"0x18abb60", !55, i64 0}
!55 = !{!"tvm-tbaa"}
!56 = !{i32 -1, i32 1}
