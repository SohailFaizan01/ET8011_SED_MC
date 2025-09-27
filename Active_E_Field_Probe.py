from SLiCAP import *
from sympy import symbols
# import numpy as np
# import matplotlib.pyplot as plt

# Project setup
prj = initProject("Active_E_Field_Probe")

################################################# Specifications #################################################
# --- Constants ---
k = 1.3806749e-23          #Boltzmann constant

# --- Antenna / System ---
L_ant    = 0.25            # Antenna length [m]
C_ant    = 12e-12          # Capacitance per meter [F/m]
Cs       = C_ant * L_ant   # Antenna capacitance [F]
Z_in     = 50              # Receiver input impedance [Ω]
L_Cable  = 25              # Max cable length [m]
T_op_min = 273             # Operating temperature range [°K] 0 C
T_op_max = 343             # Operating temperature range [°K] 70 C
P_cons   = 5e-2            # Max power consumption [W]
f_min    = 9e3             # Lower -3dB frequency [Hz]
f_max    = 80e6            # Upper -3dB frequency [Hz]
P_1dB    = 0               # 1dB compression point [dBm]
VDD_max  = 1.8             # Supply voltage [V]
E_max    = 1               # Max E-field [V/m]
P_int    = 50              # Max intermodulation Products power [dBm]

# --- Amplifier ---
Z_in_amp  = 50             # Amplifier input impedance [Ω]
Z_out_amp = 50             # Amplifier output impedance [Ω]
V_in_max  = L_ant * E_max  # Max input voltage [V]
# I_in_max  = 5e-3           # Max input current [A]
# I_out_max = 15e-3          # Max output current [A]
A_cl      = 6              # Closed-loop gain

specs = []

# --- Active Antenna (System) ---
specs.append(specItem("L_ant",
                         description = "Antenna length",
                         value       = L_ant,
                         units       = "m",
                         specType    = "System"))

specs.append(specItem("C_ant",
                         description = "Antenna capacitance",
                         value       = C_ant,
                         units       = "F/m",
                         specType    = "System"))

specs.append(specItem("C_s",
                         description = "Source capacitance",
                         value       = Cs,
                         units       = "F",
                         specType    = "System"))

specs.append(specItem("Z_in",
                         description = "Receiver input impedance",
                         value       = Z_in,
                         units       = "Ohm",
                         specType    = "System"))

specs.append(specItem("Cable_len",
                         description = "Max coax cable length",
                         value       = L_Cable,
                         units       = "m",
                         specType    = "System"))

specs.append(specItem("T_op_min",
                         description = "Minimum Operating temperature",
                         value       = T_op_min,
                         units       = "K",
                         specType    = "System"))

specs.append(specItem("T_op_max",
                         description = "Maximum Operating temperature",
                         value       = T_op_max,
                         units       = "K",
                         specType    = "System"))

specs.append(specItem("P_cons",
                         description = "Max power consumption",
                         value       = P_cons,
                         units       = "W",
                         specType    = "System"))

specs.append(specItem("f_-3dB_min",
                         description = "Minimum -3 dB frequency range",
                         value       = f_min,
                         units       = "Hz",
                         specType    = "System"))

specs.append(specItem("f_-3dB_max",
                         description = "Maximum -3 dB frequency range",
                         value       = f_max,
                         units       = "Hz",
                         specType    = "System"))

specs.append(specItem("P_1dB",
                         description = "1 dB compression point at receiver input (1 V/m)",
                         value       = P_1dB,
                         units       = "dBm",
                         specType    = "System"))

specs.append(specItem("VDD",
                         description = "Power Supply Voltage",
                         value       = VDD_max,
                         units       = "V",
                         specType    = "System"))

specs.append(specItem("E_max",
                         description = "Maximum E-field input",
                         value       = E_max,
                         units       = "V/m",
                         specType    = "System"))

specs.append(specItem("P_int",
                         description = "Maximum intermodulation product power",
                         value       = P_int,
                         units       = "dBm",
                         specType    = "System"))

# --- Amplifier ---
specs.append(specItem("Z_in_amp",
                         description = "Amplifier input impedance",
                         value       = Z_in_amp,
                         units       = "Ohm",
                         specType    = "Amplifier"))

specs.append(specItem("Z_out_amp",
                         description = "Amplifier output impedance",
                         value       = Z_out_amp,
                         units       = "Ohm",
                         specType    = "Amplifier"))

specs.append(specItem("V_in",
                         description = "Amplifier input voltage",
                         value       = V_in_max,
                         units       = "V",
                         specType    = "Amplifier"))

# specs.append(specItem("I_in",
#                          description = "Amplifier input current",
#                          value       = I_in_max,
#                          units       = "A",
#                          specType    = "Amplifier"))

# specs.append(specItem("I_out",
#                          description = "Amplifier output current",
#                          value       = I_out_max,
#                          units       = "A",
#                          specType    = "Amplifier"))

specs.append(specItem("A_cl",
                         description = "Amplifier closed-loop gain",
                         value       = A_cl,
                         units       = "NA",
                         specType    = "Amplifier"))

specs2csv(specs, "specs.csv")






################################################## Circuit Data ##################################################
fileName = "Active_E_Field_Probe"
fileName = 'KiCad/' + fileName + '/' + fileName + '.kicad_sch'

cir = makeCircuit(fileName,imgWidth=1000)

specs2circuit(specs, cir)

# result = doMatrix(cir)

# Iv     = result.Iv # Vector with independent variables 
#                    # (independent sources)
# M      = result.M  # MNA matrix
# Dv     = result.Dv # Vector with dependent variables 
#                    # (unknown nodal voltages and branch currents)

# print(Iv)

# print(M)

# print(Dv)

V_gain = doLaplace(cir, source='V1', detector='V_out').laplace
# L_gain = doLaplace(cir, )

# Plot gain
gain        = doLaplace(cir, source='V1', detector='V_out', numeric=True)
asymptotic  = doLaplace(cir, source='V1', detector='V_out', numeric=True, transfer='asymptotic', lgref='M1')
loopgain    = doLaplace(cir, source='V1', detector='V_out', numeric=True, transfer='loopgain', lgref='M1')
servo       = doLaplace(cir, source='V1', detector='V_out', numeric=True, transfer="servo", lgref='M1')
direct      = doLaplace(cir, source='V1', detector='V_out', numeric=True, transfer="direct", lgref='M1')

eqn2html("gain", gain.laplace)
eqn2html("asymptotic", asymptotic.laplace)
eqn2html("loopgain", loopgain.laplace)
eqn2html("servo", servo.laplace)
eqn2html("direct", direct.laplace)

# fb_model    = [gain, asymptotic, loopgain, servo, direct]
# fbmodel_mag = plotSweep("fb_mag", "Magnitude plots feedback model parameters", fb_model, 10, 10e5, 200)
# img2html("fb_mag.svg", width=600)


noise = doNoise(cir, source="V1", detector="V_out")

onoise = noise.onoise
NT = noise.onoiseTerms






############################################## Specifications HTML ##############################################
htmlPage("Specifications", index=False, label='Specifications')

specs2html(specs, types=[])

head2html("Additional Specifications", label='Add_Specs')
text2html("- Intermodulation products must be below -50 dBm in the frequency band of interest.")
text2html("- CMOS18 technology must be used.")
text2html("- The antenna must be protected against electrostatic discharge.")
text2html("- Input referred noise must be below:")

img2html("noise_function_plot.svg", width=700, label='nft', caption='')


f = symbols('f')
eqn2html(
    arg1='S_En',
    arg2=1e-15 * (1 + (1e12/f**2)),
    units='V**2/m**2 1/Hz',
    label='eq_sen',
    labelText='Input-referred noise'
)

img2html("noise_function_plot_HZ.svg", width=700, label='nft', caption='')

eqn2html(
    arg1='S_En',
    arg2=1e-15 * (1 + (1e12/f**2)),
    units='V**2/Hz',
    label='eq_sen',
    labelText='Input-referred noise'
)
# # Define the noise spectrum function
# def S_En(f):
#     return 1e-15 * (1 + 1e12 / f**2) * L_ant**2

# # Frequency range (log scale)
# f = np.logspace(3, 9, 1000)  # 1 kHz to 1 GHz

# # Compute spectrum
# S = S_En(f)

# # Plot
# plt.figure(figsize=(7,5))
# plt.loglog(f, S, label=r"$S_{En}(f)$")
# plt.xlabel("Frequency $f$ [Hz]")
# plt.ylabel(r"$S_{En}(f)$ $\left[\frac{V^2}{Hz}\right]$")
# plt.title("Noise Spectrum")
# plt.grid(True, which="both", ls="--")
# plt.legend()
# plt.show()


#################################################### Two Port ####################################################
htmlPage("Two Port", index=False, label='Two_Port')

text2html("## Two-Port Representation of the Active Antenna")

text2html("We start with a general **ABCD two-port matrix** representation:")

# eqn2html(
#     arg1=Matrix([[A, B],[C, D]]),
#     arg2=Matrix([[symbols('V1')],[symbols('I1')]]),
#     label='eq_abcd',
#     labelText='Two-port ABCD definition'
# )

# Constraint: no current into the input (open input port)
text2html("Since no current flows into the input, we obtain the condition:")

eqn2html('A/B', '0', label='eq_open')

# Characteristic impedance relation
text2html("For matching with 50 Ohm system impedance:")

eqn2html('D/C', 'Z0', label='eq_match')

# C defined in terms of Cs
eqn2html('C', '5*Cs/2', label='eq_c')

# Substitution of s = jω
eqn2html('s', 'j*2*pi*f', label='eq_s')

# ---------------------------
# Antenna Parameters
# ---------------------------
text2html("### Antenna Parameters")

eqn2html('Cs', '0.25*12e-12', units='F', label='eq_cs')
eqn2html('Voc', '0.25*1', units='V', label='eq_voc')

# ---------------------------
# Output Voltage
# ---------------------------
text2html("The output voltage is given by:")

eqn2html('V_out', 'sqrt(P*R)*2', label='eq_vout')

text2html("Numerical evaluation yields:")

eqn2html('V_out', '0.2236*2', units='V', label='eq_vout_num')

# RMS relation
eqn2html('V_RMS', '0.316', units='V', label='eq_vrms')

# ---------------------------
# Input Current Relation
# ---------------------------
text2html("Finally, the input current into the 2-port is:")

eqn2html('I_in', 'Voc*C + I0*D', label='eq_in')






################################################# Design Choices #################################################
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
<tr><td>Gain?</td>                      <td> > {gain_req:.2f}</td> <td> {V_gain}</td></tr>
<tr><td>Output Impedance</td>           <td> {Z_out_amp} </td>     <td> 50</td></tr>
<tr><td>Power Consumption</td>          <td> < {P_cons} W</td>     <td> {max_power_out}</td></tr>
<tr><td>Noise</td>                      <td> {noise_spec:.2e}</td>  <td> {noise_obt:.2e}</td></tr>
<tr><td>ESD Protection</td>             <td> Yes </td>             <td> Yes</td></tr>
<tr><td>Intermodulation products</td>   <td> < {P_int} dBm</td>    <td> There is no attenuation currently</td></tr>
</table>
""")