#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Apr 19 13:02:51 2025

@author: anton
"""
import SLiCAP as sl
from SLiCAP.SLiCAPkicad import _kicadNetlist
import sympy as sp
import numpy as np

# Available optimization mathods
METHODS = ["min(RMSnoise)", "min(I_DS)", "min(AE)@I_DS", "max(AE)@I_DS", "I_DS@AE", "min(f_T)", "min(c_iss*g_m)"]

# Error messages   
ERRORS = {1:  "Found multiple nullors.", 
          2:  "No noise budget left for MOS input stage.",
          3:  "Could not determine drain current.", 
          4:  "Current above maximum value:", 
          5:  "c_min below its minimum. Value changed to 1.01!", 
          6:  "L below its minimum. Value changed to L_min!", 
          7:  "Unknown optimization method:", 
          8:  "Too many iterations on output noise result.", 
          9:  "Width below minimum value:", 
          10: "width above maximum value:", 
          11: "Too many iterations on inversion coefficient.", 
          12: "Inversion coefficient above critical.",
          13: "Specified current below minimum value:",
          14: "Found negative inversion coefficient: please increase W_spec!"}

def _printError(code, arg=""):
    print("\nERROR: " + ERRORS[code] + " " + arg + "\n")
    
class results():
    def __init__(self):
        self.method       = None # Selected optimization method
        self.model        = None # Will be copied from process.name
        self.channel      = None # MOS channel type "P or "N"
        self.IC           = None # Inversion coefficient
        self.nRMS         = None # Weighted RMS output noise
        self.L            = None # MOS channel length [m]
        self.W            = None # MOS channel width [m]
        self.IDS          = None # MOS channel current [A]
        self.VGS          = None # MOS gate-source voltage [V]
        self.gm           = None # MOS transconductance [S]
        self.ciss         = None # MOS input capacitance at shorted output [F]
        self.fT           = None # MOS cut-off frequency [Hz]
        self.gm_ID        = None # MOS transconductance efficiency [V^-1]
        self.gm_ciss      = None # g_m(c_iss) noise function
        self.ovar_ciss_fT = None # ovar(c_iss, f_T) noise function
        self.n_min        = None # Minumum noise (noise-free nullor)
        self.ovar         = None # Expression detector-referred variance
        self.costs        = None # Costs function
        self.detType      = None # Detector type
        self.detUnits      = None # Detector units
        self.errors       = []   # List with error codes found during the design process
    
class process():
    def __init__(self):
        self.name    = ""              # Subcircuit name of "noisy nullor" with MOS noise sources
        self.L       = sp.Symbol("L")  # Selected channel length
        self.IG      = sp.Symbol("IG") # DC gate current [A]
        self.W_min   = 0               # Minimum channel width [m]
        self.W_max   = 1               # Maximum channel width [m] (number of fingers * width per finger)
        self.W_spec  = sp.Symbol("W")  # Specified width for method 'I_DS@AE'[m]
        self.L_min   = 0               # Minimum channel length [m]
        self.channel = None            # Channel type "P" or "N" must correspond with subcircuit name
        self.CGBO    = 'CGBO'          # Model name of gate-bulk overlap capacitance per unit of length
        
class specObject():
    def __init__(self):    
        self.noiseRMS = None # RMS output noise budget (source, feedback network, input stage transistor)
        self.f_min    = None # Lower limit of frequency range of interest [Hz]
        self.f_max    = None # Upper limit of frequency range of interest [Hz]
        self.ID_max   = None # Maximum channel current [A]
        self.ID_spec  = None # Specified current budget for methods W_max@I_DS [A]
        
def _update_results(cir, rmsNoise, n_min, ovar , errors):
    result        = results()
    result.IC     = cir.getParValue("IC_X1", numeric=True)
    result.L      = cir.getParValue("L")
    result.W      = cir.getParValue("W")
    result.IDS    = sp.Abs(cir.getParValue("ID"))
    result.VGS    = sp.Abs(cir.getParValue("VGS_X1", numeric=True))
    result.gm     = cir.getParValue("g_m_X1", numeric=True)
    result.ciss   = cir.getParValue("c_iss_X1", numeric=True)
    result.fT     = cir.getParValue("f_T_X1", numeric=True)
    # result.VGS    = cir_2.getParValue("V_GS_X1", numeric=True)  # Needs library update
    result.nRMS   = rmsNoise
    if n_min != None:
        result.n_min  = n_min
    result.errors = errors
    result.gm_ID  = sp.Abs(result.gm/result.IDS)
    result.ovar   = ovar
    return result

def print_results(results):
    for key in results.keys():
        result = results[key]
        print("\n--------------------------")
        print(result.method, result.channel, "- channel\n--------------------------")
        if result.method != "new":
            try:
                print("%s_no     [u%s]  :"%(result.detType, result.detUnits), sp.N(result.nRMS*1e6, 3))
                try:
                    print("%s_no_min [u%s]  :"%(result.detType, result.detUnits), sp.N(result.n_min*1e6, 3))
                except:
                    pass
                print("W        [um]  :", sp.N(result.W*1e6, 3))
                print("L        [um]  :", sp.N(result.L*1e6, 3))
                print("I_DS     [uA]  :", sp.N(result.IDS*1e6, 3))
                print("V_GS     [V]   :", sp.N(result.VGS, 3))
                print("g_m      [mS]  :", sp.N(result.gm*1e3, 3))
                print("f_T      [GHz] :", sp.N(result.fT/1e9, 3))
                print("g_m/I_DS [V^-1]:", sp.N(result.gm_ID, 3))
                print("IC       []    :", sp.N(result.IC, 3))
                print("c_iss    [pF]  :", sp.N(result.ciss*1e12, 3))
            except:
                print("No valid results.")
            if len(result.errors):
                print("\nErrors:")
                for error in result.errors:
                    print("-", ERRORS[error])
        else:
            print(sp.N(result.ovar,3))
        
def _updateCircuit(file_name, model):
    cir_name = file_name.split('.')[0]
    f = open(sl.ini.cir_path + file_name, "r")
    lines = f.readlines()
    f.close()
    found = False
    error = False
    new_lines = []
    for line in lines:
        if not found:
            if line[0] == "N":
                line = "X" + line[1:-2] + model + " W={W} L={L} ID={ID} IG={IG}\n"
                found = True
            new_lines.append(line)
        elif line[0] == "N":
            _printError(1)
            error = True
        else:
            new_lines.append(line)
    if found and not error:
        f = open(sl.ini.cir_path + cir_name + "_" + model + ".cir", "w")
        f.writelines(new_lines)
        f.close()
    cir = sl.makeCircuit(cir_name+ "_" + model + ".cir")
    return cir
                            
def _find_min(f, var):
    try:
        num, den = f.as_numer_denom()
        x_min    = sp.solve(den, var)[0]
    except IndexError:
        x_min = 0
        
    df_dc    = sp.diff(f, var)
    num, den = df_dc.as_numer_denom()

    x_opts   = sp.solve(num, var)
    xs       = []
    ys       = []
    for x in x_opts:
        real_part, imag_part = x.as_real_imag()
        if real_part > x_min and real_part > 1e6 * sp.Abs(imag_part):
            xs.append(real_part)
            ys.append(f.subs(var, real_part))
    try:
        xs = np.array(xs)
        ys = np.array(ys)
        x  = xs[np.argmin(ys)]
        y  = np.min(ys)
    except:
        y = None
        x = None
    return y, x 

def designMOSinputStage(kicad_sch, specs, models, methods, tol_ic=0.001, maxiter=20):
    """
    This function determines the geometry and operating conditions of a MOS
    input stage of a negatiove feedback amplifier. This finction combines
    symbolic and numeric analysis.
    
    The amplifier circuit (*kicad schematic*) **must comprise the following circuit elements**:

    1. Signal source with source impedance
    2. Feedback network(s) with nonzero noise temperature for the resistors
    3. Ideal controller (nullor)
    4. Optional: an output noise weighting transfer function H(s) or H(f)
    5. Detector specification
    
    All circuit elements should have numeric values assigned, either with the 
    element definition in the circuit or with parameter definitions.
    
    Specifications should be given as a specification object with the following attributes:
        
    >>> specs = specObject()
    
    >>> specs.noiseRMS = 50e-6  # Total weighted RMS output noise over the frequency range of interest
    >>> specs.f_min    = 1e2    # Lower limit of frequency range of interest
    >>> specs.f_max    = 1e6    # Upper limit of frequency range of interest
    >>> specs.ID_max   = 1      # Maximum current budget
    >>> specs.ID_spec  = 0.1e-3 # Current budget for 'min(AE)@I_DS' method
    
    Models should be defined as a list with process objects. The name of the model should
    be that of a sub circuit of a nullor with parameterized equivalent input
    noise sources according to the EKV model. 
    
    Examples for NMOS and PMOS in CMOS 18 are "MN18_noisyNullor" and "MP18_noisyNullor", respectively.
    These subcircuit definitions can be found in SLiCAP.lib.
    
    Process parameter names are not critical, model parameter names, however,
    should not be modified.
    
    A process object has the following attributes:

    >>> models = []

    >>> model         = process()

    >>> model.name    = "MN18_noisyNullor" # Name of the library model of the nullor with MOS EKV model input noise sources
    >>> model.channel = "N"                # N or P channel MOS
    >>> model.IG      = 0                  # DC gate current
    >>> model.L       = 0.18e-6            # Desired channel length
    >>> model.W_min   = 0.18e-6            # Minimum channel width
    >>> model.W_spec  = 100e-6             # Specified width for method 'I_DS@AE'[m]
    >>> model.W_max   = 10e-3              # Maximum total device width (Width per finger times number of fingers
    >>> model.L_min   = 0.18e-6            # Minimum channel width
    >>> model.CGBO    = 'CGBO_N18'         # Name of the gate-bulk overlap capacitance per unit of length

    >>> models.append(model)

    >>> model         = process()

    >>> model.name    = "MP18_noisyNullor"
    >>> model.channel = "P"
    >>> model.IG      = 0
    >>> model.L       = 0.18e-6
    >>> model.W_min   = 0.18e-6
    >>> model.W_max   = 10e-3              # Maximum total device width (Width per finger times number of fingers
    >>> model.W_spec  = 100e-6             # Specified width for method 'I_DS@AE'[m]
    >>> model.L_min   = 0.18e-6            # Minimum channel width
    >>> model.CGBO    = 'CGBO_P18'
    
    >>> models.append(model) 

    Built-in optimization methods are:
    1. min(RMSnoise)  : Minimum noise (cut-off frequency at or above critical inversion. 
                        No iteration on inversion coefficient).
    2. min(I_DS)      : Lowest drain current (does not always converge to the correct value)
    3. min(AE)@I_DS   : Smallest area at a specified current.
                        Yields no result if the calculated width is below minimum
    4. max(AE)@I_DS   : Largest area at a specified current.
                        Yields no result if the calculated width is above maximum
    5. I_DS@AE        : Drain current at a given W and L.  
                        Yields no result if the inversion level is above critical
    6. min(f_T)       : Lowest cut-off frequency, yields the lowest flicker noise contribution
    7. min(c_iss*g_m) : Lowest product of c_iss and g_m.   
                        Yields no result if the inversion level is above critical                       
    """

    RESULTS = {}
    for model in models:
        _kicadNetlist(kicad_sch, "MOSdesign")
        cir_name = kicad_sch.split("/")[-1].split(".")[0] + ".cir" 
        for method in methods:
            print("\nMETHOD:", method, "\n")
            cir = _updateCircuit(cir_name, model.name)
            detP, detN = cir.detector
            if detP != None:
                detType = detP[0]
            elif detN != None:
                detType = detN[0]
            if detType == "I":
                detUnits = "A"
            else:
                detUnits = "V"
            if method not in METHODS:
                _printError(7, arg=method)
                return RESULTS
            if method == "min(RMSnoise)":
                result = _min_RMS(cir, model, specs)
            elif method == "min(I_DS)":
                result = _min_I(cir, model, specs, tol_ic, maxiter)
            elif method == "min(f_T)":
                result  = _min_fT(cir, model, specs, tol_ic, maxiter)
            elif method == "min(AE)@I_DS":
                try:
                    result = _min_AE(cir, model, specs, tol_ic, maxiter)
                except:
                    result = results()
            elif method == "max(AE)@I_DS":
                try:
                    result = _max_AE(cir, model, specs, tol_ic, maxiter)
                except:
                    result = results()
            elif method == "I_DS@AE":
                try:
                    result = _I_AE(cir, model, specs, tol_ic, maxiter)
                except:
                    result = results()
            elif method == "min(c_iss*g_m)":
                try:
                    result = _min_CG(cir, model, specs, tol_ic, maxiter)
                except:
                    result = results()
                    
            result.method       = method
            result.model        = model.name
            result.channel      = model.channel
            result.detType      = detType
            result.detUnits     = detUnits
        
            RESULTS[model.name + "_" + method] = result
                
    return RESULTS

def _min_I(cir, model, specs, tol_ic, maxiter): 
    # Define symbolic variables
    g_m, c_iss, ID = sp.symbols("g_m, c_iss, ID")
    
    # Save symbolic definition of gm, IC and c_iss
    gm       = cir.getParValue("g_m_X1", substitute=False)
    ic       = cir.getParValue("IC_X1",  substitute=False)
    ci       = cir.getParValue("c_iss_X1", substitute = False)
    cb       = cir.getParValue(model.CGBO)
    
    # Define initial values for the loop
    IC       = 0.01
    rel_err  = 1
    i        = 0  
    IC_found = 0
    IC_crit = 0
    while rel_err > tol_ic and i < maxiter and IC_found <= IC_crit:
        print('.', end='')
        errors = []
        # Set initial parameter valies
        cir.defPar("IC_X1", IC)       # Apply current guess for the inversion coefficient
        cir.defPar("c_iss_X1", c_iss) # Restore symbolic definition of c_iss
        cir.defPar("g_m_X1", g_m)     # Restore symbolic definition of g_m
        cir.defPar("IG", 0)           # Ignore gate shot noise (leakage current)
        cir.defPar(model.CGBO, 0)     # Set gate bulk overlap capacitance to zero to enable (g_m, c_iss) monomials
        cir.defPar("L", model.L)      # Define channel length
        
        cir.delPar("W")               # Delete previously defined width
        cir.delPar("ID")              # Delete previously defined drain current
        
        # Express W in c_iss: W is proportional with c_iss if the gate-bulk overlap capacitance is set to zero (see above)
        ciss = cir.getParValue("c_gs_X1") + cir.getParValue("c_gb_X1")  + cir.getParValue("c_dg_X1") # This yields ciss=a*W
        Ws   = sp.solve(sp.Symbol("c_iss") - ciss, sp.Symbol("W"))[0] # This yields W=ciss/a, where a is a constant
        cir.defPar("W", Ws)
        
        # Express the output noise spectrum in c_iss, g_m, and f
        onoise   = sl.doNoise(cir, pardefs='Circuit', numeric=True).onoise
        
        # Wtite the output noise as a sum of products of numerically calculated integrals and 
        # coefficients in the form of (g_m^x * c_iss^y), where x and y are positive or negative integers.
        # The coefficient "1" (x=0 and y=0) is the noise with a noise-free controller.
        coeffs   = sl.integrated_monomial_coeffs(sp.expand(onoise), (g_m, c_iss), sl.ini.frequency, specs.f_min, specs.f_max)
        ovar = 0
        try:
            n_min   = sp.sqrt(coeffs[1])
            if  n_min >= specs.noiseRMS:
                _printError(2, arg=str(sp.N(sp.sqrt(coeffs[1]), 3)))
                errors.append(2)
        except:
            n_min = 0
     
        for key in coeffs.keys():
            ovar += key * coeffs[key]
        
        ovar = sp.simplify(ovar)
        
        # Now write the output noise in terms of ID and W
        gm_num    = sl.fullSubs(gm, cir.parDefs)
        ovar_ID_W = ovar.subs({c_iss: ciss, g_m: gm_num})
        
        # Obtain ID(W) that satisfies the noise budget
        ID_W      = sp.solve(ovar_ID_W - specs.noiseRMS**2, ID)[0]
        ID_found, W = _find_min(ID_W, sp.Symbol("W"))

        if W == None:
            W = model.W_min
            ID_found = ID_W.subs(sp.Symbol("W"), W)
        elif W < model.W_min:
            errors.append(9)
        elif W > model.W_max:
            errors.append(10)
        
        # Check the inversion coefficient and run the script again if the
        # Inversion coefficient deviates too much from its assumed value
        cir.defPars({"IC_X1": ic, "c_iss_X1": ci, "g_m_X1": gm, "W": W, 
                     "L": model.L, "IG": model.IG, "ID": ID_found, model.CGBO: cb})
        IC_found  = sp.N(cir.getParValue("IC_X1"))
    
        rel_err   = sp.Abs(1-IC/IC_found)
        IC        = IC_found
        i        += 1
        IC_crit = sp.N(cir.getParValue("IC_CRIT_X1"))
        if i > maxiter:
            errors.append(11)
            break 
    print()   
    # Check the RMS noise
    noiseResult  = sl.doNoise(cir, pardefs="circuit", numeric=True)
    rmsNoise     = sl.rmsNoise(noiseResult, "onoise", specs.f_min, specs.f_max)
    result       = _update_results(cir, rmsNoise, n_min, ovar , errors)
    if sp.N(cir.getParValue("IC_X1")) > sp.N(cir.getParValue("IC_CRIT_X1")):
        errors.append(12)
    return result    

def _min_CG(cir, model, specs, tol_ic, maxiter):  
    # Define symbolic variables
    g_m, c_iss, ID = sp.symbols("g_m, c_iss, ID")
    
    # Save symbolic definition of gm, IC and c_iss
    gm       = cir.getParValue("g_m_X1", substitute=False)
    ic       = cir.getParValue("IC_X1",  substitute=False)
    ci       = cir.getParValue("c_iss_X1", substitute = False)
    cb       = cir.getParValue(model.CGBO)
    
    # Define initial values for the loop
    IC       = 0.01
    rel_err  = 1
    i        = 0  
    IC_found = 0
    IC_crit  = 0
    while rel_err > tol_ic and i < maxiter and IC_found <= IC_crit:
        print('.', end = '')
        errors = []
        # Set initial parameter valies
        cir.defPar("IC_X1", IC)       # Apply current guess for the inversion coefficient
        cir.defPar("c_iss_X1", c_iss) # Restore symbolic definition of c_iss
        cir.defPar("g_m_X1", g_m)     # Restore symbolic definition of g_m
        cir.defPar("IG", 0)           # Ignore gate shot noise (leakage current)
        cir.defPar(model.CGBO, 0)     # Set gate bulk overlap capacitance to zero to enable (g_m, c_iss) monomials
        cir.defPar("L", model.L)      # Define channel length
        
        cir.delPar("W")               # Delete previously defined width
        cir.delPar("ID")              # Delete previously defined drain current
        
        # Express W in c_iss: W is proportional with c_iss if the gate-bulk overlap capacitance is set to zero (see above)
        ciss = cir.getParValue("c_gs_X1") + cir.getParValue("c_gb_X1")  + cir.getParValue("c_dg_X1") # This yields ciss=a*W
        Ws   = sp.solve(sp.Symbol("c_iss") - ciss, sp.Symbol("W"))[0] # This yields W=ciss/a, where a is a constant
        cir.defPar("W", Ws)
        
        # Express the output noise spectrum in c_iss, g_m, and f
        onoise   = sl.doNoise(cir, pardefs='Circuit', numeric=True).onoise
        # Wtite the output noise as a sum of products of numerically calculated integrals and 
        # coefficients in the form of (g_m^x * c_iss^y), where x and y are positive or negative integers.
        # The coefficient "1" (x=0 and y=0) is the noise with a noise-free controller.
        coeffs   = sl.integrated_monomial_coeffs(sp.expand(onoise), (g_m, c_iss), sl.ini.frequency, specs.f_min, specs.f_max)
        ovar = 0
        try:
            n_min   = sp.sqrt(coeffs[1])
            gm_ciss = None
            if  n_min >= specs.noiseRMS:
                _printError(2, arg=str(sp.N(sp.sqrt(coeffs[1]), 3)))
                errors.append(2)
        except:
            n_min = 0
     
        for key in coeffs.keys():
            ovar += key * coeffs[key]
        
        ovar = sp.simplify(ovar)
        
        # Obtain an expression for gm(c_iss) to satisfy the noise requirement
        gm_ciss             = sp.solve(ovar - specs.noiseRMS**2, g_m)[0] 
        costs               = c_iss * gm_ciss
        min_costs, ciss_opt = _find_min(costs, c_iss)
        if ciss_opt == None:
            ciss_opt = ciss.subs(sp.Symbol("W"), model.W_min)
            min_costs = costs.subs(c_iss, ciss_opt)
    
        gm_found            = min_costs/ciss_opt

        # Calculate the corresponding width and check if it satisfies the range
        W = Ws.subs(sp.Symbol("c_iss"), ciss_opt)
        
        if W < model.W_min:
            W = model.W_min
            errors.append(9)
        elif W > model.W_max:
            W = model.W_max
            errors.append(10)
            
        cir.defPar("W", W)
        cir.defPar("g_m_X1", gm)  # Restore definition for g_m_X1
        try:
            sols = sp.solve(cir.getParValue("g_m_X1") - gm_found, sp.Symbol("ID"))
            ID_found = sols[0]
        except IndexError:
            ID_found = 0
            _printError(3, arg="ID set to zero!")
            errors.append(3)
        if ID_found > specs.ID_max:
            _printError(4, arg="(ID=%s A) Will be set to maximum."%(str(sp.N(ID,3))))
            errors.append(4)
                
        # Check the inversion coefficient and run the script again if the
        # Inversion coefficient deviates too much from its assumed value
        cir.defPars({"IC_X1": ic, "c_iss_X1": ci, "g_m_X1": gm, "W": W, 
                     "L": model.L, "IG": model.IG, "ID": ID_found, model.CGBO: cb})
        IC_found     = sp.N(cir.getParValue("IC_X1"))
        
        if IC_found <= 0:
            errors.append(14)
            break
    
        rel_err      = sp.Abs(1-IC/IC_found)
        IC           = IC_found
        i           += 1
        if i > maxiter:
            errors.append(11)
            break
        IC_crit = sp.N(cir.getParValue("IC_CRIT_X1"))
    print()    
    # Check the RMS noise
    noiseResult  = sl.doNoise(cir, pardefs="circuit", numeric=True)
    rmsNoise     = sl.rmsNoise(noiseResult, "onoise", specs.f_min, specs.f_max)
    result       = _update_results(cir, rmsNoise, n_min, ovar , errors)
    if sp.N(cir.getParValue("IC_X1")) > sp.N(cir.getParValue("IC_CRIT_X1")):
        errors.append(12)
    return result    

def _min_AE(cir, model, specs, tol_ic, maxiter):
    return _lim_AE(cir, model, specs, tol_ic, maxiter, "lower")

def _max_AE(cir, model, specs, tol_ic, maxiter):
    return _lim_AE(cir, model, specs, tol_ic, maxiter, "upper")
    
def _lim_AE(cir, model, specs, tol_ic, maxiter, limit):  
    # Define symbolic variables
    g_m, c_iss, ID = sp.symbols("g_m, c_iss, ID")
    
    # Save symbolic definition of gm, IC and c_iss
    gm       = cir.getParValue("g_m_X1", substitute=False)
    ic       = cir.getParValue("IC_X1",  substitute=False)
    ci       = cir.getParValue("c_iss_X1", substitute = False)
    cb       = cir.getParValue(model.CGBO)
    
    # Define initial values for the loop
    IC       = 0.01
    rel_err  = 1
    i        = 0
    IC_found = 0
    IC_crit  = 0
    while rel_err > tol_ic and i < maxiter and IC_found <= IC_crit:
        print('.', end = '')
        errors = []
        # Set initial parameter valies
        cir.defPar("IC_X1", IC)       # Apply current guess for the inversion coefficient
        cir.defPar("c_iss_X1", c_iss) # Restore symbolic definition of c_iss
        cir.defPar("g_m_X1", g_m)     # Restore symbolic definition of g_m
        cir.defPar("IG", 0)           # Ignore gate shot noise (leakage current)
        cir.defPar(model.CGBO, 0)     # Set gate bulk overlap capacitance to zero to enable (g_m, c_iss) monomials
        cir.defPar("L", model.L)      # Define channel length
        
        cir.delPar("W")               # Delete previously defined width
        cir.delPar("ID")              # Delete previously defined drain current
        
        # Express W in c_iss: W is proportional with c_iss if the gate-bulk overlap capacitance is set to zero (see above)
        ciss = cir.getParValue("c_gs_X1") + cir.getParValue("c_gb_X1")  + cir.getParValue("c_dg_X1") # This yields ciss=a*W
        Ws   = sp.solve(sp.Symbol("c_iss") - ciss, sp.Symbol("W"))[0] # This yields W=ciss/a, where a is a constant
        cir.defPar("W", Ws)
        
        # Express the output noise spectrum in c_iss, g_m, and f
        onoise   = sl.doNoise(cir, pardefs='Circuit', numeric=True).onoise
        
        # Wtite the output noise as a sum of products of numerically calculated integrals and 
        # coefficients in the form of (g_m^x * c_iss^y), where x and y are positive or negative integers.
        # The coefficient "1" (x=0 and y=0) is the noise with a noise-free controller.
        coeffs   = sl.integrated_monomial_coeffs(sp.expand(onoise), (g_m, c_iss), sl.ini.frequency, specs.f_min, specs.f_max)
        ovar = 0
        try:
            n_min   = sp.sqrt(coeffs[1])
            if  n_min >= specs.noiseRMS:
                _printError(2, arg=str(sp.N(sp.sqrt(coeffs[1]), 3)))
                errors.append(2)
        except:
            n_min = 0
     
        for key in coeffs.keys():
            ovar += key * coeffs[key]
        
        ovar = sp.simplify(ovar)
        
        # Now write the output noise in terms of ID and W
        gm_num    = sl.fullSubs(gm, cir.parDefs)
        ovar_ID_W = ovar.subs({c_iss: ciss, g_m: gm_num})
        
        # Obtain ID(W) that satisfies the noise budget
        ID_W          = sp.solve(ovar_ID_W - specs.noiseRMS**2, ID)[0]
        ID_min, W_opt = _find_min(ID_W, sp.Symbol("W"))
        
        if model.channel == "P":
            ID_spec   = - specs.ID_spec
        else:
            ID_spec   = specs.ID_spec
            
        sols          = sp.solve(ID_W - ID_spec, sp.Symbol("W"))
   
        found = []
        for sol in sols:
            real_part, imag_part = sol.as_real_imag()

            if real_part > model.W_min and real_part < model.W_max:
                found.append(real_part)
        
        W_min = np.min(np.array(found))
        W_max = np.max(np.array(found))
        if limit == "lower":
            W        = W_min
        elif limit == "upper":
            W        = W_max
        
        ID_found     = ID_spec
        # Check the inversion coefficient and run the script again if the
        # Inversion coefficient deviates too much from its assumed value
        cir.defPars({"IC_X1": ic, "c_iss_X1": ci, "g_m_X1": gm, "W": W, 
                     "L": model.L, "IG": model.IG, "ID": ID_found, model.CGBO: cb})
        IC_found     = sp.N(cir.getParValue("IC_X1"))
    
        rel_err      = sp.Abs(1-IC/IC_found)
        IC           = IC_found
        i           += 1
        IC_crit = sp.N(cir.getParValue("IC_CRIT_X1"))
        if i >= maxiter:
            errors.append(11)
            break
    print()     
    if (limit == "lower" and W > W_opt) or (limit == "upper" and W < W_opt):
        noiseResult = None
    else:
        # Check the RMS noise
        noiseResult  = sl.doNoise(cir, pardefs="circuit", numeric=True)
        rmsNoise     = sl.rmsNoise(noiseResult, "onoise", specs.f_min, specs.f_max)
        result       = _update_results(cir, rmsNoise, n_min, ovar , errors)
        if sp.N(cir.getParValue("IC_X1")) > sp.N(cir.getParValue("IC_CRIT_X1")):
            errors.append(12)
    return result    

def _min_fT(cir, model, specs, tol_ic, maxiter):
    # Define symbolic variables
    g_m, c_iss, ID = sp.symbols("g_m, c_iss, ID")
    
    # Save symbolic definition of gm, IC and c_iss
    gm       = cir.getParValue("g_m_X1", substitute=False)
    ic       = cir.getParValue("IC_X1",  substitute=False)
    ci       = cir.getParValue("c_iss_X1", substitute = False)
    cb       = cir.getParValue(model.CGBO)
    
    # Define initial values for the loop
    IC       = 0.01
    rel_err  = 1
    i        = 0  
    IC_found = 0
    IC_crit  = 0
    while rel_err > tol_ic and i < maxiter and IC_found <= IC_crit:
        print('.', end = '')
        errors = []
        # Set initial parameter valies
        cir.defPar("IC_X1", IC)       # Apply current guess for the inversion coefficient
        cir.defPar("c_iss_X1", c_iss) # Restore symbolic definition of c_iss
        cir.defPar("g_m_X1", g_m)     # Restore symbolic definition of g_m
        cir.defPar("IG", 0)           # Ignore gate shot noise (leakage current)
        cir.defPar(model.CGBO, 0)     # Set gate bulk overlap capacitance to zero to enable (g_m, c_iss) monomials
        cir.defPar("L", model.L)      # Define channel length
        
        cir.delPar("W")               # Delete previously defined width
        cir.delPar("ID")              # Delete previously defined drain current
        
        # Express W in c_iss: W is proportional with c_iss if the gate-bulk overlap capacitance is set to zero (see above)
        ciss = cir.getParValue("c_gs_X1") + cir.getParValue("c_gb_X1")  + cir.getParValue("c_dg_X1") # This yields ciss=a*W
        Ws   = sp.solve(sp.Symbol("c_iss") - ciss, sp.Symbol("W"))[0] # This yields W=ciss/a, where a is a constant
        cir.defPar("W", Ws)
        
        # Express the output noise spectrum in c_iss, g_m, and f
        onoise   = sl.doNoise(cir, pardefs='Circuit', numeric=True).onoise
        
        # Wtite the output noise as a sum of products of numerically calculated integrals and 
        # coefficients in the form of (g_m^x * c_iss^y), where x and y are positive or negative integers.
        # The coefficient "1" (x=0 and y=0) is the noise with a noise-free controller.
        coeffs   = sl.integrated_monomial_coeffs(sp.expand(onoise), (g_m, c_iss), sl.ini.frequency, specs.f_min, specs.f_max)
        ovar = 0
        try:
            n_min   = sp.sqrt(coeffs[1])
            if  n_min >= specs.noiseRMS:
                _printError(2, arg=str(sp.N(sp.sqrt(coeffs[1]), 3)))
                errors.append(2)
        except:
            n_min = 0
     
        for key in coeffs.keys():
            ovar += key * coeffs[key]
        
        ovar = sp.simplify(ovar)
        ovar_ciss_fT     = sp.N(ovar.subs(sp.Symbol("g_m"), sp.sympify("f_T*2*pi*c_iss")))
        fT_ciss          = sp.solve(ovar_ciss_fT - specs.noiseRMS**2, sp.Symbol("f_T"))[0]
        
        fT_opt, ciss_opt = _find_min(fT_ciss, c_iss)
        gm_opt           = sp.N(fT_opt*2*sp.pi*ciss_opt)
        # Calculate the corresponding width and check if it satisfies the range
        W = Ws.subs(sp.Symbol("c_iss"), ciss_opt)
        
        if W < model.W_min:
            W = model.W_min
            errors.append(9)
        elif W > model.W_max:
            W = model.W_max
            errors.append(10)
            
        cir.defPar("W", W)
        cir.defPar("g_m_X1", gm)     # Restore definition for g_m_X1
        try:
            sols = sp.solve(cir.getParValue("g_m_X1") - gm_opt, sp.Symbol("ID"))
            #print("SOLS:", sols)
            ID_found = sols[0]
            #print(sp.N(cir.getParValue("g_m_X1"), 3), "=", sp.N(gm_opt,3))
        except IndexError:
            ID_found = 0
            _printError(3, arg="ID set to zero!")
            errors.append(3)
        if ID_found > specs.ID_max:
            _printError(4, arg="(ID=%s A) Will be set to maximum."%(str(sp.N(ID,3))))
            errors.append(4)
        
        # Define the parameters in the validation circuit
        cir.defPars({"W": W, "L": model.L, "IG": model.IG, "ID": ID})
        
        # Check the inversion coefficient and run the script again if the
        # Inversion coefficient deviates too much from its assumed value
        cir.defPars({"IC_X1": ic, "c_iss_X1": ci, "g_m_X1": gm, "W": W, 
                     "L": model.L, "IG": model.IG, "ID": ID_found, model.CGBO: cb})
        IC_found     = sp.N(cir.getParValue("IC_X1"))
    
        rel_err      = sp.Abs(1-IC/IC_found)
        IC           = IC_found
        i           += 1
        if i > maxiter:
            errors.append(11)
        IC_crit = sp.N(cir.getParValue("IC_CRIT_X1"))
    print()    
    # Check the RMS noise
    noiseResult  = sl.doNoise(cir, pardefs="circuit", numeric=True)
    rmsNoise     = sl.rmsNoise(noiseResult, "onoise", specs.f_min, specs.f_max)
    result       = _update_results(cir, rmsNoise, n_min, ovar , errors)
    if sp.N(cir.getParValue("IC_X1")) > sp.N(cir.getParValue("IC_CRIT_X1")):
        errors.append(12)
    return result 

def _min_RMS(cir, model, specs):
    # Initialization
    rmsNoise   = None
    errors     = []
    W          = model.W_min
    # Define symbolic variables
    g_m, c_iss, ID = sp.symbols("g_m, c_iss, ID")
    
    # Save symbolic definition of gm, IC and c_iss
    gm       = cir.getParValue("g_m_X1", substitute=False)
    ic       = cir.getParValue("IC_X1",  substitute=False)
    ci       = cir.getParValue("c_iss_X1", substitute = False)
    cb       = cir.getParValue(model.CGBO)
    
    # below critical inversion the noise drops with increasing fT
    # for a given fT the noise has an optimum ciss
    # 1. Start with the peak fT at IC=ICcrit and given L
    # 2. Calculate the optimum ciss for the peak fT
    # 3. Calculate the current at IC_crit and minimum width
    # 4. With given L and IC, calculate the required width
    # 5. Calculate the current from the current at the minimum width and the obtained width
    
    # Determine critical inversion level at minimum geometry
    cir.delPar("ID")
    cir.defPars({"W": model.W_min, "L": model.L})
    IC = cir.getParValue("IC_CRIT_X1")
    
    # Find IDS at this inversion level and for this geometry
    if sp.Symbol("IC_i_X1") in cir.parDefs.keys():
        IC_expr = cir.getParValue("IC_i_X1")
    else:
        IC_expr = cir.getParValue("IC_X1")
    if model.channel == "P":
        IC_expr =  -IC_expr   
        
    ID_IC = sp.solve(sl.assumePosParams(IC_expr) - sp.Symbol("IC"), sp.Symbol("ID", positive=True))[0]
    ID_ICcrit = sl.clearAssumptions(ID_IC).subs(sp.Symbol("IC"), IC)
    if model.channel == "P":
        ID_ICcrit = -ID_ICcrit
        
    # Get f_T at critical inversion
    cir.defPar("ID", ID_ICcrit) 
    f_Tmax = cir.getParValue("f_T_X1")

    cir.defPar("g_m_X1", "g_m")     # Redefine g_m_X1
    cir.defPar("c_iss_X1", "c_iss") # Redefine c_iss_X1
    cir.defPar("IC_X1", IC)         # Apply current guess for the inversion coefficient
    cir.defPar(model.CGBO, 0)       # Set gate bulk overlap capacitance to zero to enable (g_m, c_iss) monomials
    cir.delPar("W")                 # Keep width symbolic
    # Express W in c_iss: W is proportional with c_iss if the gate-bulk overlap capacitance is set to zero (see above)
    ciss = cir.getParValue("c_gs_X1") + cir.getParValue("c_gb_X1")  + cir.getParValue("c_dg_X1") # This yields ciss=a*W
    Ws   = sp.solve(sp.Symbol("c_iss") - ciss, sp.Symbol("W"))[0] # This yields W=ciss/a, where a is a constant
    cir.defPar("W", Ws)
    # Express the output noise spectrum in c_iss, g_m, and f
    onoise   = sl.doNoise(cir, pardefs='Circuit', numeric=True).onoise         
    # Wtite the output noise as a sum of products of numerically calculated integrals and 
    # coefficients in the form of (g_m^x * c_iss^y), where x and y are positive or negative integers.
    # The coefficient "1" (x=0 and y=0) is the noise with a noise-free controller.
    coeffs   = sl.integrated_monomial_coeffs(sp.expand(onoise), (g_m, c_iss), sl.ini.frequency, specs.f_min, specs.f_max)
    ovar = 0
    try:
        n_min   = sp.sqrt(coeffs[1])
        gm_ciss = None
        if  n_min >= specs.noiseRMS:
            _printError(2, arg=str(sp.N(sp.sqrt(coeffs[1]), 3)))
            errors.append(2)
    except:
        n_min = 0
    
    for key in coeffs.keys():
        ovar += key * coeffs[key]
    # The function g_m_c_iss gives the lowest possible value of g_m for a given value of c_iss 
    # at which the noise requirement is satisfied.
    gm_ciss  = sp.solve(ovar - specs.noiseRMS**2, g_m)[0]
    
    # Write the noise equation as a function of c_iss and f_T
    ovar_ciss_fT = sp.N(ovar.subs(sp.Symbol("g_m"), sp.sympify("f_T*2*pi*c_iss")))        
        
    # Take the derivative of this function (vs. c_iss) and solve c_iss for the lowest noise
    diff_ciss_fT = sp.diff(ovar_ciss_fT.subs(sp.Symbol("f_T"), f_Tmax), sp.Symbol("c_iss"))
    num, den = diff_ciss_fT.as_numer_denom()

    sol = sp.solve(sl.assumePosParams(num), sp.Symbol("c_iss", positive=True))[0]
    c_iss_opt = sl.clearAssumptions(sol).subs(sp.Symbol("f_T"), f_Tmax)
            
    # Calculate the width for this c_iss_opt
    W = Ws.subs({sp.Symbol("c_iss"): c_iss_opt, sp.Symbol("L"): model.L})
    if W < model.W_min:
        _printError(9, arg=str(sp.N(W,3)))
        W = model.W_min
                
    # Calculate ID required at this width    
    ID_found = ID_ICcrit*W/model.W_min
    
    # Set to maximum and correct the width if necessary
    if ID_found > specs.ID_max:
        errors.append(4)
        W  = W * specs.ID_max/ID_found
        ID_found = specs.ID_max
        if model.channel == "P":
            ID_found = -ID_found
            
    # Define the obtained parameters in the validation circuit
    cir.defPars({"IC_X1": ic, "c_iss_X1": ci, "g_m_X1": gm, "W": W, 
                 "L": model.L, "IG": model.IG, "ID": ID_found, model.CGBO: cb})
    
    # Evaluate the noise
    noiseResult = sl.doNoise(cir, pardefs="circuit", numeric=True)
    rmsNoise = sl.rmsNoise(noiseResult, "onoise", specs.f_min, specs.f_max)
    
    result = _update_results(cir, rmsNoise, n_min, ovar, errors)
    result.gm_ciss      = gm_ciss
    result.ovar_ciss_fT = ovar_ciss_fT
    return result  

def _I_AE(cir, model, specs, tol_ic, maxiter):
    # Define symbolic variables
    g_m, c_iss, ID = sp.symbols("g_m, c_iss, ID")
    
    # Save symbolic definition of gm, IC and c_iss
    gm       = cir.getParValue("g_m_X1", substitute=False)
    ic       = cir.getParValue("IC_X1",  substitute=False)
    ci       = cir.getParValue("c_iss_X1", substitute = False)
    cb       = cir.getParValue(model.CGBO)
    
    # Define initial values for the loop
    IC       = 0.01
    rel_err  = 1
    i        = 0  
    IC_found = 0
    IC_crit = 0
    while rel_err > tol_ic and i < maxiter and IC_found <= IC_crit:
        print('.', end='')
        errors = []
        # Set initial parameter valies
        cir.defPar("IC_X1", IC)       # Apply current guess for the inversion coefficient
        cir.defPar("c_iss_X1", c_iss) # Restore symbolic definition of c_iss
        cir.defPar("g_m_X1", g_m)     # Restore symbolic definition of g_m
        cir.defPar("IG", 0)           # Ignore gate shot noise (leakage current)
        cir.defPar(model.CGBO, 0)     # Set gate bulk overlap capacitance to zero to enable (g_m, c_iss) monomials
        cir.defPar("L", model.L)      # Define channel length
        
        cir.delPar("W")               # Delete previously defined width
        cir.delPar("ID")              # Delete previously defined drain current
        
        # Express W in c_iss: W is proportional with c_iss if the gate-bulk overlap capacitance is set to zero (see above)
        ciss = cir.getParValue("c_gs_X1") + cir.getParValue("c_gb_X1")  + cir.getParValue("c_dg_X1") # This yields ciss=a*W
        ciss = ciss.subs(sp.Symbol("W"), model.W_spec) # This assigns a numeric value to ciss
        
        cir.defPar("W", model.W_spec)
        cir.defPar(c_iss, ciss)
        
        # Express the output noise spectrum in c_iss, g_m, and f
        onoise   = sl.doNoise(cir, pardefs='Circuit', numeric=True).onoise
        
        # Wtite the output noise as a sum of products of numerically calculated integrals and 
        # coefficients in the form of (g_m^x * c_iss^y), where x and y are positive or negative integers.
        # The coefficient "1" (x=0 and y=0) is the noise with a noise-free controller.
        try:
            coeffs   = sl.integrated_monomial_coeffs(sp.expand(onoise), (g_m, c_iss), sl.ini.frequency, specs.f_min, specs.f_max)
            ovar = 0
         
            for key in coeffs.keys():
                ovar += key * coeffs[key]
        except:
            sp.pprint(sp.N(onoise, 3))
            
        gm_sel   = sl.fullSubs(gm, cir.parDefs)
        ovar_ID  = sp.simplify(ovar).subs(g_m, gm_sel)
        ID_found = sp.solve(ovar_ID - specs.noiseRMS**2, ID)[0]
        W        = model.W_spec
        
        # Check the inversion coefficient and run the script again if the
        # Inversion coefficient deviates too much from its assumed value
        cir.defPars({"IC_X1": ic, "c_iss_X1": ci, "g_m_X1": gm, "W": W, 
                     "L": model.L, "IG": model.IG, "ID": ID_found, model.CGBO: cb})
        IC_found  = sp.N(cir.getParValue("IC_X1"))
        if IC_found <= 0:
            errors.append(14)
            break
        
        rel_err   = sp.Abs(1-IC/IC_found)
        IC        = IC_found
        i        += 1
        IC_crit = sp.N(cir.getParValue("IC_CRIT_X1"))
        if i > maxiter:
            errors.append(11)
            break 
    print()   
    # Check the RMS noise
    noiseResult  = sl.doNoise(cir, pardefs="circuit", numeric=True)
    rmsNoise     = sl.rmsNoise(noiseResult, "onoise", specs.f_min, specs.f_max)
    n_min        = None
    result       = _update_results(cir, rmsNoise, n_min, ovar , errors)
    if sp.N(cir.getParValue("IC_X1")) > sp.N(cir.getParValue("IC_CRIT_X1")):
        errors.append(12)
    return result    

if __name__ == "__main__":
    
    sl.initProject("MOSdesign")
    
    # Schematic file
    kicad_sch = "kicad/Trimp/Trimp.kicad_sch"
    
    # Noise specifications
    specs = specObject()
    specs.noiseRMS = 0.1e-3
    specs.f_min    = 1e3
    specs.f_max    = 1e7
    specs.ID_max   = 10 # Always positive, also for P-channel!
    specs.ID_spec  = 100e-6
    
    # Technology specifications
    models = []
    
    model         = process()
    model.name    = "MN18_noisyNullor"
    #model.name    = "MN18_noisyNullor_simple" # Requires SLiCAP 4.0.6
    model.channel = "N"
    model.IG      = 0
    model.L       = 0.5e-6
    model.W_spec  = 500e-6
    model.W_min   = 0.18e-6
    model.W_max   = 1
    model.L_min   = 0.18e-6
    model.CGBO    = 'CGBO_N18'
    
    models.append(model)
    
    model         = process()
    model.name    = "MP18_noisyNullor"
    #model.name    = "MP18_noisyNullor_simple" # Requires SLiCAP 4.0.6
    model.channel = "P"
    model.IG      = 0
    model.L       = 0.5e-6
    model.W_spec  = 50e-6
    model.W_min   = 0.18e-6
    model.W_max   = 1
    model.L_min   = 0.18e-6
    model.CGBO    = 'CGBO_P18'
    
    models.append(model)
    
    # Perform noise design
    res = designMOSinputStage(kicad_sch, specs, models, methods=["min(RMSnoise)", "min(I_DS)", "min(AE)@I_DS", "max(AE)@I_DS", "I_DS@AE", "min(f_T)", "min(c_iss*g_m)"])
    print_results(res)