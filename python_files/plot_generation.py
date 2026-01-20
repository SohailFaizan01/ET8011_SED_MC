from SLiCAP import *
from .circuit import cir
# from .optimize_W_IC import noise_expr

# --- Gains ---
gain        = doLaplace(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='gain')
asymptotic  = doLaplace(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='asymptotic')
loopgain    = doLaplace(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='loopgain')
servo       = doLaplace(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='servo')
direct      = doLaplace(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='direct')


# --- Output Impedance (AC analysis to compute v(out)/i(test)) ---
#Rout_result = doLaplace(cir, numeric=True, source='I1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='gain')

# --- Plots ---
fb_model    = [gain, asymptotic, loopgain, servo, direct]
fbmodel_mag = plotSweep("fb_mag", "Magnitude plots feedback model parameters", fb_model, 1, 10e9, 200)
# onoise_mag  = plotSweep("onoise", "Output noise spectral density", [noise_expr], 1e3, 1e9, 200)
# inoise_mag  = plotSweep("inoise", "input noise spectral density", [noise_expr], 1e3, 1e9, 200, funcType='inoise')
#R_out_mag   = plotSweep("R_out", "Magnitude plot output impedance", [Rout_result], 10, 10e9, 200)

# twoport = doMatrix(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1')

# for k, v in noise.inoiseTerms.items():
#     print(f"{k}: {N(v, 3)}")
