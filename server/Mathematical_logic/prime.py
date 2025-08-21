from .utils import is_prime
def hint(secret:int)->tuple[str,str]:
    return ("Số nguyên tố" if is_prime(secret) else "Không phải số nguyên tố", "prime")
