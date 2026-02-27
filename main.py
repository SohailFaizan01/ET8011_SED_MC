from SLiCAP import *
import json
import os
from pathlib import Path


CACHE_DIR = Path("cache")
DEFAULT_STAGE_PN = "KiCad/Active_E_Field_Probe/stage_PN/Active_E_Field_Probe.kicad_sch"
DEFAULT_STAGE_NP = "KiCad/Active_E_Field_Probe/stage_NP/Active_E_Field_Probe.kicad_sch"
DEFAULT_STAGE_NN = "KiCad/Active_E_Field_Probe/stage_NN/Active_E_Field_Probe.kicad_sch"


def _safe_name(raw_name):
    return "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in raw_name)


def _cache_path_for(design_name):
    return CACHE_DIR / f"first_stage_result_{_safe_name(design_name)}.json"


def _save_first_stage_result(path, result):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fobj:
        json.dump(result, fobj, indent=2)


def _load_first_stage_result(path):
    with path.open("r", encoding="utf-8") as fobj:
        return json.load(fobj)


def _apply_first_stage_result(cir_obj, result):
    cir_obj.defPar(result["w_param"], float(result["W1"]))
    cir_obj.defPar(result["id_param"], float(result["ID1"]))
    cir_obj.defPar(result["wc_param"], float(result["W1C"]))


def _build_design_runs():
    dual_enabled = os.getenv("RUN_DUAL_DESIGNS", "0") == "1"
    if dual_enabled:
        first_project = os.getenv("KICAD_PROJECT_PN", DEFAULT_STAGE_PN)
        second_project = os.getenv("KICAD_PROJECT_NP", DEFAULT_STAGE_NP)
        if not first_project or not second_project:
            raise RuntimeError(
                "RUN_DUAL_DESIGNS=1 requires both KICAD_PROJECT_PN and KICAD_PROJECT_NP."
            )
        return [
            {
                "name": "pmos_first_nmos_second",
                "project": first_project,
                "stage1_flavor": "P",
                "stage2_flavor": "N",
            },
            {
                "name": "nmos_first_pmos_second",
                "project": second_project,
                "stage1_flavor": "N",
                "stage2_flavor": "P",
            },
        ]

    return [
        {
            "name": os.getenv("DESIGN_NAME", "default"),
            "project": os.getenv("KICAD_PROJECT", DEFAULT_STAGE_NN),
            "stage1_flavor": os.getenv("STAGE1_FLAVOR"),
            "stage2_flavor": os.getenv("STAGE2_FLAVOR"),
        }
    ]


def run():
    initProject("Active_E_Field_Probe")

    # Keep specifications loaded for project bookkeeping.
    from python_files import specifications  # noqa: F401
    from python_files.circuit import make_project_circuit
    from python_files.three_optimize_third_stage import optimize_third_stage
    from python_files.three_optimize_first_stage import optimize_first_stage_parallel
    from python_files.three_optimize_second_stage import optimize_second_stage
    from python_files.html_circuit_performance import generate_circuit_performance_html

    skip_first_stage = os.getenv("SKIP_FIRST_STAGE_OPT", "0") == "1"
    design_runs = _build_design_runs()
    all_results = []

    for cfg in design_runs:
        print("\n============================================================")
        print(f"Running design: {cfg['name']}")
        print(f"KiCad source : {cfg['project']}")
        print("============================================================")

        cir = make_project_circuit(cfg["project"])
        cache_path = _cache_path_for(cfg["name"])

        print(f"[{cfg['name']}] Stage 3 optimization: START", flush=True)
        third_stage_result = optimize_third_stage(cir)
        print(f"[{cfg['name']}] Stage 3 optimization: DONE", flush=True)

        print(
            f"[{cfg['name']}] Stage 2 optimization: START "
            f"(requested flavor={cfg['stage2_flavor'] or 'auto'})",
            flush=True,
        )
        second_stage_result = optimize_second_stage(
            cir,
            stage2_flavor=cfg["stage2_flavor"],
        )
        print(
            f"[{cfg['name']}] Stage 2 optimization: DONE "
            f"({second_stage_result['w_param']}={second_stage_result['W2']*1e6:.2f}um, "
            f"{second_stage_result['id_param']}={second_stage_result['ID2']*1e3:.3f}mA)",
            flush=True,
        )

        if skip_first_stage:
            if not cache_path.exists():
                raise FileNotFoundError(
                    f"SKIP_FIRST_STAGE_OPT=1 but no cached result found at '{cache_path}'. "
                    "Run once without SKIP_FIRST_STAGE_OPT to generate it."
                )
            cached = _load_first_stage_result(cache_path)
            _apply_first_stage_result(cir, cached)
            first_stage_result = cached
            print(
                "Loaded cached first-stage result: "
                f"{cached['w_param']}={cached['W1']}, "
                f"{cached['id_param']}={cached['ID1']}, "
                f"{cached['wc_param']}={cached['W1C']}"
            )
        else:
            print(f"[{cfg['name']}] Stage 1 optimization: START", flush=True)
            first_stage_result = optimize_first_stage_parallel(
                cir,
                stage1_flavor=cfg["stage1_flavor"],
            )
            if first_stage_result is None:
                raise RuntimeError(
                    f"First-stage optimization did not produce a valid result for '{cfg['name']}'."
                )
            _save_first_stage_result(cache_path, first_stage_result)
            print(f"Saved first-stage result to '{cache_path}'.")
            print(f"[{cfg['name']}] Stage 1 optimization: DONE", flush=True)

        all_results.append(
            {
                "design": cfg["name"],
                "project": cfg["project"],
                "stage_tag": f"{first_stage_result['stage1_flavor']}{second_stage_result['stage2_flavor']}",
                "third_stage": third_stage_result,
                "first_stage": first_stage_result,
                "second_stage": second_stage_result,
                "cir": cir,
            }
        )

    print("\n======================= Run Summary =======================")
    for result in all_results:
        first = result["first_stage"]
        second = result["second_stage"]
        print(
            f"{result['design']}: "
            f"{first['w_param']}={first['W1']*1e6:.2f}um, "
            f"{first['id_param']}={first['ID1']*1e3:.3f}mA, "
            f"{first['wc_param']}={first['W1C']*1e6:.2f}um, "
            f"{second['w_param']}={second['W2']*1e6:.2f}um, "
            f"{second['id_param']}={second['ID2']*1e3:.3f}mA"
        )

    # Keep existing shared HTML behavior unchanged.
    if len(design_runs) == 1:
        from python_files import html_specifications  # noqa: F401
        from python_files import html_design_choices  # noqa: F401
        result = all_results[0]
        generate_circuit_performance_html(
            result["cir"],
            design_tag=result["stage_tag"],
            iq=result["third_stage"]["Iq"],
            i_peak=result["third_stage"]["I_peak"],
        )
    else:
        for result in all_results:
            generate_circuit_performance_html(
                result["cir"],
                design_tag=result["stage_tag"],
                iq=result["third_stage"]["Iq"],
                i_peak=result["third_stage"]["I_peak"],
            )


if __name__ == "__main__":
    run()
