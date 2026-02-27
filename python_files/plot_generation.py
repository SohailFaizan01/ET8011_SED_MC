################################################# Generate Plots for HTML pages #################################################

from SLiCAP import *
from sympy import cancel, Number, expand


def _name(base, suffix):
    return f"{base}_{suffix}" if suffix else base


def _safe_restore_id_p(cir, id_p_original):
    if id_p_original is not None:
        cir.defPar("ID_P", id_p_original)


def generate_performance_plots(cir, suffix="", iq=None, i_peak=None):
    # --- Gains ---
    gain = doLaplace(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='gain')
    asymptotic = doLaplace(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='asymptotic')
    loopgain = doLaplace(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='loopgain')
    servo = doLaplace(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='servo')
    direct = doLaplace(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='direct')

    pole_zero_lg = doPZ(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='loopgain')
    pole_zero_s = doPZ(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='servo')
    pole_zero_g = doPZ(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='gain')

    stepped_pz_image = None
    id_p_original = None
    try:
        id_p_original = float(cir.getParValue("ID_P"))
    except Exception:
        id_p_original = None

    if iq is not None and i_peak is not None:
        i_inter = (iq + i_peak) / 2.0
        cir.defPar("ID_P", -1 * i_inter)
        pole_zero_g_2 = doPZ(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='gain')
        cir.defPar("ID_P", -1 * i_peak)
        pole_zero_g_3 = doPZ(cir, numeric=True, source='V1', detector='V_Amp_out', pardefs='circuit', lgref='Gm_M1_X1', transfer='gain')
        stepped_pz_image = _name("Stepped_PZ_plot_P_peak", suffix)
        plotPZ(stepped_pz_image, "Stepped PZ plot P_peak", [pole_zero_g, pole_zero_g_2, pole_zero_g_3], xscale="G", yscale="G", xmin=-3, xmax=1, ymin=-4, ymax=4)

    _safe_restore_id_p(cir, id_p_original)

    # --- Noise ---
    noise_expr = doNoise(cir, source="V1", detector="V_vo", numeric=True, pardefs='circuit')
    noise_expr.inoise = cancel(noise_expr.inoise)

    try:
        num, den = noise_expr.inoise.as_numer_denom()
        atoms = num.atoms(Number).union(den.atoms(Number))
        if atoms:
            coeffs = [abs(c.evalf()) for c in atoms]
            if coeffs:
                max_coeff = max(coeffs)
                if max_coeff > 1e50:
                    num_scaled = expand(num / max_coeff)
                    den_scaled = expand(den / max_coeff)
                    noise_expr.inoise = num_scaled / den_scaled
    except Exception:
        pass

    fb_model_mag = [gain, asymptotic, loopgain, servo, direct]
    fb_model_ph = [gain, asymptotic, loopgain, servo, direct]

    fb_mag_image = _name("fb_mag", suffix)
    ph_mag_image = _name("ph_mag", suffix)
    inoise_image = _name("inoise", suffix)

    plotSweep(fb_mag_image, "Magnitude plots feedback model parameters", fb_model_mag, 1e3, 1e10, 200, yLim=[-75, 75], funcType='dBmag')
    plotSweep(ph_mag_image, "Phase plots feedback model parameters", fb_model_ph, 1e3, 1e10, 200, yLim=[-190, 190], funcType='phase')
    plotSweep(inoise_image, "input noise spectral density", [noise_expr], 1e3, 1e9, 200, funcType='inoise')

    return {
        "gain": gain,
        "asymptotic": asymptotic,
        "loopgain": loopgain,
        "servo": servo,
        "direct": direct,
        "pole_zero_lg": pole_zero_lg,
        "pole_zero_s": pole_zero_s,
        "pole_zero_g": pole_zero_g,
        "noise_expr": noise_expr,
        "fb_mag_image": f"{fb_mag_image}.svg",
        "ph_mag_image": f"{ph_mag_image}.svg",
        "inoise_image": f"{inoise_image}.svg",
        "stepped_pz_image": f"{stepped_pz_image}.svg" if stepped_pz_image else None,
    }
