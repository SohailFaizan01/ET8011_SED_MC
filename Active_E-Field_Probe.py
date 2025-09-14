import SLiCAP as sl
sl.initProject("Active_E-field_Probe")

# Create a circuit object from a schematic file or a SLiCAP netlist:
fileName = "Active_E-Field_Probe"

# KiCAD version 8.0
fileName = 'KiCad/' + fileName + '/' + fileName + '.kicad_sch'

cir = sl.makeCircuit(fileName,imgWidth=400)


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

