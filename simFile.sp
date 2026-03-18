stage_1_2_bias
I4 1 2 I value={-ID2_P} noise=0 dc=0 dcvar=0
V1 3 1 V value=0 noise=0 dc=0 dcvar=0
V5 4 0 V value={VGS1C_N} noise=0 dc=0 dcvar=0
V6 5 0 V value={VDS1T_N} noise=0 dc=0 dcvar=0
V7 6 0 V value={VDS1_N} noise=0 dc=0 dcvar=0
V8 7 0 V value={VDS1C_N} noise=0 dc=0 dcvar=0
V10 3 0 V value={VDD} noise=0 dc=0 dcvar=0
V11 8 0 V value={VGS1_N} noise=0 dc=0 dcvar=0
X1 6 8 5 0 CMOS18N W={W1_N} L={L1_N} ID={ID1_N}
X4 0 7 2 2 CMOS18P W={W2_P} L={L2_P} ID={ID2_P}
X5 6 8 5 0 CMOS18N W={W1_N} L={L1_N} ID={ID1_N}
X7 7 4 6 0 CMOS18N W={W1C_N} L={L1C_N} ID={ID1_N}
X8 7 4 6 0 CMOS18N W={W1C_N} L={L1C_N} ID={ID1_N}
.param L_ant=1/4
.param C_ant=3/250000000000
.param C_s=3/1000000000000
.param Z_in=50
.param Cable_len=25
.param T_op_min=273
.param T_op_max=343
.param P_cons=1/20
.param f_-3dB_min=9000
.param f_-3dB_max=80000000
.param P_1dB=0
.param VDD=9/5
.param E_max=1
.param P_int=50
.param Z_in_amp=50
.param Z_out_amp=50
.param V_in=1/4
.param A_cl=5/2
.param W_N=451943/20000000000
.param L_N=9/50000000
.param ID_N=2844689/50000000000
.param W_P=7061609/100000000000
.param L_P=9/50000000
.param ID_P=-2844689/50000000000
.param W1_N=610349/50000000000
.param L1_N=9/50000000
.param ID1_N=6379333/100000000000
.param W1C_N=1049667/5000000000000
.param L1C_N=9/50000000
.param W2_P=2636017/5000000000000
.param L2_P=9/50000000
.param ID2_P=-4488533/100000000000
.param R_ph=200
.param VDS1T_N=1/40
.param VDS1_N=1/20
.param VGS1_N=0
.param VDS1C_N=41/40
.param VGS1C_N=0
** Python input section **
.param L_ant=1/4
.param C_ant=3/250000000000
.param C_s=3/1000000000000
.param Z_in=50
.param Cable_len=25
.param T_op_min=273
.param T_op_max=343
.param P_cons=1/20
.param f_-3dB_min=9000
.param f_-3dB_max=80000000
.param P_1dB=0
.param VDD=9/5
.param E_max=1
.param P_int=50
.param Z_in_amp=50
.param Z_out_amp=50
.param V_in=1/4
.param A_cl=5/2
.param W_N=451943/20000000000
.param L_N=9/50000000
.param ID_N=2844689/50000000000
.param W_P=7061609/100000000000
.param L_P=9/50000000
.param ID_P=-2844689/50000000000
.param W1_N=610349/50000000000
.param L1_N=9/50000000
.param ID1_N=6379333/100000000000
.param W1C_N=1049667/5000000000000
.param L1C_N=9/50000000
.param W2_P=2636017/5000000000000
.param L2_P=9/50000000
.param ID2_P=-4488533/100000000000
.param R_ph=200
.param VDS1T_N=1/40
.param VDS1_N=1/20
.param VDS1C_N=41/40
.param VGS1_N=0.0
.param VGS1C_N=0.0
.control
set wr_vecnames
set wr_singlescale
dc V11 0.0 1.2 0.01
let I_X1 = I(V7)
let I_X8 = I(V8)
wrdata cir\stage_1_2_bias_specs.csv I_X1 I_X8
.endc
.end