################################################# Circuit Performance HTML Page #################################################
from SLiCAP import *
import numpy as np
import sympy as sp
from .plot_generation import *

htmlPage("Circuit Performance", index=False, label='Circuit_Performance')

##### Circuit Image
head2html("Circuit")
img2html("Active_E_Field_Probe.svg",  width=1000)

##### Gain functions and plots
head2html("Graphs")
head3html("Magnitude Plot")
img2html("fb_mag.svg",  width=800)

eqn2html("gain",        gain.laplace)
eqn2html("asymptotic",  asymptotic.laplace)
eqn2html("loopgain",    loopgain.laplace)
eqn2html("servo",       servo.laplace)
eqn2html("direct",      direct.laplace)

##### Pole Zero Plot
pz2html(PoleZero, label='PoleZero Loopgain', labelText='PoleZero Loopgain')

##### Input referred noise
head3html("Noise Spectrum")
img2html("noise_function_plot_HZ.svg", width=750)
img2html("inoise.svg",  width=700)
eqn2html("S_IRnoise",   noise_expr.inoise)










############################################## Random Blocks of Code ##############################################

##### Print Output Impedance Stuff
# Output Impedance
#img2html("R_out.svg",   width=600)
#eqn2html("R_out",       Rout_result.laplace, units="Ohm")

##### Output referred noise
# img2html("onoise.svg",  width=600)
# eqn2html("S_ORnoise",   noise_expr.onoise)

##### Print MNA Matrix Stuff
# eqn2html("MNA_Matrix",   twoport.M)
# eqn2html("MNA_Iv",   twoport.Iv)
# eqn2html("MNA_Dv",   twoport.Dv)
# eqn2html("MNA_something", twoport.M.inv())