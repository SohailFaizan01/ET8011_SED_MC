############################################################################
######## This script will optimize the second stage #########
############################################################################

from SLiCAP import *
import numpy as np
import sympy as sp
from .circuit import cir

# find IC for local bandwidth = 100MHz

# Size minimum W and I for gm => 1/(2*pi*rout*ciss) = 100MHz, ciss = ciss third stage, rout = 1/gm

############################################################################
##### Second Stage Optimization (Local Bandwidth = 100 MHz) #####
############################################################################

f_target = 100e6
two_pi = 2 * np.pi

# -------------------------------------------------------------------------
# STEP 1 — Read Ciss of third stage
# -------------------------------------------------------------------------

Ciss3 = float(cir.getParValue("C_iss_2")) + float(cir.getParValue("C_iss_X3"))   # <-- adapt name if needed

# Required gm
gm_req = two_pi * f_target * Ciss3

print(f"\nRequired gm2 = {gm_req*1e3:.3f} mS")

# -------------------------------------------------------------------------
# STEP 2 — Sweep IC to find minimum power solution
# -------------------------------------------------------------------------

IC_candidates = np.linspace(0.5, 20, 40)   # moderate → strong inversion

best_solution = None

for IC in IC_candidates:

    # Temporarily set IC
    cir.defPar("IC_X4", IC)

    # Get gm/ID from model
    gm_over_ID = float(cir.getParValue("g_m_X4")) / float(cir.getParValue("ID2_N"))

    # Required drain current
    ID = gm_req / gm_over_ID

    # Width from IC definition
    W = ID / IC

    # Enforce minimum width (optional)
    W = max(W, 1e-6)

    # Apply
    cir.defPar("W2_N", W)
    cir.defPar("ID2_N", ID)

    # Extract actual gm
    gm_actual = float(cir.getParValue("g_m_X4"))

    # Check if gm requirement satisfied
    if gm_actual >= gm_req:

        power = ID   # proportional to power (VDD constant)

        solution = {
            "IC": IC,
            "ID": ID,
            "W": W,
            "gm": gm_actual,
            "power": power
        }

        if best_solution is None or power < best_solution["power"]:
            best_solution = solution

# -------------------------------------------------------------------------
# Apply Best Solution
# -------------------------------------------------------------------------

if best_solution is None:
    print("\nNo valid second-stage solution found.")
else:
    cir.defPar("W2_N", best_solution["W"])
    cir.defPar("ID2_N", best_solution["ID"])

    print("\n----- Second Stage Optimization -----")
    print(f"W2    = {best_solution['W']*1e6:.2f} µm")
    print(f"ID2   = {best_solution['ID']*1e3:.3f} mA")
    print(f"IC2   = {best_solution['IC']:.2f}")
    print(f"gm2   = {best_solution['gm']*1e3:.3f} mS")
