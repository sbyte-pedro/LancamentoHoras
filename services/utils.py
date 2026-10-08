def passarParaDecimal(row: str) -> float:
    parts = row.split(":")
    hora = int(parts[0])
    minuto = int(parts[1]) / 60 if len(parts) > 1 else 0.0
    return hora + minuto
