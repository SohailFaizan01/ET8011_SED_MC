################################################# Generate Plots for HTML pages #################################################

from SLiCAP import *
from sympy import cancel, Number, expand
from .circuit import cir
from .three_optimize_third_stage import I_peak, Iq

# --- Gains ---
gain        = doLaplace(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='gain')
asymptotic  = doLaplace(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='asymptotic')
loopgain    = doLaplace(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='loopgain')
servo       = doLaplace(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='servo')
direct      = doLaplace(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='direct')

PoleZeroLG   = doPZ(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='loopgain')
PoleZeroS   = doPZ(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='servo')
PoleZeroG    = doPZ(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='gain')


step_dict_P_swing = {   "params":   "ID_P",
                        "method":   "lin",
                        "start":    str(-1*Iq),
                        "stop":     str(-1*I_peak),
                        "num":      10            
                    }

# step_dict_N_swing = {   "params":   "ID_N",
#                         "method":   "lin",
#                         "start":    "60e-6",
#                         "stop":     "4.56e-3",
#                         "num":      3            
#                     }
step_dict_N_swing = {}
step_dict_N_swing['params'] = "ID_N"
step_dict_N_swing['method'] = "lin"
step_dict_N_swing['start']  = 60e-6 
step_dict_N_swing['stop']   = 4.56e-3
step_dict_N_swing['num']    = 3

I_inter = (Iq + I_peak) / 2
# plotPZ("Stepped_PZ_plot_P_q", "Stepped PZ plot P_q", PoleZeroG, xscale="G", yscale="G", xmin=-3, xmax=1, ymin=-4, ymax=4)
cir.defPar("ID_P", -1*I_inter)
PoleZeroLG_2   = doPZ(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='loopgain')
PoleZeroG_2   = doPZ(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='gain')
# plotPZ("Stepped_PZ_plot_P_inter", "Stepped PZ plot P_inter", PoleZeroG_2, xscale="G", yscale="G", xmin=-3, xmax=1, ymin=-4, ymax=4)

cir.defPar("ID_P", -1*I_peak)
PoleZeroLG_3   = doPZ(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='loopgain')
PoleZeroG_3   = doPZ(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='gain')
plotPZ("Stepped_PZ_plot_P_peak", "Stepped PZ plot P_peak", [PoleZeroG,PoleZeroG_2,PoleZeroG_3], xscale="G", yscale="G", xmin=-3, xmax=1, ymin=-4, ymax=4)  



# pzStepped_P_swing_LG  = doPZ(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='loopgain', stepdict=step_dict_P_swing)
# pzStepped_N_swing_LG  = doPZ(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='loopgain', stepdict=step_dict_N_swing)
# pzStepped_P_swing_G   = doPZ(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='gain', stepdict=step_dict_P_swing)
# pzStepped_N_swing_G   = doPZ(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='gain', stepdict=step_dict_N_swing)




# pz_stepped_P_swing_LG = plotPZ("pzStepped", "Stepped PZ plot", pzStepped_P_swing_LG, xscale="M", yscale="M", xmin=-1000, xmax=200, ymin=-2e3, ymax=2e3)
# pz_stepped_N_swing_LG = plotPZ("pzStepped", "Stepped PZ plot", pzStepped_N_swing_LG, xscale="M", yscale="M", xmin=-1000, xmax=200, ymin=-2e3, ymax=2e3)

# pz_stepped_P_swing_G = plotPZ("pzStepped", "Stepped PZ plot", pzStepped_P_swing_G, xscale="M", yscale="M", xmin=-1000, xmax=200, ymin=-2e3, ymax=2e3)
# pz_stepped_N_swing_G = plotPZ("pzStepped", "Stepped PZ plot", pzStepped_N_swing_G, xscale="M", yscale="M", xmin=-1000, xmax=200, ymin=-2e3, ymax=2e3)

# plotPZ("Stepped_PZ_plot_P_swing_LG", "Stepped PZ plot P_swing", pzStepped_P_swing_LG, xscale="M", yscale="M", xmin=-1000, xmax=200, ymin=-2e3, ymax=2e3)
# plotPZ("Stepped_PZ_plot_N_swing_LG", "Stepped PZ plot N_swing", pzStepped_N_swing_LG, xscale="M", yscale="M", xmin=-1000, xmax=200, ymin=-2e3, ymax=2e3)

# plotPZ("Stepped_PZ_plot_P_swing_G", "Stepped PZ plot P_swing G", pzStepped_P_swing_G, xscale="M", yscale="M", xmin=-1000, xmax=200, ymin=-2e3, ymax=2e3)
# plotPZ("Stepped_PZ_plot_N_swing_G", "Stepped PZ plot N_swing G", pzStepped_N_swing_G, xscale="M", yscale="M", xmin=-1000, xmax=200, ymin=-2e3, ymax=2e3)



# --- Plots Data Generation ---
noise_expr = doNoise(cir, source="V1", detector="V_vo", numeric=True, pardefs='circuit')
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
fb_model_mag = [gain, asymptotic, loopgain, servo, direct]
fb_model_ph = [gain, asymptotic, loopgain, servo, direct]
plotSweep("fb_mag", "Magnitude plots feedback model parameters", fb_model_mag, 1e3, 1e10, 200, yLim=[-75, 75], funcType='dBmag')
plotSweep("ph_mag", "Phase plots feedback model parameters", fb_model_ph, 1e3, 1e10, 200, yLim=[-190, 190], funcType='phase')
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
