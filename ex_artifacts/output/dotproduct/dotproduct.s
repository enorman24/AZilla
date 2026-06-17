	.text
	.attribute	4, 16
	.attribute	5, "rv64i2p1_m2p0_f2p2_d2p2_v1p0_zicsr2p0_zve32f1p0_zve32x1p0_zve64d1p0_zve64f1p0_zve64x1p0_zvl128b1p0_zvl32b1p0_zvl64b1p0"
	.file	"TVMMod"
	.globl	__tvm_ffi_dotproduct
	.p2align	2
	.type	__tvm_ffi_dotproduct,@function
__tvm_ffi_dotproduct:
.Lfunc_begin0:
	.file	1 "." "IRModule.CodeGenLLVM"
	.loc	1 0 0
	.cfi_startproc
	addi	sp, sp, -16
	.cfi_def_cfa_offset 16
	sd	ra, 8(sp)
	.cfi_offset ra, -8
	sext.w	a2, a2
.Ltmp0:
	li	a0, 3
.Ltmp1:
	bne	a2, a0, .LBB0_50
.Ltmp2:
	beqz	a1, .LBB0_51
.Ltmp3:
	lw	a3, 0(a1)
.Ltmp4:
	li	a0, 63
	blt	a0, a3, .LBB0_5
.Ltmp5:
	li	a2, 7
	bltu	a2, a3, .LBB0_45
.Ltmp6:
	li	a2, 145
	srl	a2, a2, a3
	andi	a2, a2, 1
	beqz	a2, .LBB0_45
.Ltmp7:
.LBB0_5:
	lw	a2, 16(a1)
.Ltmp8:
	ld	a5, 8(a1)
.Ltmp9:
	blt	a0, a2, .LBB0_8
.Ltmp10:
	li	a0, 7
	bltu	a0, a2, .LBB0_46
.Ltmp11:
	li	a0, 145
	srl	a0, a0, a2
	andi	a0, a0, 1
	beqz	a0, .LBB0_46
.Ltmp12:
.LBB0_8:
	lw	a0, 32(a1)
.Ltmp13:
	ld	a4, 24(a1)
.Ltmp14:
	li	a6, 63
	blt	a6, a0, .LBB0_11
.Ltmp15:
	li	a6, 7
	bltu	a6, a0, .LBB0_47
.Ltmp16:
	li	a6, 145
	srl	a6, a6, a0
	andi	a6, a6, 1
	beqz	a6, .LBB0_47
.Ltmp17:
.LBB0_11:
	beqz	a5, .LBB0_52
.Ltmp18:
	addi	a3, a3, -70
.Ltmp19:
	snez	a3, a3
	addi	a3, a3, -1
	andi	a3, a3, 24
	add	a3, a5, a3
.Ltmp20:
	lw	a6, 16(a3)
	li	a5, 1
	bne	a6, a5, .LBB0_53
.Ltmp21:
	lhu	a6, 22(a3)
	bne	a6, a5, .LBB0_54
.Ltmp22:
	lbu	a5, 21(a3)
	li	a6, 32
	bne	a5, a6, .LBB0_54
.Ltmp23:
	lbu	a5, 20(a3)
	li	a6, 2
	bne	a5, a6, .LBB0_54
.Ltmp24:
	lw	a5, 8(a3)
	li	a6, 1
	bne	a5, a6, .LBB0_55
.Ltmp25:
	beqz	a4, .LBB0_56
.Ltmp26:
	addi	a2, a2, -70
.Ltmp27:
	snez	a2, a2
	addi	a2, a2, -1
	andi	a2, a2, 24
	add	a4, a4, a2
.Ltmp28:
	lw	a5, 16(a4)
	li	a2, 1
	bne	a5, a2, .LBB0_57
.Ltmp29:
	lhu	a5, 22(a4)
	bne	a5, a2, .LBB0_58
.Ltmp30:
	lbu	a2, 21(a4)
	li	a5, 32
	bne	a2, a5, .LBB0_58
.Ltmp31:
	lbu	a2, 20(a4)
	li	a5, 2
	bne	a2, a5, .LBB0_58
.Ltmp32:
	lw	a2, 8(a4)
	li	a5, 1
	bne	a2, a5, .LBB0_59
.Ltmp33:
	ld	a5, 40(a1)
.Ltmp34:
	beqz	a5, .LBB0_60
.Ltmp35:
	addi	a0, a0, -70
.Ltmp36:
	snez	a0, a0
	addi	a0, a0, -1
	andi	a0, a0, 24
	add	a5, a5, a0
.Ltmp37:
	lw	a1, 16(a5)
.Ltmp38:
	li	a0, 1
	bne	a1, a0, .LBB0_61
.Ltmp39:
	lhu	a1, 22(a5)
	bne	a1, a0, .LBB0_62
.Ltmp40:
	lbu	a0, 21(a5)
	li	a1, 32
	bne	a0, a1, .LBB0_62
.Ltmp41:
	lbu	a0, 20(a5)
	li	a1, 2
	bne	a0, a1, .LBB0_62
.Ltmp42:
	lw	a0, 8(a5)
	li	a1, 1
	bne	a0, a1, .LBB0_63
.Ltmp43:
	ld	t1, 24(a3)
.Ltmp44:
	ld	t4, 32(a3)
.Ltmp45:
	lw	t2, 12(a3)
	ld	a0, 0(a3)
.Ltmp46:
	ld	t0, 24(a4)
.Ltmp47:
	ld	t3, 32(a4)
.Ltmp48:
	ld	a1, 0(a4)
.Ltmp49:
	ld	a6, 24(a5)
.Ltmp50:
	ld	a2, 0(a5)
.Ltmp51:
	li	a7, -1
	srli	a7, a7, 32
	beqz	t4, .LBB0_31
.Ltmp52:
	ld	t4, 0(t4)
.Ltmp53:
	and	t4, t4, a7
	li	t5, 1
	bne	t4, t5, .LBB0_64
.Ltmp54:
.LBB0_31:
	beqz	a0, .LBB0_65
.Ltmp55:
	beqz	t3, .LBB0_34
.Ltmp56:
	ld	t3, 0(t3)
.Ltmp57:
	and	t3, t3, a7
	li	t4, 1
	bne	t3, t4, .LBB0_66
.Ltmp58:
.LBB0_34:
	lw	t3, 12(a4)
	bne	t2, t3, .LBB0_68
.Ltmp59:
	beqz	a1, .LBB0_69
.Ltmp60:
	lw	t3, 12(a5)
	bne	t2, t3, .LBB0_70
.Ltmp61:
	beqz	a2, .LBB0_71
.Ltmp62:
	ld	t1, 0(t1)
.Ltmp63:
	and	t1, t1, a7
	li	t2, 64
	bne	t1, t2, .LBB0_72
.Ltmp64:
	ld	a3, 40(a3)
.Ltmp65:
	bnez	a3, .LBB0_73
.Ltmp66:
	ld	a3, 0(t0)
	and	a3, a3, a7
	li	t0, 64
.Ltmp67:
	bne	a3, t0, .LBB0_75
.Ltmp68:
	ld	a3, 40(a4)
	bnez	a3, .LBB0_76
.Ltmp69:
	ld	a3, 0(a6)
	and	a3, a3, a7
	li	a4, 1
.Ltmp70:
	bne	a3, a4, .LBB0_77
.Ltmp71:
	ld	a3, 40(a5)
	bnez	a3, .LBB0_78
.Ltmp72:
	call	dotproduct_compute_
.Ltmp73:
	li	a0, 0
	ld	ra, 8(sp)
	addi	sp, sp, 16
	ret
.LBB0_45:
.Ltmp74:
.Lpcrel_hi12:
	auipc	a0, %pcrel_hi(.L.str)
	addi	a0, a0, %pcrel_lo(.Lpcrel_hi12)
.Lpcrel_hi13:
	auipc	a1, %pcrel_hi(.L.str.8)
.Ltmp75:
	addi	a2, a1, %pcrel_lo(.Lpcrel_hi13)
.Lpcrel_hi14:
	auipc	a1, %pcrel_hi(.L.str.9)
	addi	a3, a1, %pcrel_lo(.Lpcrel_hi14)
.Ltmp76:
.Lpcrel_hi15:
	auipc	a1, %pcrel_hi(.L.str.4)
	addi	a4, a1, %pcrel_lo(.Lpcrel_hi15)
.Lpcrel_hi16:
	auipc	a1, %pcrel_hi(.L.str.5)
	addi	a5, a1, %pcrel_lo(.Lpcrel_hi16)
.Lpcrel_hi17:
	auipc	a1, %pcrel_hi(.L.str.10)
	addi	a6, a1, %pcrel_lo(.Lpcrel_hi17)
.Lpcrel_hi18:
	auipc	a1, %pcrel_hi(.L.str.11)
	addi	a7, a1, %pcrel_lo(.Lpcrel_hi18)
	j	.LBB0_48
.LBB0_46:
.Ltmp77:
.Lpcrel_hi19:
	auipc	a0, %pcrel_hi(.L.str)
	addi	a0, a0, %pcrel_lo(.Lpcrel_hi19)
.Lpcrel_hi20:
	auipc	a1, %pcrel_hi(.L.str.8)
.Ltmp78:
	addi	a2, a1, %pcrel_lo(.Lpcrel_hi20)
.Ltmp79:
.Lpcrel_hi21:
	auipc	a1, %pcrel_hi(.L.str.12)
	addi	a3, a1, %pcrel_lo(.Lpcrel_hi21)
.Ltmp80:
.Lpcrel_hi22:
	auipc	a1, %pcrel_hi(.L.str.4)
	addi	a4, a1, %pcrel_lo(.Lpcrel_hi22)
.Lpcrel_hi23:
	auipc	a1, %pcrel_hi(.L.str.5)
	addi	a5, a1, %pcrel_lo(.Lpcrel_hi23)
.Lpcrel_hi24:
	auipc	a1, %pcrel_hi(.L.str.10)
	addi	a6, a1, %pcrel_lo(.Lpcrel_hi24)
.Lpcrel_hi25:
	auipc	a1, %pcrel_hi(.L.str.11)
	addi	a7, a1, %pcrel_lo(.Lpcrel_hi25)
	j	.LBB0_48
.LBB0_47:
.Ltmp81:
.Lpcrel_hi26:
	auipc	a0, %pcrel_hi(.L.str)
.Ltmp82:
	addi	a0, a0, %pcrel_lo(.Lpcrel_hi26)
.Lpcrel_hi27:
	auipc	a1, %pcrel_hi(.L.str.8)
.Ltmp83:
	addi	a2, a1, %pcrel_lo(.Lpcrel_hi27)
.Ltmp84:
.Lpcrel_hi28:
	auipc	a1, %pcrel_hi(.L.str.13)
	addi	a3, a1, %pcrel_lo(.Lpcrel_hi28)
.Ltmp85:
.Lpcrel_hi29:
	auipc	a1, %pcrel_hi(.L.str.4)
	addi	a4, a1, %pcrel_lo(.Lpcrel_hi29)
.Lpcrel_hi30:
	auipc	a1, %pcrel_hi(.L.str.5)
	addi	a5, a1, %pcrel_lo(.Lpcrel_hi30)
.Lpcrel_hi31:
	auipc	a1, %pcrel_hi(.L.str.10)
	addi	a6, a1, %pcrel_lo(.Lpcrel_hi31)
.Lpcrel_hi32:
	auipc	a1, %pcrel_hi(.L.str.11)
	addi	a7, a1, %pcrel_lo(.Lpcrel_hi32)
.LBB0_48:
	li	a1, 6
.LBB0_49:
	call	__tvm_set_raised_6
	li	a0, -1
	ld	ra, 8(sp)
	addi	sp, sp, 16
	ret
.LBB0_50:
.Ltmp86:
.Lpcrel_hi0:
	auipc	a0, %pcrel_hi(.L.str)
	addi	a0, a0, %pcrel_lo(.Lpcrel_hi0)
.Lpcrel_hi1:
	auipc	a1, %pcrel_hi(.L.str.1)
.Ltmp87:
	addi	a2, a1, %pcrel_lo(.Lpcrel_hi1)
.Lpcrel_hi2:
	auipc	a1, %pcrel_hi(.L.str.2)
	addi	a3, a1, %pcrel_lo(.Lpcrel_hi2)
.Lpcrel_hi3:
	auipc	a1, %pcrel_hi(.L.str.3)
	addi	a4, a1, %pcrel_lo(.Lpcrel_hi3)
.Lpcrel_hi4:
	auipc	a1, %pcrel_hi(.L.str.4)
	addi	a5, a1, %pcrel_lo(.Lpcrel_hi4)
.Lpcrel_hi5:
	auipc	a1, %pcrel_hi(.L.str.5)
	addi	a6, a1, %pcrel_lo(.Lpcrel_hi5)
.Lpcrel_hi6:
	auipc	a1, %pcrel_hi(.L.str.6)
	addi	a7, a1, %pcrel_lo(.Lpcrel_hi6)
	j	.LBB0_48
.LBB0_51:
.Ltmp88:
.Lpcrel_hi7:
	auipc	a0, %pcrel_hi(.L.str)
	addi	a0, a0, %pcrel_lo(.Lpcrel_hi7)
.Lpcrel_hi8:
	auipc	a1, %pcrel_hi(.L.str.7)
.Ltmp89:
	addi	a2, a1, %pcrel_lo(.Lpcrel_hi8)
.Lpcrel_hi9:
	auipc	a1, %pcrel_hi(.L.str.4)
	addi	a3, a1, %pcrel_lo(.Lpcrel_hi9)
.Lpcrel_hi10:
	auipc	a1, %pcrel_hi(.L.str.5)
	addi	a4, a1, %pcrel_lo(.Lpcrel_hi10)
.Lpcrel_hi11:
	auipc	a1, %pcrel_hi(.L.str.6)
	addi	a5, a1, %pcrel_lo(.Lpcrel_hi11)
	li	a1, 4
	li	a6, 0
	li	a7, 0
	j	.LBB0_49
.LBB0_52:
.Ltmp90:
.Lpcrel_hi33:
	auipc	a0, %pcrel_hi(.L.str)
.Ltmp91:
	addi	a0, a0, %pcrel_lo(.Lpcrel_hi33)
.Lpcrel_hi34:
	auipc	a1, %pcrel_hi(.L.str.8)
.Ltmp92:
	addi	a2, a1, %pcrel_lo(.Lpcrel_hi34)
.Ltmp93:
.Lpcrel_hi35:
	auipc	a1, %pcrel_hi(.L.str.9)
	addi	a3, a1, %pcrel_lo(.Lpcrel_hi35)
.Ltmp94:
.Lpcrel_hi36:
	auipc	a1, %pcrel_hi(.L.str.4)
	addi	a4, a1, %pcrel_lo(.Lpcrel_hi36)
.Lpcrel_hi37:
	auipc	a1, %pcrel_hi(.L.str.5)
	addi	a5, a1, %pcrel_lo(.Lpcrel_hi37)
.Lpcrel_hi38:
	auipc	a1, %pcrel_hi(.L.str.10)
	addi	a6, a1, %pcrel_lo(.Lpcrel_hi38)
.Lpcrel_hi39:
	auipc	a1, %pcrel_hi(.L.str.11)
	addi	a7, a1, %pcrel_lo(.Lpcrel_hi39)
	j	.LBB0_48
.LBB0_53:
.Ltmp95:
.Lpcrel_hi40:
	auipc	a0, %pcrel_hi(.L.str.14)
.Ltmp96:
	addi	a0, a0, %pcrel_lo(.Lpcrel_hi40)
.Lpcrel_hi41:
	auipc	a1, %pcrel_hi(.L.str.15)
.Ltmp97:
	addi	a2, a1, %pcrel_lo(.Lpcrel_hi41)
.Ltmp98:
.Lpcrel_hi42:
	auipc	a1, %pcrel_hi(.L.str.16)
	addi	a3, a1, %pcrel_lo(.Lpcrel_hi42)
.Ltmp99:
.Lpcrel_hi43:
	auipc	a1, %pcrel_hi(.L.str.17)
	addi	a4, a1, %pcrel_lo(.Lpcrel_hi43)
.Lpcrel_hi44:
	auipc	a1, %pcrel_hi(.L.str.9)
	addi	a5, a1, %pcrel_lo(.Lpcrel_hi44)
.Lpcrel_hi45:
	auipc	a1, %pcrel_hi(.L.str.10)
	addi	a6, a1, %pcrel_lo(.Lpcrel_hi45)
.Lpcrel_hi46:
	auipc	a1, %pcrel_hi(.L.str.12)
	addi	a7, a1, %pcrel_lo(.Lpcrel_hi46)
	j	.LBB0_79
.LBB0_54:
.Ltmp100:
.Lpcrel_hi47:
	auipc	a0, %pcrel_hi(.L.str)
.Ltmp101:
	addi	a0, a0, %pcrel_lo(.Lpcrel_hi47)
.Lpcrel_hi48:
	auipc	a1, %pcrel_hi(.L.str.15)
.Ltmp102:
	addi	a2, a1, %pcrel_lo(.Lpcrel_hi48)
.Ltmp103:
.Lpcrel_hi49:
	auipc	a1, %pcrel_hi(.L.str.16)
	addi	a3, a1, %pcrel_lo(.Lpcrel_hi49)
.Ltmp104:
.Lpcrel_hi50:
	auipc	a1, %pcrel_hi(.L.str.18)
	addi	a4, a1, %pcrel_lo(.Lpcrel_hi50)
.Lpcrel_hi51:
	auipc	a1, %pcrel_hi(.L.str.9)
	addi	a5, a1, %pcrel_lo(.Lpcrel_hi51)
.Lpcrel_hi52:
	auipc	a1, %pcrel_hi(.L.str.10)
	addi	a6, a1, %pcrel_lo(.Lpcrel_hi52)
.Lpcrel_hi53:
	auipc	a1, %pcrel_hi(.L.str.19)
	addi	a7, a1, %pcrel_lo(.Lpcrel_hi53)
	j	.LBB0_79
.LBB0_55:
.Ltmp105:
.Lpcrel_hi54:
	auipc	a0, %pcrel_hi(.L.str.14)
.Ltmp106:
	addi	a0, a0, %pcrel_lo(.Lpcrel_hi54)
.Lpcrel_hi55:
	auipc	a1, %pcrel_hi(.L.str.15)
.Ltmp107:
	addi	a2, a1, %pcrel_lo(.Lpcrel_hi55)
.Ltmp108:
.Lpcrel_hi56:
	auipc	a1, %pcrel_hi(.L.str.16)
	addi	a3, a1, %pcrel_lo(.Lpcrel_hi56)
.Ltmp109:
.Lpcrel_hi57:
	auipc	a1, %pcrel_hi(.L.str.20)
	addi	a4, a1, %pcrel_lo(.Lpcrel_hi57)
.Lpcrel_hi58:
	auipc	a1, %pcrel_hi(.L.str.9)
	addi	a5, a1, %pcrel_lo(.Lpcrel_hi58)
.Lpcrel_hi59:
	auipc	a1, %pcrel_hi(.L.str.10)
	addi	a6, a1, %pcrel_lo(.Lpcrel_hi59)
.Lpcrel_hi60:
	auipc	a1, %pcrel_hi(.L.str.21)
	addi	a7, a1, %pcrel_lo(.Lpcrel_hi60)
	j	.LBB0_79
.LBB0_56:
.Ltmp110:
.Lpcrel_hi61:
	auipc	a0, %pcrel_hi(.L.str)
.Ltmp111:
	addi	a0, a0, %pcrel_lo(.Lpcrel_hi61)
.Lpcrel_hi62:
	auipc	a1, %pcrel_hi(.L.str.8)
.Ltmp112:
	addi	a2, a1, %pcrel_lo(.Lpcrel_hi62)
.Ltmp113:
.Lpcrel_hi63:
	auipc	a1, %pcrel_hi(.L.str.12)
	addi	a3, a1, %pcrel_lo(.Lpcrel_hi63)
.Ltmp114:
.Lpcrel_hi64:
	auipc	a1, %pcrel_hi(.L.str.4)
	addi	a4, a1, %pcrel_lo(.Lpcrel_hi64)
.Lpcrel_hi65:
	auipc	a1, %pcrel_hi(.L.str.5)
	addi	a5, a1, %pcrel_lo(.Lpcrel_hi65)
.Lpcrel_hi66:
	auipc	a1, %pcrel_hi(.L.str.10)
	addi	a6, a1, %pcrel_lo(.Lpcrel_hi66)
.Lpcrel_hi67:
	auipc	a1, %pcrel_hi(.L.str.11)
	addi	a7, a1, %pcrel_lo(.Lpcrel_hi67)
	j	.LBB0_48
.LBB0_57:
.Ltmp115:
.Lpcrel_hi68:
	auipc	a0, %pcrel_hi(.L.str.14)
.Ltmp116:
	addi	a0, a0, %pcrel_lo(.Lpcrel_hi68)
.Lpcrel_hi69:
	auipc	a1, %pcrel_hi(.L.str.15)
.Ltmp117:
	addi	a2, a1, %pcrel_lo(.Lpcrel_hi69)
.Lpcrel_hi70:
	auipc	a1, %pcrel_hi(.L.str.22)
	addi	a3, a1, %pcrel_lo(.Lpcrel_hi70)
.Ltmp118:
.Lpcrel_hi71:
	auipc	a1, %pcrel_hi(.L.str.17)
	addi	a4, a1, %pcrel_lo(.Lpcrel_hi71)
.Ltmp119:
.Lpcrel_hi72:
	auipc	a1, %pcrel_hi(.L.str.10)
	addi	a6, a1, %pcrel_lo(.Lpcrel_hi72)
.Lpcrel_hi73:
	auipc	a1, %pcrel_hi(.L.str.12)
	addi	a5, a1, %pcrel_lo(.Lpcrel_hi73)
	j	.LBB0_74
.LBB0_58:
.Ltmp120:
.Lpcrel_hi74:
	auipc	a0, %pcrel_hi(.L.str)
.Ltmp121:
	addi	a0, a0, %pcrel_lo(.Lpcrel_hi74)
.Lpcrel_hi75:
	auipc	a1, %pcrel_hi(.L.str.15)
.Ltmp122:
	addi	a2, a1, %pcrel_lo(.Lpcrel_hi75)
.Lpcrel_hi76:
	auipc	a1, %pcrel_hi(.L.str.22)
	addi	a3, a1, %pcrel_lo(.Lpcrel_hi76)
.Ltmp123:
.Lpcrel_hi77:
	auipc	a1, %pcrel_hi(.L.str.18)
	addi	a4, a1, %pcrel_lo(.Lpcrel_hi77)
.Ltmp124:
.Lpcrel_hi78:
	auipc	a1, %pcrel_hi(.L.str.12)
	addi	a5, a1, %pcrel_lo(.Lpcrel_hi78)
.Lpcrel_hi79:
	auipc	a1, %pcrel_hi(.L.str.10)
	addi	a6, a1, %pcrel_lo(.Lpcrel_hi79)
.Lpcrel_hi80:
	auipc	a1, %pcrel_hi(.L.str.19)
	addi	a7, a1, %pcrel_lo(.Lpcrel_hi80)
	j	.LBB0_79
.LBB0_59:
.Ltmp125:
.Lpcrel_hi81:
	auipc	a0, %pcrel_hi(.L.str.14)
.Ltmp126:
	addi	a0, a0, %pcrel_lo(.Lpcrel_hi81)
.Lpcrel_hi82:
	auipc	a1, %pcrel_hi(.L.str.15)
.Ltmp127:
	addi	a2, a1, %pcrel_lo(.Lpcrel_hi82)
.Lpcrel_hi83:
	auipc	a1, %pcrel_hi(.L.str.22)
	addi	a3, a1, %pcrel_lo(.Lpcrel_hi83)
.Ltmp128:
.Lpcrel_hi84:
	auipc	a1, %pcrel_hi(.L.str.20)
	addi	a4, a1, %pcrel_lo(.Lpcrel_hi84)
.Ltmp129:
.Lpcrel_hi85:
	auipc	a1, %pcrel_hi(.L.str.12)
	addi	a5, a1, %pcrel_lo(.Lpcrel_hi85)
.Lpcrel_hi86:
	auipc	a1, %pcrel_hi(.L.str.10)
	addi	a6, a1, %pcrel_lo(.Lpcrel_hi86)
.Lpcrel_hi87:
	auipc	a1, %pcrel_hi(.L.str.21)
	addi	a7, a1, %pcrel_lo(.Lpcrel_hi87)
	j	.LBB0_79
.LBB0_60:
.Ltmp130:
.Lpcrel_hi88:
	auipc	a0, %pcrel_hi(.L.str)
.Ltmp131:
	addi	a0, a0, %pcrel_lo(.Lpcrel_hi88)
.Lpcrel_hi89:
	auipc	a1, %pcrel_hi(.L.str.8)
.Ltmp132:
	addi	a2, a1, %pcrel_lo(.Lpcrel_hi89)
.Lpcrel_hi90:
	auipc	a1, %pcrel_hi(.L.str.13)
	addi	a3, a1, %pcrel_lo(.Lpcrel_hi90)
.Ltmp133:
.Lpcrel_hi91:
	auipc	a1, %pcrel_hi(.L.str.4)
	addi	a4, a1, %pcrel_lo(.Lpcrel_hi91)
.Ltmp134:
.Lpcrel_hi92:
	auipc	a1, %pcrel_hi(.L.str.5)
	addi	a5, a1, %pcrel_lo(.Lpcrel_hi92)
.Lpcrel_hi93:
	auipc	a1, %pcrel_hi(.L.str.10)
	addi	a6, a1, %pcrel_lo(.Lpcrel_hi93)
.Lpcrel_hi94:
	auipc	a1, %pcrel_hi(.L.str.11)
	addi	a7, a1, %pcrel_lo(.Lpcrel_hi94)
	j	.LBB0_48
.LBB0_61:
.Ltmp135:
.Lpcrel_hi95:
	auipc	a0, %pcrel_hi(.L.str.14)
	addi	a0, a0, %pcrel_lo(.Lpcrel_hi95)
.Lpcrel_hi96:
	auipc	a1, %pcrel_hi(.L.str.15)
	addi	a2, a1, %pcrel_lo(.Lpcrel_hi96)
.Lpcrel_hi97:
	auipc	a1, %pcrel_hi(.L.str.23)
	addi	a3, a1, %pcrel_lo(.Lpcrel_hi97)
.Ltmp136:
.Lpcrel_hi98:
	auipc	a1, %pcrel_hi(.L.str.17)
	addi	a4, a1, %pcrel_lo(.Lpcrel_hi98)
.Ltmp137:
.Lpcrel_hi99:
	auipc	a1, %pcrel_hi(.L.str.13)
	addi	a5, a1, %pcrel_lo(.Lpcrel_hi99)
.Ltmp138:
.Lpcrel_hi100:
	auipc	a1, %pcrel_hi(.L.str.10)
	addi	a6, a1, %pcrel_lo(.Lpcrel_hi100)
.Lpcrel_hi101:
	auipc	a1, %pcrel_hi(.L.str.12)
	addi	a7, a1, %pcrel_lo(.Lpcrel_hi101)
	j	.LBB0_79
.LBB0_62:
.Ltmp139:
.Lpcrel_hi102:
	auipc	a0, %pcrel_hi(.L.str)
	addi	a0, a0, %pcrel_lo(.Lpcrel_hi102)
.Lpcrel_hi103:
	auipc	a1, %pcrel_hi(.L.str.15)
	addi	a2, a1, %pcrel_lo(.Lpcrel_hi103)
.Lpcrel_hi104:
	auipc	a1, %pcrel_hi(.L.str.23)
	addi	a3, a1, %pcrel_lo(.Lpcrel_hi104)
.Ltmp140:
.Lpcrel_hi105:
	auipc	a1, %pcrel_hi(.L.str.18)
	addi	a4, a1, %pcrel_lo(.Lpcrel_hi105)
.Ltmp141:
.Lpcrel_hi106:
	auipc	a1, %pcrel_hi(.L.str.13)
	addi	a5, a1, %pcrel_lo(.Lpcrel_hi106)
.Ltmp142:
.Lpcrel_hi107:
	auipc	a1, %pcrel_hi(.L.str.10)
	addi	a6, a1, %pcrel_lo(.Lpcrel_hi107)
.Lpcrel_hi108:
	auipc	a1, %pcrel_hi(.L.str.19)
	addi	a7, a1, %pcrel_lo(.Lpcrel_hi108)
	j	.LBB0_79
.LBB0_63:
.Ltmp143:
.Lpcrel_hi109:
	auipc	a0, %pcrel_hi(.L.str.14)
	addi	a0, a0, %pcrel_lo(.Lpcrel_hi109)
.Lpcrel_hi110:
	auipc	a1, %pcrel_hi(.L.str.15)
	addi	a2, a1, %pcrel_lo(.Lpcrel_hi110)
.Lpcrel_hi111:
	auipc	a1, %pcrel_hi(.L.str.23)
	addi	a3, a1, %pcrel_lo(.Lpcrel_hi111)
.Ltmp144:
.Lpcrel_hi112:
	auipc	a1, %pcrel_hi(.L.str.20)
	addi	a4, a1, %pcrel_lo(.Lpcrel_hi112)
.Ltmp145:
.Lpcrel_hi113:
	auipc	a1, %pcrel_hi(.L.str.13)
	addi	a5, a1, %pcrel_lo(.Lpcrel_hi113)
.Ltmp146:
.Lpcrel_hi114:
	auipc	a1, %pcrel_hi(.L.str.10)
	addi	a6, a1, %pcrel_lo(.Lpcrel_hi114)
.Lpcrel_hi115:
	auipc	a1, %pcrel_hi(.L.str.21)
	addi	a7, a1, %pcrel_lo(.Lpcrel_hi115)
	j	.LBB0_79
.LBB0_64:
.Ltmp147:
.Lpcrel_hi116:
	auipc	a0, %pcrel_hi(.L.str.14)
.Ltmp148:
	addi	a0, a0, %pcrel_lo(.Lpcrel_hi116)
.Lpcrel_hi117:
	auipc	a1, %pcrel_hi(.L.str.15)
.Ltmp149:
	addi	a2, a1, %pcrel_lo(.Lpcrel_hi117)
.Ltmp150:
.Lpcrel_hi118:
	auipc	a1, %pcrel_hi(.L.str.16)
	addi	a3, a1, %pcrel_lo(.Lpcrel_hi118)
.Ltmp151:
.Lpcrel_hi119:
	auipc	a1, %pcrel_hi(.L.str.24)
	addi	a4, a1, %pcrel_lo(.Lpcrel_hi119)
.Ltmp152:
.Lpcrel_hi120:
	auipc	a1, %pcrel_hi(.L.str.9)
	addi	a5, a1, %pcrel_lo(.Lpcrel_hi120)
.Ltmp153:
.Lpcrel_hi121:
	auipc	a1, %pcrel_hi(.L.str.25)
	addi	a6, a1, %pcrel_lo(.Lpcrel_hi121)
.Ltmp154:
	j	.LBB0_67
.Ltmp155:
.LBB0_65:
.Lpcrel_hi122:
	auipc	a0, %pcrel_hi(.L.str.14)
.Ltmp156:
	addi	a0, a0, %pcrel_lo(.Lpcrel_hi122)
.Lpcrel_hi123:
	auipc	a1, %pcrel_hi(.L.str.16)
.Ltmp157:
	addi	a2, a1, %pcrel_lo(.Lpcrel_hi123)
.Ltmp158:
.Lpcrel_hi124:
	auipc	a1, %pcrel_hi(.L.str.26)
	addi	a3, a1, %pcrel_lo(.Lpcrel_hi124)
.Ltmp159:
.Lpcrel_hi125:
	auipc	a1, %pcrel_hi(.L.str.9)
	addi	a4, a1, %pcrel_lo(.Lpcrel_hi125)
.Ltmp160:
.Lpcrel_hi126:
	auipc	a1, %pcrel_hi(.L.str.4)
	addi	a5, a1, %pcrel_lo(.Lpcrel_hi126)
.Ltmp161:
.Lpcrel_hi127:
	auipc	a1, %pcrel_hi(.L.str.5)
	addi	a6, a1, %pcrel_lo(.Lpcrel_hi127)
.Ltmp162:
.Lpcrel_hi128:
	auipc	a1, %pcrel_hi(.L.str.27)
	addi	a7, a1, %pcrel_lo(.Lpcrel_hi128)
	j	.LBB0_48
.Ltmp163:
.LBB0_66:
.Lpcrel_hi129:
	auipc	a0, %pcrel_hi(.L.str.14)
.Ltmp164:
	addi	a0, a0, %pcrel_lo(.Lpcrel_hi129)
.Lpcrel_hi130:
	auipc	a1, %pcrel_hi(.L.str.15)
.Ltmp165:
	addi	a2, a1, %pcrel_lo(.Lpcrel_hi130)
.Ltmp166:
.Lpcrel_hi131:
	auipc	a1, %pcrel_hi(.L.str.22)
	addi	a3, a1, %pcrel_lo(.Lpcrel_hi131)
.Ltmp167:
.Lpcrel_hi132:
	auipc	a1, %pcrel_hi(.L.str.24)
	addi	a4, a1, %pcrel_lo(.Lpcrel_hi132)
.Ltmp168:
.Lpcrel_hi133:
	auipc	a1, %pcrel_hi(.L.str.12)
	addi	a5, a1, %pcrel_lo(.Lpcrel_hi133)
.Ltmp169:
.Lpcrel_hi134:
	auipc	a1, %pcrel_hi(.L.str.25)
	addi	a6, a1, %pcrel_lo(.Lpcrel_hi134)
.Ltmp170:
.LBB0_67:
	li	a1, 7
	li	a7, 0
	j	.LBB0_80
.Ltmp171:
.LBB0_68:
.Lpcrel_hi135:
	auipc	a0, %pcrel_hi(.L.str.14)
.Ltmp172:
	addi	a0, a0, %pcrel_lo(.Lpcrel_hi135)
.Lpcrel_hi136:
	auipc	a1, %pcrel_hi(.L.str.15)
.Ltmp173:
	addi	a2, a1, %pcrel_lo(.Lpcrel_hi136)
.Ltmp174:
.Lpcrel_hi137:
	auipc	a1, %pcrel_hi(.L.str.28)
	addi	a3, a1, %pcrel_lo(.Lpcrel_hi137)
.Ltmp175:
.Lpcrel_hi138:
	auipc	a1, %pcrel_hi(.L.str.29)
	addi	a4, a1, %pcrel_lo(.Lpcrel_hi138)
.Ltmp176:
.Lpcrel_hi139:
	auipc	a1, %pcrel_hi(.L.str.12)
	addi	a5, a1, %pcrel_lo(.Lpcrel_hi139)
.Ltmp177:
.Lpcrel_hi140:
	auipc	a1, %pcrel_hi(.L.str.30)
	addi	a6, a1, %pcrel_lo(.Lpcrel_hi140)
.Ltmp178:
.Lpcrel_hi141:
	auipc	a1, %pcrel_hi(.L.str.31)
	addi	a7, a1, %pcrel_lo(.Lpcrel_hi141)
	j	.LBB0_79
.Ltmp179:
.LBB0_69:
.Lpcrel_hi142:
	auipc	a0, %pcrel_hi(.L.str.14)
.Ltmp180:
	addi	a0, a0, %pcrel_lo(.Lpcrel_hi142)
.Lpcrel_hi143:
	auipc	a1, %pcrel_hi(.L.str.22)
.Ltmp181:
	addi	a2, a1, %pcrel_lo(.Lpcrel_hi143)
.Ltmp182:
.Lpcrel_hi144:
	auipc	a1, %pcrel_hi(.L.str.26)
	addi	a3, a1, %pcrel_lo(.Lpcrel_hi144)
.Ltmp183:
.Lpcrel_hi145:
	auipc	a1, %pcrel_hi(.L.str.12)
	addi	a4, a1, %pcrel_lo(.Lpcrel_hi145)
.Ltmp184:
.Lpcrel_hi146:
	auipc	a1, %pcrel_hi(.L.str.4)
	addi	a5, a1, %pcrel_lo(.Lpcrel_hi146)
.Ltmp185:
.Lpcrel_hi147:
	auipc	a1, %pcrel_hi(.L.str.5)
	addi	a6, a1, %pcrel_lo(.Lpcrel_hi147)
.Ltmp186:
.Lpcrel_hi148:
	auipc	a1, %pcrel_hi(.L.str.27)
	addi	a7, a1, %pcrel_lo(.Lpcrel_hi148)
	j	.LBB0_48
.Ltmp187:
.LBB0_70:
.Lpcrel_hi149:
	auipc	a0, %pcrel_hi(.L.str.14)
.Ltmp188:
	addi	a0, a0, %pcrel_lo(.Lpcrel_hi149)
.Lpcrel_hi150:
	auipc	a1, %pcrel_hi(.L.str.15)
.Ltmp189:
	addi	a2, a1, %pcrel_lo(.Lpcrel_hi150)
.Ltmp190:
.Lpcrel_hi151:
	auipc	a1, %pcrel_hi(.L.str.32)
	addi	a3, a1, %pcrel_lo(.Lpcrel_hi151)
.Ltmp191:
.Lpcrel_hi152:
	auipc	a1, %pcrel_hi(.L.str.29)
	addi	a4, a1, %pcrel_lo(.Lpcrel_hi152)
.Ltmp192:
.Lpcrel_hi153:
	auipc	a1, %pcrel_hi(.L.str.13)
	addi	a5, a1, %pcrel_lo(.Lpcrel_hi153)
.Ltmp193:
.Lpcrel_hi154:
	auipc	a1, %pcrel_hi(.L.str.30)
	addi	a6, a1, %pcrel_lo(.Lpcrel_hi154)
.Ltmp194:
.Lpcrel_hi155:
	auipc	a1, %pcrel_hi(.L.str.31)
	addi	a7, a1, %pcrel_lo(.Lpcrel_hi155)
	j	.LBB0_79
.Ltmp195:
.LBB0_71:
.Lpcrel_hi156:
	auipc	a0, %pcrel_hi(.L.str.14)
.Ltmp196:
	addi	a0, a0, %pcrel_lo(.Lpcrel_hi156)
.Lpcrel_hi157:
	auipc	a1, %pcrel_hi(.L.str.23)
.Ltmp197:
	addi	a2, a1, %pcrel_lo(.Lpcrel_hi157)
.Ltmp198:
.Lpcrel_hi158:
	auipc	a1, %pcrel_hi(.L.str.26)
	addi	a3, a1, %pcrel_lo(.Lpcrel_hi158)
.Ltmp199:
.Lpcrel_hi159:
	auipc	a1, %pcrel_hi(.L.str.13)
	addi	a4, a1, %pcrel_lo(.Lpcrel_hi159)
.Ltmp200:
.Lpcrel_hi160:
	auipc	a1, %pcrel_hi(.L.str.4)
	addi	a5, a1, %pcrel_lo(.Lpcrel_hi160)
.Ltmp201:
.Lpcrel_hi161:
	auipc	a1, %pcrel_hi(.L.str.5)
	addi	a6, a1, %pcrel_lo(.Lpcrel_hi161)
.Ltmp202:
.Lpcrel_hi162:
	auipc	a1, %pcrel_hi(.L.str.27)
	addi	a7, a1, %pcrel_lo(.Lpcrel_hi162)
	j	.LBB0_48
.Ltmp203:
.LBB0_72:
.Lpcrel_hi163:
	auipc	a0, %pcrel_hi(.L.str.14)
.Ltmp204:
	addi	a0, a0, %pcrel_lo(.Lpcrel_hi163)
.Lpcrel_hi164:
	auipc	a1, %pcrel_hi(.L.str.33)
.Ltmp205:
	addi	a2, a1, %pcrel_lo(.Lpcrel_hi164)
.Ltmp206:
.Lpcrel_hi165:
	auipc	a1, %pcrel_hi(.L.str.34)
	addi	a3, a1, %pcrel_lo(.Lpcrel_hi165)
.Ltmp207:
.Lpcrel_hi166:
	auipc	a1, %pcrel_hi(.L.str.29)
	addi	a4, a1, %pcrel_lo(.Lpcrel_hi166)
.Ltmp208:
.Lpcrel_hi167:
	auipc	a1, %pcrel_hi(.L.str.9)
	addi	a5, a1, %pcrel_lo(.Lpcrel_hi167)
.Ltmp209:
.Lpcrel_hi168:
	auipc	a1, %pcrel_hi(.L.str.10)
	addi	a6, a1, %pcrel_lo(.Lpcrel_hi168)
.Ltmp210:
.Lpcrel_hi169:
	auipc	a1, %pcrel_hi(.L.str.35)
	addi	a7, a1, %pcrel_lo(.Lpcrel_hi169)
	j	.LBB0_79
.Ltmp211:
.LBB0_73:
.Lpcrel_hi170:
	auipc	a0, %pcrel_hi(.L.str.14)
.Ltmp212:
	addi	a0, a0, %pcrel_lo(.Lpcrel_hi170)
.Lpcrel_hi171:
	auipc	a1, %pcrel_hi(.L.str.33)
.Ltmp213:
	addi	a2, a1, %pcrel_lo(.Lpcrel_hi171)
.Ltmp214:
.Lpcrel_hi172:
	auipc	a1, %pcrel_hi(.L.str.36)
	addi	a3, a1, %pcrel_lo(.Lpcrel_hi172)
.Lpcrel_hi173:
	auipc	a1, %pcrel_hi(.L.str.29)
	addi	a4, a1, %pcrel_lo(.Lpcrel_hi173)
.Ltmp215:
.Lpcrel_hi174:
	auipc	a1, %pcrel_hi(.L.str.10)
	addi	a6, a1, %pcrel_lo(.Lpcrel_hi174)
.Ltmp216:
.Lpcrel_hi175:
	auipc	a1, %pcrel_hi(.L.str.9)
	addi	a5, a1, %pcrel_lo(.Lpcrel_hi175)
.Ltmp217:
.LBB0_74:
	li	a1, 8
	mv	a7, a5
	j	.LBB0_80
.LBB0_75:
.Ltmp218:
.Lpcrel_hi176:
	auipc	a0, %pcrel_hi(.L.str.14)
.Ltmp219:
	addi	a0, a0, %pcrel_lo(.Lpcrel_hi176)
.Lpcrel_hi177:
	auipc	a1, %pcrel_hi(.L.str.33)
.Ltmp220:
	addi	a2, a1, %pcrel_lo(.Lpcrel_hi177)
.Ltmp221:
.Lpcrel_hi178:
	auipc	a1, %pcrel_hi(.L.str.37)
	addi	a3, a1, %pcrel_lo(.Lpcrel_hi178)
.Lpcrel_hi179:
	auipc	a1, %pcrel_hi(.L.str.29)
	addi	a4, a1, %pcrel_lo(.Lpcrel_hi179)
.Ltmp222:
.Lpcrel_hi180:
	auipc	a1, %pcrel_hi(.L.str.12)
	addi	a5, a1, %pcrel_lo(.Lpcrel_hi180)
.Ltmp223:
.Lpcrel_hi181:
	auipc	a1, %pcrel_hi(.L.str.10)
	addi	a6, a1, %pcrel_lo(.Lpcrel_hi181)
.Ltmp224:
.Lpcrel_hi182:
	auipc	a1, %pcrel_hi(.L.str.35)
	addi	a7, a1, %pcrel_lo(.Lpcrel_hi182)
	j	.LBB0_79
.LBB0_76:
.Ltmp225:
.Lpcrel_hi183:
	auipc	a0, %pcrel_hi(.L.str.14)
.Ltmp226:
	addi	a0, a0, %pcrel_lo(.Lpcrel_hi183)
.Lpcrel_hi184:
	auipc	a1, %pcrel_hi(.L.str.33)
.Ltmp227:
	addi	a2, a1, %pcrel_lo(.Lpcrel_hi184)
.Ltmp228:
.Lpcrel_hi185:
	auipc	a1, %pcrel_hi(.L.str.38)
	addi	a3, a1, %pcrel_lo(.Lpcrel_hi185)
.Lpcrel_hi186:
	auipc	a1, %pcrel_hi(.L.str.29)
	addi	a4, a1, %pcrel_lo(.Lpcrel_hi186)
.Ltmp229:
.Lpcrel_hi187:
	auipc	a1, %pcrel_hi(.L.str.12)
	addi	a5, a1, %pcrel_lo(.Lpcrel_hi187)
.Ltmp230:
.Lpcrel_hi188:
	auipc	a1, %pcrel_hi(.L.str.10)
	addi	a6, a1, %pcrel_lo(.Lpcrel_hi188)
.Ltmp231:
.Lpcrel_hi189:
	auipc	a1, %pcrel_hi(.L.str.9)
	addi	a7, a1, %pcrel_lo(.Lpcrel_hi189)
	j	.LBB0_79
.LBB0_77:
.Ltmp232:
.Lpcrel_hi190:
	auipc	a0, %pcrel_hi(.L.str.14)
.Ltmp233:
	addi	a0, a0, %pcrel_lo(.Lpcrel_hi190)
.Lpcrel_hi191:
	auipc	a1, %pcrel_hi(.L.str.33)
.Ltmp234:
	addi	a2, a1, %pcrel_lo(.Lpcrel_hi191)
.Ltmp235:
.Lpcrel_hi192:
	auipc	a1, %pcrel_hi(.L.str.39)
	addi	a3, a1, %pcrel_lo(.Lpcrel_hi192)
.Lpcrel_hi193:
	auipc	a1, %pcrel_hi(.L.str.29)
	addi	a4, a1, %pcrel_lo(.Lpcrel_hi193)
.Lpcrel_hi194:
	auipc	a1, %pcrel_hi(.L.str.13)
	addi	a5, a1, %pcrel_lo(.Lpcrel_hi194)
.Ltmp236:
.Lpcrel_hi195:
	auipc	a1, %pcrel_hi(.L.str.10)
	addi	a6, a1, %pcrel_lo(.Lpcrel_hi195)
.Ltmp237:
.Lpcrel_hi196:
	auipc	a1, %pcrel_hi(.L.str.12)
	addi	a7, a1, %pcrel_lo(.Lpcrel_hi196)
	j	.LBB0_79
.LBB0_78:
.Ltmp238:
.Lpcrel_hi197:
	auipc	a0, %pcrel_hi(.L.str.14)
.Ltmp239:
	addi	a0, a0, %pcrel_lo(.Lpcrel_hi197)
.Lpcrel_hi198:
	auipc	a1, %pcrel_hi(.L.str.33)
.Ltmp240:
	addi	a2, a1, %pcrel_lo(.Lpcrel_hi198)
.Ltmp241:
.Lpcrel_hi199:
	auipc	a1, %pcrel_hi(.L.str.40)
	addi	a3, a1, %pcrel_lo(.Lpcrel_hi199)
.Lpcrel_hi200:
	auipc	a1, %pcrel_hi(.L.str.29)
	addi	a4, a1, %pcrel_lo(.Lpcrel_hi200)
.Lpcrel_hi201:
	auipc	a1, %pcrel_hi(.L.str.13)
	addi	a5, a1, %pcrel_lo(.Lpcrel_hi201)
.Ltmp242:
.Lpcrel_hi202:
	auipc	a1, %pcrel_hi(.L.str.10)
	addi	a6, a1, %pcrel_lo(.Lpcrel_hi202)
.Ltmp243:
.Lpcrel_hi203:
	auipc	a1, %pcrel_hi(.L.str.9)
	addi	a7, a1, %pcrel_lo(.Lpcrel_hi203)
.LBB0_79:
	li	a1, 8
.LBB0_80:
	call	__tvm_set_raised_12
	li	a0, -1
	ld	ra, 8(sp)
	addi	sp, sp, 16
	ret
.Ltmp244:
.Lfunc_end0:
	.size	__tvm_ffi_dotproduct, .Lfunc_end0-__tvm_ffi_dotproduct
	.cfi_endproc

	.p2align	2
	.type	__tvm_set_raised_6,@function
__tvm_set_raised_6:
.Lfunc_begin1:
	.cfi_startproc
	addi	sp, sp, -64
	.cfi_def_cfa_offset 64
	sd	ra, 56(sp)
	.cfi_offset ra, -8
	mv	t0, a1
	sd	a2, 8(sp)
	sd	a3, 16(sp)
	sd	a4, 24(sp)
	sd	a5, 32(sp)
	sd	a6, 40(sp)
	sd	a7, 48(sp)
	addi	a1, sp, 8
	mv	a2, t0
	call	TVMFFIErrorSetRaisedFromCStrParts
	ld	ra, 56(sp)
	addi	sp, sp, 64
	ret
.Lfunc_end1:
	.size	__tvm_set_raised_6, .Lfunc_end1-__tvm_set_raised_6
	.cfi_endproc

	.p2align	2
	.type	__tvm_set_raised_12,@function
__tvm_set_raised_12:
.Lfunc_begin2:
	.cfi_startproc
	addi	sp, sp, -112
	.cfi_def_cfa_offset 112
	sd	ra, 104(sp)
	.cfi_offset ra, -8
	mv	t0, a1
	sd	a2, 8(sp)
	sd	a3, 16(sp)
	sd	a4, 24(sp)
	sd	a5, 32(sp)
.Lpcrel_hi204:
	auipc	a1, %pcrel_hi(.L.str.4)
	addi	a1, a1, %pcrel_lo(.Lpcrel_hi204)
	sd	a1, 40(sp)
.Lpcrel_hi205:
	auipc	a1, %pcrel_hi(.L.str.5)
	addi	a1, a1, %pcrel_lo(.Lpcrel_hi205)
	sd	a1, 48(sp)
	sd	a6, 56(sp)
	sd	a7, 64(sp)
	addi	a1, sp, 72
	vsetivli	zero, 2, e64, m1, ta, ma
	vmv.v.i	v8, 0
	vse64.v	v8, (a1)
	addi	a1, sp, 88
	vse64.v	v8, (a1)
	addi	a1, sp, 8
	mv	a2, t0
	call	TVMFFIErrorSetRaisedFromCStrParts
	ld	ra, 104(sp)
	addi	sp, sp, 112
	ret
.Lfunc_end2:
	.size	__tvm_set_raised_12, .Lfunc_end2-__tvm_set_raised_12
	.cfi_endproc

	.p2align	2
	.type	dotproduct_compute_,@function
dotproduct_compute_:
.Lfunc_begin3:
	.loc	1 0 0
	.cfi_startproc
	flw	fa5, 0(a0)
	flw	fa4, 0(a1)
	fmv.w.x	fa3, zero
	csrr	a7, vlenb
	srli	a3, a7, 3
	andi	a3, a3, 2032
	fmadd.s	fa5, fa5, fa4, fa3
	bnez	a3, .LBB3_7
.Ltmp245:
	srli	a4, a7, 1
	addi	a3, a4, -1
	andi	a5, a3, 63
	li	a3, 64
	sub	a3, a3, a5
	vsetvli	a6, zero, e32, m1, ta, ma
	vfmv.s.f	v8, fa5
	addi	a6, a1, 4
	slli	a7, a7, 1
	addi	t0, a0, 4
	li	t1, 63
	mv	t2, a4
.Ltmp246:
.LBB3_2:
	vl2re32.v	v10, (t0)
	vl2re32.v	v12, (a6)
	vsetvli	t3, zero, e32, m2, ta, ma
	vfmul.vv	v10, v10, v12
	vfredosum.vs	v8, v10, v8
	xor	t3, a5, t2
	add	t2, t2, a4
	add	a6, a6, a7
	add	t0, t0, a7
	bne	t3, t1, .LBB3_2
.Ltmp247:
	vfmv.f.s	fa5, v8
.Ltmp248:
.LBB3_4:
	slli	a4, a3, 2
	add	a3, a1, a4
	add	a0, a0, a4
.Ltmp249:
	addi	a1, a1, 256
.Ltmp250:
.LBB3_5:
	flw	fa4, 0(a0)
	flw	fa3, 0(a3)
	fmadd.s	fa5, fa4, fa3, fa5
.Ltmp251:
	addi	a3, a3, 4
	addi	a0, a0, 4
	bne	a3, a1, .LBB3_5
.Ltmp252:
	fsw	fa5, 0(a2)
	ret
.Ltmp253:
.LBB3_7:
	li	a3, 1
	j	.LBB3_4
.Lfunc_end3:
	.size	dotproduct_compute_, .Lfunc_end3-dotproduct_compute_
	.cfi_endproc

	.weak	__tvm_ffi_main
	.p2align	2
	.type	__tvm_ffi_main,@function
__tvm_ffi_main:
.Lfunc_begin4:
	.cfi_startproc
	tail	__tvm_ffi_dotproduct
.Lfunc_end4:
	.size	__tvm_ffi_main, .Lfunc_end4-__tvm_ffi_main
	.cfi_endproc

	.section	.text.tvm.fp16.conv,"ax",@progbits
	.weak	__truncsfhf2
	.p2align	2
	.type	__truncsfhf2,@function
__truncsfhf2:
.Lfunc_begin5:
	.cfi_startproc
	fmv.x.w	a0, fa0
	slli	a1, a0, 33
	srli	a1, a1, 33
	lui	a2, 817152
	addw	a2, a1, a2
	lui	a3, 755712
	addw	a3, a1, a3
	bgeu	a2, a3, .LBB5_4
	lui	a2, 16
	addiw	a2, a2, -1
	srliw	a3, a0, 13
	and	a1, a3, a2
	slli	a4, a0, 51
	srli	a4, a4, 51
	lui	a5, 1
	addiw	a7, a5, 1
	lui	a6, 1048548
	bltu	a4, a7, .LBB5_6
	addiw	a6, a6, 1
	add	a1, a1, a6
.LBB5_3:
	srliw	a0, a0, 31
	slli	a0, a0, 15
	or	a0, a1, a0
	ret
.LBB5_4:
	lui	a2, 522240
	addiw	a2, a2, 1
	bltu	a1, a2, .LBB5_8
	slli	a1, a0, 42
	srli	a1, a1, 55
	lui	a2, 8
	addiw	a2, a2, -512
	or	a1, a1, a2
	srliw	a0, a0, 31
	slli	a0, a0, 15
	or	a0, a1, a0
	ret
.LBB5_6:
	add	a1, a1, a6
	bne	a4, a5, .LBB5_3
	and	a1, a1, a2
	andi	a3, a3, 1
	add	a1, a1, a3
	srliw	a0, a0, 31
	slli	a0, a0, 15
	or	a0, a1, a0
	ret
.LBB5_8:
	srli	a2, a1, 23
	li	a3, 142
	bgeu	a3, a2, .LBB5_10
	li	a1, 31
	slli	a1, a1, 10
	srliw	a0, a0, 31
	slli	a0, a0, 15
	or	a0, a1, a0
	ret
.LBB5_10:
	srli	a1, a1, 24
	li	a3, 45
	bgeu	a1, a3, .LBB5_12
	srliw	a0, a0, 31
	slli	a0, a0, 15
	or	a0, zero, a0
	ret
.LBB5_12:
	li	a1, 113
	subw	a1, a1, a2
	slli	a3, a0, 41
	srli	a3, a3, 41
	lui	a4, 2048
	or	a3, a3, a4
	addi	a2, a2, -81
	sllw	a2, a3, a2
	snez	a2, a2
	srlw	a1, a3, a1
	slli	a3, a1, 51
	srli	a3, a3, 51
	or	a2, a3, a2
	lui	a3, 1
	addiw	a4, a3, 1
	srliw	a1, a1, 13
	bltu	a2, a4, .LBB5_14
	addi	a1, a1, 1
	srliw	a0, a0, 31
	slli	a0, a0, 15
	or	a0, a1, a0
	ret
.LBB5_14:
	bne	a2, a3, .LBB5_3
	andi	a2, a1, 1
	add	a1, a2, a1
	srliw	a0, a0, 31
	slli	a0, a0, 15
	or	a0, a1, a0
	ret
.Lfunc_end5:
	.size	__truncsfhf2, .Lfunc_end5-__truncsfhf2
	.cfi_endproc

	.weak	__extendhfsf2
	.p2align	2
	.type	__extendhfsf2,@function
__extendhfsf2:
.Lfunc_begin6:
	.cfi_startproc
	slli	a1, a0, 49
	srli	a1, a1, 49
	addi	a2, a1, -1024
	slli	a2, a2, 48
	srli	a2, a2, 59
	li	a3, 14
	bltu	a3, a2, .LBB6_2
	slli	a1, a1, 13
	lui	a2, 229376
	add	a1, a1, a2
	j	.LBB6_11
.LBB6_2:
	srli	a2, a1, 10
	li	a3, 31
	bltu	a2, a3, .LBB6_4
	slli	a1, a1, 13
	lui	a2, 522240
	or	a1, a1, a2
	j	.LBB6_11
.LBB6_4:
	beqz	a1, .LBB6_11
	sltiu	a2, a1, 256
	xori	a2, a2, 1
	slli	a2, a2, 3
	srlw	a3, a1, a2
	sltiu	a2, a3, 16
	xori	a5, a2, 1
	li	a6, 256
	li	a4, 32
	bltu	a1, a6, .LBB6_7
	li	a4, 24
.LBB6_7:
	slli	a5, a5, 2
	srlw	a3, a3, a5
	sltiu	a5, a3, 4
	xori	a6, a5, 1
	addi	a2, a2, -1
	andi	a2, a2, -4
	add	a2, a4, a2
	slli	a6, a6, 1
	srlw	a3, a3, a6
	addi	a5, a5, -1
	andi	a5, a5, -2
	li	a4, 2
	add	a2, a2, a5
	bltu	a3, a4, .LBB6_9
	li	a3, -2
	j	.LBB6_10
.LBB6_9:
	negw	a3, a3
.LBB6_10:
	add	a2, a3, a2
	addi	a3, a2, -8
	sllw	a1, a1, a3
	lui	a3, 2048
	xor	a1, a1, a3
	slli	a2, a2, 23
	lui	a3, 274432
	subw	a3, a3, a2
	or	a1, a1, a3
.LBB6_11:
	lui	a2, 8
	and	a0, a0, a2
	slli	a0, a0, 16
	or	a0, a1, a0
	fmv.w.x	fa0, a0
	ret
.Lfunc_end6:
	.size	__extendhfsf2, .Lfunc_end6-__extendhfsf2
	.cfi_endproc

	.type	.L.str,@object
	.section	.rodata,"a",@progbits
.L.str:
	.asciz	"TypeError"
	.size	.L.str, 10

	.type	.L.str.1,@object
.L.str.1:
	.asciz	"Expected "
	.size	.L.str.1, 10

	.type	.L.str.2,@object
.L.str.2:
	.asciz	"3"
	.size	.L.str.2, 2

	.type	.L.str.3,@object
.L.str.3:
	.asciz	" arguments"
	.size	.L.str.3, 11

	.type	.L.str.4,@object
.L.str.4:
	.asciz	" when calling:\n  `"
	.size	.L.str.4, 19

	.type	.L.str.5,@object
.L.str.5:
	.asciz	"dotproduct(a: Tensor([64], float32), b: Tensor([64], float32), c: Tensor([1], float32))"
	.size	.L.str.5, 88

	.type	.L.str.6,@object
.L.str.6:
	.asciz	"`"
	.size	.L.str.6, 2

	.type	.L.str.7,@object
.L.str.7:
	.asciz	"args pointer is NULL"
	.size	.L.str.7, 21

	.type	.L.str.8,@object
.L.str.8:
	.asciz	"Mismatched type on argument #"
	.size	.L.str.8, 30

	.type	.L.str.9,@object
.L.str.9:
	.asciz	"0"
	.size	.L.str.9, 2

	.type	.L.str.10,@object
.L.str.10:
	.asciz	"`,\n  expected "
	.size	.L.str.10, 15

	.type	.L.str.11,@object
.L.str.11:
	.asciz	"Tensor"
	.size	.L.str.11, 7

	.type	.L.str.12,@object
.L.str.12:
	.asciz	"1"
	.size	.L.str.12, 2

	.type	.L.str.13,@object
.L.str.13:
	.asciz	"2"
	.size	.L.str.13, 2

	.type	.L.str.14,@object
.L.str.14:
	.asciz	"ValueError"
	.size	.L.str.14, 11

	.type	.L.str.15,@object
.L.str.15:
	.asciz	"Mismatched "
	.size	.L.str.15, 12

	.type	.L.str.16,@object
.L.str.16:
	.asciz	"a"
	.size	.L.str.16, 2

	.type	.L.str.17,@object
.L.str.17:
	.asciz	".ndim on argument #"
	.size	.L.str.17, 20

	.type	.L.str.18,@object
.L.str.18:
	.asciz	".dtype on argument #"
	.size	.L.str.18, 21

	.type	.L.str.19,@object
.L.str.19:
	.asciz	"float32"
	.size	.L.str.19, 8

	.type	.L.str.20,@object
.L.str.20:
	.asciz	".device_type on argument #"
	.size	.L.str.20, 27

	.type	.L.str.21,@object
.L.str.21:
	.asciz	"cpu"
	.size	.L.str.21, 4

	.type	.L.str.22,@object
.L.str.22:
	.asciz	"b"
	.size	.L.str.22, 2

	.type	.L.str.23,@object
.L.str.23:
	.asciz	"c"
	.size	.L.str.23, 2

	.type	.L.str.24,@object
.L.str.24:
	.asciz	".strides on argument #"
	.size	.L.str.24, 23

	.type	.L.str.25,@object
.L.str.25:
	.asciz	"`,\n  expected to be compact array"
	.size	.L.str.25, 34

	.type	.L.str.26,@object
.L.str.26:
	.asciz	" data pointer is NULL on argument #"
	.size	.L.str.26, 36

	.type	.L.str.27,@object
.L.str.27:
	.asciz	"`,\n  expected non-NULL data pointer"
	.size	.L.str.27, 36

	.type	.L.str.28,@object
.L.str.28:
	.asciz	"b.device_id"
	.size	.L.str.28, 12

	.type	.L.str.29,@object
.L.str.29:
	.asciz	" on argument #"
	.size	.L.str.29, 15

	.type	.L.str.30,@object
.L.str.30:
	.asciz	"`,\n  expected to match "
	.size	.L.str.30, 24

	.type	.L.str.31,@object
.L.str.31:
	.asciz	"a.device_id"
	.size	.L.str.31, 12

	.type	.L.str.32,@object
.L.str.32:
	.asciz	"c.device_id"
	.size	.L.str.32, 12

	.type	.L.str.33,@object
.L.str.33:
	.asciz	"Invalid "
	.size	.L.str.33, 9

	.type	.L.str.34,@object
.L.str.34:
	.asciz	"a.shape[0]"
	.size	.L.str.34, 11

	.type	.L.str.35,@object
.L.str.35:
	.asciz	"64"
	.size	.L.str.35, 3

	.type	.L.str.36,@object
.L.str.36:
	.asciz	"a.byte_offset"
	.size	.L.str.36, 14

	.type	.L.str.37,@object
.L.str.37:
	.asciz	"b.shape[0]"
	.size	.L.str.37, 11

	.type	.L.str.38,@object
.L.str.38:
	.asciz	"b.byte_offset"
	.size	.L.str.38, 14

	.type	.L.str.39,@object
.L.str.39:
	.asciz	"c.shape[0]"
	.size	.L.str.39, 11

	.type	.L.str.40,@object
.L.str.40:
	.asciz	"c.byte_offset"
	.size	.L.str.40, 14

	.section	.debug_loc,"",@progbits
.Ldebug_loc0:
	.quad	-1
	.quad	.Lfunc_begin0
	.quad	.Lfunc_begin0-.Lfunc_begin0
	.quad	.Ltmp38-.Lfunc_begin0
	.half	1
	.byte	91
	.quad	.Ltmp74-.Lfunc_begin0
	.quad	.Ltmp75-.Lfunc_begin0
	.half	1
	.byte	91
	.quad	.Ltmp77-.Lfunc_begin0
	.quad	.Ltmp78-.Lfunc_begin0
	.half	1
	.byte	91
	.quad	.Ltmp81-.Lfunc_begin0
	.quad	.Ltmp83-.Lfunc_begin0
	.half	1
	.byte	91
	.quad	.Ltmp86-.Lfunc_begin0
	.quad	.Ltmp87-.Lfunc_begin0
	.half	1
	.byte	91
	.quad	.Ltmp88-.Lfunc_begin0
	.quad	.Ltmp89-.Lfunc_begin0
	.half	1
	.byte	91
	.quad	.Ltmp90-.Lfunc_begin0
	.quad	.Ltmp92-.Lfunc_begin0
	.half	1
	.byte	91
	.quad	.Ltmp95-.Lfunc_begin0
	.quad	.Ltmp97-.Lfunc_begin0
	.half	1
	.byte	91
	.quad	.Ltmp100-.Lfunc_begin0
	.quad	.Ltmp102-.Lfunc_begin0
	.half	1
	.byte	91
	.quad	.Ltmp105-.Lfunc_begin0
	.quad	.Ltmp107-.Lfunc_begin0
	.half	1
	.byte	91
	.quad	.Ltmp110-.Lfunc_begin0
	.quad	.Ltmp112-.Lfunc_begin0
	.half	1
	.byte	91
	.quad	.Ltmp115-.Lfunc_begin0
	.quad	.Ltmp117-.Lfunc_begin0
	.half	1
	.byte	91
	.quad	.Ltmp120-.Lfunc_begin0
	.quad	.Ltmp122-.Lfunc_begin0
	.half	1
	.byte	91
	.quad	.Ltmp125-.Lfunc_begin0
	.quad	.Ltmp127-.Lfunc_begin0
	.half	1
	.byte	91
	.quad	.Ltmp130-.Lfunc_begin0
	.quad	.Ltmp132-.Lfunc_begin0
	.half	1
	.byte	91
	.quad	0
	.quad	0
.Ldebug_loc1:
	.quad	-1
	.quad	.Lfunc_begin0
	.quad	.Lfunc_begin0-.Lfunc_begin0
	.quad	.Ltmp0-.Lfunc_begin0
	.half	1
	.byte	92
	.quad	0
	.quad	0
.Ldebug_loc2:
	.quad	-1
	.quad	.Lfunc_begin0
	.quad	.Ltmp4-.Lfunc_begin0
	.quad	.Ltmp19-.Lfunc_begin0
	.half	1
	.byte	93
	.quad	.Ltmp74-.Lfunc_begin0
	.quad	.Ltmp76-.Lfunc_begin0
	.half	1
	.byte	93
	.quad	.Ltmp77-.Lfunc_begin0
	.quad	.Ltmp80-.Lfunc_begin0
	.half	1
	.byte	93
	.quad	.Ltmp81-.Lfunc_begin0
	.quad	.Ltmp85-.Lfunc_begin0
	.half	1
	.byte	93
	.quad	.Ltmp90-.Lfunc_begin0
	.quad	.Ltmp94-.Lfunc_begin0
	.half	1
	.byte	93
	.quad	0
	.quad	0
.Ldebug_loc3:
	.quad	-1
	.quad	.Lfunc_begin0
	.quad	.Ltmp8-.Lfunc_begin0
	.quad	.Ltmp27-.Lfunc_begin0
	.half	1
	.byte	92
	.quad	.Ltmp77-.Lfunc_begin0
	.quad	.Ltmp79-.Lfunc_begin0
	.half	1
	.byte	92
	.quad	.Ltmp81-.Lfunc_begin0
	.quad	.Ltmp84-.Lfunc_begin0
	.half	1
	.byte	92
	.quad	.Ltmp90-.Lfunc_begin0
	.quad	.Ltmp93-.Lfunc_begin0
	.half	1
	.byte	92
	.quad	.Ltmp95-.Lfunc_begin0
	.quad	.Ltmp98-.Lfunc_begin0
	.half	1
	.byte	92
	.quad	.Ltmp100-.Lfunc_begin0
	.quad	.Ltmp103-.Lfunc_begin0
	.half	1
	.byte	92
	.quad	.Ltmp105-.Lfunc_begin0
	.quad	.Ltmp108-.Lfunc_begin0
	.half	1
	.byte	92
	.quad	.Ltmp110-.Lfunc_begin0
	.quad	.Ltmp113-.Lfunc_begin0
	.half	1
	.byte	92
	.quad	0
	.quad	0
.Ldebug_loc4:
	.quad	-1
	.quad	.Lfunc_begin0
	.quad	.Ltmp20-.Lfunc_begin0
	.quad	.Ltmp65-.Lfunc_begin0
	.half	2
	.byte	125
	.byte	0
	.quad	.Ltmp95-.Lfunc_begin0
	.quad	.Ltmp99-.Lfunc_begin0
	.half	2
	.byte	125
	.byte	0
	.quad	.Ltmp100-.Lfunc_begin0
	.quad	.Ltmp104-.Lfunc_begin0
	.half	2
	.byte	125
	.byte	0
	.quad	.Ltmp105-.Lfunc_begin0
	.quad	.Ltmp109-.Lfunc_begin0
	.half	2
	.byte	125
	.byte	0
	.quad	.Ltmp110-.Lfunc_begin0
	.quad	.Ltmp114-.Lfunc_begin0
	.half	2
	.byte	125
	.byte	0
	.quad	.Ltmp115-.Lfunc_begin0
	.quad	.Ltmp118-.Lfunc_begin0
	.half	2
	.byte	125
	.byte	0
	.quad	.Ltmp120-.Lfunc_begin0
	.quad	.Ltmp123-.Lfunc_begin0
	.half	2
	.byte	125
	.byte	0
	.quad	.Ltmp125-.Lfunc_begin0
	.quad	.Ltmp128-.Lfunc_begin0
	.half	2
	.byte	125
	.byte	0
	.quad	.Ltmp130-.Lfunc_begin0
	.quad	.Ltmp133-.Lfunc_begin0
	.half	2
	.byte	125
	.byte	0
	.quad	.Ltmp135-.Lfunc_begin0
	.quad	.Ltmp136-.Lfunc_begin0
	.half	2
	.byte	125
	.byte	0
	.quad	.Ltmp139-.Lfunc_begin0
	.quad	.Ltmp140-.Lfunc_begin0
	.half	2
	.byte	125
	.byte	0
	.quad	.Ltmp143-.Lfunc_begin0
	.quad	.Ltmp144-.Lfunc_begin0
	.half	2
	.byte	125
	.byte	0
	.quad	.Ltmp147-.Lfunc_begin0
	.quad	.Ltmp151-.Lfunc_begin0
	.half	2
	.byte	125
	.byte	0
	.quad	.Ltmp155-.Lfunc_begin0
	.quad	.Ltmp159-.Lfunc_begin0
	.half	2
	.byte	125
	.byte	0
	.quad	.Ltmp163-.Lfunc_begin0
	.quad	.Ltmp167-.Lfunc_begin0
	.half	2
	.byte	125
	.byte	0
	.quad	.Ltmp171-.Lfunc_begin0
	.quad	.Ltmp175-.Lfunc_begin0
	.half	2
	.byte	125
	.byte	0
	.quad	.Ltmp179-.Lfunc_begin0
	.quad	.Ltmp183-.Lfunc_begin0
	.half	2
	.byte	125
	.byte	0
	.quad	.Ltmp187-.Lfunc_begin0
	.quad	.Ltmp191-.Lfunc_begin0
	.half	2
	.byte	125
	.byte	0
	.quad	.Ltmp195-.Lfunc_begin0
	.quad	.Ltmp199-.Lfunc_begin0
	.half	2
	.byte	125
	.byte	0
	.quad	.Ltmp203-.Lfunc_begin0
	.quad	.Ltmp207-.Lfunc_begin0
	.half	2
	.byte	125
	.byte	0
	.quad	0
	.quad	0
.Ldebug_loc5:
	.quad	-1
	.quad	.Lfunc_begin0
	.quad	.Ltmp13-.Lfunc_begin0
	.quad	.Ltmp36-.Lfunc_begin0
	.half	1
	.byte	90
	.quad	.Ltmp81-.Lfunc_begin0
	.quad	.Ltmp82-.Lfunc_begin0
	.half	1
	.byte	90
	.quad	.Ltmp90-.Lfunc_begin0
	.quad	.Ltmp91-.Lfunc_begin0
	.half	1
	.byte	90
	.quad	.Ltmp95-.Lfunc_begin0
	.quad	.Ltmp96-.Lfunc_begin0
	.half	1
	.byte	90
	.quad	.Ltmp100-.Lfunc_begin0
	.quad	.Ltmp101-.Lfunc_begin0
	.half	1
	.byte	90
	.quad	.Ltmp105-.Lfunc_begin0
	.quad	.Ltmp106-.Lfunc_begin0
	.half	1
	.byte	90
	.quad	.Ltmp110-.Lfunc_begin0
	.quad	.Ltmp111-.Lfunc_begin0
	.half	1
	.byte	90
	.quad	.Ltmp115-.Lfunc_begin0
	.quad	.Ltmp116-.Lfunc_begin0
	.half	1
	.byte	90
	.quad	.Ltmp120-.Lfunc_begin0
	.quad	.Ltmp121-.Lfunc_begin0
	.half	1
	.byte	90
	.quad	.Ltmp125-.Lfunc_begin0
	.quad	.Ltmp126-.Lfunc_begin0
	.half	1
	.byte	90
	.quad	.Ltmp130-.Lfunc_begin0
	.quad	.Ltmp131-.Lfunc_begin0
	.half	1
	.byte	90
	.quad	0
	.quad	0
.Ldebug_loc6:
	.quad	-1
	.quad	.Lfunc_begin0
	.quad	.Ltmp28-.Lfunc_begin0
	.quad	.Ltmp70-.Lfunc_begin0
	.half	2
	.byte	126
	.byte	0
	.quad	.Ltmp115-.Lfunc_begin0
	.quad	.Ltmp119-.Lfunc_begin0
	.half	2
	.byte	126
	.byte	0
	.quad	.Ltmp120-.Lfunc_begin0
	.quad	.Ltmp124-.Lfunc_begin0
	.half	2
	.byte	126
	.byte	0
	.quad	.Ltmp125-.Lfunc_begin0
	.quad	.Ltmp129-.Lfunc_begin0
	.half	2
	.byte	126
	.byte	0
	.quad	.Ltmp130-.Lfunc_begin0
	.quad	.Ltmp134-.Lfunc_begin0
	.half	2
	.byte	126
	.byte	0
	.quad	.Ltmp135-.Lfunc_begin0
	.quad	.Ltmp137-.Lfunc_begin0
	.half	2
	.byte	126
	.byte	0
	.quad	.Ltmp139-.Lfunc_begin0
	.quad	.Ltmp141-.Lfunc_begin0
	.half	2
	.byte	126
	.byte	0
	.quad	.Ltmp143-.Lfunc_begin0
	.quad	.Ltmp145-.Lfunc_begin0
	.half	2
	.byte	126
	.byte	0
	.quad	.Ltmp147-.Lfunc_begin0
	.quad	.Ltmp152-.Lfunc_begin0
	.half	2
	.byte	126
	.byte	0
	.quad	.Ltmp155-.Lfunc_begin0
	.quad	.Ltmp160-.Lfunc_begin0
	.half	2
	.byte	126
	.byte	0
	.quad	.Ltmp163-.Lfunc_begin0
	.quad	.Ltmp168-.Lfunc_begin0
	.half	2
	.byte	126
	.byte	0
	.quad	.Ltmp171-.Lfunc_begin0
	.quad	.Ltmp176-.Lfunc_begin0
	.half	2
	.byte	126
	.byte	0
	.quad	.Ltmp179-.Lfunc_begin0
	.quad	.Ltmp184-.Lfunc_begin0
	.half	2
	.byte	126
	.byte	0
	.quad	.Ltmp187-.Lfunc_begin0
	.quad	.Ltmp192-.Lfunc_begin0
	.half	2
	.byte	126
	.byte	0
	.quad	.Ltmp195-.Lfunc_begin0
	.quad	.Ltmp200-.Lfunc_begin0
	.half	2
	.byte	126
	.byte	0
	.quad	.Ltmp203-.Lfunc_begin0
	.quad	.Ltmp208-.Lfunc_begin0
	.half	2
	.byte	126
	.byte	0
	.quad	.Ltmp211-.Lfunc_begin0
	.quad	.Ltmp215-.Lfunc_begin0
	.half	2
	.byte	126
	.byte	0
	.quad	.Ltmp218-.Lfunc_begin0
	.quad	.Ltmp222-.Lfunc_begin0
	.half	2
	.byte	126
	.byte	0
	.quad	.Ltmp225-.Lfunc_begin0
	.quad	.Ltmp229-.Lfunc_begin0
	.half	2
	.byte	126
	.byte	0
	.quad	0
	.quad	0
.Ldebug_loc7:
	.quad	-1
	.quad	.Lfunc_begin0
	.quad	.Ltmp37-.Lfunc_begin0
	.quad	.Ltmp73-.Lfunc_begin0
	.half	2
	.byte	127
	.byte	0
	.quad	.Ltmp135-.Lfunc_begin0
	.quad	.Ltmp138-.Lfunc_begin0
	.half	2
	.byte	127
	.byte	0
	.quad	.Ltmp139-.Lfunc_begin0
	.quad	.Ltmp142-.Lfunc_begin0
	.half	2
	.byte	127
	.byte	0
	.quad	.Ltmp143-.Lfunc_begin0
	.quad	.Ltmp146-.Lfunc_begin0
	.half	2
	.byte	127
	.byte	0
	.quad	.Ltmp147-.Lfunc_begin0
	.quad	.Ltmp153-.Lfunc_begin0
	.half	2
	.byte	127
	.byte	0
	.quad	.Ltmp155-.Lfunc_begin0
	.quad	.Ltmp161-.Lfunc_begin0
	.half	2
	.byte	127
	.byte	0
	.quad	.Ltmp163-.Lfunc_begin0
	.quad	.Ltmp169-.Lfunc_begin0
	.half	2
	.byte	127
	.byte	0
	.quad	.Ltmp171-.Lfunc_begin0
	.quad	.Ltmp177-.Lfunc_begin0
	.half	2
	.byte	127
	.byte	0
	.quad	.Ltmp179-.Lfunc_begin0
	.quad	.Ltmp185-.Lfunc_begin0
	.half	2
	.byte	127
	.byte	0
	.quad	.Ltmp187-.Lfunc_begin0
	.quad	.Ltmp193-.Lfunc_begin0
	.half	2
	.byte	127
	.byte	0
	.quad	.Ltmp195-.Lfunc_begin0
	.quad	.Ltmp201-.Lfunc_begin0
	.half	2
	.byte	127
	.byte	0
	.quad	.Ltmp203-.Lfunc_begin0
	.quad	.Ltmp209-.Lfunc_begin0
	.half	2
	.byte	127
	.byte	0
	.quad	.Ltmp211-.Lfunc_begin0
	.quad	.Ltmp217-.Lfunc_begin0
	.half	2
	.byte	127
	.byte	0
	.quad	.Ltmp218-.Lfunc_begin0
	.quad	.Ltmp223-.Lfunc_begin0
	.half	2
	.byte	127
	.byte	0
	.quad	.Ltmp225-.Lfunc_begin0
	.quad	.Ltmp230-.Lfunc_begin0
	.half	2
	.byte	127
	.byte	0
	.quad	.Ltmp232-.Lfunc_begin0
	.quad	.Ltmp236-.Lfunc_begin0
	.half	2
	.byte	127
	.byte	0
	.quad	.Ltmp238-.Lfunc_begin0
	.quad	.Ltmp242-.Lfunc_begin0
	.half	2
	.byte	127
	.byte	0
	.quad	0
	.quad	0
.Ldebug_loc8:
	.quad	-1
	.quad	.Lfunc_begin0
	.quad	.Ltmp44-.Lfunc_begin0
	.quad	.Ltmp63-.Lfunc_begin0
	.half	2
	.byte	118
	.byte	0
	.quad	.Ltmp147-.Lfunc_begin0
	.quad	.Ltmp203-.Lfunc_begin0
	.half	2
	.byte	118
	.byte	0
	.quad	0
	.quad	0
.Ldebug_loc9:
	.quad	-1
	.quad	.Lfunc_begin0
	.quad	.Ltmp45-.Lfunc_begin0
	.quad	.Ltmp53-.Lfunc_begin0
	.half	2
	.byte	141
	.byte	0
	.quad	0
	.quad	0
.Ldebug_loc10:
	.quad	-1
	.quad	.Lfunc_begin0
	.quad	.Ltmp46-.Lfunc_begin0
	.quad	.Ltmp73-.Lfunc_begin0
	.half	2
	.byte	122
	.byte	0
	.quad	.Ltmp147-.Lfunc_begin0
	.quad	.Ltmp148-.Lfunc_begin0
	.half	2
	.byte	122
	.byte	0
	.quad	.Ltmp155-.Lfunc_begin0
	.quad	.Ltmp156-.Lfunc_begin0
	.half	2
	.byte	122
	.byte	0
	.quad	.Ltmp163-.Lfunc_begin0
	.quad	.Ltmp164-.Lfunc_begin0
	.half	2
	.byte	122
	.byte	0
	.quad	.Ltmp171-.Lfunc_begin0
	.quad	.Ltmp172-.Lfunc_begin0
	.half	2
	.byte	122
	.byte	0
	.quad	.Ltmp179-.Lfunc_begin0
	.quad	.Ltmp180-.Lfunc_begin0
	.half	2
	.byte	122
	.byte	0
	.quad	.Ltmp187-.Lfunc_begin0
	.quad	.Ltmp188-.Lfunc_begin0
	.half	2
	.byte	122
	.byte	0
	.quad	.Ltmp195-.Lfunc_begin0
	.quad	.Ltmp196-.Lfunc_begin0
	.half	2
	.byte	122
	.byte	0
	.quad	.Ltmp203-.Lfunc_begin0
	.quad	.Ltmp204-.Lfunc_begin0
	.half	2
	.byte	122
	.byte	0
	.quad	.Ltmp211-.Lfunc_begin0
	.quad	.Ltmp212-.Lfunc_begin0
	.half	2
	.byte	122
	.byte	0
	.quad	.Ltmp218-.Lfunc_begin0
	.quad	.Ltmp219-.Lfunc_begin0
	.half	2
	.byte	122
	.byte	0
	.quad	.Ltmp225-.Lfunc_begin0
	.quad	.Ltmp226-.Lfunc_begin0
	.half	2
	.byte	122
	.byte	0
	.quad	.Ltmp232-.Lfunc_begin0
	.quad	.Ltmp233-.Lfunc_begin0
	.half	2
	.byte	122
	.byte	0
	.quad	.Ltmp238-.Lfunc_begin0
	.quad	.Ltmp239-.Lfunc_begin0
	.half	2
	.byte	122
	.byte	0
	.quad	0
	.quad	0
.Ldebug_loc11:
	.quad	-1
	.quad	.Lfunc_begin0
	.quad	.Ltmp47-.Lfunc_begin0
	.quad	.Ltmp67-.Lfunc_begin0
	.half	2
	.byte	117
	.byte	0
	.quad	.Ltmp147-.Lfunc_begin0
	.quad	.Ltmp217-.Lfunc_begin0
	.half	2
	.byte	117
	.byte	0
	.quad	0
	.quad	0
.Ldebug_loc12:
	.quad	-1
	.quad	.Lfunc_begin0
	.quad	.Ltmp48-.Lfunc_begin0
	.quad	.Ltmp57-.Lfunc_begin0
	.half	2
	.byte	140
	.byte	0
	.quad	.Ltmp147-.Lfunc_begin0
	.quad	.Ltmp163-.Lfunc_begin0
	.half	2
	.byte	140
	.byte	0
	.quad	0
	.quad	0
.Ldebug_loc13:
	.quad	-1
	.quad	.Lfunc_begin0
	.quad	.Ltmp49-.Lfunc_begin0
	.quad	.Ltmp73-.Lfunc_begin0
	.half	2
	.byte	123
	.byte	0
	.quad	.Ltmp147-.Lfunc_begin0
	.quad	.Ltmp149-.Lfunc_begin0
	.half	2
	.byte	123
	.byte	0
	.quad	.Ltmp155-.Lfunc_begin0
	.quad	.Ltmp157-.Lfunc_begin0
	.half	2
	.byte	123
	.byte	0
	.quad	.Ltmp163-.Lfunc_begin0
	.quad	.Ltmp165-.Lfunc_begin0
	.half	2
	.byte	123
	.byte	0
	.quad	.Ltmp171-.Lfunc_begin0
	.quad	.Ltmp173-.Lfunc_begin0
	.half	2
	.byte	123
	.byte	0
	.quad	.Ltmp179-.Lfunc_begin0
	.quad	.Ltmp181-.Lfunc_begin0
	.half	2
	.byte	123
	.byte	0
	.quad	.Ltmp187-.Lfunc_begin0
	.quad	.Ltmp189-.Lfunc_begin0
	.half	2
	.byte	123
	.byte	0
	.quad	.Ltmp195-.Lfunc_begin0
	.quad	.Ltmp197-.Lfunc_begin0
	.half	2
	.byte	123
	.byte	0
	.quad	.Ltmp203-.Lfunc_begin0
	.quad	.Ltmp205-.Lfunc_begin0
	.half	2
	.byte	123
	.byte	0
	.quad	.Ltmp211-.Lfunc_begin0
	.quad	.Ltmp213-.Lfunc_begin0
	.half	2
	.byte	123
	.byte	0
	.quad	.Ltmp218-.Lfunc_begin0
	.quad	.Ltmp220-.Lfunc_begin0
	.half	2
	.byte	123
	.byte	0
	.quad	.Ltmp225-.Lfunc_begin0
	.quad	.Ltmp227-.Lfunc_begin0
	.half	2
	.byte	123
	.byte	0
	.quad	.Ltmp232-.Lfunc_begin0
	.quad	.Ltmp234-.Lfunc_begin0
	.half	2
	.byte	123
	.byte	0
	.quad	.Ltmp238-.Lfunc_begin0
	.quad	.Ltmp240-.Lfunc_begin0
	.half	2
	.byte	123
	.byte	0
	.quad	0
	.quad	0
.Ldebug_loc14:
	.quad	-1
	.quad	.Lfunc_begin0
	.quad	.Ltmp50-.Lfunc_begin0
	.quad	.Ltmp73-.Lfunc_begin0
	.half	2
	.byte	128
	.byte	0
	.quad	.Ltmp147-.Lfunc_begin0
	.quad	.Ltmp154-.Lfunc_begin0
	.half	2
	.byte	128
	.byte	0
	.quad	.Ltmp155-.Lfunc_begin0
	.quad	.Ltmp162-.Lfunc_begin0
	.half	2
	.byte	128
	.byte	0
	.quad	.Ltmp163-.Lfunc_begin0
	.quad	.Ltmp170-.Lfunc_begin0
	.half	2
	.byte	128
	.byte	0
	.quad	.Ltmp171-.Lfunc_begin0
	.quad	.Ltmp178-.Lfunc_begin0
	.half	2
	.byte	128
	.byte	0
	.quad	.Ltmp179-.Lfunc_begin0
	.quad	.Ltmp186-.Lfunc_begin0
	.half	2
	.byte	128
	.byte	0
	.quad	.Ltmp187-.Lfunc_begin0
	.quad	.Ltmp194-.Lfunc_begin0
	.half	2
	.byte	128
	.byte	0
	.quad	.Ltmp195-.Lfunc_begin0
	.quad	.Ltmp202-.Lfunc_begin0
	.half	2
	.byte	128
	.byte	0
	.quad	.Ltmp203-.Lfunc_begin0
	.quad	.Ltmp210-.Lfunc_begin0
	.half	2
	.byte	128
	.byte	0
	.quad	.Ltmp211-.Lfunc_begin0
	.quad	.Ltmp216-.Lfunc_begin0
	.half	2
	.byte	128
	.byte	0
	.quad	.Ltmp218-.Lfunc_begin0
	.quad	.Ltmp224-.Lfunc_begin0
	.half	2
	.byte	128
	.byte	0
	.quad	.Ltmp225-.Lfunc_begin0
	.quad	.Ltmp231-.Lfunc_begin0
	.half	2
	.byte	128
	.byte	0
	.quad	.Ltmp232-.Lfunc_begin0
	.quad	.Ltmp237-.Lfunc_begin0
	.half	2
	.byte	128
	.byte	0
	.quad	.Ltmp238-.Lfunc_begin0
	.quad	.Ltmp243-.Lfunc_begin0
	.half	2
	.byte	128
	.byte	0
	.quad	0
	.quad	0
.Ldebug_loc15:
	.quad	-1
	.quad	.Lfunc_begin0
	.quad	.Ltmp51-.Lfunc_begin0
	.quad	.Ltmp73-.Lfunc_begin0
	.half	2
	.byte	124
	.byte	0
	.quad	.Ltmp147-.Lfunc_begin0
	.quad	.Ltmp150-.Lfunc_begin0
	.half	2
	.byte	124
	.byte	0
	.quad	.Ltmp155-.Lfunc_begin0
	.quad	.Ltmp158-.Lfunc_begin0
	.half	2
	.byte	124
	.byte	0
	.quad	.Ltmp163-.Lfunc_begin0
	.quad	.Ltmp166-.Lfunc_begin0
	.half	2
	.byte	124
	.byte	0
	.quad	.Ltmp171-.Lfunc_begin0
	.quad	.Ltmp174-.Lfunc_begin0
	.half	2
	.byte	124
	.byte	0
	.quad	.Ltmp179-.Lfunc_begin0
	.quad	.Ltmp182-.Lfunc_begin0
	.half	2
	.byte	124
	.byte	0
	.quad	.Ltmp187-.Lfunc_begin0
	.quad	.Ltmp190-.Lfunc_begin0
	.half	2
	.byte	124
	.byte	0
	.quad	.Ltmp195-.Lfunc_begin0
	.quad	.Ltmp198-.Lfunc_begin0
	.half	2
	.byte	124
	.byte	0
	.quad	.Ltmp203-.Lfunc_begin0
	.quad	.Ltmp206-.Lfunc_begin0
	.half	2
	.byte	124
	.byte	0
	.quad	.Ltmp211-.Lfunc_begin0
	.quad	.Ltmp214-.Lfunc_begin0
	.half	2
	.byte	124
	.byte	0
	.quad	.Ltmp218-.Lfunc_begin0
	.quad	.Ltmp221-.Lfunc_begin0
	.half	2
	.byte	124
	.byte	0
	.quad	.Ltmp225-.Lfunc_begin0
	.quad	.Ltmp228-.Lfunc_begin0
	.half	2
	.byte	124
	.byte	0
	.quad	.Ltmp232-.Lfunc_begin0
	.quad	.Ltmp235-.Lfunc_begin0
	.half	2
	.byte	124
	.byte	0
	.quad	.Ltmp238-.Lfunc_begin0
	.quad	.Ltmp241-.Lfunc_begin0
	.half	2
	.byte	124
	.byte	0
	.quad	0
	.quad	0
.Ldebug_loc16:
	.quad	-1
	.quad	.Lfunc_begin0
	.quad	.Lfunc_begin3-.Lfunc_begin0
	.quad	.Ltmp249-.Lfunc_begin0
	.half	1
	.byte	90
	.quad	.Ltmp253-.Lfunc_begin0
	.quad	.Lfunc_end3-.Lfunc_begin0
	.half	1
	.byte	90
	.quad	0
	.quad	0
.Ldebug_loc17:
	.quad	-1
	.quad	.Lfunc_begin0
	.quad	.Lfunc_begin3-.Lfunc_begin0
	.quad	.Ltmp250-.Lfunc_begin0
	.half	1
	.byte	91
	.quad	.Ltmp253-.Lfunc_begin0
	.quad	.Lfunc_end3-.Lfunc_begin0
	.half	1
	.byte	91
	.quad	0
	.quad	0
.Ldebug_loc18:
	.quad	-1
	.quad	.Lfunc_begin0
	.quad	.Lfunc_begin3-.Lfunc_begin0
	.quad	.Ltmp250-.Lfunc_begin0
	.half	3
	.byte	17
	.byte	1
	.byte	159
	.quad	.Ltmp253-.Lfunc_begin0
	.quad	.Lfunc_end3-.Lfunc_begin0
	.half	3
	.byte	17
	.byte	1
	.byte	159
	.quad	0
	.quad	0
	.section	.debug_abbrev,"",@progbits
	.byte	1
	.byte	17
	.byte	1
	.byte	37
	.byte	14
	.byte	19
	.byte	5
	.byte	3
	.byte	14
	.byte	16
	.byte	23
	.byte	27
	.byte	14
	.ascii	"\264B"
	.byte	25
	.byte	17
	.byte	1
	.byte	85
	.byte	23
	.byte	0
	.byte	0
	.byte	2
	.byte	46
	.byte	1
	.byte	17
	.byte	1
	.byte	18
	.byte	6
	.byte	64
	.byte	24
	.byte	3
	.byte	14
	.byte	39
	.byte	25
	.byte	73
	.byte	19
	.byte	0
	.byte	0
	.byte	3
	.byte	5
	.byte	0
	.byte	3
	.byte	14
	.byte	73
	.byte	19
	.byte	0
	.byte	0
	.byte	4
	.byte	5
	.byte	0
	.byte	2
	.byte	23
	.byte	3
	.byte	14
	.byte	73
	.byte	19
	.byte	0
	.byte	0
	.byte	5
	.byte	52
	.byte	0
	.byte	2
	.byte	23
	.byte	3
	.byte	14
	.byte	73
	.byte	19
	.byte	0
	.byte	0
	.byte	6
	.byte	46
	.byte	1
	.byte	17
	.byte	1
	.byte	18
	.byte	6
	.byte	64
	.byte	24
	.byte	3
	.byte	14
	.byte	39
	.byte	25
	.byte	54
	.byte	11
	.byte	73
	.byte	19
	.byte	0
	.byte	0
	.byte	7
	.byte	5
	.byte	0
	.byte	2
	.byte	24
	.byte	3
	.byte	14
	.byte	73
	.byte	19
	.byte	0
	.byte	0
	.byte	8
	.byte	36
	.byte	0
	.byte	3
	.byte	14
	.byte	62
	.byte	11
	.byte	11
	.byte	11
	.byte	0
	.byte	0
	.byte	9
	.byte	15
	.byte	0
	.byte	0
	.byte	0
	.byte	10
	.byte	15
	.byte	0
	.byte	73
	.byte	19
	.byte	0
	.byte	0
	.byte	0
	.section	.debug_info,"",@progbits
.Lcu_begin0:
	.word	.Ldebug_info_end0-.Ldebug_info_start0
.Ldebug_info_start0:
	.half	4
	.word	.debug_abbrev
	.byte	8
	.byte	1
	.word	.Linfo_string0
	.half	2
	.word	.Linfo_string1
	.word	.Lline_table_start0
	.word	.Linfo_string2

	.quad	0
	.word	.Ldebug_ranges0
	.byte	2
	.quad	.Lfunc_begin0
	.word	.Lfunc_end0-.Lfunc_begin0
	.byte	1
	.byte	82
	.word	.Linfo_string3

	.word	367
	.byte	3
	.word	.Linfo_string23
	.word	374
	.byte	4
	.word	.Ldebug_loc0
	.word	.Linfo_string6
	.word	374
	.byte	4
	.word	.Ldebug_loc1
	.word	.Linfo_string7
	.word	367
	.byte	3
	.word	.Linfo_string24
	.word	374
	.byte	5
	.word	.Ldebug_loc2
	.word	.Linfo_string8
	.word	367
	.byte	5
	.word	.Ldebug_loc3
	.word	.Linfo_string9
	.word	367
	.byte	5
	.word	.Ldebug_loc4
	.word	.Linfo_string10
	.word	374
	.byte	5
	.word	.Ldebug_loc5
	.word	.Linfo_string11
	.word	367
	.byte	5
	.word	.Ldebug_loc6
	.word	.Linfo_string12
	.word	374
	.byte	5
	.word	.Ldebug_loc7
	.word	.Linfo_string13
	.word	374
	.byte	5
	.word	.Ldebug_loc8
	.word	.Linfo_string14
	.word	374
	.byte	5
	.word	.Ldebug_loc9
	.word	.Linfo_string15
	.word	374
	.byte	5
	.word	.Ldebug_loc10
	.word	.Linfo_string16
	.word	375
	.byte	5
	.word	.Ldebug_loc11
	.word	.Linfo_string18
	.word	374
	.byte	5
	.word	.Ldebug_loc12
	.word	.Linfo_string19
	.word	374
	.byte	5
	.word	.Ldebug_loc13
	.word	.Linfo_string20
	.word	375
	.byte	5
	.word	.Ldebug_loc14
	.word	.Linfo_string21
	.word	374
	.byte	5
	.word	.Ldebug_loc15
	.word	.Linfo_string22
	.word	375
	.byte	0
	.byte	6
	.quad	.Lfunc_begin3
	.word	.Lfunc_end3-.Lfunc_begin3
	.byte	1
	.byte	82
	.word	.Linfo_string5

	.byte	3
	.word	367
	.byte	4
	.word	.Ldebug_loc16
	.word	.Linfo_string16
	.word	375
	.byte	4
	.word	.Ldebug_loc17
	.word	.Linfo_string20
	.word	375
	.byte	7
	.byte	1
	.byte	92
	.word	.Linfo_string22
	.word	375
	.byte	5
	.word	.Ldebug_loc18
	.word	.Linfo_string25
	.word	367
	.byte	0
	.byte	8
	.word	.Linfo_string4
	.byte	5
	.byte	4
	.byte	9
	.byte	10
	.word	380
	.byte	8
	.word	.Linfo_string17
	.byte	4
	.byte	4
	.byte	0
.Ldebug_info_end0:
	.section	.debug_ranges,"",@progbits
.Ldebug_ranges0:
	.quad	.Lfunc_begin0
	.quad	.Lfunc_end0
	.quad	.Lfunc_begin3
	.quad	.Lfunc_end3
	.quad	0
	.quad	0
	.section	.debug_str,"MS",@progbits,1
.Linfo_string0:
	.asciz	"TVM"
.Linfo_string1:
	.asciz	"IRModule.CodeGenLLVM"
.Linfo_string2:
	.asciz	"."
.Linfo_string3:
	.asciz	"__tvm_ffi_dotproduct"
.Linfo_string4:
	.asciz	"int32"
.Linfo_string5:
	.asciz	"dotproduct_compute_"
.Linfo_string6:
	.asciz	"args"
.Linfo_string7:
	.asciz	"num_args"
.Linfo_string8:
	.asciz	"a_handle.type_index"
.Linfo_string9:
	.asciz	"b_handle.type_index"
.Linfo_string10:
	.asciz	"a_handle"
.Linfo_string11:
	.asciz	"c_handle.type_index"
.Linfo_string12:
	.asciz	"b_handle"
.Linfo_string13:
	.asciz	"c_handle"
.Linfo_string14:
	.asciz	"dotproduct.a_handle_shape"
.Linfo_string15:
	.asciz	"dotproduct.a_handle_strides"
.Linfo_string16:
	.asciz	"a"
.Linfo_string17:
	.asciz	"float32"
.Linfo_string18:
	.asciz	"dotproduct.b_handle_shape"
.Linfo_string19:
	.asciz	"dotproduct.b_handle_strides"
.Linfo_string20:
	.asciz	"b"
.Linfo_string21:
	.asciz	"dotproduct.c_handle_shape"
.Linfo_string22:
	.asciz	"c"
.Linfo_string23:
	.asciz	"self_handle"
.Linfo_string24:
	.asciz	"result"
.Linfo_string25:
	.asciz	"i"
	.section	.debug_pubnames,"",@progbits
	.word	.LpubNames_end0-.LpubNames_start0
.LpubNames_start0:
	.half	2
	.word	.Lcu_begin0
	.word	388
	.word	42
	.asciz	"__tvm_ffi_dotproduct"
	.word	292
	.asciz	"dotproduct_compute_"
	.word	0
.LpubNames_end0:
	.section	.debug_pubtypes,"",@progbits
	.word	.LpubTypes_end0-.LpubTypes_start0
.LpubTypes_start0:
	.half	2
	.word	.Lcu_begin0
	.word	388
	.word	367
	.asciz	"int32"
	.word	380
	.asciz	"float32"
	.word	0
.LpubTypes_end0:
	.section	".note.GNU-stack","",@progbits
	.section	.debug_line,"",@progbits
.Lline_table_start0:
