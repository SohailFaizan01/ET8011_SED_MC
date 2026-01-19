################################################## Circuit Data ##################################################

from SLiCAP import *
from .specifications import *
import numpy as np
from sympy import *
s = symbols("s")
# t = symbols("t", real=True, positive=True)
# w = symbols("w", real=True)

fileName = "Active_E_Field_Probe"
fileName = 'KiCad/' + fileName + '/' + fileName + '.kicad_sch'

cir = makeCircuit(fileName,imgWidth=1000)
# cirAsymptotic = makeCircuit(fileName,imgWidth=1000)

# print(cir.controlled)

specs2circuit(specs, cir)

# cirAsymptotic.defPar("c_dg_X1", 0)
# cir.defPar("c_dg_X2", 0)
# cir.defPar("c_dg_X3", 0)

# --- Gains ---
gain        = doLaplace(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='gain')
asymptotic  = doLaplace(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='asymptotic')
loopgain    = doLaplace(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='loopgain')
servo       = doLaplace(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='servo')
direct      = doLaplace(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='direct')

# --- Noise ---
noise       = doNoise(cir, source="V1", detector="V_vo", numeric=True, pardefs='circuit')

# --- Output Impedance (AC analysis to compute v(out)/i(test)) ---
#Rout_result = doLaplace(cir, numeric=True, source='I1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='gain')

# --- Plots ---
fb_model    = [gain, asymptotic, loopgain, servo, direct]
fbmodel_mag = plotSweep("fb_mag", "Magnitude plots feedback model parameters", fb_model, 1, 10e9, 200)
onoise_mag  = plotSweep("onoise", "Output noise spectral density", [noise], 1e3, 1e9, 200)
# inoise_mag  = plotSweep("inoise", "input noise spectral density", [noise], 1e3, 1e9, 200, funcType='inoise')
#R_out_mag   = plotSweep("R_out", "Magnitude plot output impedance", [Rout_result], 10, 10e9, 200)

# twoport = doMatrix(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1')

# for k, v in noise.inoiseTerms.items():
#     print(f"{k}: {N(v, 3)}")
