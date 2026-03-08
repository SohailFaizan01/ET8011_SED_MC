from SLiCAP import *
from sympy import symbols
from .specifications import specs


def generate_specifications_html(label_suffix=""):
    suffix = f"_{label_suffix}" if label_suffix else ""
    htmlPage("Specifications", index=False, label=f"Specifications{suffix}")
    specs2html(specs)

    head2html("Additional Specifications", label=f"Add_Specs{suffix}")
    text2html("- Intermodulation products must be below -50 dBm in the frequency band of interest.")
    text2html("- CMOS18 technology must be used.")
    text2html("- The antenna must be protected against electrostatic discharge.")
    text2html("- Input referred noise must be below:")

    img2html("noise_function_plot_HZ.svg", width=700)

    f = symbols("f")
    eqn2html(
        arg1="S_En",
        arg2=1e-15 * (1 + (1e12 / f**2)),
        units="V**2/m**2 1/Hz",
        label=f"eq_sen_field{suffix}",
        labelText="Input-referred noise",
    )
    eqn2html(
        arg1="S_En",
        arg2=1e-9 * (1 + (1e12 / f**2)),
        units="V**2/Hz",
        label=f"eq_sen_voltage{suffix}",
        labelText="Input-referred noise",
    )
