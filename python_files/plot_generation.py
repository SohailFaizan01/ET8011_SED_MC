################################################# Generate Plots for HTML pages #################################################

from SLiCAP import *
from sympy import cancel, Number, expand


def _name(base, suffix):
    return f"{base}_{suffix}" if suffix else base


def _safe_restore_id_p(cir, id_p_original):
    if id_p_original is not None:
        cir.defPar("ID_P", id_p_original)


def _build_step_currents(iq, i_peak, num_points=5):
    if iq is None or i_peak is None:
        return []
    if num_points < 2:
        num_points = 2
    iq_f = float(iq)
    ip_f = float(i_peak)
    step = (ip_f - iq_f) / float(num_points - 1)
    return [iq_f + idx * step for idx in range(num_points)]


def _customize_markers_per_step(fig, num_steps):
    if not fig.axes or not fig.axes[0]:
        return fig
    pz_axis = fig.axes[0][0]
    traces = getattr(pz_axis, "traces", [])
    if not traces:
        return fig

    for trace_obj in traces:
        label = str(getattr(trace_obj, "label", "")).strip()
        if not label:
            continue
        parts = label.split()
        if not parts:
            continue
        kind = parts[0].lower()
        run_idx = None
        if "run" in label:
            tail = label.split("run", 1)[1]
            number_chars = "".join(ch for ch in tail if ch.isdigit())
            if number_chars:
                run_idx = max(0, int(number_chars) - 1)
        if run_idx is None:
            continue

        is_endpoint = run_idx == 0 or run_idx == (num_steps - 1)
        if kind == "poles":
            trace_obj.marker = 'x' if is_endpoint else '.'
        elif kind == "zeros":
            trace_obj.marker = 'o' if is_endpoint else '.'

    fig.plot()
    return fig


def _generate_stepped_pz_plot(cir, transfer, suffix, currents, base_name):
    if not currents:
        return None
    pz_results = []
    for idx, i_val in enumerate(currents, start=1):
        cir.defPar("ID_P", -abs(float(i_val)))
        pz_result = doPZ(
            cir,
            numeric=True,
            source='V1',
            detector='V_Amp_out',
            pardefs='circuit',
            lgref='Gm_M1_X1',
            transfer=transfer,
        )
        pz_result.label = f"run {idx}"
        pz_results.append(pz_result)

    image_name = _name(base_name, suffix)
    fig = plotPZ(
        image_name,
        f"Stepped PZ plot {transfer}",
        pz_results,
        xscale="G",
        yscale="G",
        xmin=-3,
        xmax=1,
        ymin=-4,
        ymax=4,
    )
    _customize_markers_per_step(fig, len(currents))
    return image_name


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

    stepped_pz_gain_image = None
    stepped_pz_loopgain_image = None
    id_p_original = None
    try:
        id_p_original = float(cir.getParValue("ID_P"))
    except Exception:
        id_p_original = None

    if iq is not None and i_peak is not None:
        currents = _build_step_currents(iq, i_peak, num_points=5)
        stepped_pz_gain_image = _generate_stepped_pz_plot(
            cir,
            transfer='gain',
            suffix=suffix,
            currents=currents,
            base_name="Stepped_PZ_plot_P_peak",
        )
        stepped_pz_loopgain_image = _generate_stepped_pz_plot(
            cir,
            transfer='loopgain',
            suffix=suffix,
            currents=currents,
            base_name="Stepped_PZ_plot_LG_peak",
        )

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
        "stepped_pz_image": f"{stepped_pz_gain_image}.svg" if stepped_pz_gain_image else None,
        "stepped_pz_gain_image": f"{stepped_pz_gain_image}.svg" if stepped_pz_gain_image else None,
        "stepped_pz_loopgain_image": f"{stepped_pz_loopgain_image}.svg" if stepped_pz_loopgain_image else None,
    }
