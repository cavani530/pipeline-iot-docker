import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import create_engine

st.set_page_config(page_title="Monitor de temperatura", layout="wide")
st.title("Monitor de temperatura IoT")
st.caption("Room Admin · Histórico de medições internas e externas")


@st.cache_resource
def banco():
    return create_engine("postgresql+psycopg2://", pool_pre_ping=True)


with banco().begin() as conn:
    conn.exec_driver_sql("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
    media = pd.read_sql("SELECT * FROM media_por_ponto ORDER BY sala, ambiente", conn)
    horas = pd.read_sql("SELECT * FROM leituras_por_hora ORDER BY hora", conn)
    dias = pd.read_sql("SELECT * FROM temp_max_min_por_dia ORDER BY dia", conn)

media["Ponto"] = media.sala + " · " + media.ambiente.map({"In": "Interno", "Out": "Externo"})
st.metric("Leituras válidas", f"{media.leituras.sum():,}".replace(",", "."))
opcoes = ["Médias por ponto", "Volume por hora", "Extremos diários"]
abas = st.tabs(opcoes)
figuras = [
    px.bar(media, x="Ponto", y="media", color="Ponto", hover_data=["leituras"],
           labels={"media": "Temperatura média (°C)"}),
    px.line(horas, x="hora", y="contagem", markers=True,
            labels={"hora": "Hora do dia", "contagem": "Leituras"}),
    px.line(dias, x="dia", y=["minima", "maxima"], markers=True,
            labels={"dia": "Data", "value": "Temperatura (°C)", "variable": "Extremo"}),
]
legendas = ["Cada barra reúne leituras da mesma sala e posição.",
            "A contagem soma todos os dias, com zero nas horas sem registros.",
            "As curvas mostram a menor e a maior leitura de cada data observada."]
for aba, figura, legenda in zip(abas, figuras, legendas):
    with aba:
        st.plotly_chart(figura, use_container_width=True)
        st.caption(legenda)
