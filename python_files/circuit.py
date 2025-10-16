################################################## Circuit Data ##################################################

from SLiCAP import *
from .specifications import *

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
    "num": 10               # Number of steps
}

linearity = doLaplace(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='gain', stepdict=stepdict_Vin)
eqn2html("Linearity", linearity.laplace)

# transient = doTimeSolve(cir, pardefs='circuit', numeric=False)
# eqn2html("transient_M", transient.M)
# eqn2html("transient_Iv", transient.Iv)
# eqn2html("transient_Dv", transient.Dv)
# eqn2html("transient_TimeSolve", transient.timeSolve)

# transienttime = doTime(cir, pardefs='circuit', numeric=False)
# eqn2html("transient_M", transienttime.M)
# eqn2html("transient_M", transienttime.M)
# eqn2html("transient_Iv", transienttime.Iv)
# eqn2html("transient_Dv", transienttime.Dv)
# eqn2html("transient_TimeSolve", transienttime.time)
# eqn2html("transient_Laplace", transienttime.laplace)

