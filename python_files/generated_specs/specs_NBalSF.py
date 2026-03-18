################################################# Specifications #################################################
from SLiCAP import *

# Auto-generated stage specs for NBalSF

specs = []

specs.append(specItem("L_ant", description = "Antenna length", value       = 2.500000e-01, units       = "m", specType    = "System"))

specs.append(specItem("C_ant", description = "Antenna capacitance", value       = 1.200000e-11, units       = "F/m", specType    = "System"))

specs.append(specItem("C_s", description = "Source capacitance", value       = 3.000000e-12, units       = "F", specType    = "System"))

specs.append(specItem("Z_in", description = "Receiver input impedance", value       = 5.000000e+01, units       = "Ohm", specType    = "System"))

specs.append(specItem("Cable_len", description = "Max coax cable length", value       = 2.500000e+01, units       = "m", specType    = "System"))

specs.append(specItem("T_op_min", description = "Minimum Operating temperature", value       = 2.730000e+02, units       = "K", specType    = "System"))

specs.append(specItem("T_op_max", description = "Maximum Operating temperature", value       = 3.430000e+02, units       = "K", specType    = "System"))

specs.append(specItem("P_cons", description = "Max power consumption", value       = 5.000000e-02, units       = "W", specType    = "System"))

specs.append(specItem("f_-3dB_min", description = "Minimum -3 dB frequency range", value       = 9.000000e+03, units       = "Hz", specType    = "System"))

specs.append(specItem("f_-3dB_max", description = "Maximum -3 dB frequency range", value       = 8.000000e+07, units       = "Hz", specType    = "System"))

specs.append(specItem("P_1dB", description = "1 dB compression point at receiver input (1 V/m)", value       = 0.000000e+00, units       = "dBm", specType    = "System"))

specs.append(specItem("VDD", description = "Power Supply Voltage", value       = 1.800000e+00, units       = "V", specType    = "System"))

specs.append(specItem("E_max", description = "Maximum E-field input", value       = 1.000000e+00, units       = "V/m", specType    = "System"))

specs.append(specItem("P_int", description = "Maximum intermodulation product power", value       = 5.000000e+01, units       = "dBm", specType    = "System"))

specs.append(specItem("Z_in_amp", description = "Amplifier input impedance", value       = 5.000000e+01, units       = "Ohm", specType    = "Amplifier"))

specs.append(specItem("Z_out_amp", description = "Amplifier output impedance", value       = 5.000000e+01, units       = "Ohm", specType    = "Amplifier"))

specs.append(specItem("V_in", description = "Amplifier input voltage", value       = 2.500000e-01, units       = "V", specType    = "Amplifier"))

specs.append(specItem("A_cl", description = "Amplifier closed-loop gain", value       = 2.500000e+00, units       = "NA", specType    = "Amplifier"))

specs.append(specItem("W_N", description = "Transistor width", value       = 2.259715e-05, units       = "m", specType    = "Amplifier"))

specs.append(specItem("L_N", description = "Transistor length", value       = 1.800000e-07, units       = "m", specType    = "Amplifier"))

specs.append(specItem("ID_N", description = "Transistor drain current", value       = 5.689378e-05, units       = "A", specType    = "Amplifier"))

specs.append(specItem("W_P", description = "Transistor width", value       = 7.061609e-05, units       = "m", specType    = "Amplifier"))

specs.append(specItem("L_P", description = "Transistor length", value       = 1.800000e-07, units       = "m", specType    = "Amplifier"))

specs.append(specItem("ID_P", description = "Transistor drain current", value       = -5.689378e-05, units       = "A", specType    = "Amplifier"))

specs.append(specItem("W1_N", description = "Transistor width", value       = 8.928578e-06, units       = "m", specType    = "Amplifier"))

specs.append(specItem("L1_N", description = "Transistor length", value       = 1.800000e-07, units       = "m", specType    = "Amplifier"))

specs.append(specItem("ID1_N", description = "Transistor drain current", value       = 1.453628e-04, units       = "A", specType    = "Amplifier"))

specs.append(specItem("W1C_N", description = "Transistor width", value       = 2.125287e-07, units       = "m", specType    = "Amplifier"))

specs.append(specItem("L1C_N", description = "Transistor length", value       = 1.800000e-07, units       = "m", specType    = "Amplifier"))

specs.append(specItem("W2_N", description = "Transistor width", value       = 3.059731e-07, units       = "m", specType    = "Amplifier"))

specs.append(specItem("L2_N", description = "Transistor length", value       = 1.800000e-07, units       = "m", specType    = "Amplifier"))

specs.append(specItem("ID2_N", description = "Transistor drain current", value       = 1.795413e-04, units       = "A", specType    = "Amplifier"))

specs.append(specItem("W2_P", description = "Transistor width", value       = 9.894621e-07, units       = "m", specType    = "Amplifier"))

specs.append(specItem("L2_P", description = "Transistor length", value       = 1.800000e-07, units       = "m", specType    = "Amplifier"))

specs.append(specItem("ID2_P", description = "Transistor drain current", value       = -1.795413e-04, units       = "A", specType    = "Amplifier"))

specs.append(specItem("R_ph", description = "Phantom Zero Resistance", value       = 2.000000e+02, units       = "Ohm", specType    = "Amplifier"))

