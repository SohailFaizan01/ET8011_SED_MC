############################################################################
######## This script will optimize the first stage #########
############################################################################

from SLiCAP import *
import numpy as np
import sympy as sp
from .circuit import cir

# Read IC_crit and IC from the library: getpar("IC_CRIT_X1") and getpar("IC_X1")

# Scale W and I such that IC = IC_crit for best noise performance

# obtain noise transfer

# compare to noise specification

# scale w to just meet the noise spec, whilst keeping IC = IC_crit, thus also adjusting I

# if convergent, report the obtained W, I, IC and gm


############################################################################
#####  Find IC_crit operating point & minimum W for noise spec  #####
############################################################################

max_iter  = 20
tol       = 0.01
converged = False

# Frequency range for evaluation
fmin = 1e3
fmax = 1e9
freqs = np.logspace(np.log10(fmin), np.log10(fmax), 50)
f = sp.Symbol('f')

# ------------------------------------------------------------
# Read IC values from model
# ------------------------------------------------------------
IC_crit = float(cir.getParValue("IC_CRIT_X1"))

# Current W and I
W = float(cir.getParValue("W1_N"))

# ------------------------------------------------------------
# 1) Move to IC = IC_crit
# ------------------------------------------------------------
ID = IC_crit * W
cir.defPar("ID1_N", ID)

# ------------------------------------------------------------
# 2) Noise optimization at fixed IC
# ------------------------------------------------------------

for i in range(max_iter):

    # Obtain noise transfer
    noise_sim = doNoise(cir, source="V1", detector="V_vo", numeric=True, pardefs='circuit').inoise

    worst_ratio = 0

    for freq in freqs:
        noise_sim_val = float(sp.N(noise_sim.subs(f, freq)))
        noise_spec_val = 1e-15 * (1 + 1e12 / freq**2)

        ratio = noise_sim_val / noise_spec_val
        worst_ratio = max(worst_ratio, ratio)

    # --------------------------------------------------------
    # Convergence check
    # --------------------------------------------------------
    if worst_ratio < 1 + tol:
        converged = True
        break

    # --------------------------------------------------------
    # Since noise ∝ 1/sqrt(W)
    # → W ∝ (noise_ratio)^2
    # --------------------------------------------------------
    scale = worst_ratio**2

    scale = max(0.5, min(2, scale))

    W *= scale

    # 1 µm rounding
    W = round(W * 1e6) * 1e-6

    # Maintain IC = IC_crit
    ID = IC_crit * W

    cir.defPar("W1_N", W)
    cir.defPar("ID1_N", ID)


# Increase gm
W *= 10
ID *= 5

cir.defPar("W1_N", W)
cir.defPar("ID1_N", ID)

# ------------------------------------------------------------
# Extract final values
# ------------------------------------------------------------
IC_final = float(cir.getParValue("IC_X1"))
gm_final = float(cir.getParValue("g_m_X1"))

# ------------------------------------------------------------
# Print results
# ------------------------------------------------------------
if not converged:
    print("\nWARNING: Noise optimization did not converge.")
else:
    print("\n----- IC_crit Noise Optimization Results -----")

print(f"W1_N  = {W*1e6:.1f} µm")
print(f"ID1_N = {ID*1e3:.3f} mA")
print(f"IC    = {IC_final:.3f}")
print(f"gm    = {gm_final*1e3:.2f} mS")
print(f"Iterations = {i+1}")