def hint(secret:int)->tuple[str,str]:
    return ("Số chẵn" if secret%2==0 else "Số lẻ", "parity")
