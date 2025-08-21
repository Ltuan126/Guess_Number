def hint(secret:int)->tuple[str,str]:
    mods=[3,4,5,6,7,8,9,11]
    m = next((x for x in mods if x<secret), mods[0])
    r = secret % m
    if r==0: return (f"Chia hết cho {m}", "mod")
    return (f"Chia cho {m} dư {r}", "mod")
    # Trả lời dạng "Chia hết cho m" hoặc "Chia cho m dư r"
    