from SLiCAP import *
import json
import os
from pathlib import Path


FIRST_STAGE_CACHE = Path("cache/first_stage_result.json")


def _save_first_stage_result(result):
    FIRST_STAGE_CACHE.parent.mkdir(parents=True, exist_ok=True)
    with FIRST_STAGE_CACHE.open("w", encoding="utf-8") as fobj:
        json.dump(result, fobj, indent=2)


def _load_first_stage_result():
    with FIRST_STAGE_CACHE.open("r", encoding="utf-8") as fobj:
        return json.load(fobj)


def _apply_first_stage_result(cir_obj, result):
    cir_obj.defPar("W1_N", float(result["W1_N"]))
    cir_obj.defPar("ID1_N", float(result["ID1_N"]))
    cir_obj.defPar("W1C_N", float(result["W1C_N"]))


def run():
    # Project setup
    initProject("Active_E_Field_Probe")

    from python_files import specifications  # noqa: F401
    from python_files import circuit

    # 3 Stage Design
    from python_files import three_optimize_third_stage  # noqa: F401
    from python_files import three_optimize_second_stage  # noqa: F401
    from python_files import three_optimize_first_stage

    # Optional debug bypass for first-stage optimization.
    skip_first_stage = os.getenv("SKIP_FIRST_STAGE_OPT", "0") == "1"
    if skip_first_stage:
        if not FIRST_STAGE_CACHE.exists():
            raise FileNotFoundError(
                f"SKIP_FIRST_STAGE_OPT=1 but no cached result found at '{FIRST_STAGE_CACHE}'. "
                "Run once without SKIP_FIRST_STAGE_OPT to generate it."
            )
        cached = _load_first_stage_result()
        _apply_first_stage_result(circuit.cir, cached)
        print(
            "Loaded cached first-stage result: "
            f"W1_N={cached['W1_N']}, ID1_N={cached['ID1_N']}, W1C_N={cached['W1C_N']}"
        )
    else:
        # Run first-stage sweep in parallel.
        result = three_optimize_first_stage.optimize_first_stage_parallel()
        if result is None:
            raise RuntimeError("First-stage optimization did not produce a valid result.")
        _save_first_stage_result(result)
        print(f"Saved first-stage result to '{FIRST_STAGE_CACHE}'.")

    # HTML generation
    from python_files import plot_generation  # noqa: F401
    from python_files import html_specifications  # noqa: F401
    from python_files import html_design_choices  # noqa: F401
    from python_files import html_circuit_performance  # noqa: F401


if __name__ == "__main__":
    run()
