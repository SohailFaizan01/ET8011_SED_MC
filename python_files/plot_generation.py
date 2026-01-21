################################################# Generate Plots for HTML pages #################################################

from SLiCAP import *
from sympy import cancel, Number, expand
from .circuit import cir
from .optimize_W_IC import noise_expr

# --- Gains ---
gain        = doLaplace(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='gain')
asymptotic  = doLaplace(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='asymptotic')
loopgain    = doLaplace(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='loopgain')
servo       = doLaplace(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='servo')
direct      = doLaplace(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='direct')

# --- Plots Data Generation ---
noise_expr.inoise = cancel(noise_expr.inoise)

# --- Scale noise expression to avoid numerical overflow ---
try:
    num, den = noise_expr.inoise.as_numer_denom()
    # Find all number literals in both numerator and denominator
    atoms = num.atoms(Number).union(den.atoms(Number))
    if atoms:
        # Get absolute values of all numeric coefficients
        coeffs = [abs(c.evalf()) for c in atoms]
        if coeffs:
            max_coeff = max(coeffs)
            # Heuristic to decide if scaling is needed
            if max_coeff > 1e50:
                # Scale numerator and denominator
                num_scaled = expand(num / max_coeff)
                den_scaled = expand(den / max_coeff)
                noise_expr.inoise = num_scaled / den_scaled
except Exception:
    # If scaling fails, proceed with the unscaled expression.
    pass
# --- End of scaling ---
fb_model = [gain, asymptotic, loopgain, servo, direct]
plotSweep("fb_mag", "Magnitude plots feedback model parameters", fb_model, 1e3, 1e10, 200, yLim=[-75, 75], funcType='dBmag')
plotSweep("inoise", "input noise spectral density", [noise_expr], 1e3, 1e9, 200, funcType='inoise')










############################################## Random Blocks of Code ##############################################

###### Output noise plot
# plotSweep("onoise", "Output noise spectral density", [noise_expr], 1e3, 1e9, 200)

###### Plot of the Output Impedance (AC analysis to compute v(out)/i(test))
# Rout_result = doLaplace(cir, numeric=True, source='I1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='gain')
# R_out_mag            = plotSweep("R_out", "Magnitude plot output impedance", [Rout_result], 10, 10e9, 200)

##### Two Port matrices
# twoport = doMatrix(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1')

##### List individual noise terms
# for k, v in noise.inoiseTerms.items():
#     print(f"{k}: {N(v, 3)}")
