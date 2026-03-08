################################################# Circuit Performance HTML Page #################################################
from SLiCAP import *

from .plot_generation import generate_performance_plots


def _performance_page_filename(design_tag):
    suffix = design_tag.upper().strip()
    if suffix:
        return f"Active_E_Field_Probe_Circuit-Performance-({suffix}).html"
    return "Active_E_Field_Probe_Circuit-Performance.html"


def generate_circuit_performance_menu_html(stage_tags):
    htmlPage("Circuit Performance", index=False, label="Circuit_Performance")
    head2html("Performance Variants")
    for stage_tag in stage_tags:
        suffix = stage_tag.upper().strip()
        file_name = _performance_page_filename(suffix)
        text2html(f'<a href="{file_name}">Circuit Performance ({suffix})</a>')


def _stage_specs_from_circuit(cir, stage1_flavor=None, stage2_flavor=None):
    stage1 = (stage1_flavor or "").upper()
    stage2 = (stage2_flavor or "").upper()

    stage_params = []

    if stage1 == "P":
        stage_params.extend(
            [
                ("W1_P", "Stage-1 PMOS width", "m"),
                ("ID1_P", "Stage-1 PMOS drain current", "A"),
                ("W1C_P", "Stage-1 PMOS cascode width", "m"),
            ]
        )
    else:
        # Default to N flavor when unspecified.
        stage_params.extend(
            [
                ("W1_N", "Stage-1 NMOS width", "m"),
                ("ID1_N", "Stage-1 NMOS drain current", "A"),
                ("W1C_N", "Stage-1 NMOS cascode width", "m"),
            ]
        )

    if stage2 in ("PN", "NP"):
        stage_params.extend(
            [
                ("W2_N", "Stage-2 NMOS width (X6 side)", "m"),
                ("ID2_N", "Stage-2 NMOS drain current (X6 side)", "A"),
                ("W2_P", "Stage-2 PMOS width (X4 side)", "m"),
                ("ID2_P", "Stage-2 PMOS drain current (X4 side)", "A"),
            ]
        )
    elif stage2 == "P":
        stage_params.extend(
            [
                ("W2_P", "Stage-2 PMOS width", "m"),
                ("ID2_P", "Stage-2 PMOS drain current", "A"),
            ]
        )
    else:
        # Default to N flavor when unspecified.
        stage_params.extend(
            [
                ("W2_N", "Stage-2 NMOS width", "m"),
                ("ID2_N", "Stage-2 NMOS drain current", "A"),
            ]
        )

    stage_params.extend(
        [
        ("W_N", "Stage-3 NMOS width", "m"),
        ("ID_N", "Stage-3 NMOS drain current", "A"),
        ("W_P", "Stage-3 PMOS width", "m"),
        ("ID_P", "Stage-3 PMOS drain current", "A"),
        ]
    )

    rows = []
    for symbol, description, units in stage_params:
        try:
            value = float(cir.getParValue(symbol))
        except Exception:
            continue
        rows.append(
            specItem(
                symbol=symbol,
                description=description,
                value=value,
                units=units,
                specType="Circuit_Performance",
            )
        )
    return rows


def generate_circuit_performance_html(
    cir,
    design_tag="",
    iq=None,
    i_peak=None,
    stage1_flavor=None,
    stage2_flavor=None,
    circuit_image="Active_E_Field_Probe.svg",
):
    suffix = design_tag.upper().strip()
    title = "Circuit Performance" if not suffix else f"Circuit Performance ({suffix})"
    label = "Circuit_Performance" if not suffix else f"Circuit_Performance_{suffix}"

    perf = generate_performance_plots(cir, suffix=suffix, iq=iq, i_peak=i_peak)

    htmlPage(title, index=False, label=label)

    head2html("Circuit")
    img2html(circuit_image, width=1000)

    head2html("Graphs")
    head3html("Magnitude Plot")
    img2html(perf["fb_mag_image"], width=800)
    img2html(perf["ph_mag_image"], width=800)

    eqn2html("gain", perf["gain"].laplace)
    eqn2html("asymptotic", perf["asymptotic"].laplace)
    eqn2html("loopgain", perf["loopgain"].laplace)
    eqn2html("servo", perf["servo"].laplace)
    eqn2html("direct", perf["direct"].laplace)

    pz2html(perf["pole_zero_lg"], label=f"PoleZero Loopgain {suffix}".strip(), labelText='PoleZero Loopgain')
    pz2html(perf["pole_zero_s"], label=f"PoleZero Servo {suffix}".strip(), labelText='PoleZero Servo')
    pz2html(perf["pole_zero_g"], label=f"PoleZero Gain {suffix}".strip(), labelText='PoleZero Gain')

    if perf["stepped_pz_gain_image"] is not None:
        head3html("Stepped PZ (Gain)")
        img2html(perf["stepped_pz_gain_image"], width=750)

    if perf["stepped_pz_loopgain_image"] is not None:
        head3html("Stepped PZ (Loopgain)")
        img2html(perf["stepped_pz_loopgain_image"], width=750)

    head3html("Noise Spectrum")
    img2html("noise_function_plot_HZ.svg", width=750)
    img2html(perf["inoise_image"], width=700)
    eqn2html("S_IRnoise", perf["noise_expr"].inoise)

    head2html("Stage Widths and Currents")
    stage_specs = _stage_specs_from_circuit(cir, stage1_flavor=stage1_flavor, stage2_flavor=stage2_flavor)
    if stage_specs:
        specs2html(stage_specs)
