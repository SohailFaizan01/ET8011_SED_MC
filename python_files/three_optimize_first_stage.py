############################################################################
######## This script will optimize the first stage #########
############################################################################

from concurrent.futures import ProcessPoolExecutor, as_completed
import os
import time

from SLiCAP import *
import numpy as np
import sympy as sp

############################################################################
# This script optimizes the first stage of the amplifier based on a
# user-provided cost function and constraints.
#
# Optimization strategy (W and ID centric):
# 1. An outer loop iterates through a range of possible widths (W1_N).
# 2. For each width, an inner loop evaluates possible drain currents (ID1_N).
# 3. For each (W1_N, ID1_N), the noise and cascode constraints are checked.
# 4. The pair that yields the lowest cost is selected as the optimum.
############################################################################

# --- Optimization Parameters ---
f = sp.Symbol('f')
noise_margin = 0.7
I_budget_stage = 1e-3
target_val = 2e9
target_stage_gain = 400
gain_cost_bias = 2
max_size_budget = 0.5

# Precomputed sweep grids
NOISE_FREQS = np.logspace(5, 7, 10)
W_SWEEP_POINTS = 30
ID_SWEEP_POINTS = 20

# Process-local circuit object.
_WORKER_CIR = None


def _has_param(cir_obj, name):
    try:
        cir_obj.getParValue(name)
        return True
    except Exception:
        return False


def detect_stage1_flavor(cir_obj, preferred=None):
    """Detect whether stage-1 variables use _N or _P suffixes."""
    if preferred:
        suffix = preferred.upper()
        if all(
            _has_param(cir_obj, p)
            for p in (f"W1_{suffix}", f"ID1_{suffix}", f"W1C_{suffix}")
        ):
            return suffix
        raise RuntimeError(
            f"Requested stage-1 flavor '{suffix}' but parameters "
            f"'W1_{suffix}', 'ID1_{suffix}', and/or 'W1C_{suffix}' were not found."
        )

    suffixes = ["N", "P"]

    for suffix in suffixes:
        if all(
            _has_param(cir_obj, p)
            for p in (f"W1_{suffix}", f"ID1_{suffix}", f"W1C_{suffix}")
        ):
            return suffix

    raise RuntimeError(
        "Could not detect stage-1 flavor. Expected parameter triplet "
        "'W1_[N/P], ID1_[N/P], W1C_[N/P]'."
    )


def _worker_init(base_cir):
    """Initialize each process with its own circuit clone from parent."""
    global _WORKER_CIR
    _WORKER_CIR = base_cir


def _tune_cascode(local_cir, initial_W1C_N, wc_par):
    """
    Reduce cascode width until pole constraint is met or min width is reached.
    Returns (success, final_W1C_N, pole_freq, stage_gain).
    """
    W1C_N = initial_W1C_N
    min_width = 180e-9

    while W1C_N >= min_width:
        local_cir.defPar(wc_par, W1C_N)
        try:
            gm_amp = float(local_cir.getParValue("g_m_X1"))
            gds_amp = float(local_cir.getParValue("g_o_X1"))
            ro_amp = 1.0 / gds_amp if gds_amp > 0 else float('inf')

            gm_casc = float(local_cir.getParValue("g_m_X7"))
            gds_casc = float(local_cir.getParValue("g_o_X7"))
            ro_casc = 1.0 / gds_casc if gds_casc > 0 else float('inf')

            cissX4 = float(local_cir.getParValue("c_iss_X4"))
        except Exception:
            W1C_N *= 0.85
            continue

        iter_pole_freq = 1 / (2 * np.pi * ro_amp * gm_casc * ro_casc * cissX4)
        iter_stage_gain = gm_amp * ro_amp * gm_casc * ro_casc
        if iter_pole_freq > target_val:
            return (True, W1C_N, iter_pole_freq, iter_stage_gain)

        W1C_N *= 0.85

    return (False, None, 0.0, 0.0)


def _noise_ok(local_cir):
    """Evaluate noise constraint for the current operating point."""
    noise_expr = doNoise(local_cir, source="V1", detector="V_vo", numeric=True, pardefs='circuit').inoise

    for freq in NOISE_FREQS:
        noise_val = float(sp.N(noise_expr.subs(f, freq)))
        noise_spec = 1e-15 * (1 + 1e12 / freq**2)
        ratio = noise_val / (noise_margin * noise_spec)
        if ratio >= 1.0:
            return False

    return True


def _evaluate_width(task):
    """Evaluate one width with a sequential current sweep in a worker process."""
    local_cir = _WORKER_CIR

    W1_val, id_sweep, denom_w, denom_id, w_par, id_par, wc_par, id_sign = task

    t0 = time.perf_counter()
    local_cir.defPar(w_par, W1_val)
    ic_crit = float(local_cir.getParValue("IC_CRIT_X1"))

    best_for_width = None
    checked_points = 0

    # Sweep high->low current. Once noise fails, lower currents are skipped.
    for id_mag in id_sweep:
        checked_points += 1
        id_val = float(id_sign * id_mag)
        local_cir.defPar(id_par, id_val)

        try:
            gm_check = float(local_cir.getParValue("g_m_X1"))
            if gm_check <= 0:
                break

            # Skip points above critical inversion; only evaluate near/under IC_crit.
            ic_x1 = float(local_cir.getParValue("IC_X1"))
            if ic_x1 > ic_crit:
                continue

            if not _noise_ok(local_cir):
                break

        except Exception:
            break

        cascode_ok, found_W1C_N, found_pole_freq, found_stage_gain = _tune_cascode(local_cir, W1_val, wc_par)
        if not cascode_ok or found_stage_gain <= 0:
            continue

        cost = ((W1_val / denom_w) * (id_mag / denom_id)) / ((found_stage_gain / target_stage_gain)**gain_cost_bias)
        candidate = {
            "cost": cost,
            "W1": W1_val,
            "ID1": id_val,
            "ID1_mag": id_mag,
            "W1C": found_W1C_N,
            "pole_freq": found_pole_freq,
            "stage_gain": found_stage_gain,
            "w_par": w_par,
            "id_par": id_par,
            "wc_par": wc_par,
        }

        if best_for_width is None or candidate["cost"] < best_for_width["cost"]:
            best_for_width = candidate

    elapsed_s = time.perf_counter() - t0
    stats = {
        "W1": W1_val,
        "checked_points": checked_points,
        "elapsed_s": elapsed_s,
        "pid": os.getpid(),
    }
    return (best_for_width, stats)


def optimize_first_stage_parallel(cir, stage1_flavor=None, max_workers=None):
    """Run first-stage optimization with process-based parallel width evaluation."""
    suffix = detect_stage1_flavor(cir, preferred=stage1_flavor)
    id_sign = 1.0 if suffix == "N" else -1.0
    w_par = f"W1_{suffix}"
    id_par = f"ID1_{suffix}"
    wc_par = f"W1C_{suffix}"

    W_N_3rd = float(cir.getParValue("W_N"))
    W_P_3rd = float(cir.getParValue("W_P"))
    ID_N_3rd = abs(float(cir.getParValue("ID_N")))

    W1_max = (W_P_3rd + W_N_3rd) / ((1 / max_size_budget) - 1)

    best_cost = float('inf')
    best_W1 = None
    best_ID1 = None
    best_W1C = None

    print(f"----- Running First Stage Optimization ({suffix}MOS) -----")
    print(f"Max {w_par} constraint: {W1_max*1e6:.2f} um")

    w_sweep = np.geomspace(W1_max, 1e-6, W_SWEEP_POINTS)
    id_sweep = np.geomspace(I_budget_stage, 10e-6, ID_SWEEP_POINTS)
    print(f"Scheduled widths for {w_par} (um): " + ", ".join(f"{w*1e6:.2f}" for w in w_sweep))

    tasks = [
        (float(W1_val), id_sweep, W_P_3rd + W_N_3rd, ID_N_3rd, w_par, id_par, wc_par, id_sign)
        for W1_val in w_sweep
    ]

    if max_workers is None:
        max_workers = max(1, min((os.cpu_count() or 2) - 1, len(tasks)))

    print(f"Evaluating {len(tasks)} widths with {max_workers} processes...")

    completed = 0
    pids = set()
    with ProcessPoolExecutor(max_workers=max_workers, initializer=_worker_init, initargs=(cir,)) as pool:
        futures = [pool.submit(_evaluate_width, task) for task in tasks]

        for future in as_completed(futures):
            completed += 1
            result, stats = future.result()
            pids.add(stats["pid"])
            print(
                f"Width done: W1={stats['W1']*1e6:.2f}um, "
                f"checked={stats['checked_points']}/{ID_SWEEP_POINTS}, "
                f"time={stats['elapsed_s']:.2f}s, "
                f"pid={stats['pid']}"
            )

            if result and result["cost"] < best_cost:
                best_cost = result["cost"]
                best_W1 = result["W1"]
                best_ID1 = result["ID1"]
                best_W1C = result["W1C"]

                print(
                    "New best found: "
                    f"W1={best_W1*1e6:.2f}um, "
                    f"ID1={best_ID1*1e3:.3f}mA, "
                    f"W1C={best_W1C*1e6:.2f}um, "
                    f"Cost={best_cost:.4f}, "
                    f"Gain={result['stage_gain']:.2f}, "
                    f"Pole Freq={result['pole_freq']/1e9:.2f}GHz"
                )

            if completed % 5 == 0 or completed == len(tasks):
                print(f"Progress: {completed}/{len(tasks)} widths")

    print(f"Process workers used: {len(pids)}")

    if best_W1 is not None and best_ID1 is not None and best_W1C is not None:
        cir.defPar(w_par, best_W1)
        cir.defPar(id_par, best_ID1)
        cir.defPar(wc_par, best_W1C)
    else:
        print(f"Could not find a valid solution for {w_par} and {id_par}.")
        return None

    print("\n--- Main Optimization Complete ---")
    print("\n----- First Stage Optimization Finished -----")
    print(f"Lowest Cost Found:      {best_cost:.4f}")
    print(f"Final Optimized {w_par}:   {best_W1*1e6:.2f} um")
    print(f"Final Optimized {id_par}:  {best_ID1*1e3:.3f} mA")
    print(f"Final Tuned {wc_par}:      {best_W1C*1e6:.2f} um")
    print(f"Resulting IC Amp:       {cir.getParValue('IC_X1'):.2f}")

    return {
        "best_cost": best_cost,
        "stage1_flavor": suffix,
        "w_param": w_par,
        "id_param": id_par,
        "wc_param": wc_par,
        "W1": best_W1,
        "ID1": best_ID1,
        "W1C": best_W1C,
    }
