# -*- coding: utf-8 -*-
"""
Created on Sat May 24 11:05:06 2025

@author: Martijn
"""
# Create and.or initialize a project:
import SLiCAP as sl

from time import time

t1=time()

# Define all the paths, create the HTML main index page, reset the parser, and
# compile the SLiCAP libraries.

prj = sl.initProject("E-Field-Probe") 

#################################################################################################

# Create a circuit object from a schematic file or a SLiCAP netlist:
    
fileName = "KiCAD-SED-MC-Active-E-Field-Probe"

# KiCAD version 9.0
fileName = sl.ini.cir_path + fileName + '/' + fileName + '.kicad_sch'

# LTspice
#fileName = ini.cir_path + fileName + '.asc'

# gSchem or lepton-eda
#fileName = ini.cir_path + fileName + '.sch'

# Use existing netlist that resides in the ini.cir_path directory
fileName = fileName + '.cir'

cir = sl.makeCircuit(fileName, update=True, imgWidth=400)

#################################################################################################

# It is convenient to define the values at the top of the file
# This makes it easy to modify them
Cs = 10e-12 # Typical value of the source capacitance
Zt = 1e6    # Target value transimpedance gain in Ohm
Bf = 5e4    # Target value -3dB bandwidth in Hz
Vn = 5e-4   # Maximum unweighted RMS output noise voltage
# Now assign these values to specification items and put these items in a list
# Create the list
specs = []
# Create specification items and append them to the list
specs.append(sl.specItem("C_s",
                         description = "Typical value of the source capacitance",
                         value       = Cs,
                         units       = "F",
                         specType    = "Interface"))
specs.append(sl.specItem("Z_t",
                         description = "Target value transimpedance gain in Ohm",
                         value       = Zt,
                         units       = "Ohmega",
                         specType    = "Functional"))
specs.append(sl.specItem("B_f",
                         description = "Target value -3dB bandwidth in Hz",
                         value       = Bf,
                         units       = "Hz",
                         specType    = "Performance"))
specs.append(sl.specItem("V_n",
                         description = "Maximum unweighted RMS output noise voltage",
                         value       = Vn,
                         units       = "V",
                         specType    = "Performance"))

#################################################################################################

# Print the contents of the dictionary with circuit parameter definitions:
if len(cir.parDefs.keys()):
    print("\nParameters with definitions:\n")
    for key in cir.parDefs.keys():
        print(key, cir.parDefs[key])
else:
    print("\nFound no parameter definitions")
# Print the contents of the list with parameters that have no definition:
if len(cir.params):
    print("\nParameters that have no definition:\n")
    for param in cir.params:
        print(param)
else:
    print("\nFound no parameters without definition")
    
#################################################################################################

# Let us define an instruction to display the symbolic MNA matrix equation.
MNA = sl.doMatrix(cir)

# We will put the instruction on a new HTML page and display it in this notebook
sl.htmlPage('Matrix equations')
# Let us put some explaining text in the report:
sl.text2html('The MNA matrix equation for the RC network is:')
sl.matrices2html(MNA, label = 'MNA', labelText = 'MNA equation of the network')
# The variables in this equation are available in the variable that holds
# the result of the execution:
#
# 1. The vector 'Iv' with independent variables:
sl.text2html('The vector with independent variables is:')
sl.eqn2html('I_v', MNA.Iv, label = 'Iv', labelText = 'Vector with independent variables')
# 2. The matrix 'M':
sl.text2html('The MNA matrix is:')
sl.eqn2html('M', MNA.M, label = 'M', labelText = 'MNA matrix')
# 3. The vercor wit dependent variables 'Dv':
sl.text2html('The vector with dependent variables is:')
sl.eqn2html('D_v', MNA.Dv, label = 'Dv', labelText = 'Vector with dependent variables')

#################################################################################################
