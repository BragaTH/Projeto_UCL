from database import buscar_historico

registros = buscar_historico()

if not registros:
    print("Nenhum registro encontrado.")
else:
    print(f"{'VAGA':<6} {'ENTRADA':<22} {'SAÍDA':<22} {'DURAÇÃO (min)'}")
    print("-" * 70)
    for vaga_id, entrada, saida, duracao in registros:
        saida   = saida or "ainda ocupada"
        duracao = str(duracao) + " min" if duracao else "-"
        print(f"{vaga_id:<6} {entrada:<22} {saida:<22} {duracao}")