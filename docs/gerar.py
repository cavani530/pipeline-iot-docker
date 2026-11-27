"""Gera evidências da execução do painel. Execute a partir da raiz do projeto."""
import argparse
import html
from pathlib import Path
import shutil
import subprocess
import sys

import pandas as pd
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path("src").resolve()))
from transformar import preparar

parser = argparse.ArgumentParser()
parser.add_argument("--amostra-ilustrada", action="store_true")
args = parser.parse_args()
previa = args.amostra_ilustrada
pasta = Path("docs")
dados = preparar("data/amostra.csv" if previa else "data/IOT-temp.csv")
pontos = dados.groupby(["sala", "ambiente"]).temperatura.mean()
horas = dados.groupby(dados.instante.dt.hour).size().reindex(range(24), fill_value=0)
dias = dados.groupby(dados.instante.dt.date).temperatura.agg(["min", "max"])
titulos = ["Médias por ponto", "Volume por hora", "Extremos diários"]
meio = "Amostra ilustrada · 8 registros" if previa else "Captura do dashboard Streamlit"
notas = [
    "A view media_por_ponto agrupa sala e posição. A média dá o mesmo peso a cada leitura. O identificador original representa um registro e não identifica um aparelho físico.",
    "A view leituras_por_hora extrai a hora do registro e soma as observações de todos os dias. Uma série de 0 a 23 preserva as horas sem registros. O volume ajuda a investigar a frequência de coleta.",
    "A view temp_max_min_por_dia agrupa pela data do CSV e calcula os extremos entre todas as posições. Uma amplitude elevada pode orientar a inspeção dos registros daquele dia.",
]
achados = [
    " · ".join(f"{sala} ({pos}): {valor:.2f} °C".replace(".", ",") for (sala,pos),valor in pontos.items()),
    f"Hora com maior contagem: {horas.idxmax():02d}h ({horas.max()} leituras; primeiro horário em caso de empate).",
    f"Faixa observada: {dias['min'].min():g} a {dias['max'].max():g} °C. Maior amplitude diária: {(dias['max']-dias['min']).max():g} °C.",
]
if previa:
    import matplotlib.pyplot as plt
    for i in range(3):
        fig, ax = plt.subplots(figsize=(10,4))
        if i == 0:
            ax.bar([f"{s} · {p}" for s,p in pontos.index], pontos, color=["#087d77","#e68148"])
            ax.set_ylabel("Média (°C)")
        elif i == 1:
            ax.plot(horas.index, horas, marker="o", color="#087d77")
            ax.set(xlabel="Hora do dia", ylabel="Leituras", xticks=range(0,24,2))
        else:
            for c,cor in [("min","#087d77"),("max","#e68148")]:
                ax.plot([d.strftime("%d/%m") for d in dias.index],dias[c],marker="o",label=c,color=cor)
            ax.legend()
            ax.set_ylabel("Temperatura (°C)")
        ax.spines[["right","top"]].set_visible(False)
        ax.set_title(titulos[i],loc="left")
        fig.tight_layout()
        fig.savefig(pasta/f"amostra-{i}.png", dpi=120)
        plt.close(fig)
with sync_playwright() as pw:
    browser = None if previa else pw.chromium.launch(args=["--no-sandbox"])
    if not previa:
        page = browser.new_page(viewport={"width":1280,"height":800}, device_scale_factor=1)
    if not previa:
        page.goto("http://localhost:8501")
        for i,titulo in enumerate(titulos):
            tab=page.get_by_role("tab",name=titulo)
            tab.click(timeout=90000)
            page.locator('[role="tabpanel"]:visible .js-plotly-plot .main-svg').first.wait_for()
            page.screenshot(path=str(pasta/f"painel-{i}.png"))
    prefixo = "amostra" if previa else "painel"
    paginas = []
    estilo = """*{box-sizing:border-box}body{font:19px Arial,sans-serif;color:#16363e;margin:0}section{padding:45px 55px;page-break-after:always}section:last-child{page-break-after:auto}small{color:#09776e;letter-spacing:1px}h1{font-size:44px}h2{font-size:34px}p{line-height:1.5}img{width:100%;max-height:520px;object-fit:contain}aside{border-left:5px solid #e68148;padding:10px 16px;background:#f6f4ec}footer{font-size:14px;color:#52686d}"""
    resumo = ("Análise demonstrativa de oito registros selecionados. Os gráficos desta versão foram gerados em Python. "
              "As capturas de Streamlit são geradas ao executar o projeto completo." if previa else
              "Visualizações capturadas do Streamlit após a carga e a conferência das contagens no PostgreSQL.")
    paginas.append(f"""<section><small>UNIFECAF · ANÁLISE E DESENVOLVIMENTO DE SISTEMAS</small><h1>Pipeline de dados com IoT e Docker</h1><p>Diogo Fuentes Pereira<br>Disruptive Architectures: IoT, Big Data e IA</p><h2>Da leitura à decisão</h2><p>Um histórico de temperaturas permite investigar diferenças entre ambientes e horários sem coleta. O projeto transforma leituras exportadas em CSV em três consultas reproduzíveis.</p><h2>Construção</h2><p>Docker Compose prepara o PostgreSQL 16 com volume persistente. Uma imagem Python instala as dependências e executa a carga assim que o banco responde. O pandas converte datas no padrão dia-mês-ano, valida campos e conta duplicatas. IDs com valores conflitantes interrompem a carga.</p><p>O SQLAlchemy grava uma fotografia integral em uma transação. A carga compara a quantidade de registros válidos, o total da tabela e a soma da view horária. O painel consulta as três views e o Plotly permite inspecionar os pontos.</p><aside>{resumo}</aside></section>""")
    for i,t in enumerate(titulos):
        img=(pasta/f"{prefixo}-{i}.png").resolve().as_uri()
        paginas.append(f"<section><small>{meio} · {i+1}/3</small><h2>{t}</h2><img src='{img}'><p>{notas[i]}</p><aside>{html.escape(achados[i])}</aside></section>")
    paginas[-1]=paginas[-1].replace("</section>","<p>Em operação, um alerta pode combinar limites específicos por ambiente com tempo de exposição e atraso da última leitura. A frequência de amostragem e a quantidade de registros por posição influenciam a interpretação das médias.</p><footer>Fonte: Atulanand Jha, Temperature Readings: IoT Devices (Kaggle). Recorte de conferência: Data Pre-Processing and Visualization OER, My Solutions.</footer></section>")
    from tempfile import TemporaryDirectory
    with TemporaryDirectory() as tmp:
        arquivo=Path(tmp)/"relatorio.html"
        arquivo.write_text("<meta charset=utf-8><style>"+estilo+"</style>"+"".join(paginas),encoding="utf8")
        if previa:
            from lxml import html as markup
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image
            styles = getSampleStyleSheet()
            flow = []
            for i, trecho in enumerate(paginas):
                if i:
                    flow.append(PageBreak())
                for tag in markup.fromstring(trecho):
                    if tag.tag == "img":
                        flow.append(Image(str(pasta/f"amostra-{i-1}.png"), 450,180))
                    elif tag.tag:
                        estilo_pdf = {"h1":"Title","h2":"Heading2","small":"Heading3"}.get(tag.tag,"BodyText")
                        flow.extend([Paragraph(html.escape(" ".join(tag.itertext())), styles[estilo_pdf]), Spacer(1,9)])
            SimpleDocTemplate(str(pasta/"Relatorio-IoT.pdf")).build(flow)
        else:
            page.goto(arquivo.as_uri())
            page.pdf(path=str(pasta/"Relatorio-IoT.pdf"),format="A4",print_background=True)
            browser.close()


falas = [
    "Como transformar um arquivo de temperaturas em informação para quem monitora um ambiente? O projeto usa Python para validar cada leitura e Docker para preparar o banco PostgreSQL.",
    "A primeira consulta calcula a média por sala e posição. Interno e externo são pontos de medição. O identificador no arquivo corresponde a uma leitura. " + achados[0],
    "A segunda consulta conta as leituras em cada hora do dia. Isso ajuda a investigar interrupções e diferenças na frequência da coleta. " + achados[1],
    "A última consulta mostra as temperaturas mínimas e máximas de cada dia. " + achados[2] + " Em uma instalação real, esses extremos ajudariam a escolher quais registros investigar antes de emitir um alerta.",
]
(pasta/"Roteiro.txt").write_text("\n\n".join(falas),encoding="utf8")
