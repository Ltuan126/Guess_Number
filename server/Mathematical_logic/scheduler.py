from typing import List, Tuple
from .parity import hint as h_parity
from .prime import hint as h_prime
from .factors import hint as h_factors
from .modulo import hint as h_mod
from .sumdiff import hint as h_sumdiff

# chu kỳ gợi ý A→B→C→D→E…
CYCLE = ["parity","prime","factors","mod","sumdiff"]
MAP = {
    "parity": h_parity,
    "prime": h_prime,
    "factors": h_factors,
    "mod": h_mod,
    "sumdiff": h_sumdiff,
}

def cycle_index_for_round(r:int)->int:
    # Round 2 -> idx 0, Round 3 -> 1, …
    return (r - 2) % len(CYCLE)

def choose_hint_for_round(round_num:int, secret:int, used_tags:List[str]|None=None)->Tuple[str,str]:
    """
    Trả (hint_text, tag). Mỗi vòng 1 gợi ý, từ Round 2 trở đi.
    Không lặp loại gợi ý với vòng liền trước nếu có thể.
    """
    if round_num < 2:
        return ("", "none")

    # chọn loại theo chu kỳ
    start_idx = cycle_index_for_round(round_num)
    order = CYCLE[start_idx:] + CYCLE[:start_idx]

    if used_tags and len(used_tags)>0:
        last = used_tags[-1]
    else:
        last = None

    for tag in order:
        if tag == last and len(order)>1:
            continue
        text, t = MAP[tag](secret)
        return (text, t)

    # fallback
    return MAP[CYCLE[start_idx]](secret)
