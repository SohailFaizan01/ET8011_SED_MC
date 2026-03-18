from SLiCAP import *
import json
import os
import shutil
from pathlib import Path


CACHE_DIR = Path("cache")
HTML_DIR = Path("html")
HTML_IMG_DIR = HTML_DIR / "img"
GENERATED_SPECS_DIR = Path("python_files") / "generated_specs"

STAGE_PN = "KiCad/Active_E_Field_Probe/stage_PN/Active_E_Field_Probe.kicad_sch"
STAGE_NP = "KiCad/Active_E_Field_Probe/stage_NP/Active_E_Field_Probe.kicad_sch"
STAGE_NN = "KiCad/Active_E_Field_Probe/stage_NN/Active_E_Field_Probe.kicad_sch"
STAGE_NBalSF = "KiCad/Active_E_Field_Probe/stage_N_balSF/Active_E_Field_Probe.kicad_sch"
STAGE_PBalSF = "KiCad/Active_E_Field_Probe/stage_P_balSF/Active_E_Field_Probe.kicad_sch"

STAGE_PN_PhZ = "KiCad/Active_E_Field_Probe/stage_PN_PhZ/Active_E_Field_Probe.kicad_sch"
STAGE_NP_PhZ = "KiCad/Active_E_Field_Probe/stage_NP_PhZ/Active_E_Field_Probe.kicad_sch"
STAGE_NN_PhZ = "KiCad/Active_E_Field_Probe/stage_NN_PhZ/Active_E_Field_Probe.kicad_sch"
STAGE_NBalSF_PhZ = "KiCad/Active_E_Field_Probe/stage_N_balSF_PhZ/Active_E_Field_Probe.kicad_sch"
STAGE_PBalSF_PhZ = "KiCad/Active_E_Field_Probe/stage_P_balSF_PhZ/Active_E_Field_Probe.kicad_sch"

DESIGN_SPECS = [
    {
        "key": "NBalSF",
        "project": STAGE_NBalSF,
        "stage1_flavor": "N",
        "stage2_flavor": "PN",
    },
        {
        "key": "PBalSF",
        "project": STAGE_PBalSF,
        "stage1_flavor": "P",
        "stage2_flavor": "NP",
    },
    {
        "key": "NP",
        "project": STAGE_NP,
        "stage1_flavor": "N",
        "stage2_flavor": "P",
    },
    {
        "key": "PN",
        "project": STAGE_PN,
        "stage1_flavor": "P",
        "stage2_flavor": "N",
    },
]

# DESIGN_SPECS = [
#     {
#         "key": "NBalSF",
#         "project": STAGE_NBalSF_PhZ,
#         "stage1_flavor": "N",
#         "stage2_flavor": "PN",
#     },
#     {
#         "key": "PBalSF",
#         "project": STAGE_PBalSF_PhZ,
#         "stage1_flavor": "P",
#         "stage2_flavor": "NP",
#     },
#     {
#         "key": "NP",
#         "project": STAGE_NP_PhZ,
#         "stage1_flavor": "N",
#         "stage2_flavor": "P",
#     },
#     {
#         "key": "PN",
#         "project": STAGE_PN_PhZ,
#         "stage1_flavor": "P",
#         "stage2_flavor": "N",
#     },
# ]


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


def _stage1_ciss_par_for_stage2(stage2_flavor, design_key=None):
    flavor = (stage2_flavor or "").upper()
    key = (design_key or "").upper()
    # Per your rule:
    # - PN, NP, and NBalSF -> X4
    # - PBalSF -> X6
    if key == "PBALSF":
        return "c_iss_X6"
    if key == "NBALSF":
        return "c_iss_X4"
    if flavor in ("PN", "NP"):
        return "c_iss_X4"
    # Default to X4 for any remaining cases.
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


def _write_stage_specs_module(
    path,
    design_key,
    stage1_flavor,
    stage2_flavor,
    cir_obj,
    base_specs,
    first_stage_result,
    second_stage_result,
    third_stage_result,
):
    path.parent.mkdir(parents=True, exist_ok=True)
    init_path = path.parent / "__init__.py"
    if not init_path.exists():
        init_path.write_text("", encoding="utf-8")

    stage1 = (stage1_flavor or "").upper()
    stage2 = (stage2_flavor or "").upper()

    stage_symbols = set()
    all_stage_symbols = {
        "W1_N", "L1_N", "ID1_N", "W1C_N", "L1C_N",
        "W1_P", "L1_P", "ID1_P", "W1C_P", "L1C_P",
        "W2_N", "L2_N", "ID2_N",
        "W2_P", "L2_P", "ID2_P",
        "W_N", "L_N", "ID_N",
        "W_P", "L_P", "ID_P",
    }

    def mark(symbol):
        stage_symbols.add(symbol)

    # Stage 1
    if stage1 == "P":
        mark("W1_P")
        mark("L1_P")
        mark("ID1_P")
        mark("W1C_P")
        mark("L1C_P")
    else:
        mark("W1_N")
        mark("L1_N")
        mark("ID1_N")
        mark("W1C_N")
        mark("L1C_N")

    # Stage 2
    if stage2 in ("PN", "NP"):
        mark("W2_N")
        mark("L2_N")
        mark("ID2_N")
        mark("W2_P")
        mark("L2_P")
        mark("ID2_P")
    elif stage2 == "P":
        mark("W2_P")
        mark("L2_P")
        mark("ID2_P")
    else:
        mark("W2_N")
        mark("L2_N")
        mark("ID2_N")

    # Stage 3 (push-pull)
    mark("W_N")
    mark("L_N")
    mark("ID_N")
    mark("W_P")
    mark("L_P")
    mark("ID_P")

    overrides = {}
    # Stage 1 overrides from optimization results.
    if first_stage_result:
        for key in ("w_param", "id_param", "wc_param"):
            par = first_stage_result.get(key)
            if par:
                value_key = "W1" if key == "w_param" else "ID1" if key == "id_param" else "W1C"
                if value_key in first_stage_result:
                    overrides[par] = float(first_stage_result[value_key])

    # Stage 2 overrides from optimization results.
    if second_stage_result:
        for key in ("w_param", "id_param"):
            par = second_stage_result.get(key)
            if par:
                value_key = "W2" if key == "w_param" else "ID2"
                if value_key in second_stage_result:
                    overrides[par] = float(second_stage_result[value_key])
        for par in ("W2_N", "W2_P", "ID2_N", "ID2_P"):
            if par in second_stage_result:
                overrides[par] = float(second_stage_result[par])

    # Stage 3 overrides from optimization results (widths only).
    if third_stage_result:
        if "Wn" in third_stage_result:
            overrides["W_N"] = float(third_stage_result["Wn"])
        if "Wp" in third_stage_result:
            overrides["W_P"] = float(third_stage_result["Wp"])

    def _format_value(raw_value):
        if isinstance(raw_value, str):
            return raw_value
        try:
            return f"{float(raw_value):.6e}"
        except Exception:
            return repr(raw_value)

    lines = []
    lines.append("################################################# Specifications #################################################\n")
    lines.append("from SLiCAP import *\n\n")
    lines.append(f"# Auto-generated stage specs for {design_key}\n\n")
    lines.append("specs = []\n\n")

    for spec in base_specs:
        symbol_raw = getattr(spec, "symbol", None)
        symbol = str(symbol_raw) if symbol_raw is not None else None
        description = getattr(spec, "description", "")
        units = getattr(spec, "units", "")
        spec_type = getattr(spec, "specType", "")
        value = getattr(spec, "value", None)

        if symbol in all_stage_symbols and symbol not in stage_symbols:
            continue

        if symbol in overrides:
            value = overrides[symbol]
        elif symbol in stage_symbols:
            value = float(cir_obj.getParValue(symbol))
        formatted = _format_value(value)

        lines.append(
            "specs.append(specItem("
            f"\"{symbol}\", "
            f"description = \"{description}\", "
            f"value       = {formatted}, "
            f"units       = \"{units}\", "
            f"specType    = \"{spec_type}\"))\n\n"
        )

    path.write_text("".join(lines), encoding="utf-8")


def run():
    _cleanup_html_outputs()
    initProject("Active_E_Field_Probe")
    from python_files import specifications
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
                cascode_ciss_par=_stage1_ciss_par_for_stage2(cfg["stage2_flavor"], cfg["key"]),
            )
            if first_stage_result is None:
                raise RuntimeError(
                    f"First-stage optimization did not produce a valid result for '{cache_key}'."
                )
            _save_first_stage_result(cache_path, cfg, first_stage_result)
            print(f"[{cache_key}] Saved first-stage cache to '{cache_path}'.")
            print(f"[{cache_key}] Stage 1 optimization: DONE", flush=True)

        specs_module_path = GENERATED_SPECS_DIR / f"specs_{cache_key}.py"
        _write_stage_specs_module(
            specs_module_path,
            cache_key,
            first_stage_result.get("stage1_flavor", cfg["stage1_flavor"]),
            second_stage_result.get("stage2_flavor", cfg["stage2_flavor"]),
            cir,
            specifications.specs,
            first_stage_result,
            second_stage_result,
            third_stage_result,
        )
        print(f"[{cache_key}] Wrote stage specs to '{specs_module_path}'.")

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
        cost_str = (
            f"{float(first['best_cost']):.4f}"
            if first.get("best_cost") is not None
            else "n/a"
        )
        print(
            f"{result['design']} ({result['stage_tag']}): "
            f"{first['w_param']}={first['W1']*1e6:.2f}um, "
            f"{first['id_param']}={first['ID1']*1e3:.3f}mA, "
            f"{first['wc_param']}={first['W1C']*1e6:.2f}um, "
            f"{second['w_param']}={second['W2']*1e6:.2f}um, "
            f"{second['id_param']}={second['ID2']*1e3:.3f}mA, "
            f"Cost={cost_str}"
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
