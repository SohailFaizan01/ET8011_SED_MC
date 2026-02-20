############################################################################
######## This script will optimize the first stage #########
############################################################################

from SLiCAP import *
import numpy as np
import sympy as sp
from .circuit import cir

############################################################################
##### First Stage Optimization (Noise + Efficiency) #####
############################################################################

max_iter_noise = 20
max_iter_ic    = 20
tol = 0.01
noise_margin = 0.8

f = sp.Symbol('f')

# Local bandwidth requirement
f_local = 100e6
two_pi = 2*np.pi

############################################################################
# STEP 1 — Find minimum W from noise (at IC_crit)
############################################################################

IC_crit = float(cir.getParValue("IC_CRIT_X1"))
W  = float(cir.getParValue("W1_N"))

IC = IC_crit
ID = IC * W

cir.defPar("ID1_N", ID)

for i in range(max_iter_noise):

    noise_expr = doNoise(cir,
                         source="V1",
                         detector="V_vo",
                         numeric=True,
                         pardefs='circuit').inoise

    worst_ratio = 0

    for freq in np.logspace(3, 9, 40):
        noise_val  = float(sp.N(noise_expr.subs(f, freq)))
        noise_spec = 1e-15 * (1 + 1e12 / freq**2)
        ratio = noise_val / (noise_margin * noise_spec)
        worst_ratio = max(worst_ratio, ratio)

    if worst_ratio <= 1 + tol:
        break

    scale = worst_ratio**2
    scale = max(0.5, min(2.0, scale))

    W *= scale
    W = round(W * 1e6) * 1e-6

    ID = IC * W
    cir.defPar("W1_N", W)
    cir.defPar("ID1_N", ID)

W_min = W

############################################################################
# STEP 2 — Compute gm required to drive stage 2
############################################################################

Ciss2 = float(cir.getParValue("c_iss_X4"))

# gm_req = 10e-3
gm_req = two_pi * f_local * Ciss2

############################################################################
# STEP 3 — Reduce IC for maximum efficiency
############################################################################

IC = IC_crit
ID = IC * W_min
cir.defPar("ID1_N", ID)

for k in range(max_iter_ic):

    IC_test = IC * 0.9
    ID_test = IC_test * W_min

    cir.defPar("ID1_N", ID_test)

    gm = float(cir.getParValue("g_m_X1"))

    if gm >= gm_req:
        IC = IC_test
        ID = ID_test
    else:
        break

############################################################################
# Final Apply
############################################################################

cir.defPar("W1_N", W_min)
cir.defPar("ID1_N", ID)

IC_final = float(cir.getParValue("IC_X1"))
gm_final = float(cir.getParValue("g_m_X1"))

print("\n----- First Stage Optimization -----")
print(f"W1_N   = {W_min*1e6:.2f} µm")
print(f"ID1_N  = {ID*1e3:.3f} mA")
print(f"IC1    = {IC_final:.3f}")
print(f"gm1    = {gm_final*1e3:.3f} mS")
print(f"gm_req = {gm_req*1e3:.3f} mS")