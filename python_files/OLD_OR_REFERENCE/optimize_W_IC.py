################################################# Optimization code for finding W and I #################################################

from SLiCAP import *
import numpy as np
import sympy as sp
from ..circuit import cir
from ..specifications import specs


# --------------------------------------------------
# User input (parameter sweep)
# --------------------------------------------------
# f_bw_req = float(input("Enter required -3 dB bandwidth [Hz]: "))
f_bw_req = 100e6

# ID_min   = float(input("Enter minimum drain current [A]: "))
ID_min = 300e-6

# ID_max   = float(input("Enter maximum drain current [A]: "))
ID_max = 300e-6

# ID_step  = float(input("Enter current step [A]: "))
ID_step = 1e-6

# IC_tol   = float(input("Enter allowed IC deviation (e.g. 0.2 for ±20%): "))
IC_tol = 0.1

# w_min  = float(input("Enter minimum w: "))
w_min = 5e-6

# w_max  = float(input("Enter maximum w: "))
w_max = 10e-6

# w_step = float(input("Enter w step size: "))
w_step = 1e-6


# --------------------------------------------------
# Define frequency grid
# --------------------------------------------------

# f_min = float(input("Enter minimum frequency [Hz]: "))
# f_max = float(input("Enter maximum frequency [Hz]: "))
# n_pts = int(input("Enter number of frequency points: "))

f_min = float(1e3)
f_max = float(1e9)
n_pts = int(600)

# keep frequency as SYMBOL
ini.frequency = sp.Symbol('f')

# numeric sweep grid
ini.step = {
    ini.frequency: np.logspace(np.log10(f_min), np.log10(f_max), n_pts)
}

# local frequency vector for comparison
f = ini.step[ini.frequency]

# --------------------------------------------------
# Noise specification
# --------------------------------------------------

def noise_spec(f_hz):
    f_hz = np.asarray(f_hz)
    f_hz = np.where(f_hz == 0, np.nan, f_hz)

    spec_hz = 1e-15 * (1 + 1e12 / f_hz**2)   # V^2/Hz

    return spec_hz

# --------------------------------------------------
# Simulation wrapper
# --------------------------------------------------

def run_simulation(w):
    """
    Run simulation for a given w. Returns noise_sim : noise spectrum [V^2/Hz]
    """

    specs[24].value = w
    specs2circuit(specs, cir)

    noise_sim = doNoise(cir, source="V1", detector="V_vo", numeric=True, pardefs='circuit')

    return noise_sim

# --------------------------------------------------
# -3 dB bandwidth computation
# --------------------------------------------------

def compute_3db_bandwidth(tf_expr, f_vec):
    """
    Computes the -3 dB bandwidth of a Laplace TF. Assumes tf_expr is a function of s.
    """

    s = sp.Symbol('s')

    # Convert Laplace TF → frequency response
    tf_jw = tf_expr.subs(s, sp.I * 2 * sp.pi * ini.frequency)

    # Numeric function of frequency
    tf_fun = sp.lambdify(ini.frequency, tf_jw, modules="numpy")

    H = tf_fun(f_vec)
    mag = np.abs(H)

    mag0 = mag[0]            # low-frequency gain
    target = mag0 / np.sqrt(2)

    idx = np.where(mag <= target)[0]

    if len(idx) == 0:
        return None

    return f_vec[idx[0]]


def find_current_for_bandwidth(f_bw_req, f_vec):
    """
    Sweeps drain current until required -3 dB bandwidth is met. Returns (ID_found, bw_found, IC_found)
    """

    ID_values = np.arange(ID_min, ID_max + ID_step, ID_step)

    for ID in ID_values:
        specs[26].value = ID
        specs2circuit(specs, cir)

        tf = doLaplace(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='gain').laplace

        bw = compute_3db_bandwidth(tf, f_vec)

        if bw is not None and bw >= f_bw_req:
            IC = cir.getParValue("IC_X1")
            return ID, bw, IC

    return None, None, None

# --------------------------------------------------
# Find current for required bandwidth
# --------------------------------------------------

ID_0, bw_0, IC_0 = find_current_for_bandwidth(f_bw_req, f)

if ID_0 is None:
    raise RuntimeError("Cannot meet bandwidth requirement within current range.")

print("\nInitial bandwidth sizing:")
print(f"  ID  = {ID_0:.3e} A")
print(f"  BW  = {bw_0:.3e} Hz")
print(f"  IC  = {IC_0:.3f}")

# --------------------------------------------------
# W Search loop
# --------------------------------------------------

found = False
w_found = None

w_values = np.arange(w_min, w_max + w_step, w_step)

for w in w_values:
    noise_expr = run_simulation(w)

    # evaluate symbolic noise on frequency grid
    noise_eval = np.array(
        [float(noise_expr.inoise.subs(ini.frequency, fi)) for fi in f]
    )

    # remove DC
    mask = f > 0
    f_eval = f[mask]
    noise_eval = noise_eval[mask]

    noise_limit = noise_spec(f_eval)

    # print(noise_eval)
    # print(noise_limit)

    if np.all(noise_eval <= noise_limit):
        w_found = w
        found = True 
        break

# --------------------------------------------------
# IC consistency check and correction
# --------------------------------------------------

IC_1 = cir.getParValue("IC_X1")
IC_dev = abs(IC_1 - IC_0) / IC_0

if IC_dev > IC_tol:
    print("\nIC deviation too large, re-adjusting current...")

    # Re-run bandwidth-based current sizing with updated W
    ID_final, bw_final, IC_final = find_current_for_bandwidth(f_bw_req, f)

    if ID_final is None:
        raise RuntimeError("Cannot re-achieve bandwidth after W optimization.")

else:
    ID_final = ID_0
    bw_final = bw_0
    IC_final = IC_1

# --------------------------------------------------
# Results
# --------------------------------------------------

print("\n========== FINAL DESIGN ==========")

print(f"Drain current     ID = {ID_final:.3e} A")
print(f"Transistor width  W  = {w_found}")
print(f"Inversion coeff   IC = {cir.getParValue('IC_X1'):.3f}")
print(f"-3 dB bandwidth   BW = {bw_final:.3e} Hz")

print("=================================")










############################################## Random Blocks of Code ##############################################

###### Inversion Coeficient
# Weak: 0.01-0.1
# Moderate: 0.1 - 10
# Strong: 10 - 100

##### Failed attempt to change the W specification
    # cir.delPar("W_X1")
    # cir.defPar("W_X1", w)

    # for spec in specs:
    #     if spec.symbol == "W1_N":
    #         spec.value = w
    #         print(spec.symbol)
    #         print(spec.value)
    #         break