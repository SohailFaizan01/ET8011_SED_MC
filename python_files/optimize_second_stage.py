############################################################################
######## This script will optimize the second stage #########
############################################################################

from SLiCAP import *
import numpy as np
import sympy as sp
from .circuit import cir

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
    print(f"Wp = {Wp*1e6:.1f} µm")
    print(f"Wn = {Wn*1e6:.1f} µm")
    print(f"Iterations = {i+1}")


############################################################################
#### Determine required quiescent current (linearity & drive capability)####
############################################################################

# ------------------------------------------------------------
# Parameters
# ------------------------------------------------------------
gm_target = 10e-3  # target gm in S (10 mS)
max_iter  = 20
tol       = 0.01
converged = False

# Read current transistor widths (fixed)
Wn = float(cir.getParValue("W_N"))
Wp = float(cir.getParValue("W_P"))

# Initial current
ID = float(cir.getParValue("ID_N"))

# ------------------------------------------------------------
# Iterative scaling to reach target gm
# ------------------------------------------------------------
for i in range(max_iter):
    
    # Update the current in the circuit
    cir.defPar("ID_N", ID)
    cir.defPar("ID_P", -ID)
    
    # Read resulting gm
    gm_sim = float(cir.getParValue("g_m_X2"))
    gm_simn = float(cir.getParValue("g_m_X3"))
    
    # Check convergence
    gm_ratio = gm_sim / gm_target
    if abs(gm_ratio - 1) < tol:
        converged = True
        break
    
    # Scale current: gm ∝ sqrt(I)
    ID *= (gm_target / gm_sim)**2
    
    # Optional: limit scaling to avoid overshoot
    ID = max(0.5*ID, min(2*ID, ID))

# ------------------------------------------------------------
# Extract final IC
# ------------------------------------------------------------
IC_final = float(cir.getParValue("IC_X2"))
IC_finaln = float(cir.getParValue("IC_X3"))

# ------------------------------------------------------------
# Print results
# ------------------------------------------------------------
if not converged:
    print("\nWARNING: Current optimization for target gm did not converge.")
else:
    print("\n----- Output Stage gm Optimization Results -----")

print(f"Iq = {ID*1e3:.2f} mA")
print(f"gmp = {gm_sim*1e3:.2f} mS")
print(f"gmn = {gm_simn*1e3:.2f} mS")
print(f"ICp = {IC_final:.2f}")
print(f"ICn = {IC_finaln:.2f}")
print(f"Iterations = {i+1}")


############################################################################
##### (Optionally) Apply pole splitting to ensure stability #####
############################################################################