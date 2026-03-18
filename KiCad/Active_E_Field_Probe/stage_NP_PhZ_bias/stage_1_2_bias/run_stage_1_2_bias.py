from pathlib import Path

from SLiCAP import *

from .specs_stage_1_2_bias import specs


def run():
    sch_path = Path(__file__).with_name("stage_1_2_bias.kicad_sch")
    if not sch_path.exists():
        raise FileNotFoundError(f"Missing schematic: {sch_path}")

    cir = makeCircuit(str(sch_path), imgWidth=1000)
    specs2circuit(specs, cir)
    return cir


if __name__ == "__main__":
    run()


simCmd = "TRAN 1n 1u"
#stepCmd = "C_c LIN 2p 20p 10"
names  = {"V_out": "V(Amp_out)"}

tran, x_name, x_units = ngspice2traces("cir/" + fileName, simCmd, names)
#tran, x_name, x_units  = ngspice2traces("cir/" + fileName, simCmd, names, stepCmd=stepCmd)

plot("tranPlot", "Transient response $V_{out}$", "lin", tran, xName=x_name, xUnits=x_units, xScale="u", yUnits="V")
