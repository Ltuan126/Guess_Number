import math
def is_prime(n:int)->bool:
    if n<2: return False
    if n%2==0: return n==2
    r=int(math.isqrt(n)); d=3
    while d<=r:
        if n%d==0: return False
        d+=2
    return True

def prime_factors(n:int):
    res=[]; c=n; e=0
    while c%2==0: c//=2; e+=1
    if e: res.append((2,e))
    p=3
    while p*p<=c:
        e=0
        while c%p==0: c//=p; e+=1
        if e: res.append((p,e))
        p+=2
    if c>1: res.append((c,1))
    return res

def fmt_factorization(f):
    return " · ".join([f"{p}" if e==1 else f"{p}^{e}" for p,e in f])
