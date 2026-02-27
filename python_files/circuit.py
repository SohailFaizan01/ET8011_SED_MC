################################################## Circuit Data ##################################################

from SLiCAP import *
from .specifications import specs
import os
from pathlib import Path

##### Path to kicad schematic
def _resolve_kicad_schematic(project):
    """Resolve a .kicad_sch file from explicit path, directory, or project name."""
    candidate = Path(project)
    if candidate.suffix == ".kicad_sch":
        if candidate.exists():
            return str(candidate)
        raise FileNotFoundError(f"Schematic file not found: '{candidate}'")

    kicad_root = Path("KiCad")

    # Legacy pattern: KiCad/<project>/<project>.kicad_sch
    legacy = kicad_root / project / f"{Path(project).name}.kicad_sch"
    if legacy.exists():
        return str(legacy)

    # If project points to a directory, use the only schematic inside it.
    proj_dir = candidate if candidate.is_dir() else (kicad_root / project)
    if proj_dir.is_dir():
        sch_files = sorted(proj_dir.glob("*.kicad_sch"))
        if len(sch_files) == 1:
            return str(sch_files[0])

    # Fallback: recursive lookup by basename anywhere under KiCad.
    matches = sorted(kicad_root.glob(f"**/{Path(project).name}.kicad_sch"))
    if matches:
        return str(matches[0])

    raise FileNotFoundError(
        f"Could not locate a .kicad_sch for '{project}'. "
        "Provide a direct file path or a valid project directory."
    )


def make_project_circuit(project):
    """Build a SLiCAP circuit object and apply shared specifications."""
    file_name = _resolve_kicad_schematic(project)
    cir_obj = makeCircuit(file_name, imgWidth=1000)
    specs2circuit(specs, cir_obj)
    return cir_obj


##### Create default slicap circuit object (backward compatible behavior)
_default_project = os.getenv("KICAD_PROJECT", "Active_E_Field_Probe")
try:
    cir = make_project_circuit(_default_project)
except FileNotFoundError:
    # Some execution paths only need make_project_circuit(); defer hard failure.
    cir = None



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
