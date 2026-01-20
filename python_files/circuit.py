################################################## Circuit Data ##################################################

from SLiCAP import *
from .specifications import specs
import numpy as np
from sympy import *
s = symbols("s")
# t = symbols("t", real=True, positive=True)
# w = symbols("w", real=True)

fileName = "Active_E_Field_Probe"
fileName = 'KiCad/' + fileName + '/' + fileName + '.kicad_sch'

cir = makeCircuit(fileName,imgWidth=1000)
# cirAsymptotic = makeCircuit(fileName,imgWidth=1000)

# print(cir.controlled)

specs2circuit(specs, cir)

# cir.defPar("c_dg_X1", 0)
# cir.defPar("c_dg_X2", 0)
# cir.defPar("c_dg_X3", 0)