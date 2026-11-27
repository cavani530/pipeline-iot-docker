import sys
from pathlib import Path
from sqlalchemy import create_engine, text
from transformar import preparar


def carregar(caminho):
    dados = preparar(caminho)
    engine = create_engine("postgresql+psycopg2://")
    modelo = Path(__file__).resolve().parents[1] / "sql/modelo.sql"
    with engine.begin() as conexao:
        conexao.execute(text("SELECT pg_advisory_xact_lock(7134001)"))
        conexao.exec_driver_sql(modelo.read_text(encoding="utf-8"))
        # O CSV representa uma fotografia completa. Falhas revertem toda a carga.
        conexao.execute(text("DELETE FROM temperature_readings"))
        dados.to_sql("temperature_readings", conexao, if_exists="append", index=False, chunksize=1000)
        total = conexao.scalar(text("SELECT COUNT(*) FROM temperature_readings"))
        horas = conexao.scalar(text("SELECT SUM(contagem) FROM leituras_por_hora"))
        if total != len(dados) or horas != total:
            raise ValueError("A contagem gravada diverge da carga.")
    print(f"Transação confirmada: {total} leituras no PostgreSQL.")


if __name__ == "__main__":
    carregar(sys.argv[1])
