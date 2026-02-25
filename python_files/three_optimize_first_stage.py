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


def _worker_init(base_cir):
    """Initialize each process with its own circuit clone from parent."""
    global _WORKER_CIR
    _WORKER_CIR = base_cir


def _tune_cascode(local_cir, initial_W1C_N):
    """
    Reduce cascode width until pole constraint is met or min width is reached.
    Returns (success, final_W1C_N, pole_freq, stage_gain).
    """
    W1C_N = initial_W1C_N
    min_width = 180e-9

    while W1C_N >= min_width:
        local_cir.defPar("W1C_N", W1C_N)
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

    W1_N, id_sweep, denom_w, denom_id = task

    t0 = time.perf_counter()
    local_cir.defPar("W1_N", W1_N)
    ic_crit = float(local_cir.getParValue("IC_CRIT_X1"))

    best_for_width = None
    checked_points = 0

    # Sweep high->low current. Once noise fails, lower currents are skipped.
    for ID1_N in id_sweep:
        checked_points += 1
        local_cir.defPar("ID1_N", ID1_N)

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

        cascode_ok, found_W1C_N, found_pole_freq, found_stage_gain = _tune_cascode(local_cir, W1_N)
        if not cascode_ok or found_stage_gain <= 0:
            continue

        cost = ((W1_N / denom_w) * (ID1_N / denom_id)) / ((found_stage_gain / target_stage_gain)**gain_cost_bias)
        candidate = {
            "cost": cost,
            "W1_N": W1_N,
            "ID1_N": ID1_N,
            "W1C_N": found_W1C_N,
            "pole_freq": found_pole_freq,
            "stage_gain": found_stage_gain,
        }

        if best_for_width is None or candidate["cost"] < best_for_width["cost"]:
            best_for_width = candidate

    elapsed_s = time.perf_counter() - t0
    stats = {
        "W1_N": W1_N,
        "checked_points": checked_points,
        "elapsed_s": elapsed_s,
        "pid": os.getpid(),
    }
    return (best_for_width, stats)


def optimize_first_stage_parallel(max_workers=None):
    """Run first-stage optimization with process-based parallel width evaluation."""
    from .circuit import cir

    W_N_3rd = float(cir.getParValue("W_N"))
    W_P_3rd = float(cir.getParValue("W_P"))
    ID_N_3rd = float(cir.getParValue("ID_N"))

    W1_max = (W_P_3rd + W_N_3rd) / ((1 / max_size_budget) - 1)

    best_cost = float('inf')
    best_W1_N = 0.0
    best_ID1_N = 0.0
    best_W1C_N = 0.0

    print("----- Running First Stage Optimization -----")
    print(f"Max W1_N constraint: {W1_max*1e6:.2f} um")

    w_sweep = np.geomspace(W1_max, 1e-6, W_SWEEP_POINTS)
    id_sweep = np.geomspace(I_budget_stage, 10e-6, ID_SWEEP_POINTS)
    print("Scheduled widths (um): " + ", ".join(f"{w*1e6:.2f}" for w in w_sweep))

    tasks = [
        (float(W1_N), id_sweep, W_P_3rd + W_N_3rd, ID_N_3rd)
        for W1_N in w_sweep
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
                f"Width done: W1={stats['W1_N']*1e6:.2f}um, "
                f"checked={stats['checked_points']}/{ID_SWEEP_POINTS}, "
                f"time={stats['elapsed_s']:.2f}s, "
                f"pid={stats['pid']}"
            )

            if result and result["cost"] < best_cost:
                best_cost = result["cost"]
                best_W1_N = result["W1_N"]
                best_ID1_N = result["ID1_N"]
                best_W1C_N = result["W1C_N"]

                print(
                    "New best found: "
                    f"W1={best_W1_N*1e6:.2f}um, "
                    f"ID1={best_ID1_N*1e3:.3f}mA, "
                    f"W1C={best_W1C_N*1e6:.2f}um, "
                    f"Cost={best_cost:.4f}, "
                    f"Gain={result['stage_gain']:.2f}, "
                    f"Pole Freq={result['pole_freq']/1e9:.2f}GHz"
                )

            if completed % 5 == 0 or completed == len(tasks):
                print(f"Progress: {completed}/{len(tasks)} widths")

    print(f"Process workers used: {len(pids)}")

    if best_W1_N > 0 and best_ID1_N > 0:
        cir.defPar("W1_N", best_W1_N)
        cir.defPar("ID1_N", best_ID1_N)
        cir.defPar("W1C_N", best_W1C_N)
    else:
        print("Could not find a valid solution for W1_N and ID1_N.")
        return None

    print("\n--- Main Optimization Complete ---")
    print("\n----- First Stage Optimization Finished -----")
    print(f"Lowest Cost Found:      {best_cost:.4f}")
    print(f"Final Optimized W1_N:   {best_W1_N*1e6:.2f} um")
    print(f"Final Optimized ID1_N:  {best_ID1_N*1e3:.3f} mA")
    print(f"Final Tuned W1C_N:      {best_W1C_N*1e6:.2f} um")
    print(f"Resulting IC Amp:       {cir.getParValue('IC_X1'):.2f}")

    return {
        "best_cost": best_cost,
        "W1_N": best_W1_N,
        "ID1_N": best_ID1_N,
        "W1C_N": best_W1C_N,
    }
