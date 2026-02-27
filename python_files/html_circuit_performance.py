################################################# Circuit Performance HTML Page #################################################
from SLiCAP import *

from .plot_generation import generate_performance_plots


def generate_circuit_performance_html(cir, design_tag="", iq=None, i_peak=None):
    suffix = design_tag.upper().strip()
    title = "Circuit Performance" if not suffix else f"Circuit Performance ({suffix})"
    label = "Circuit_Performance" if not suffix else f"Circuit_Performance_{suffix}"

    perf = generate_performance_plots(cir, suffix=suffix, iq=iq, i_peak=i_peak)

    htmlPage(title, index=False, label=label)

    head2html("Circuit")
    img2html("Active_E_Field_Probe.svg", width=1000)

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

    if perf["stepped_pz_image"] is not None:
        img2html(perf["stepped_pz_image"], width=750)

    head3html("Noise Spectrum")
    img2html("noise_function_plot_HZ.svg", width=750)
    img2html(perf["inoise_image"], width=700)
    eqn2html("S_IRnoise", perf["noise_expr"].inoise)
