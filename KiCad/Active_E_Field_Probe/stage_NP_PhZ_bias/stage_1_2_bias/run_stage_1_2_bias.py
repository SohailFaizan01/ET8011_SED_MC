from pathlib import Path
import sys

import numpy as np
from SLiCAP import *

try:
    from .specs_stage_1_2_bias import specs
except ImportError:
    # Allow running as a standalone script.
    repo_root = Path(__file__).resolve().parents[4]
    sys.path.insert(0, str(repo_root))
    from KiCad.Active_E_Field_Probe.stage_NP_PhZ_bias.stage_1_2_bias.specs_stage_1_2_bias import specs


SCH_NAME = "stage_1_2_bias.kicad_sch"
CIR_NAME = "stage_1_2_bias"
CIR_NAME_SPECS = "stage_1_2_bias_specs"

# Sweep settings (edit as needed)
VGS1_N_START = 0.0
VGS1_N_STOP = 1.2
VGS1_N_STEP = 0.01

VGS1C_N_START = 0.0
VGS1C_N_STOP = 1.2
VGS1C_N_STEP = 0.05


def _spec_value(symbol, default=None):
    for item in specs:
        sym = getattr(item, "symbol", None)
        if sym is not None and str(sym) == symbol:
            return float(getattr(item, "value", default))
    return default


def _build_par_list(overrides=None):
    params = []
    for item in specs:
        sym = getattr(item, "symbol", None)
        if sym is None:
            continue
        params.append((str(sym), getattr(item, "value", None)))
    if overrides:
        for key, value in overrides.items():
            params = [(k, v) for (k, v) in params if k != key]
            params.append((key, value))
    return params


def _export_spice_with_specs(base_cir_path, out_cir_path, spec_list):
    base_text = Path(base_cir_path).read_text(encoding="utf-8")
    lines = []
    for item in spec_list:
        sym = getattr(item, "symbol", None)
        if sym is None:
            continue
        val = getattr(item, "value", None)
        if val == "" or val is None:
            continue
        lines.append(f".param {str(sym)}={val}")

    insert_block = "\n".join(lines) + "\n"
    if ".end" in base_text.lower():
        parts = base_text.rsplit(".end", 1)
        out_text = parts[0].rstrip() + "\n" + insert_block + ".end" + parts[1]
    else:
        out_text = base_text.rstrip() + "\n" + insert_block + "\n.end\n"

    Path(out_cir_path).write_text(out_text, encoding="utf-8")


def _find_crossing(x, y, target):
    if len(x) == 0:
        return None, None
    y = np.asarray(y, dtype=float)
    x = np.asarray(x, dtype=float)
    diff = y - target
    sign = np.sign(diff)
    for idx in range(len(diff) - 1):
        if sign[idx] == 0:
            return float(x[idx]), 0.0
        if sign[idx] * sign[idx + 1] < 0:
            x0, x1 = x[idx], x[idx + 1]
            y0, y1 = diff[idx], diff[idx + 1]
            if y1 == y0:
                return float(x0), 0.0
            return float(x0 - y0 * (x1 - x0) / (y1 - y0)), 0.0
    closest = int(np.argmin(np.abs(diff)))
    return float(x[closest]), float(abs(diff[closest]))


def _run_dc_sweep(vgs1c_value, target_id):
    cir_file = str(Path("cir") / CIR_NAME_SPECS)
    sim_cmd = f"dc V11 {VGS1_N_START} {VGS1_N_STOP} {VGS1_N_STEP}"
    names = {
        "I_X1": "@x1.m1[id]",
        "I_X8": "@x8.m1[id]",
    }
    par_list = _build_par_list(
        overrides={
            "VGS1_N": VGS1_N_START,
            "VGS1C_N": vgs1c_value,
        }
    )

    try:
        traces, x_name, x_units = ngspice2traces(cir_file, sim_cmd, names, parList=par_list)
    except Exception:
        # Fallback to branch currents if subckt currents are unavailable.
        names = {
            "I_X1": "I(V7)",
            "I_X8": "I(V8)",
        }
        print("WARNING: Falling back to branch currents I(V7)/I(V8); these are not per-device currents.")
        traces, x_name, x_units = ngspice2traces(cir_file, sim_cmd, names, parList=par_list)

    i_x1 = traces["I_X1"]
    i_x8 = traces["I_X8"]

    vgs1_n_x1, err_x1 = _find_crossing(i_x1.xData, i_x1.yData, target_id)
    vgs1_n_x8, err_x8 = _find_crossing(i_x8.xData, i_x8.yData, target_id)
    return (vgs1_n_x1, err_x1), (vgs1_n_x8, err_x8)


def run():
    sch_path = Path(__file__).with_name(SCH_NAME)
    if not sch_path.exists():
        raise FileNotFoundError(f"Missing schematic: {sch_path}")

    # Ensure netlist exists (and update if needed).
    cir = makeCircuit(str(sch_path), imgWidth=1000)
    specs2circuit(specs, cir)
    base_cir = Path("cir") / f"{CIR_NAME}.cir"
    out_cir = Path("cir") / f"{CIR_NAME_SPECS}.cir"
    _export_spice_with_specs(base_cir, out_cir, specs)

    target_id = _spec_value("ID1_N")
    if target_id is None:
        raise RuntimeError("ID1_N not found in specs list.")

    vgs1c_values = np.arange(VGS1C_N_START, VGS1C_N_STOP + VGS1C_N_STEP / 2, VGS1C_N_STEP)
    print("Sweep results (target ID1_N = {:.6e} A)".format(target_id))
    print("VGS1C_N (V) | VGS1_N @ I_X1=ID1_N (V) | VGS1_N @ I_X8=ID1_N (V)")

    best_x1 = (None, float("inf"), None)
    best_x8 = (None, float("inf"), None)

    for vgs1c in vgs1c_values:
        (vgs1_n_x1, err_x1), (vgs1_n_x8, err_x8) = _run_dc_sweep(vgs1c, target_id)
        print(f"{vgs1c:10.4f} | {vgs1_n_x1:24.6f} | {vgs1_n_x8:24.6f}")

        if vgs1_n_x1 is not None and err_x1 is not None and err_x1 < best_x1[1]:
            best_x1 = (vgs1c, err_x1, vgs1_n_x1)
        if vgs1_n_x8 is not None and err_x8 is not None and err_x8 < best_x8[1]:
            best_x8 = (vgs1c, err_x8, vgs1_n_x8)

    print("\nBest matches (by interpolation):")
    if best_x1[2] is not None:
        print(f"X1: VGS1C_N={best_x1[0]:.6f} V, VGS1_N={best_x1[2]:.6f} V, err={best_x1[1]:.3e} A")
    if best_x8[2] is not None:
        print(f"X8: VGS1C_N={best_x8[0]:.6f} V, VGS1_N={best_x8[2]:.6f} V, err={best_x8[1]:.3e} A")

    def _try_par(name):
        try:
            return float(cir.getParValue(name))
        except Exception:
            return None

    return cir


if __name__ == "__main__":
    run()
