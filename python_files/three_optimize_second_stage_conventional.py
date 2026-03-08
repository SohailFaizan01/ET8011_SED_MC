from SLiCAP import *
import numpy as np


def _has_param(cir_obj, name):
    try:
        cir_obj.getParValue(name)
        return True
    except Exception:
        return False


def detect_stage2_flavor_conventional(cir_obj, preferred=None):
    if preferred:
        suffix = preferred.upper()
        if suffix not in ("N", "P"):
            raise RuntimeError(f"Unsupported conventional stage-2 flavor '{preferred}'. Use 'N' or 'P'.")
        if all(_has_param(cir_obj, p) for p in (f"W2_{suffix}", f"ID2_{suffix}")):
            return suffix
        raise RuntimeError(
            f"Requested stage-2 flavor '{suffix}' but parameters "
            f"'W2_{suffix}' and/or 'ID2_{suffix}' were not found."
        )

    for suffix in ("N", "P"):
        if all(_has_param(cir_obj, p) for p in (f"W2_{suffix}", f"ID2_{suffix}")):
            return suffix

    raise RuntimeError(
        "Could not detect conventional stage-2 flavor. Expected parameter pair 'W2_[N/P], ID2_[N/P]'."
    )


def optimize_second_stage_conventional(cir, stage2_flavor=None):
    print("\n--- Optimizing Second Stage (Conventional N/P) ---")
    suffix = detect_stage2_flavor_conventional(cir, preferred=stage2_flavor)

    id_sign = 1.0 if suffix == "N" else -1.0
    w_par = f"W2_{suffix}"
    id_par = f"ID2_{suffix}"

    f_local = 100e6
    V_swing_est = 0.45
    drive_offset = 0.25
    max_iter = 30
    tolerance = 0.01

    Ciss_X2 = float(cir.getParValue("c_iss_X2"))
    Ciss_X3 = float(cir.getParValue("c_iss_X3"))
    Ciss3 = Ciss_X2 + Ciss_X3
    gm_target = 2 * np.pi * f_local * Ciss3

    id_target_mag = (V_swing_est * gm_target) * (1 + drive_offset)
    id_target = id_sign * id_target_mag
    cir.defPar(id_par, id_target)

    gm_sym = "g_m_X6" if suffix == "N" else "g_m_X4"

    W_low = 0.1e-6
    W_high = 1000e-6
    W = (W_low + W_high) / 2.0

    converged = False
    for i in range(max_iter):
        W = (W_low + W_high) / 2.0
        cir.defPar(w_par, W)

        try:
            gm_sim = abs(float(cir.getParValue(gm_sym)))
        except Exception:
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

    print(f"\n----- Second Stage ({suffix}MOS Conventional) Sizing -----")
    if converged:
        print(f"Converged in {i+1} iterations.")
    else:
        print(f"WARNING: Max iterations ({max_iter}) reached. Result may not be accurate.")

    print(f"Final {w_par:<12}= {W*1e6:.2f} um")
    print(f"Final {id_par:<12}= {id_target*1e3:.3f} mA")
    print(f"Resulting gm({gm_sym}) = {cir.getParValue(gm_sym)*1e3:.3f} mS")

    return {
        "stage2_flavor": suffix,
        "w_param": w_par,
        "id_param": id_par,
        "W2": W,
        "ID2": id_target,
        "gm_target": gm_target,
        "id_target_mag": id_target_mag,
        "gm_eval_symbol": gm_sym,
    }
