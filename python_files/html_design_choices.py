from SLiCAP import *


def generate_design_choices_html(label_suffix=""):
    suffix = f"_{label_suffix}" if label_suffix else ""
    htmlPage("Design Process", index=False, label=f"Design_Process{suffix}")

    head3html("Amplifier Type")
    text2html(
        "Current-to-voltage amplifier. To avoid non-linearity of the input ESD protection "
        "(TVS diode), a current input is required. The output quantity is voltage, "
        "as this will be read out by the spectrum analyser."
    )

    head3html("Input / Output Impedances")
    text2html(
        "- As the input type is current, the input impedance must approach 0 Ohm.<br>"
        "- To minimize reflections and maximize power transfer, a 50 Ohm output impedance is required."
    )
    text2html(
        "<b>Implementation:</b> The general feedback controller will satisfy this requirement "
        "if sufficient loop gain is achieved, such that the input behaves as a virtual ground. "
        "A brute-force approach is used for simplicity; the impact on noise performance must still be validated."
    )

    head3html("Feedback Structure")
    text2html("Passive integrating feedback structure to compensate the differentiated input signal.")
    text2html("<b>Implementation:</b> Capacitive feedback (integrator).")

    head3html("Controller")
    text2html(
        "A two-stage controller is required to obtain sufficient loop gain. "
        "A single-stage design cannot simultaneously provide enough gain and a low output impedance of 50 Ohm. "
        "A class-AB output stage is selected to reduce power consumption."
    )

    head3html("Noise")
    text2html(
        "The first stage dominates the total noise performance. Noise contributions from the second stage "
        "are divided by the gain of the first stage and are therefore less significant."
    )
