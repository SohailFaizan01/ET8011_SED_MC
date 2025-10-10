################################################## Circuit Data ##################################################

from SLiCAP import *
from .specifications import *

fileName = "Active_E_Field_Probe"
fileName = 'KiCad/' + fileName + '/' + fileName + '.kicad_sch'

cir = makeCircuit(fileName,imgWidth=1000)

specs2circuit(specs, cir)

# print("Available loop gain references:")
# print(cir.controlled)


V_gain = doLaplace(cir, numeric=True, pardefs='circuit').laplace


# Plot gain
gain        = doLaplace(cir, numeric=True, pardefs='circuit')
asymptotic  = doLaplace(cir, numeric=True, transfer='asymptotic', pardefs='circuit')
loopgain    = doLaplace(cir, numeric=True, transfer='loopgain', pardefs='circuit')
servo       = doLaplace(cir, numeric=True, transfer="servo", pardefs='circuit')
direct      = doLaplace(cir, numeric=True, transfer="direct", pardefs='circuit')

eqn2html("gain", gain.laplace)
eqn2html("asymptotic", asymptotic.laplace)
eqn2html("loopgain", loopgain.laplace)
eqn2html("servo", servo.laplace)
eqn2html("direct", direct.laplace)

fb_model    = [gain, asymptotic, loopgain, servo, direct]
fbmodel_mag = plotSweep("fb_mag", "Magnitude plots feedback model parameters", fb_model, 10, 10e9, 200)
img2html("fb_mag.svg", width=600)


noise = doNoise(cir, source="V1", detector="V_out")

onoise = noise.onoise
NT = noise.onoiseTerms

# transient = doTimeSolve(cir, pardefs='circuit', numeric=False)
# eqn2html("transient_M", transient.M)
# eqn2html("transient_Iv", transient.Iv)
# eqn2html("transient_Dv", transient.Dv)
# eqn2html("transient_TimeSolve", transient.timeSolve)

# transienttime = doTime(cir, pardefs='circuit', numeric=False)
# eqn2html("transient_M", transienttime.M)
# eqn2html("transient_Iv", transienttime.Iv)
# eqn2html("transient_Dv", transienttime.Dv)
# eqn2html("transient_TimeSolve", transienttime.time)
# eqn2html("transient_Laplace", transienttime.laplace)