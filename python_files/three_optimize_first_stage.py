############################################################################
######## This script will optimize the first stage #########
############################################################################

from SLiCAP import *
import numpy as np
import sympy as sp
from .circuit import cir

############################################################################
# This script optimizes the first stage of the amplifier based on a
# user-provided cost function and constraints.
#
# Optimization strategy (W and ID centric):
# 1. An outer loop iterates downwards through a range of possible widths (W1_N).
# 2. For each width, an inner loop finds the minimum drain current (ID1_N)
#    that satisfies the noise constraint. This search starts from a high
#    current value determined by the maximum inversion coefficient (max_ic_x1).
# 3. The cost function is evaluated for each valid (W1_N, ID1_N) pair.
# 4. The pair that yields the lowest cost is selected as the optimum.
#
############################################################################

# --- Optimization Parameters ---
f = sp.Symbol('f')
noise_margin = 0.7
max_ic_x1 = 5.0 # Used to calculate the starting current for the inner loop
max_size_budget = 0.5
tol = 0.01

# --- Normalization and Constraint values ---
W_N_3rd = float(cir.getParValue("W_N"))
W_P_3rd = float(cir.getParValue("W_P"))
ID_N_3rd = float(cir.getParValue("ID_N"))

W1_N_max = ((W_P_3rd + W_N_3rd)/( (1/max_size_budget) - 1 ))

# --- Initial values ---
best_cost = float('inf')
best_W1_N = 0
best_ID1_N = 0

print("----- Running First Stage Optimization -----")
print(f"Max W1_N constraint: {W1_N_max*1e6:.2f} µm")

############################################################################
# STEP 1 — Find optimal W1_N and ID1_N for noise and efficiency
############################################################################
# Outer loop: Iterate through possible widths, from high to low
for W1_N in np.geomspace(W1_N_max * 0.99, 1e-6, 30):
    cir.defPar("W1_N", W1_N)

    # --- Find the starting current for this width ---
    try:
        cir.defPar("IC_X1", max_ic_x1)
        ID1_N_start = float(cir.getParValue("ID1_N"))
    except Exception as e:
        # If we can't even get the starting current, this width is likely invalid.
        print(f"Skipping W1_N={W1_N*1e6:.2f}µm, cannot calculate starting current. Error: {e}")
        continue
    
    # Inner loop: For this W, find the minimum ID that meets the noise spec
    ID1_N = ID1_N_start
    for j in range(25):
        cir.defPar("ID1_N", ID1_N)
        
        try:
            print(f"--> Trying W1_N={W1_N*1e6:.2f}µm, ID1_N={ID1_N*1e3:.3f}mA")
            noise_expr = doNoise(cir, source="V1", detector="V_vo", numeric=True, pardefs='circuit').inoise
            worst_ratio = 0
            for freq in np.logspace(3, 8, 50):
                noise_val = float(sp.N(noise_expr.subs(f, freq)))
                noise_spec = 1e-15 * (1 + 1e12 / freq**2)
                ratio = noise_val / (noise_margin * noise_spec)
                if ratio > worst_ratio:
                    worst_ratio = ratio
        except Exception:
            # If doNoise fails, this point is invalid
            worst_ratio = float('inf')

        if worst_ratio == float('inf'):
            break # Exit inner loop if noise calculation fails

        if worst_ratio < 1 - tol:
            ID1_N *= 0.85 # Descend current
        else:
            # Noise is at or above the budget. Go back to the last valid current.
            ID1_N /= 0.85 
            break
    
    if worst_ratio == float('inf'):
        continue

    # We now have the minimum ID1_N for this W1_N. Calculate the cost.
    cost = (W1_N / W_P_3rd) * (ID1_N / ID_N_3rd)
    
    if cost < best_cost:
        best_cost = cost
        best_W1_N = W1_N
        best_ID1_N = ID1_N
        print(f"New best found: W1_N={best_W1_N*1e6:.2f}µm, ID1_N={best_ID1_N*1e3:.3f}mA, Cost={best_cost:.4f}")

# --- Apply the best found parameters ---
if best_W1_N > 0 and best_ID1_N > 0:
    cir.defPar("W1_N", best_W1_N)
    cir.defPar("ID1_N", best_ID1_N)
else:
    print("Could not find a valid solution for W1_N and ID1_N.")
    exit()

print("\n--- Main Optimization Complete ---")
print(f"Best W1_N: {best_W1_N*1e6:.2f} µm")
print(f"Best ID1_N: {best_ID1_N*1e3:.3f} mA")
print(f"Lowest Cost: {best_cost:.4f}")


############################################################################
# STEP 2 — Tune Cascode Width (W1C_N)
############################################################################
print("\n--- Starting Cascode Tuning (Step 2) ---")

# Start with the initial size and increment it
W1C_N = 0.1e-6
cir.defPar("W1C_N", W1C_N)

# The target value for the condition
target_val = 1 / (2 * np.pi * 2e9)

for i in range(50): # Max 50 iterations to prevent infinite loop
    # Get transistor parameters from SLiCAP
    try:
        gm_amp = float(cir.getParValue("g_m_X1"))
        ro_amp = 0.5*float(cir.getParValue("r_o_X1"))
        gm_casc = float(cir.getParValue("g_m_X2"))
        ro_casc = float(cir.getParValue("r_o_X2"))
        cissX4 = float(cir.getParValue("c_iss_X4"))
    except Exception as e:
        print(f"Error getting parameters from SLiCAP: {e}")
        W1C_N = 0 # Mark as failed
        break

    # NOTE: The following expression is implemented as per the user's comment.
    # Its physical units (Gain * Capacitance) do not match the target's units (seconds),
    # so this relies on a specific interpretation understood by the user.
    current_val = gm_amp * ro_amp * gm_casc * ro_casc * cissX4
    
    print(f"Iter {i}: W1C_N={W1C_N*1e6:.2f}µm -> Val={current_val:.3e} (Target: > {target_val:.3e})")

    if current_val > target_val:
        print("Target condition met.")
        break
    
    # Increase width to meet the condition
    W1C_N *= 1.25 # Increase by 25%
    cir.defPar("W1C_N", W1C_N)
else:
    print("Warning: Cascode tuning loop reached max iterations without meeting the condition.")


############################################################################
# Final Results
############################################################################
print("\n----- First Stage Optimization Finished -----")
if best_W1_N > 0:
    print(f"Final Optimized W1_N:  {best_W1_N*1e6:.2f} µm")
    print(f"Final Optimized ID1_N: {best_ID1_N * 1e3:.3f} mA")
else:
    print("Optimization failed to find a solution for the first stage.")

if W1C_N > 0:
    print(f"Final Tuned W1C_N:     {W1C_N*1e6:.2f} µm")
else:
    print("Cascode tuning failed.")