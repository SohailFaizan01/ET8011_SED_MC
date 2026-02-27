############################################################################
######## This script will optimize the second stage #########
############################################################################

from SLiCAP import *
import numpy as np


def _has_param(cir_obj, name):
    try:
        cir_obj.getParValue(name)
        return True
    except Exception:
        return False


def detect_stage2_flavor(cir_obj, preferred=None):
    """Detect whether stage-2 variables use _N or _P suffixes."""
    if preferred:
        suffix = preferred.upper()
        if all(_has_param(cir_obj, p) for p in (f"W2_{suffix}", f"ID2_{suffix}")):
            return suffix
        raise RuntimeError(
            f"Requested stage-2 flavor '{suffix}' but parameters "
            f"'W2_{suffix}' and/or 'ID2_{suffix}' were not found."
        )

    suffixes = ["N", "P"]

    for suffix in suffixes:
        if all(_has_param(cir_obj, p) for p in (f"W2_{suffix}", f"ID2_{suffix}")):
            return suffix

    raise RuntimeError(
        "Could not detect stage-2 flavor. Expected parameter pair 'W2_[N/P], ID2_[N/P]'."
    )


def optimize_second_stage(cir, stage2_flavor=None):
    print("\n--- Optimizing Second Stage (Source Follower) ---")

    suffix = detect_stage2_flavor(cir, preferred=stage2_flavor)
    id_sign = 1.0 if suffix == "N" else -1.0
    w_par = f"W2_{suffix}"
    id_par = f"ID2_{suffix}"

    # ==========================================================================
    # Optimization Parameters
    # ==========================================================================
    f_local = 100e6         # Hz, local bandwidth target for the pole formed by Rout2 and Ciss3
    V_swing_est = 0.45      # V, estimated peak voltage swing required at stage 2 output to drive stage 3
    drive_offset = 0.25     # additional current margin to ensure drive capability
    max_iter = 30
    tolerance = 0.01

    # ==========================================================================
    # STEP 1: Determine target gm from bandwidth requirement
    # ==========================================================================
    Ciss_X2 = float(cir.getParValue("c_iss_X2"))  # PMOS of 3rd stage
    Ciss_X3 = float(cir.getParValue("c_iss_X3"))  # NMOS of 3rd stage
    Ciss3 = Ciss_X2 + Ciss_X3

    gm_target = 2 * np.pi * f_local * Ciss3

    # ==========================================================================
    # STEP 2: Determine target ID magnitude from swing/slew requirement
    # ==========================================================================
    id_target_mag = (V_swing_est * gm_target) * (1 + drive_offset)
    id_target = id_sign * id_target_mag

    # ==========================================================================
    # STEP 3: Find transistor width W for required gm and ID
    # ==========================================================================
    cir.defPar(id_par, id_target)

    W_low = 0.1e-6
    W_high = 1000e-6
    W = (W_low + W_high) / 2.0

    converged = False
    for i in range(max_iter):
        W = (W_low + W_high) / 2.0
        cir.defPar(w_par, W)

        try:
            gm_sim = abs(float(cir.getParValue("g_m_X4")))
        except Exception:
            print(f"Warning: Simulation failed for W={W*1e6:.2f}um. Adjusting search range.")
            W_low = W
            continue

        error = abs(gm_sim - gm_target) / gm_target
        if error < tolerance:
            converged = True
            break

        if gm_sim < gm_target:
            W_low = W
        else:
            W_high = W

    W = (W_low + W_high) / 2.0
    cir.defPar(w_par, W)

    print(f"\n----- Second Stage ({suffix}MOS Source Follower) Sizing -----")
    if converged:
        print(f"Converged in {i+1} iterations.")
    else:
        print(f"WARNING: Max iterations ({max_iter}) reached. Result may not be accurate.")

    print(f"\nTarget Bandwidth   = {f_local/1e6:.0f} MHz")
    print(f"Input Cap Stage 3  = {Ciss3*1e15:.1f} fF")
    print(f"Required gm        = {gm_target*1e3:.2f} mS")
    print(f"Required |Id|      = {id_target_mag*1e3:.2f} mA (for {V_swing_est:.2f}V swing)")
    print("----------------------------------------------------")
    print(f"Final {w_par:<12}= {W*1e6:.1f} um")
    print(f"Final {id_par:<12}= {id_target*1e3:.2f} mA")
    print(f"Resulting gm       = {cir.getParValue('g_m_X4')*1e3:.2f} mS")
    print(f"Resulting IC       = {cir.getParValue('IC_X4'):.2f}")

    return {
        "stage2_flavor": suffix,
        "w_param": w_par,
        "id_param": id_par,
        "W2": W,
        "ID2": id_target,
        "gm_target": gm_target,
        "id_target_mag": id_target_mag,
    }
