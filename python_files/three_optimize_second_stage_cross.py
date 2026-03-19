from SLiCAP import *
import numpy as np


def _match_stage2_ratio(cir_obj, gm_n_sym, gm_p_sym, max_iter=50, tol=0.01):
    w2_n = float(cir_obj.getParValue("W2_N"))
    w2_p = float(cir_obj.getParValue("W2_P"))
    id2_n_org = float(cir_obj.getParValue("ID2_N"))
    id2_p_org = float(cir_obj.getParValue("ID2_P"))

    id_ref_mag = max(abs(id2_n_org), abs(id2_p_org), 10e-6)
    cir_obj.defPar("ID2_N", id_ref_mag)
    cir_obj.defPar("ID2_P", -id_ref_mag)

    converged = False
    for i in range(max_iter):
        cir_obj.defPar("W2_N", w2_n)
        cir_obj.defPar("W2_P", w2_p)

        gm_n = abs(float(cir_obj.getParValue(gm_n_sym)))
        gm_p = abs(float(cir_obj.getParValue(gm_p_sym)))
        if max(gm_n, gm_p) == 0:
            break

        err = abs(gm_n - gm_p) / max(gm_n, gm_p)
        if err < tol:
            converged = True
            break

        scale = (gm_n / gm_p) ** 2 if gm_p > 0 else 1.0
        scale = max(0.5, min(2.0, scale))
        w2_p *= scale
        w2_p = max(w2_p, 0.1e-6)

    cir_obj.defPar("W2_N", w2_n)
    cir_obj.defPar("W2_P", w2_p)
    cir_obj.defPar("ID2_N", id2_n_org)
    cir_obj.defPar("ID2_P", id2_p_org)

    ratio = w2_p / w2_n if w2_n > 0 else float("nan")
    return ratio, converged, i + 1


def optimize_second_stage_cross(cir, stage2_flavor):
    """
    Cross flavors:
    - PN: optimize gm of X6 (N side), keep matched W2_P/W2_N ratio.
    - NP: optimize gm of X4 (P side), keep matched W2_P/W2_N ratio.
    """
    flavor = stage2_flavor.upper()
    if flavor not in ("PN", "NP"):
        raise RuntimeError(f"Unsupported cross stage-2 flavor '{stage2_flavor}'. Use PN or NP.")

    print(f"\n--- Optimizing Second Stage (Cross flavor {flavor}) ---")

    gm_n_sym = "g_m_X6"
    gm_p_sym = "g_m_X4"
    gm_sym = gm_n_sym if flavor == "PN" else gm_p_sym

    f_local = 100e6
    V_swing_est = 0.45
    drive_offset = 0.25
    max_iter = 30
    tolerance = 0.01

    Ciss_X2 = float(cir.getParValue("c_iss_X2"))
    Ciss_X3 = float(cir.getParValue("c_iss_X3"))
    Ciss3 = Ciss_X2 + Ciss_X3
    gm_target = 2*(2 * np.pi * f_local * Ciss3)

    id_target_mag = 2* (V_swing_est * gm_target) * (1 + drive_offset)
    cir.defPar("ID2_N", id_target_mag)
    cir.defPar("ID2_P", -id_target_mag)

    ratio_wp_wn, ratio_converged, ratio_iter = _match_stage2_ratio(cir, gm_n_sym, gm_p_sym)
    print("\n----- Stage-2 gm matching (equal |ID2|) -----")
    print(f"Detected gm(N)     = {gm_n_sym}")
    print(f"Detected gm(P)     = {gm_p_sym}")
    print(f"Ratio W2_P/W2_N    = {ratio_wp_wn:.3f}")
    if ratio_converged:
        print(f"Converged in       = {ratio_iter} iterations")
    else:
        print(f"WARNING: ratio loop reached max iterations ({ratio_iter}).")

    W_low = 0.1e-6
    W_high = 1000e-6
    W = (W_low + W_high) / 2.0
    converged = False

    # W is always W2_N in this cross optimizer; W2_P follows the ratio.
    for i in range(max_iter):
        W = (W_low + W_high) / 2.0
        cir.defPar("W2_N", W)
        cir.defPar("W2_P", ratio_wp_wn * W)

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
    cir.defPar("W2_N", W)
    cir.defPar("W2_P", ratio_wp_wn * W)
    cir.defPar("ID2_N", id_target_mag)
    cir.defPar("ID2_P", -id_target_mag)

    print(f"\n----- Second Stage (Cross {flavor}) Sizing -----")
    if converged:
        print(f"Converged in {i+1} iterations.")
    else:
        print(f"WARNING: Max iterations ({max_iter}) reached. Result may not be accurate.")

    print(f"Final W2_N         = {float(cir.getParValue('W2_N'))*1e6:.2f} um")
    print(f"Final W2_P         = {float(cir.getParValue('W2_P'))*1e6:.2f} um")
    print(f"Final ID2_N        = {float(cir.getParValue('ID2_N'))*1e3:.3f} mA")
    print(f"Final ID2_P        = {float(cir.getParValue('ID2_P'))*1e3:.3f} mA")
    print(f"Resulting gm({gm_sym}) = {cir.getParValue(gm_sym)*1e3:.3f} mS")

    return {
        "stage2_flavor": flavor,
        "w_param": "W2_N",
        "id_param": "ID2_N",
        "W2": float(cir.getParValue("W2_N")),
        "ID2": float(cir.getParValue("ID2_N")),
        "W2_N": float(cir.getParValue("W2_N")),
        "W2_P": float(cir.getParValue("W2_P")),
        "ID2_N": float(cir.getParValue("ID2_N")),
        "ID2_P": float(cir.getParValue("ID2_P")),
        "gm_n_symbol": gm_n_sym,
        "gm_p_symbol": gm_p_sym,
        "gm_eval_symbol": gm_sym,
        "ratio_w2p_w2n": ratio_wp_wn,
        "gm_target": gm_target,
        "id_target_mag": id_target_mag,
    }
