#################################################### Two Port ####################################################

from SLiCAP import *

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










############################################## Random Blocks of Code ##############################################