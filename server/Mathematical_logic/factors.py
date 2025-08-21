# server/Mathematical_logic/factors.py
import random
from .utils import is_prime, prime_factors

def hint(secret: int) -> tuple[str, str]:
    """
    Gợi ý an toàn về thừa số:
    - KHÔNG in "s = ..." hay liệt kê đầy đủ tích các thừa số
    - Chỉ tiết lộ 1 thuộc tính không đủ để suy ra s ngay
    """
    if is_prime(secret):
        # Vẫn giữ category "factors" nhưng không lặp lại nội dung ở hint_prime
        return ("Không có thừa số nguyên tố khác ngoài chính nó", "factors")

    fac = prime_factors(secret)              # [(p, exp), ...]
    distinct_cnt = len(fac)                  # số thừa số nguyên tố phân biệt
    total_cnt = sum(e for _, e in fac)       # tổng số thừa số (tính bội)
    p_min = min(p for p, _ in fac)           # thừa số nguyên tố nhỏ nhất

    variants = [
        f"Thừa số nguyên tố nhỏ nhất là {p_min}",
        f"Có {distinct_cnt} thừa số nguyên tố phân biệt",
        f"Tổng số thừa số nguyên tố (tính cả bội số) là {total_cnt}",
    ]
    return (random.choice(variants), "factors")
