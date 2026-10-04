from dataclasses import dataclass, field


@dataclass
class MilpModel:
    cx: object
    cell_lo: object = None
    cell_hi: object = None
    formulation: str = 'A'
    cuts: list = field(default_factory=list)
    fixed_y: dict = field(default_factory=dict)
    target_matches: int | None = None
    weights: object = None
    first_feasible: bool = False


@dataclass
class SolveResult:
    status: str
    kappa_incumbent: int | None
    kappa_lb: int | None
    kappa_opt: int | None
    lb_is_certificate: bool
    bound: float | None
    gap: float | None
    wall_s: float
    nodes: int | None
    x: object
    y: object
    cut_iters: int = 0
    cuts_added: int = 0
