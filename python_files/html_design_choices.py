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

Vout_Amp_req = (10**(-3)*10**P_1dB * Z_in)**0.5 * (Z_in/(Z_in+Z_out_amp))
gain_req = Vout_Amp_req * ((Z_in+Z_out_amp)/Z_in)/V_in_max

max_power_out = Vout_Amp_req**2/100

noise_spec = 1e-15 * (1 + (1e12/(9e3)**2))
noise_obt = 100*T_op_max*k

text2html(f"""
<table>
<tr><td>Spec</td>                       <td>Required:</td>         <td>Obtained:</td></tr>
<tr><td>Gain?</td>                      <td> > {gain_req:.2f}</td> <td> {N(V_gain, 2)}</td></tr>
<tr><td>Output Impedance</td>           <td> {Z_out_amp} </td>     <td> 50</td></tr>
<tr><td>Power Consumption</td>          <td> < {P_cons} W</td>     <td> {max_power_out}</td></tr>
<tr><td>Noise</td>                      <td> {noise_spec:.2e}</td> <td> {noise_obt:.2e}</td></tr>
<tr><td>ESD Protection</td>             <td> Yes </td>             <td> Yes</td></tr>
<tr><td>Intermodulation products</td>   <td> < {P_int} dBm</td>    <td> There is no attenuation currently</td></tr>
</table>
""")