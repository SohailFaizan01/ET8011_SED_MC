from SLiCAP import *

# Project setup
prj = initProject("Active_E-field_Probe")

################################################# Specifications #################################################

# --- Antenna / System ---
L_ant    = 0.25            # Antenna length [m]
C_ant    = 12e-12          # Capacitance per meter [F/m]
Cs       = C_ant * L_ant   # Antenna capacitance [F]
Z_in     = 50              # Receiver input impedance [Ω]
L_Cable  = 25              # Max cable length [m]
T_op_min = 0               # Operating temperature range [°C]
T_op_max = 70              # Operating temperature range [°C]
P_cons   = 5e-2            # Max power consumption [W]
f_min    = 9e3             # Lower -3dB frequency [Hz]
f_max    = 80e6            # Upper -3dB frequency [Hz]
P_1dB    = 0               # 1dB compression point [dBm]
VDD_max  = 1.8             # Supply voltage [V]
E_max    = 1               # Max E-field [V/m]

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
                         units       = "degC",
                         specType    = "System"))

specs.append(specItem("T_op_max",
                         description = "Maximum Operating temperature",
                         value       = T_op_max,
                         units       = "degC",
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

htmlPage("Specifications", index=False, label='Specifications')

specs2html(specs, types=[])

head2html("Additional Specifications", label='Add_Specs')
text2html("- Intermodulation products must be below -50 dBm in the frequency band of interest.")
text2html("- CMOS18 technology must be used.")
text2html("- The antenna must be protected against electrostatic discharge.")
text2html("- Input referred noise must be below:")

from sympy import symbols

# define symbol
f = symbols('f')

eqn2html(
    arg1='S_En',
    arg2=1e-15 * (1 + (1e12/f**2)),
    units='V**2/m**2 Hz',
    label='eq_sen',
    labelText='Input-referred noise'
)

################################################## Circuit Data ##################################################

# Create a circuit object from a schematic file or a SLiCAP netlist:
fileName = "Active_E-Field_Probe"
fileName = 'KiCad/' + fileName + '/' + fileName + '.kicad_sch'

cir = makeCircuit(fileName,imgWidth=400)

specs2circuit(specs, cir)

# ---------------------------
# Symbols
# ---------------------------
A, B, C, D, Cs, Voc, Vout, f, s, Z0 = symbols('A B C D Cs Voc Vout f s Z0', real=True)
j = I  # imaginary unit

# ---------------------------
# Text and Equations
# ---------------------------
text2html("## Two-Port Representation of the Active Antenna")

text2html("We start with a general **ABCD two-port matrix** representation:")

eqn2html(
    arg1=Matrix([[A, B],[C, D]]),
    arg2=Matrix([[symbols('V1')],[symbols('I1')]]),
    label='eq_abcd',
    labelText='Two-port ABCD definition'
)



# Constraint: no current into the input (open input port)
text2html("Since no current flows into the input, we obtain the condition:")

eqn2html('A/B', '0', label='eq_open')

# Characteristic impedance relation
text2html("For matching with 50 Ω system impedance:")

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