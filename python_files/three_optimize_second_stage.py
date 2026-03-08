from .three_optimize_second_stage_conventional import optimize_second_stage_conventional
from .three_optimize_second_stage_cross import optimize_second_stage_cross


def optimize_second_stage(cir, stage2_flavor=None):
    """
    Dispatch second-stage optimization by flavor:
    - Conventional: 'N', 'P'
    - Cross-coupled variants: 'PN', 'NP'
    """
    flavor = (stage2_flavor or "N").upper().strip()
    if flavor in ("N", "P"):
        return optimize_second_stage_conventional(cir, stage2_flavor=flavor)
    if flavor in ("PN", "NP"):
        return optimize_second_stage_cross(cir, stage2_flavor=flavor)
    raise RuntimeError(
        f"Unsupported stage2_flavor '{stage2_flavor}'. Expected one of: N, P, PN, NP."
    )
