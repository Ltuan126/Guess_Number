import random
def hint(secret:int)->tuple[str,str]:
    # ưu tiên tổng; nếu khó chọn thì hiệu
    if secret>2:
        a = random.randint(1, secret-1)
        b = secret - a
        if a!=b and a>0 and b>0:
            return (f"Là tổng của {a} và {b}", "sumdiff")
    a = random.randint(secret+3, secret+12)
    b = a - secret
    return (f"Là hiệu của {a} và {b} (a - b)", "sumdiff")
