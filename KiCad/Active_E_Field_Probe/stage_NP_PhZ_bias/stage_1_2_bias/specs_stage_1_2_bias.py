################################################# Specifications #################################################
from SLiCAP import *
from python_files.generated_specs import specs_NP as base_specs

# Start with the generated NP specs.
specs = list(base_specs.specs)

# Append additional specs below.
# Example:
# specs.append(specItem("R_extra", description="Extra resistor", value=1e3, units="Ohm", specType="Amplifier"))
specs.append(specItem("VDS1T_N", description="Tail VDS", value=25e-3, units="V", specType="Biasing"))
specs.append(specItem("VDS1_N", description="Amp VDS", value=50e-3, units="V", specType="Biasing"))
specs.append(specItem("VGS1_N", description="Amp VGS", value=0.0, units="V", specType="Biasing"))
specs.append(specItem("VDS1C_N", description="Casc VDS", value=1.025, units="V", specType="Biasing"))
specs.append(specItem("VGS1C_N", description="Casc VGS", value=0.0, units="V", specType="Biasing"))
