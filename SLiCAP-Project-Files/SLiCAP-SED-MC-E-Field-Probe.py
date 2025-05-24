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