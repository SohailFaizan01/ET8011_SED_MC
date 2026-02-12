################################################## Circuit Data ##################################################

from SLiCAP import *
from .specifications import specs
from sympy import N

##### Path to kicad schematic
fileName = "Active_E_Field_Probe"
fileName = 'KiCad/' + fileName + '/' + fileName + '.kicad_sch'

##### Create slicap circuit object
cir = makeCircuit(fileName,imgWidth=1000)

##### Import predefined specifications to the kicad circuit
specs2circuit(specs, cir)










############################################## Random Blocks of Code ##############################################

##### List the available loopgain references
# print("Available loop gain references:")
# print(cir.controlled)

##### Set drain gate capacitance to 0
# cir.defPar("c_dg_X1", 0)
# cir.defPar("c_dg_X2", 0)
# cir.defPar("c_dg_X3", 0)

##### Print parameter value
# print(N(cir.getParValue("f_T_X1"),2))
# print(N(cir.getParValue("g_m_X1"),2))
# print(N(cir.getParValue("g_m_X2"),2))
# print(N(cir.getParValue("g_m_X3"),2))
#print(N(cir.getParValue("c_gs_X1"),2))
#print(cir.parDefs)