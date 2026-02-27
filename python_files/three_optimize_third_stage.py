############################################################################
######## This script will optimize the three stage #########
############################################################################

from SLiCAP import *
import numpy as np

I_peak = None
Iq = None


def optimize_third_stage(cir):
    global I_peak, Iq
    gm_peak_n = float("nan")
    gm_peak_p = float("nan")
    gm_quiescent_n = float("nan")
    gm_quiescent_p = float("nan")
    ICn_p = float("nan")
    ICp_p = float("nan")

    ############################################################################
    ##### Determine the ratio of Wn and Wp that yields the same gm #####
    ############################################################################

    max_iter = 10
    tolerance = 0.01
    converged = False

    for i in range(max_iter):
        gm2 = float(cir.getParValue("g_m_X2"))  # PMOS
        gm3 = float(cir.getParValue("g_m_X3"))  # NMOS

        error = abs(gm2 - gm3) / max(abs(gm2), abs(gm3))
        if error < tolerance:
            converged = True
            break

        Wn = float(cir.getParValue("W_N"))
        Wp = float(cir.getParValue("W_P"))

        if gm3 < gm2:
            scale = (gm2 / gm3) ** 2
            scale = max(0.5, min(2.0, scale))
            Wn *= scale
        else:
            scale = (gm3 / gm2) ** 2
            scale = max(0.5, min(2.0, scale))
            Wp *= scale

        Wn = round(Wn * 1e6) * 1e-6
        Wp = round(Wp * 1e6) * 1e-6

        cir.defPar("W_N", Wn)
        cir.defPar("W_P", Wp)

    gm2 = float(cir.getParValue("g_m_X2"))
    gm3 = float(cir.getParValue("g_m_X3"))

    Wn_final = float(cir.getParValue("W_N"))
    Wp_final = float(cir.getParValue("W_P"))
    ratio = Wp_final / Wn_final

    if not converged:
        print("\nMaximum iterations reached - gm matching not achieved.")
    else:
        print("\n----- Obtained gm-matched ratio -----")
        print(f"Ratio Wp/Wn        = {ratio:.2f}")
        print(f"Wn                 = {Wn_final*1e6:.0f} um")
        print(f"Wp                 = {Wp_final*1e6:.0f} um")
        print(f"gmn                = {gm3*1e3:.2f} mS")
        print(f"gmp                = {gm2*1e3:.2f} mS")
        print(f"Iterations         = {i+1}")

    ############################################################################
    #### Output Stage Bias + Drive Capability Sizing ####
    ############################################################################

    gm_quiescent_target = 1e-3
    gm_peak_target = 10e-3
    drive_capability = 4.5e-3

    max_iter_outer = 20
    max_iter_inner = 15
    tol = 0.02

    Iq = 0.5e-3

    for outer in range(max_iter_outer):
        I_peak = Iq + drive_capability

        W = 20e-6
        for _inner in range(max_iter_inner):
            cir.defPar("W_N", W)
            cir.defPar("W_P", W * ratio)
            cir.defPar("ID_N", I_peak)
            cir.defPar("ID_P", -I_peak)

            gm_peak_p = float(cir.getParValue("g_m_X2"))
            error_peak = (gm_peak_p - gm_peak_target) / gm_peak_target
            if abs(error_peak) < tol:
                gm_peak_n = float(cir.getParValue("g_m_X3"))
                ICp_p = float(cir.getParValue("IC_X2"))
                ICn_p = float(cir.getParValue("IC_X3"))
                break

            W *= gm_peak_target / gm_peak_p

        cir.defPar("ID_N", Iq)
        cir.defPar("ID_P", -Iq)

        gm_quiescent_p = float(cir.getParValue("g_m_X2"))
        gm_quiescent_n = float(cir.getParValue("g_m_X3"))
        error_q = (gm_quiescent_p - gm_quiescent_target) / gm_quiescent_target

        if abs(error_q) < tol:
            break

        Iq *= (gm_quiescent_target / gm_quiescent_p) ** 2

    Wp_final = float(cir.getParValue("W_P"))
    Wn_final = float(cir.getParValue("W_N"))

    cir.defPar("ID_N", Iq)
    cir.defPar("ID_P", -Iq)

    ICp_q = float(cir.getParValue("IC_X2"))
    ICn_q = float(cir.getParValue("IC_X3"))
    I_peak = Iq + drive_capability

    print("\n----- Output Stage Bias Sizing -----")
    print(f"Iterations         = {outer+1}")
    print(f"Peak current       = {(I_peak)*1e3:.2f} mA")
    print(f"Iq                 = {Iq*1e3:.2f} mA")
    print(f"Wn                 = {Wn_final*1e6:.1f} um")
    print(f"Wp                 = {Wp_final*1e6:.1f} um")

    print("\n----- Output Stage Parameters Peak Current-----")
    print(f"gmn peak           = {gm_peak_n*1e3:.2f} mS")
    print(f"gmp peak           = {gm_peak_p*1e3:.2f} mS")
    print(f"Gain peak - N      = {(gm_peak_n + gm_quiescent_p)*100:.2f}")
    print(f"Gain peak - P      = {(gm_peak_p + gm_quiescent_n)*100:.2f}")
    print(f"ICn peak           = {ICn_p:.1f}")
    print(f"ICp peak           = {ICp_p:.1f}")

    print("\n----- Output Stage Parameters Quiescent Current-----")
    print(f"gmn quiescent      = {gm_quiescent_n*1e3:.2f} mS")
    print(f"gmp quiescent      = {gm_quiescent_p*1e3:.2f} mS")
    print(f"Gain quiescent     = {(gm_quiescent_p + gm_quiescent_n)*100:.2f}")
    print(f"ICn quiescent      = {ICn_q:.2f}")
    print(f"ICp quiescent      = {ICp_q:.2f}")

    return {
        "ratio_wp_wn": ratio,
        "Iq": Iq,
        "I_peak": I_peak,
        "Wn": Wn_final,
        "Wp": Wp_final,
    }
