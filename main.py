from SLiCAP import *
import json
import os
import shutil
from pathlib import Path


CACHE_DIR = Path("cache")
HTML_DIR = Path("html")
HTML_IMG_DIR = HTML_DIR / "img"

STAGE_PN = "KiCad/Active_E_Field_Probe/stage_PN/Active_E_Field_Probe.kicad_sch"
STAGE_NP = "KiCad/Active_E_Field_Probe/stage_NP/Active_E_Field_Probe.kicad_sch"
STAGE_NN = "KiCad/Active_E_Field_Probe/stage_NN/Active_E_Field_Probe.kicad_sch"
STAGE_NBalSF = "KiCad/Active_E_Field_Probe/stage_N_balSF/Active_E_Field_Probe.kicad_sch"

STAGE_PN_PhZ = "KiCad/Active_E_Field_Probe/stage_PN_PhZ/Active_E_Field_Probe.kicad_sch"
STAGE_NP_PhZ = "KiCad/Active_E_Field_Probe/stage_NP_PhZ/Active_E_Field_Probe.kicad_sch"
STAGE_NN_PhZ = "KiCad/Active_E_Field_Probe/stage_NN_PhZ/Active_E_Field_Probe.kicad_sch"
STAGE_NBalSF_PhZ = "KiCad/Active_E_Field_Probe/stage_N_balSF_PhZ/Active_E_Field_Probe.kicad_sch"

# DESIGN_SPECS = [
#     {
#         "key": "NBalSF",
#         "project": STAGE_NBalSF,
#         "stage1_flavor": "N",
#         "stage2_flavor": "PN",
#     },
#     {
#         "key": "NP",
#         "project": STAGE_NP,
#         "stage1_flavor": "N",
#         "stage2_flavor": "P",
#     },
#     {
#         "key": "PN",
#         "project": STAGE_PN,
#         "stage1_flavor": "P",
#         "stage2_flavor": "N",
#     },
# ]

DESIGN_SPECS = [
    {
        "key": "NBalSF",
        "project": STAGE_NBalSF_PhZ,
        "stage1_flavor": "N",
        "stage2_flavor": "PN",
    },
    {
        "key": "NP",
        "project": STAGE_NP_PhZ,
        "stage1_flavor": "N",
        "stage2_flavor": "P",
    },
    {
        "key": "PN",
        "project": STAGE_PN_PhZ,
        "stage1_flavor": "P",
        "stage2_flavor": "N",
    },
]


def _safe_name(raw_name):
    return "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in raw_name)


def _cache_path_for(design_key):
    return CACHE_DIR / f"first_stage_{_safe_name(design_key)}.json"


def _save_first_stage_result(path, cfg, result):
    payload = {
        "meta": {
            "design_key": cfg["key"],
        },
        "result": result,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fobj:
        json.dump(payload, fobj, indent=2)


def _load_first_stage_result(path):
    with path.open("r", encoding="utf-8") as fobj:
        payload = json.load(fobj)
    if "result" in payload and "meta" in payload:
        return payload
    # Backward compatibility for old cache shape.
    return {"meta": {}, "result": payload}


def _validate_cached_result(cir_obj, cfg, cached_payload):
    meta = cached_payload.get("meta", {})
    result = cached_payload["result"]

    if meta:
        if meta.get("design_key") != cfg["key"]:
            raise RuntimeError(
                f"Cached first-stage result mismatch for '{cfg['key']}': "
                f"design_key={meta.get('design_key')!r}."
            )
    for key in ("w_param", "id_param", "wc_param"):
        par_name = result[key]
        try:
            cir_obj.getParValue(par_name)
        except Exception as exc:
            raise RuntimeError(
                f"Cached first-stage result incompatible with '{cfg['key']}': "
                f"parameter '{par_name}' not found."
            ) from exc

    return result


def _stage1_ciss_par_for_stage2(stage2_flavor):
    flavor = (stage2_flavor or "").upper()
    if flavor == "PN":
        return "c_iss_X4"
    if flavor == "NP":
        return "c_iss_X6"
    return "c_iss_X4"


def _apply_first_stage_result(cir_obj, result):
    cir_obj.defPar(result["w_param"], float(result["W1"]))
    cir_obj.defPar(result["id_param"], float(result["ID1"]))
    cir_obj.defPar(result["wc_param"], float(result["W1C"]))


def _select_design_specs():
    requested = os.getenv("RUN_DESIGNS", "").strip()
    if not requested:
        return DESIGN_SPECS

    wanted = {item.strip().upper() for item in requested.split(",") if item.strip()}
    selected = [cfg for cfg in DESIGN_SPECS if cfg["key"] in wanted]
    if not selected:
        raise RuntimeError(
            f"RUN_DESIGNS={requested!r} did not match any known design keys: "
            + ", ".join(cfg["key"] for cfg in DESIGN_SPECS)
        )
    return selected


def _cleanup_html_outputs():
    # Remove stale project indices to avoid duplicate table-of-contents links.
    for file_name in ("index.html", "Active_E_Field_Probe_index.html", "Circuit-data.html"):
        path = HTML_DIR / file_name
        if path.exists():
            path.unlink()

    # Remove stale circuit-performance pages from previous naming strategies.
    for path in HTML_DIR.glob("Active_E_Field_Probe_Circuit-Performance*.html"):
        path.unlink()

    # Remove stale performance plots so only current-run outputs exist.
    for pattern in (
        "fb_mag*.svg",
        "ph_mag*.svg",
        "inoise*.svg",
        "Stepped_PZ_plot_P_peak*.svg",
        "Stepped_PZ_plot_LG_peak*.svg",
        "Active_E_Field_Probe_*.svg",
    ):
        for path in HTML_IMG_DIR.glob(pattern):
            path.unlink()


def _snapshot_circuit_image(design_key):
    src = HTML_IMG_DIR / "Active_E_Field_Probe.svg"
    if not src.exists():
        return "Active_E_Field_Probe.svg"
    dst_name = f"Active_E_Field_Probe_{design_key.upper()}.svg"
    dst = HTML_IMG_DIR / dst_name
    shutil.copyfile(src, dst)
    return dst_name


def _dedupe_main_index_links():
    index_path = HTML_DIR / "index.html"
    if not index_path.exists():
        return
    token = '<li><a href="Active_E_Field_Probe_index.html">Active_E_Field_Probe</a></li>'
    text = index_path.read_text(encoding="utf-8")
    if text.count(token) <= 1:
        return
    text = text.replace(token, "")
    text = text.replace("<!-- INSERT -->", f"{token}<!-- INSERT -->", 1)
    index_path.write_text(text, encoding="utf-8")


def run():
    _cleanup_html_outputs()
    initProject("Active_E_Field_Probe")
    from python_files import specifications  # noqa: F401
    from python_files.circuit import make_project_circuit
    from python_files.three_optimize_third_stage import optimize_third_stage
    from python_files.three_optimize_first_stage import optimize_first_stage_parallel
    from python_files.three_optimize_second_stage import optimize_second_stage
    from python_files.html_specifications import generate_specifications_html
    from python_files.html_design_choices import generate_design_choices_html
    from python_files.html_circuit_performance import (
        generate_circuit_performance_html,
        generate_circuit_performance_menu_html,
    )

    skip_first_stage = os.getenv("SKIP_FIRST_STAGE_OPT", "0") == "1"
    design_runs = _select_design_specs()
    all_results = []

    generate_specifications_html()
    generate_design_choices_html()

    for cfg in design_runs:
        print("\n============================================================")
        cache_key = cfg["key"]
        html_key = cache_key
        print(f"Running design: {cache_key}")
        print(f"KiCad source : {cfg['project']}")
        print("============================================================")

        # Dedicated circuit instance per design.
        cir = make_project_circuit(cfg["project"])
        circuit_image = _snapshot_circuit_image(cache_key)
        cache_path = _cache_path_for(cache_key)

        print(f"[{cache_key}] Stage 3 optimization: START", flush=True)
        third_stage_result = optimize_third_stage(cir)
        print(f"[{cache_key}] Stage 3 optimization: DONE", flush=True)

        print(
            f"[{cache_key}] Stage 2 optimization: START "
            f"(requested flavor={cfg['stage2_flavor']})",
            flush=True,
        )
        second_stage_result = optimize_second_stage(
            cir,
            stage2_flavor=cfg["stage2_flavor"],
        )
        print(
            f"[{cache_key}] Stage 2 optimization: DONE "
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
            cached_payload = _load_first_stage_result(cache_path)
            first_stage_result = _validate_cached_result(cir, cfg, cached_payload)
            _apply_first_stage_result(cir, first_stage_result)
            print(
                    f"[{cache_key}] Loaded cached first-stage result: "
                f"{first_stage_result['w_param']}={first_stage_result['W1']}, "
                f"{first_stage_result['id_param']}={first_stage_result['ID1']}, "
                f"{first_stage_result['wc_param']}={first_stage_result['W1C']}"
            )
        else:
            print(f"[{cache_key}] Stage 1 optimization: START", flush=True)
            first_stage_result = optimize_first_stage_parallel(
                cir,
                stage1_flavor=cfg["stage1_flavor"],
                cascode_ciss_par=_stage1_ciss_par_for_stage2(cfg["stage2_flavor"]),
            )
            if first_stage_result is None:
                raise RuntimeError(
                    f"First-stage optimization did not produce a valid result for '{cache_key}'."
                )
            _save_first_stage_result(cache_path, cfg, first_stage_result)
            print(f"[{cache_key}] Saved first-stage cache to '{cache_path}'.")
            print(f"[{cache_key}] Stage 1 optimization: DONE", flush=True)

        # key is used only for cache identity and HTML naming.
        stage_tag = html_key
        all_results.append(
            {
                "design": cache_key,
                "project": cfg["project"],
                "stage_tag": stage_tag,
                "third_stage": third_stage_result,
                "first_stage": first_stage_result,
                "second_stage": second_stage_result,
                "cir": cir,
                "circuit_image": circuit_image,
            }
        )

    print("\n======================= Run Summary =======================")
    for result in all_results:
        first = result["first_stage"]
        second = result["second_stage"]
        print(
            f"{result['design']} ({result['stage_tag']}): "
            f"{first['w_param']}={first['W1']*1e6:.2f}um, "
            f"{first['id_param']}={first['ID1']*1e3:.3f}mA, "
            f"{first['wc_param']}={first['W1C']*1e6:.2f}um, "
            f"{second['w_param']}={second['W2']*1e6:.2f}um, "
            f"{second['id_param']}={second['ID2']*1e3:.3f}mA"
        )

    for result in all_results:
        generate_circuit_performance_html(
            result["cir"],
            design_tag=result["stage_tag"],
            iq=result["third_stage"]["Iq"],
            i_peak=result["third_stage"]["I_peak"],
            stage1_flavor=result["first_stage"]["stage1_flavor"],
            stage2_flavor=result["second_stage"]["stage2_flavor"],
            circuit_image=result["circuit_image"],
        )
    generate_circuit_performance_menu_html([result["stage_tag"] for result in all_results])
    _dedupe_main_index_links()


if __name__ == "__main__":
    run()
