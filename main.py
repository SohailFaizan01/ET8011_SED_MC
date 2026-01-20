from SLiCAP import *

# Project setup
prj = initProject("Active_E_Field_Probe")

from python_files import specifications
from python_files import circuit
# from python_files import optimize_W_IC
from python_files import plot_generation
from python_files import html_specifications
from python_files import html_twoport
from python_files import html_design_choices


############################################## Random Blocks of Code ##############################################

##########      Plot Generation      ###########
# # Define the noise spectrum function
# def S_En(f):
#     return 1e-15 * (1 + 1e12 / f**2)

# # Frequency range (log scale)
# f = np.logspace(3, 9, 1000)  # 1 kHz to 1 GHz

# # Compute spectrum
# S = S_En(f)

# # Plot
# plt.figure(figsize=(7,5))
# plt.loglog(f, S, label=r"$S_{En}(f)$")
# plt.xlabel("Frequency $f$ [Hz]")
# plt.ylabel(r"$S_{En}(f)$ $\left[\frac{V^2}{Hz}\right]$")
# plt.title("Noise Spectrum")
# plt.grid(True, which="both", ls="--")
# plt.legend()
# plt.show()

# ##########      Loop Gain References      ###########
# print("Available loop gain references:")
# print(cir.controlled)