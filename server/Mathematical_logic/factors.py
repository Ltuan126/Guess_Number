from .utils import is_prime, prime_factors, fmt_factorization
def hint(secret:int)->tuple[str,str]:
    if is_prime(secret):
        return ("Thừa số nguyên tố duy nhất là chính nó", "factors")
    fac = prime_factors(secret)
    pmin = min(p for p,_ in fac)
    return (f"Có thừa số nguyên tố là {pmin} (phân tích: {secret} = {fmt_factorization(fac)})", "factors")
