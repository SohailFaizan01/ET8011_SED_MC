################################################# Specifications #################################################

from SLiCAP import *

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
                         value       = '(0.25*2*pi*80e6)/(s^2 + (2*pi*80e6)^2)',
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