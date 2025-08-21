from typing import List, Tuple
from .factors import hint as h_factors
from .modulo import hint as h_mod
from .parity import hint as h_parity
from .prime import hint as h_prime
from .sumdiff import hint as h_sumdiff

CYCLE = ["parity", "prime", "factors", "mod", "sumdiff"]
MAP = {
    "parity": h_parity,
    "prime": h_prime,
    "factors": h_factors,
    "mod": h_mod,
    "sumdiff": h_sumdiff,
}

def _cycle_index(round_num: int) -> int:
    return (round_num - 2) % len(CYCLE)  # round 2 -> 0

def choose_hint_for_round(round_num: int, secret: int, used_tags: List[str] | None = None) -> Tuple[str, str]:
    if round_num < 2:
        return ("", "none")  # vòng 1 không có hint
    start = _cycle_index(round_num)
    order = CYCLE[start:] + CYCLE[:start]
    last = used_tags[-1] if used_tags else None
    for tag in order:
        if tag == last and len(order) > 1:
            continue
        text, t = MAP[tag](secret)
        return (text, t)
    return MAP[CYCLE[start]](secret)
