############################################################################
######## This script will optimize the first stage #########
############################################################################

from SLiCAP import *
import numpy as np
import sympy as sp
from .circuit import cir

############################################################################
##### First Stage Joint Noise + Bandwidth Optimization (Improved) #####
############################################################################

max_iter_noise = 20
max_iter_bw    = 15
max_iter_ic    = 10

tol = 0.01
noise_margin = 0.8

BW_desired = 80e6

# USER SETTINGS
W_max      = 200e-6      # upper width limit
step       = 190e-6
objective  = "max_gm"    # "max_gm", "min_power", "max_gm_over_I"

f = sp.Symbol('f')
s = sp.Symbol('s')

############################################################################
# STEP 1 — Find W_min from noise at IC = IC_crit
############################################################################

IC_crit = float(cir.getParValue("IC_CRIT_X1"))
W  = float(cir.getParValue("W1_N"))

IC = IC_crit
ID = IC * W
cir.defPar("ID1_N", ID)

for i in range(max_iter_noise):

    noise_expr = doNoise(cir, source="V1", detector="V_vo",
                         numeric=True, pardefs='circuit').inoise

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
# STEP 2 — Sweep W between Wmin and Wmax
############################################################################

solutions = []

W_candidates = np.arange(W_min, W_max + step, step)

for W in W_candidates:

    W = round(W * 1e6) * 1e-6
    IC = IC_crit
    ID = IC * W

    cir.defPar("W1_N", W)
    cir.defPar("ID1_N", ID)

    ########################################################################
    # STEP 2A — Increase current until bandwidth met
    ########################################################################

    for j in range(max_iter_bw):

        LG = doLaplace(cir, numeric=True,
                       source='V1', detector='V_Amp_out',
                       pardefs='circuit',
                       lgref='Gm_M1_X1',
                       transfer='loopgain').laplace

        LG_DC = abs(sp.N(LG.subs(s, 1e3)))
        LG_3dB_target = LG_DC / sp.sqrt(2)
        LG_eval = abs(sp.N(LG.subs(s, 2*sp.pi*BW_desired*1j)))

        if LG_eval >= LG_3dB_target:
            break

        scale = LG_3dB_target / LG_eval
        ID *= scale
        cir.defPar("ID1_N", ID)

    ########################################################################
    # STEP 2B — Reduce IC for efficiency
    ########################################################################

    IC = ID / W

    for k in range(max_iter_ic):

        IC_test = IC * 0.9
        ID_test = IC_test * W
        cir.defPar("ID1_N", ID_test)

        # Check bandwidth again
        LG = doLaplace(cir, numeric=True,
                       source='V1', detector='V_Amp_out',
                       pardefs='circuit',
                       lgref='Gm_M1_X1',
                       transfer='loopgain').laplace

        LG_DC = abs(sp.N(LG.subs(s, 1e3)))
        LG_3dB_target = LG_DC / sp.sqrt(2)
        LG_eval = abs(sp.N(LG.subs(s, 2*sp.pi*BW_desired*1j)))

        if LG_eval >= LG_3dB_target:
            IC = IC_test
            ID = ID_test
        else:
            break

    ########################################################################
    # Store solution
    ########################################################################

    gm  = float(cir.getParValue("g_m_X1"))
    power = ID   # proportional (Vdd constant)

    solutions.append({
        "W": W,
        "ID": ID,
        "IC": IC,
        "gm": gm,
        "power": power
    })

############################################################################
# STEP 3 — Select Best Solution
############################################################################

best = None

for sol in solutions:

    if objective == "max_gm":
        score = sol["gm"]

    elif objective == "min_power":
        score = -sol["power"]

    elif objective == "max_gm_over_I":
        score = sol["gm"] / sol["ID"]

    if best is None or score > best["score"]:
        sol["score"] = score
        best = sol

############################################################################
# Final Apply Best
############################################################################

cir.defPar("W1_N", best["W"])
cir.defPar("ID1_N", best["ID"])

IC_final = float(cir.getParValue("IC_X1"))
gm_final = float(cir.getParValue("g_m_X1"))

print("\n----- First Stage Joint Optimization (Global) -----")
print(f"W1_N               = {best['W']*1e6:.0f} µm")
print(f"ID1_N              = {best['ID']*1e3:.2f} mA")
print(f"IC                 = {IC_final:.2f}")
print(f"gm1                = {gm_final*1e3:.1f} mS")




# Read IC_crit and IC from the library: getpar("IC_CRIT_X1") and getpar("IC_X1")

# Scale W and I such that IC = IC_crit for best noise performance

# obtain noise transfer

# compare to noise specification

# scale w to just meet the noise spec, whilst keeping IC = IC_crit, thus also adjusting I

# if convergent, report the obtained W, I, IC and gm


############################################################################
#####  Find IC_crit operating point & minimum W for noise spec  #####
############################################################################

# max_iter  = 20
# tol       = 0.01
# converged = False

# # Frequency range for evaluation
# fmin = 1e3
# fmax = 1e9
# freqs = np.logspace(np.log10(fmin), np.log10(fmax), 50)
# f = sp.Symbol('f')

# # ------------------------------------------------------------
# # Read IC values from model
# # ------------------------------------------------------------
# IC_crit = float(cir.getParValue("IC_CRIT_X1"))

# # Current W and I
# W = float(cir.getParValue("W1_N"))

# # ------------------------------------------------------------
# # 1) Move to IC = IC_crit
# # ------------------------------------------------------------
# ID = IC_crit * W
# cir.defPar("ID1_N", ID)

# # ------------------------------------------------------------
# # 2) Noise optimization at fixed IC
# # ------------------------------------------------------------

# for i in range(max_iter):

#     # Obtain noise transfer
#     noise_sim = doNoise(cir, source="V1", detector="V_vo", numeric=True, pardefs='circuit').inoise

#     worst_ratio = 0

#     for freq in freqs:
#         noise_sim_val = float(sp.N(noise_sim.subs(f, freq)))
#         noise_spec_val = 1e-15 * (1 + 1e12 / freq**2)

#         ratio = noise_sim_val / noise_spec_val
#         worst_ratio = max(worst_ratio, ratio)

#     # --------------------------------------------------------
#     # Convergence check
#     # --------------------------------------------------------
#     if worst_ratio < 1 + tol:
#         converged = True
#         break

#     # --------------------------------------------------------
#     # Since noise ∝ 1/sqrt(W)
#     # → W ∝ (noise_ratio)^2
#     # --------------------------------------------------------
#     scale = worst_ratio**2

#     scale = max(0.5, min(2, scale))

#     W *= scale

#     # 1 µm rounding
#     W = round(W * 1e6) * 1e-6

#     # Maintain IC = IC_crit
#     ID = IC_crit * W

#     cir.defPar("W1_N", W)
#     cir.defPar("ID1_N", ID)


# # Increase gm
# W *= 10
# ID *= 5

# cir.defPar("W1_N", W)
# cir.defPar("ID1_N", ID)

# # ------------------------------------------------------------
# # Extract final values
# # ------------------------------------------------------------
# IC_final = float(cir.getParValue("IC_X1"))
# gm_final = float(cir.getParValue("g_m_X1"))

# # ------------------------------------------------------------
# # Print results
# # ------------------------------------------------------------
# if not converged:
#     print("\nWARNING: Noise optimization did not converge.")
# else:
#     print("\n----- IC_crit Noise Optimization Results -----")

# print(f"W1_N  = {W*1e6:.1f} µm")
# print(f"ID1_N = {ID*1e3:.3f} mA")
# print(f"IC    = {IC_final:.3f}")
# print(f"gm    = {gm_final*1e3:.2f} mS")
# print(f"Iterations = {i+1}")