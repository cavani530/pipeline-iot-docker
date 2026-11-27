import numpy as np
import pandas as pd

COLUNAS = {"id": "reading_id", "room_id/id": "sala", "noted_date": "instante",
           "temp": "temperatura", "out/in": "ambiente"}


def preparar(caminho):
    bruto = pd.read_csv(caminho, usecols=list(COLUNAS), dtype="string")
    dados = bruto.rename(columns=COLUNAS).apply(lambda col: col.str.strip())
    dados["instante"] = pd.to_datetime(dados["instante"], format="%d-%m-%Y %H:%M", errors="coerce")
    dados["temperatura"] = pd.to_numeric(dados["temperatura"], errors="coerce")
    dados["ambiente"] = dados["ambiente"].str.title()
    validos = dados.dropna().copy()
    validos = validos[validos.sala.ne("") & validos.reading_id.ne("") &
                      validos.ambiente.isin(["In", "Out"]) & np.isfinite(validos.temperatura)]
    unicos = validos.drop_duplicates()
    if unicos.reading_id.duplicated().any():
        raise ValueError("Um ID possui registros divergentes. Confira o CSV.")
    if unicos.empty:
        raise ValueError("O arquivo não contém leituras válidas.")
    print(f"Lidas: {len(bruto)} | Inválidas: {len(bruto)-len(validos)} | "
          f"Duplicatas: {len(validos)-len(unicos)} | Válidas únicas: {len(unicos)}")
    return unicos
