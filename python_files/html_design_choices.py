################################################# Design Choices #################################################

from SLiCAP import *
from sympy import symbols, N
from .specifications import *
from .circuit import *

htmlPage("Design Process", index=False, label='Design_Process')
head2html("Initial choices")
text2html("<ul>"
"           <li>Protect against ESD => TVS Diode => Current input to avoid non linear impedance voltage division</li>"
"           <li>Current input => 0 Ohm input impedance</li>"
"           <li>50 Ohm matched circuit => 50 Ohm output impedance => D/C = 50</li>"
"</ul>")

head2html("Most simple solution:")
#insert Link

head3html("Does it meet the specifications?")
Vout_Amp_req = (10**(-3)*10**P_1dB * Z_in)**0.5 * (Z_in/(Z_in+Z_out_amp))**(-1)
gain_req = Vout_Amp_req/V_in_max
max_power_out = Vout_Amp_req**2/50 + id_n*VDD

text2html(f"""
<table>
<tr><td>Spec</td>                       <td>Required:</td>         <td>Obtained:</td></tr>
<tr><td>Gain?</td>                      <td> > {N(gain_req,2)}</td> <td> {N(gain.laplace,2)}</td></tr>
<tr><td>Output Impedance</td>           <td> {Z_out_amp} </td>     <td> See Graph</td></tr>
<tr><td>Power Consumption</td>          <td> < {P_cons} W</td>     <td> {N(max_power_out,2)}</td></tr>
<tr><td>Noise</td>                      <td> See Graph </td>       <td> See Graph</td></tr>
<tr><td>ESD Protection</td>             <td> Yes </td>             <td> Yes</td></tr>
<tr><td>Intermodulation products</td>   <td> < {P_int} dBm</td>    <td> TBD</td></tr>
</table>
""")

# Plot gain
eqn2html("gain",        gain.laplace)
eqn2html("asymptotic",  asymptotic.laplace)
eqn2html("loopgain",    loopgain.laplace)
eqn2html("servo",       servo.laplace)
eqn2html("direct",      direct.laplace)

img2html("fb_mag.svg",  width=600)

# Output Impedance
#img2html("R_out.svg",   width=600)
#eqn2html("R_out",       Rout_result.laplace, units="Ohm")

# Noise
img2html("noise_function_plot_HZ.svg", width=700)
img2html("inoise.svg",  width=600)
eqn2html("S_IRnoise",   noise.inoise)
img2html("onoise.svg",  width=600)
eqn2html("S_ORnoise",   noise.onoise)

# eqn2html("MNA_Matrix",   twoport.M)
# eqn2html("MNA_Iv",   twoport.Iv)
# eqn2html("MNA_Dv",   twoport.Dv)

# eqn2html("MNA_something", twoport.M.inv())

