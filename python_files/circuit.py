################################################## Circuit Data ##################################################

from SLiCAP import *
from .specifications import *
import numpy as np
from sympy import *
s = symbols("s")
# t = symbols("t", real=True, positive=True)
# w = symbols("w", real=True)

fileName = "Active_E_Field_Probe"
fileName = 'KiCad/' + fileName + '/' + fileName + '.kicad_sch'

cir = makeCircuit(fileName,imgWidth=1000)

specs2circuit(specs, cir)

# --- Gains ---
gain        = doLaplace(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='gain')
asymptotic  = doLaplace(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='asymptotic')
loopgain    = doLaplace(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='loopgain')
servo       = doLaplace(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='servo')
direct      = doLaplace(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='direct')

# --- Noise ---
noise       = doNoise(cir, source="V1", detector="V_Amp_out", numeric=True, pardefs='circuit')

# --- Output Impedance (AC analysis to compute v(out)/i(test)) ---
#Rout_result = doLaplace(cir, numeric=True, source='I1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='gain')

# --- Plots ---
fb_model    = [gain, asymptotic, loopgain, servo]
fbmodel_mag = plotSweep("fb_mag", "Magnitude plots feedback model parameters", fb_model, 1, 10e9, 200)
onoise_mag  = plotSweep("onoise", "Output noise spectral density", [noise], 0.01, 10e9, 200)
inoise_mag  = plotSweep("inoise", "input noise spectral density", [noise], 0.01, 10e9, 200) #fix input referred
#R_out_mag   = plotSweep("R_out", "Magnitude plot output impedance", [Rout_result], 10, 10e9, 200)

twoport = doMatrix(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1')

stepdict_Vin = {
    "method": 'lin',        # Linear stepping
    "params": 'V_in',       # Parameter to step (must exist in your circuit)
    "start": 0.01,          # Starting value
    "stop": 0.25,           # Ending value
    "num": 1000               # Number of steps
}

lin_gain = doLaplace(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='gain', stepdict=stepdict_Vin).laplace
ip_V = np.linspace(0.01, 0.25, 1000)
# test = lin_gain[0].subs(s,2*sp.pi*80e6)
# eqn2html("lin_gain_at_80MHz", lin_gain.laplace)

num_gain = [expr.subs(s, 2 * sp.pi * 80e6).evalf() for expr in lin_gain]
# diff_gain= [expr.subs(s, 2 * sp.pi * 80e6).evalf() for expr in lin_gain]
# dG_dVin= np.gradient(lin_gain.subs(s,2*sp.pi*80e6).Y, ip_V)
derivatives = []
for i in range(len(num_gain) - 1):
    # Get the y values (y2 and y1)
    y2 = num_gain[i + 1]
    y1 = num_gain[i]

    # Get the corresponding x values (x2 and x1)
    x2 = ip_V[i + 1]
    x1 = ip_V[i]
    
    # Calculate the slope and append it to the results list
    slope = (y2 - y1) / (x2 - x1)
    derivatives.append(slope)

# Convert the final list to a NumPy array for consistency
dG_dVin_manual = np.array(derivatives)



# fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
fig, (ax1) = plt.subplots(1, figsize=(10, 8), sharex=True)


ax1.plot(ip_V[0:(len(num_gain) - 1)], (dG_dVin_manual))
ax1.set_title('diff_gain_magn')
ax1.set_ylabel('V_in')
ax1.grid(True)

plt.tight_layout()

# 5. Export the plot to an SVG file
plt.savefig("html/img/diff_gain.svg")
img2html("diff_gain.svg", width=600)





# transient = doTimeSolve(cir, pardefs='circuit', numeric=True)
# eqn2html("transient_M", transient.M)
# eqn2html("transient_Iv", transient.Iv)
# eqn2html("transient_Dv", transient.Dv)
# eqn2html("transient_TimeSolve", transient.timeSolve)

# G_transient_laplace = ((sp.laplace_transform(transient.timeSolve[3], t, s, noconds=True))/((0.25*2*sp.pi*80e6)/(s*s + (2*sp.pi*80e6)**2)))
# eqn2html("G_transient_laplace", G_transient_laplace)
# G_transient_fourier = G_transient_laplace.subs(s, sp.I*w)
# eqn2html("G_transient_fourier", G_transient_fourier)



# # 1. Create numerical functions from your symbolic expression
# G_fourier_magnitude_func = sp.lambdify(w, sp.Abs(G_transient_fourier), 'numpy')
# G_fourier_phase_func = sp.lambdify(w, sp.arg(G_transient_fourier), 'numpy')


# # 2. Generate a frequency range for plotting (in rad/s)
# frequency_range_rads = np.linspace((2*np.pi*80e6)/2, 2*np.pi*80e6*3, 1000)
# frequency_range_mhz = frequency_range_rads / (2 * np.pi * 1e6)

# # 3. Evaluate the magnitude and phase over the frequency range
# magnitude_values = G_fourier_magnitude_func(frequency_range_rads)
# phase_values_deg = np.rad2deg(G_fourier_phase_func(frequency_range_rads))

# # 4. Create the plots
# fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

# # Plot Magnitude
# ax1.plot(frequency_range_mhz, magnitude_values)
# ax1.set_title('Magnitude of G_transient_fourier')
# ax1.set_ylabel('Magnitude')
# ax1.grid(True)

# # Plot Phase
# ax2.plot(frequency_range_mhz, phase_values_deg)
# ax2.set_title('Phase of G_transient_fourier')
# ax2.set_xlabel('Frequency (MHz)')
# ax2.set_ylabel('Phase (degrees)')
# ax2.grid(True)

# plt.tight_layout()

# # 5. Export the plot to an SVG file
# plt.savefig("html/img/fourier_plot.svg")
# img2html("fourier_plot.svg", width=600)

# transienttime = doTime(cir, pardefs='circuit', numeric=False)
# eqn2html("transient_M", transienttime.M)
# eqn2html("transient_Iv", transienttime.Iv)
# eqn2html("transient_Dv", transienttime.Dv)
# eqn2html("transient_TimeSolve", transienttime.time)
# eqn2html("transient_Laplace", transienttime.laplace)