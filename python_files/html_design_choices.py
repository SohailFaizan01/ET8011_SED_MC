################################################# Design Choices #################################################

from SLiCAP import *
from sympy import symbols, N
from .specifications import *
from .circuit import cir
from .plot_generation import *

htmlPage("Design Process", index=False, label='Design_Process')

# --------------------------------------------------
# Amplifier Type
# --------------------------------------------------

head3html("Amplifier Type")

text2html(
    "Current-to-voltage amplifier. To avoid non-linearity of the input ESD protection "
    "(TVS diode), a current input is required. The output quantity is voltage, "
    "as this will be read out by the spectrum analyser."
)

# --------------------------------------------------
# Input / Output Impedances
# --------------------------------------------------

head3html("Input / Output Impedances")

text2html(
    "- As the input type is current, the input impedance must approach 0 Ohm.<br>"
    "- To minimize reflections and maximize power transfer, a 50 Ohm output impedance is required."
)

text2html(
    "<b>Implementation:</b> The general feedback controller will satisfy this requirement "
    "if sufficient loop gain is achieved, such that the input behaves as a virtual ground. "
    "A brute-force approach is used for simplicity; the impact on noise performance "
    "must still be validated."
)

# --------------------------------------------------
# Feedback Structure
# --------------------------------------------------

head3html("Feedback Structure")

text2html(
    "Passive integrating feedback structure to compensate the differentiated input signal."
)

text2html(
    "<b>Implementation:</b> Capacitive feedback (integrator)."
)

# --------------------------------------------------
# Controller Architecture
# --------------------------------------------------

head3html("Controller")

text2html(
    "A two-stage controller is required to obtain sufficient loop gain. "
    "A single-stage design cannot simultaneously provide enough gain and a low output "
    "impedance of 50 Ohm. A class-AB output stage is selected to reduce power consumption."
)

text2html("<b>Input stage options:</b>")

text2html(
    "- Common-source (CS): Inverting stage, results in a positive feedback loop with the output stage.<br>"
    "- Common-drain (CD): Insufficient gain.<br>"
    "- Common-gate (CG): Loads the signal source.<br>"
    "- Differential pair: Provides gain without loading the input, but has higher noise."
)

text2html("<b>Output stage options:</b>")

text2html(
    "- Complementary parallel stage: Provides gain with low power consumption.<br>"
    "- Anti-parallel (CS-CD) stage: Not suitable due to lack of gain and large voltage swing "
    "requirements in the first stage, increasing non-linearity."
)

text2html(
    "<b>Final implementation:</b> Differential input stage combined with a complementary "
    "parallel output stage."
)

text2html(
    "<b>Differential input stage:</b> NMOS devices are preferred over PMOS devices, "
    "as they can be made smaller for the same performance."
)

# --------------------------------------------------
# Noise Considerations
# --------------------------------------------------

head3html("Noise")

text2html(
    "The first stage dominates the total noise performance. Noise contributions from the "
    "second stage are divided by the gain of the first stage and are therefore less significant."
)

text2html(
    "The width of the input transistor pair is increased until the noise specification is met. "
    "The drain current is increased accordingly to maintain a constant inversion coefficient (IC), "
    "and thereby preserve the transit frequency (fT)."
)

# --------------------------------------------------
# Drive Capability
# --------------------------------------------------

head3html("Drive Capability")

text2html(
    "The drive capability of the first stage must at least supply the gate current of the "
    "second stage."
)

text2html(
    "The second stage determines the main drive capability, as it directly drives the output."
)

eqn2html("P_out", "1e-3", units="W", label="eq_power")
eqn2html("V_out", "(1e-3 * 50)**0.5", units="V", label="eq_vout")

text2html(
    "To account for the 50 Ohm output impedance, the required voltage swing is doubled."
)

eqn2html("V_out", "2 * (1e-3 * 50)**0.5", units="V", label="eq_vout_amp")
eqn2html("I_drive", "2 * (1e-3 * 50)**0.5 / 100", units="A", label="eq_drive")

# --------------------------------------------------
# Transfer Requirement
# --------------------------------------------------

head3html("Transfer")

eqn2html("A_v", "0.4472 / 0.25", label="eq_gain")

text2html(
    "From the required gain, the feedback capacitor is chosen relative to the sensing capacitor."
)

eqn2html("C_fb", "0.56 * C_s", units="F", label="eq_cfb")

# --------------------------------------------------
# Distortion / Non-Linearity
# --------------------------------------------------

head3html("Distortion / Non-Linearity")

text2html(
    "TBD"
)

# --------------------------------------------------
# Biasing
# --------------------------------------------------

head3html("Biasing")

text2html(
    "TBD"
)











############################################## Random Blocks of Code ##############################################

###### Old Initial choices
# head3html("Initial choices")
# text2html("<ul>"
# "           <li>Protect against ESD => TVS Diode => Current input to avoid non linear impedance voltage division</li>"
# "           <li>Current input => 0 Ohm input impedance</li>"
# "           <li>50 Ohm matched circuit => 50 Ohm output impedance => D/C = 50</li>"
# "</ul>")

###### Old 'does it meet the specs' table
# head3html("Does it meet the specifications?")
# Vout_Amp_req = (10**(-3)*10**P_1dB * Z_in)**0.5 * (Z_in/(Z_in+Z_out_amp))**(-1)
# gain_req = Vout_Amp_req/V_in_max
# max_power_out = Vout_Amp_req**2/50 + id_n*VDD

# text2html(f"""
# <table>
# <tr><td>Spec</td>                       <td>Required:</td>         <td>Obtained:</td></tr>
# <tr><td>Gain?</td>                      <td> > {N(gain_req,2)}</td> <td> {N(gain.laplace,2)}</td></tr>
# <tr><td>Output Impedance</td>           <td> {Z_out_amp} </td>     <td> See Graph</td></tr>
# <tr><td>Power Consumption</td>          <td> < {P_cons} W</td>     <td> {N(max_power_out,2)}</td></tr>
# <tr><td>Noise</td>                      <td> See Graph </td>       <td> See Graph</td></tr>
# <tr><td>ESD Protection</td>             <td> Yes </td>             <td> Yes</td></tr>
# <tr><td>Intermodulation products</td>   <td> < {P_int} dBm</td>    <td> TBD</td></tr>
# </table>
# """)