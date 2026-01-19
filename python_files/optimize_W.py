from SLiCAP import *
import numpy as np
from .circuit import *
from .specifications import *

# --------------------------------------------------
# Define frequency grid (SLiCAP-style)
# --------------------------------------------------

# f_min = float(input("Enter minimum frequency [Hz]: "))
# f_max = float(input("Enter maximum frequency [Hz]: "))
# n_pts = int(input("Enter number of frequency points: "))

f_min = float(1e3)
f_max = float(1e9)
n_pts = int(1e3)

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
# Given in: V^2 / (milli)^2 / Hz
# Converted internally to: V^2 / Hz
# --------------------------------------------------

def noise_spec(f_hz):
    f_hz = np.asarray(f_hz)
    f_hz = np.where(f_hz == 0, np.nan, f_hz)

    spec_milli = 1e-15 * (1 + 1e12 / f_hz**2)   # V^2/(milli)^2/Hz
    spec_hz    = spec_milli * 1               # convert to V^2/Hz

    return spec_hz


# --------------------------------------------------
# Simulation wrapper
# --------------------------------------------------

def run_simulation(w):
    """
    Run simulation for a given w.
    Returns:
        noise_sim : noise spectrum [V^2/Hz]
    """
    # cir.delPar("W_X1")
    # cir.defPar("W_X1", w)

    # for spec in specs:
    #     if spec.symbol == "W1_N":
    #         spec.value = w
    #         print(spec.symbol)
    #         print(spec.value)
    #         break
    specs[24].value = w

    print(specs[24].value)

    specs2circuit(specs, cir)

    noise_sim = doNoise(cir, source="V1", detector="V_vo", numeric=True, pardefs='circuit')

    return noise_sim


# --------------------------------------------------
# User input (parameter sweep)
# --------------------------------------------------

w_min  = float(input("Enter minimum w: "))
w_max  = float(input("Enter maximum w: "))
w_step = 5e-6


# --------------------------------------------------
# Search loop
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
# Result
# --------------------------------------------------
inoise_mag  = plotSweep("inoise", "input noise spectral density", [noise_expr], 1e3, 1e9, 200, funcType='inoise')

if found:
    print(f"\nSUCCESS: minimum w meeting noise spec = {w_found}")
else:
    print("\nFAILURE: no value of w in the given range meets the noise specification.")

