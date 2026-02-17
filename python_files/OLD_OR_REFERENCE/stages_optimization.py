############################################################################
######## This script will optimize both the first and second stage #########
############################################################################

from SLiCAP import *
import numpy as np
import sympy as sp
from ..circuit import cir

#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#
#@@@@@@@@@@@@@@@@@@@@@@@ FIRST STAGE W OPTIMIZATION @@@@@@@@@@@@@@@@@@@@@@@#
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#

############################################################################
#####  Determine minimum W for sufficient noise performance #####
# Note: DECREASING W MEANS LESS GAIN IN THE FIRST STAGE, POWER CONSUMPTION IN THE SECOND STAGE WILL SUFFER DRASTICALLY
############################################################################

# max_iter  = 10
# tol       = 0.01        # 1% margin tolerance
# converged = False

# # Frequency range for evaluation
# fmin = 1e3
# fmax = 1e9
# freqs = np.logspace(np.log10(fmin), np.log10(fmax), 50)
# f = sp.Symbol('f')

# for i in range(max_iter):

#     # --------------------------------------------------------
#     # Obtain noise expression
#     # --------------------------------------------------------
#     noise_expr = doNoise(cir, source="V1", detector="V_vo", numeric=True, pardefs='circuit').inoise

#     W = float(cir.getParValue("W1_N"))

#     # --------------------------------------------------------
#     # Evaluate worst-case noise ratio over frequency
#     # --------------------------------------------------------
#     worst_ratio = 0

#     for freq in freqs:
#         noise_sim = float(sp.N(noise_expr.subs(f, freq)))
#         noise_spec = 1e-15 * (1 + 1e12 / freq**2)

#         ratio = noise_sim / noise_spec
#         worst_ratio = max(worst_ratio, ratio)

#     # --------------------------------------------------------
#     # Check convergence
#     # --------------------------------------------------------

#     if worst_ratio < 1 + tol:
#         converged = True
#         break

#     # --------------------------------------------------------
#     # Proportional scaling
#     # If noise too high → increase W
#     # --------------------------------------------------------
#     scale = worst_ratio**2

#     # Clamp for stability
#     scale = max(0.5, min(2.0, scale))

#     W *= scale

#     # Round to 1 µm grid
#     W = round(W * 1e6) * 1e-6

#     cir.defPar("W1_N", W)

# # ------------------------------------------------------------
# # Print results
# # ------------------------------------------------------------
# W_final = float(cir.getParValue("W1_N"))

# if not converged:
#     print("\nMaximum iterations reached — noise target not met.")
#     print(f"W = {W_final*1e6:.0f} µm")
# else:
    
#     print("\nNoise requirement satisfied.")
#     print("\n----- Noise Sizing Results -----")
#     print(f"W = {W_final*1e6:.0f} µm")
#     print(f"Iterations = {i+1}")


############################################################################
#####  Determine minimum W for sufficient loopgain #####
############################################################################




#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#
#@@@@@@@@@@@@@@@@@@@@@@@ SECOND STAGE OPTIMIZATION @@@@@@@@@@@@@@@@@@@@@@@@#
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#

############################################################################
##### Determine the ratio of Wn and Wp that yields the same gm #####
############################################################################

max_iter  = 10
tolerance = 0.01
converged = False

for i in range(max_iter):

    gm2 = float(cir.getParValue("g_m_X2"))  # PMOS
    gm3 = float(cir.getParValue("g_m_X3"))  # NMOS

    error = abs(gm2 - gm3) / max(abs(gm2), abs(gm3))

    if error < tolerance:
        converged = True
        break

    Wn = float(cir.getParValue("W_N"))
    Wp = float(cir.getParValue("W_P"))

    # --------------------------------------------------------
    # Physics-based proportional scaling
    # gm ∝ sqrt(W)  →  W ∝ gm^2
    # --------------------------------------------------------
    if gm3 < gm2:
        scale = (gm2 / gm3)**2
        scale = max(0.5, min(2.0, scale))   # clamp
        Wn *= scale
    else:
        scale = (gm3 / gm2)**2
        scale = max(0.5, min(2.0, scale))   # clamp
        Wp *= scale

    # Round to 1 µm grid
    Wn = round(Wn * 1e6) * 1e-6
    Wp = round(Wp * 1e6) * 1e-6

    cir.defPar("W_N", Wn)
    cir.defPar("W_P", Wp)

# --------------------------------------------------
# Final evaluation
# --------------------------------------------------

gm2 = float(cir.getParValue("g_m_X2"))
gm3 = float(cir.getParValue("g_m_X3"))

Wn_final = float(cir.getParValue("W_N"))
Wp_final = float(cir.getParValue("W_P"))

ratio = Wp_final / Wn_final

# --------------------------------------------------
# Print results
# --------------------------------------------------

if not converged:
    print("\nMaximum iterations reached — gm matching not achieved.")
else:
    print("\n----- Obtained gm-matched ratio -----")
    print(f"Ratio Wp/Wn = {ratio:.2f}")
    print(f"Wn = {Wn_final*1e6:.0f} µm")
    print(f"Wp = {Wp_final*1e6:.0f} µm")
    print(f"gmn = {gm3*1e3:.2f} mS")
    print(f"gmp = {gm2*1e3:.2f} mS")
    print(f"Iterations = {i+1}")


############################################################################
#### Determine required quiescent current (linearity & drive capability)####
#Need to know GM, there will be a range of solutions for a given I and W
############################################################################

# ------------------------------------------------------------
# Initial quiescent currents
# ------------------------------------------------------------
IqN = 4.5e-3
IqP = -4.5e-3

cir.defPar("ID_N", IqN)
cir.defPar("ID_P", IqP)

# ------------------------------------------------------------
# User input: desired DC loopgain magnitude
# ------------------------------------------------------------
LG_desired = 10      # example value (unitless)
max_iter   = 20
tol        = 0.01

converged = False
s = sp.Symbol('s')

for i in range(max_iter):

    # Compute loopgain
    LG = doLaplace(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='loopgain').laplace
    LG_DC = abs(sp.N(LG.subs(s, 1e3)))

    # Compare with desired
    error = (LG_DC - LG_desired)/LG_desired

    if abs(error) < tol:
        converged = True
        break

    # --------------------------------------------------------
    # Scaling rule:
    # If loopgain too small → increase current (↑gm)
    # If loopgain too large → decrease current
    # --------------------------------------------------------
    scale = max(0.5, min(2.0, LG_desired / LG_DC))              #Implement proportional scaling to speed up convergence

    IqN *= scale
    IqP  = -abs(IqN)

    cir.defPar("ID_N", IqN)
    cir.defPar("ID_P", IqP)

# ------------------------------------------------------------
# Print results
# ------------------------------------------------------------
if not converged:
    print("\nERROR: Maximum iterations reached. Desired loopgain not achieved.")
else:
    print("\n----- Bias Current Sizing Results -----")
    print(f"IqN = {IqN*1e3:.2f} mA")
    print(f"IqP = {IqP*1e3:.2f} mA")
    print(f"Iterations = {i+1}")


############################################################################
##### Determine the required Ciss to ensure sufficient bandwidth #####
############################################################################

# ------------------------------------------------------------
# User input
# ------------------------------------------------------------
BW_desired = 100e6        # desired bandwidth (Hz)
max_iter   = 10
tol        = 0.01         # 1% tolerance
converged  = False

# ------------------------------------------------------------
# Obtain loopgain transfer function
# ------------------------------------------------------------
LG = doLaplace(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='loopgain').laplace
s = sp.Symbol('s')

# ------------------------------------------------------------
# Loopgain magnitude at DC and -3dB
# ------------------------------------------------------------
LG_DC = abs(sp.N(LG.subs(s, 1e3)))
LG_3dB_target = LG_DC / sp.sqrt(2)

# ------------------------------------------------------------
# Iterative scaling
# ------------------------------------------------------------
Wn = cir.getParValue("W_N")
Wp = cir.getParValue("W_P")

for i in range(max_iter):

    # Evaluate loopgain at desired BW
    LG_eval = abs(sp.N(LG.subs(s, 2*sp.pi*BW_desired*1j)))

    # If magnitude too small → bandwidth too small → reduce W
    scale = max(0.5, min(2.0, (LG_eval/LG_3dB_target)**2))      #Implement proportional scaling to speed up convergence
    # if LG_eval < LG_3dB_target:
    #     scale = 0.8
    # else:
    #     scale = 1.2

    Wn *= scale
    Wp  = Wn * ratio

    Wn = round(Wn * 1e6) * 1e-6   # round to nearest 1 µm
    Wp = round(Wp * 1e6) * 1e-6

    cir.defPar("W_N", Wn)
    cir.defPar("W_P", Wp)

    # Recompute loopgain with new widths
    LG = doLaplace(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='loopgain').laplace

    LG_DC = abs(sp.N(LG.subs(s, 1e3)))
    LG_3dB_target = LG_DC / sp.sqrt(2)
    LG_eval = abs(sp.N(LG.subs(s, 2*sp.pi*BW_desired*1j)))

    # Check convergence
    if abs(LG_eval - LG_3dB_target)/LG_3dB_target < tol:
        converged = True
        break

# ------------------------------------------------------------
# Print results
# ------------------------------------------------------------
if not converged:
    print("\n  Maximum iterations reached — no valid bandwidth found.")
else:
    print("\nObtained desired -3dB Bandwidth.")
    print("\n----- Bandwidth Sizing Results -----")
    print(f"Wn = {Wn*1e6:.1f} µm")
    print(f"Wp = {Wp*1e6:.1f} µm")
    print(f"Iterations = {i+1}")


############################################################################
##### (Optionally) Apply pole splitting to ensure stability #####
############################################################################


#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#
#@@@@@@@@@@@@@@@@@@@@@@@ FIRST STAGE I OPTIMIZATION @@@@@@@@@@@@@@@@@@@@@@@#
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@#

############################################################################
##### Determine minimum ID1_N for sufficient drive capability #####f
# PRETTY POINTLESS AS THE ABOVE ALREADY OPTIMIZES FOR THE SPECIFIED FIRST STAGE CURRENT
############################################################################

# max_iter  = 10
# tol       = 0.01
# converged = False
# BW_desired = 100e6

# s = sp.Symbol('s')

# ID1 = float(cir.getParValue("ID1_N"))

# for i in range(max_iter):
#     # print(ID1)
#     # ------------------------------------------------------------
#     # Recompute loopgain
#     # ------------------------------------------------------------
#     LG = doLaplace(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='loopgain').laplace

#     LG_DC = abs(sp.N(LG.subs(s, 1e3)))
#     LG_3dB_target = LG_DC / sp.sqrt(2)

#     LG_eval = abs(sp.N(LG.subs(s, 2*sp.pi*BW_desired*1j)))

#     ratio = LG_3dB_target / LG_eval
#     error = ratio - 1

#     # ------------------------------------------------------------
#     # Convergence check
#     # ------------------------------------------------------------
#     if abs(error) < tol:
#         converged = True
#         break

#     # ------------------------------------------------------------
#     # Proportional scaling
#     # Since BW ∝ ID → linear scaling works well
#     # ------------------------------------------------------------
#     scale = ratio
#     # print(scale)
#     # Clamp for stability
#     scale = max(0.7, min(1.3, scale))

#     ID1 *= scale
#     # ID1 = max(ID1, 10e-6)  # prevent collapse

#     cir.defPar("ID1_N", ID1)

# # ------------------------------------------------------------
# # Print results
# # ------------------------------------------------------------

# if not converged:
#     print("\nMaximum iterations reached — no valid minimum current found.")
# else:
#     print("\nMinimum drive current found.")
#     print("\n----- Drive Current Optimization -----")
#     print(f"ID1_N = {ID1*1e3:.2f} mA")
#     print(f"Iterations = {i+1}")