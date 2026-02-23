############################################################################
######## This script will optimize the second stage #########
############################################################################

from SLiCAP import *
import numpy as np
import sympy as sp
from .circuit import cir

print("\n--- Optimizing Second Stage (Source Follower) ---")

# ==========================================================================
# Optimization Parameters
# ==========================================================================
f_local = 100e6         # Hz, local bandwidth target for the pole formed by Rout2 and Ciss3
V_swing_est = 0.45      # V, estimated peak voltage swing required at stage 2 output to drive stage 3
drive_offset = 0.25  # %, additional current margin to ensure drive capability (accounts for non-idealities)
max_iter = 30
tolerance = 0.01

# ==========================================================================
# STEP 1: Determine target gm from bandwidth requirement
# The pole is at fp = 1 / (2*pi*Rout2*Ciss3)
# With Rout2 ~= 1/gm2, we get fp = gm2 / (2*pi*Ciss3)
# So, gm_target = 2 * pi * f_local * Ciss3
# ==========================================================================

Ciss_X2 = float(cir.getParValue("c_iss_X2"))  # PMOS of 3rd stage
Ciss_X3 = float(cir.getParValue("c_iss_X3"))  # NMOS of 3rd stage
Ciss3 = Ciss_X2 + Ciss_X3

gm_target = 2 * np.pi * f_local * Ciss3

# ==========================================================================
# STEP 2: Determine target ID from swing/slew requirement
# The bias current must be large enough to source/sink the current for the
# capacitive load of the third stage at the maximum frequency and swing.
# I_peak = C * dV/dt = C * V_peak * 2*pi*f
# Id_target >= I_peak = Ciss3 * V_swing_est * 2*pi*f_local
# This simplifies to: Id_target = V_swing_est * gm_target
# This corresponds to your formula Id = (0.45)/ro with ro=1/gm.
# ==========================================================================

Id_target = (V_swing_est * gm_target) * (1 + drive_offset)

# ==========================================================================
# STEP 3: Find transistor width W for the required gm and Id
# We have a target gm and a target Id. We use a binary search to find the
# width W that satisfies these conditions for the fixed target current.
# This method is more robust than proportional scaling, especially if the
# transistor enters weak inversion where gm becomes independent of W.
# ==========================================================================

# Set the target current, which remains fixed during the search for W.
cir.defPar("ID2_N", Id_target)

# --- Binary Search for Width ---
W_low = 0.1e-6   # Minimum realistic width
W_high = 1000e-6 # Maximum realistic width
W = (W_low + W_high) / 2.0

converged = False
for i in range(max_iter):
    # Set the midpoint width for this iteration
    W = (W_low + W_high) / 2.0
    cir.defPar("W2_N", W)

    try:
        gm_sim = float(cir.getParValue("g_m_X4"))
    except Exception as e:
        # If simulation fails, this width might be invalid.
        # Assume it's too small and increase the lower bound to avoid getting stuck.
        print(f"Warning: Simulation failed for W={W*1e6:.2f}µm. Adjusting search range.")
        W_low = W
        continue

    # Check for convergence
    error = abs(gm_sim - gm_target) / gm_target
    if error < tolerance:
        converged = True
        break

    if gm_sim < gm_target:
        # gm is too low, need a larger width
        W_low = W
    else:
        # gm is too high, need a smaller width
        W_high = W

# Final application of the determined width
W = (W_low + W_high) / 2.0
cir.defPar("W2_N", W)

# ==========================================================================
# Final application and reporting
# ==========================================================================

print("\n----- Second Stage (Source Follower) Sizing -----")
if converged:
    print(f"Converged in {i+1} iterations.")
else:
    print(f"WARNING: Max iterations ({max_iter}) reached. Result may not be accurate.")

print(f"\nTarget Bandwidth   = {f_local/1e6:.0f} MHz")
print(f"Input Cap Stage 3  = {Ciss3*1e15:.1f} fF")
print(f"Required gm        = {gm_target*1e3:.2f} mS")
print(f"Required Id        = {Id_target*1e3:.2f} mA (for {V_swing_est:.2f}V swing)")
print("----------------------------------------------------")
print(f"Final W2_N         = {W*1e6:.1f} µm")
print(f"Final ID2_N        = {Id_target*1e3:.2f} mA")
print(f"Resulting gm       = {cir.getParValue('g_m_X4')*1e3:.2f} mS")
print(f"Resulting IC       = {cir.getParValue('IC_X4'):.2f}")
