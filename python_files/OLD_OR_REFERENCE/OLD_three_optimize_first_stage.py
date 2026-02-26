############################################################################
######## This script will optimize the first stage #########
############################################################################

from SLiCAP import *
import numpy as np
import sympy as sp
from ..circuit import cir

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

def tune_cascode(initial_W1C_N):
    """
    Checks if the cascode can be tuned to meet its performance condition for the
    current operating point (ID1_N). It iterates by reducing the cascode width.
    Returns (bool: success, float: final_W1C_N).
    """
    W1C_N = initial_W1C_N
    target_val = 1 / (2 * np.pi * 2e9)

    for i in range(15):  # Reduced iterations for speed inside the main loop
        cir.defPar("W1C_N", W1C_N)
        try:
            gds_amp = float(cir.getParValue("g_o_X1"))
            ro_amp = 1.0 / gds_amp if gds_amp > 0 else float('inf')
            
            gm_casc = float(cir.getParValue("g_m_X7"))
            gds_casc = float(cir.getParValue("g_o_X7"))
            ro_casc = 1.0 / gds_casc if gds_casc > 0 else float('inf')

            cissX4 = float(cir.getParValue("c_iss_X4"))
        except Exception:
            # If params can't be read, this W1C_N is likely invalid. Try smaller.
            W1C_N *= 0.85
            continue

        # This formula is preserved from the original script, despite dimensional mismatch.
        current_val = ro_amp * gm_casc * ro_casc * cissX4
        
        if current_val < target_val:
            return (True, W1C_N)  # Success
        
        W1C_N *= 0.85

    return (False, None)  # Failure

# --- Optimization Parameters ---
f = sp.Symbol('f')
noise_margin = 0.7
max_ic_x1 = 5.0 # Used to calculate the starting current for the inner loop
max_size_budget = 0.4
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
best_W1C_N = 0

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
    
    # Inner loop: For this W, find the minimum ID that meets the noise spec using a binary search
    ID_high = ID1_N_start
    ID_low = 1e-7  # A very small current, but not zero
    best_ID_for_W = -1
    best_W1C_for_W = -1

    print(f"--> Searching for min ID for W1_N={W1_N*1e6:.2f}µm...")

    for j in range(15): # Binary search for 15 iterations
        ID_mid = (ID_low + ID_high) / 2
        if (ID_high - ID_low) / ID_high < 0.01:
            break # Stop if search space is small

        cir.defPar("ID1_N", ID_mid)

        noise_ok = False
        cascode_ok = False
        found_W1C_N = None

        try:
            # Pre-flight check: Verify that the operating point is valid before calling
            # the expensive doNoise function. This helps prevent hangs if the OP solver fails.
            gm_check = float(cir.getParValue("g_m_X1"))
            if not gm_check > 0:
                raise ValueError("Invalid operating point: gm <= 0")
            
            # 1. Check Noise Specification
            noise_expr = doNoise(cir, source="V1", detector="V_vo", numeric=True, pardefs='circuit').inoise
            worst_ratio = 0
            # Use fewer frequency points during search for speed
            for freq in np.logspace(3, 8, 15):
                noise_val = float(sp.N(noise_expr.subs(f, freq)))
                noise_spec = 1e-15 * (1 + 1e12 / freq**2)
                ratio = noise_val / (noise_margin * noise_spec)
                if ratio > worst_ratio:
                    worst_ratio = ratio
            
            if worst_ratio < 1:
                noise_ok = True

        except Exception as e:
            noise_ok = False

        # 2. If noise is OK, check if cascode can be tuned
        if noise_ok:
            cascode_ok, found_W1C_N = tune_cascode(W1_N)

        if noise_ok and cascode_ok:
            # This is a valid solution, store it and try an even lower current
            best_ID_for_W = ID_mid
            best_W1C_for_W = found_W1C_N
            ID_high = ID_mid
        else:
            # One or both specs not met, current is too low
            ID_low = ID_mid
    
    if best_ID_for_W < 0:
        print(f"    Could not find a valid current for this width. Stopping search.")
        break

    # We now have the minimum ID1_N for this W1_N. Calculate the cost.
    ID1_N = best_ID_for_W
    cost = (W1_N / (W_P_3rd + W_N_3rd)) * (ID1_N / ID_N_3rd)
    
    if cost < best_cost:
        best_cost = cost
        best_W1_N = W1_N
        best_ID1_N = ID1_N
        best_W1C_N = best_W1C_for_W
        print(f"New best found: W1={best_W1_N*1e6:.2f}µm, ID1={best_ID1_N*1e3:.3f}mA, W1C={best_W1C_N*1e6:.2f}µm, Cost={best_cost:.4f}")

# --- Apply the best found parameters ---
if best_W1_N > 0 and best_ID1_N > 0:
    cir.defPar("W1_N", best_W1_N)
    cir.defPar("ID1_N", best_ID1_N)
    cir.defPar("W1C_N", best_W1C_N)
else:
    print("Could not find a valid solution for W1_N and ID1_N.")
    exit()

print("\n--- Main Optimization Complete ---")

############################################################################
# Final Results
############################################################################
print("\n----- First Stage Optimization Finished -----")
if best_W1_N > 0:
    print(f"Lowest Cost Found:      {best_cost:.4f}")
    print(f"Final Optimized W1_N:   {best_W1_N*1e6:.2f} µm")
    print(f"Final Optimized ID1_N:  {best_ID1_N * 1e3:.3f} mA")
    print(f"Final Tuned W1C_N:      {best_W1C_N*1e6:.2f} µm")
else:
    print("Optimization failed to find a solution for the first stage.")