"""Monta um MP4 H.264 a partir das capturas e do roteiro do relatório."""
from pathlib import Path
import shutil
import subprocess
import textwrap
from tempfile import TemporaryDirectory
from PIL import Image, ImageDraw, ImageFont

pasta=Path("docs")
real=(pasta/"painel-0.png").exists()
prefixo="painel" if real else "amostra"
falas=(pasta/"Roteiro.txt").read_text(encoding="utf8").split("\n\n")
fonte="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
def executar(*args):
    subprocess.run(args,check=True)

with TemporaryDirectory() as tmp:
    base=Path(tmp)
    partes=[]
    for i,fala in enumerate(falas):
        tela=Image.new("RGB",(1280,800),"#f5f7f5")
        d=ImageDraw.Draw(tela)
        d.text((40,20),"TEMPERATURAS IoT   /   "+("Streamlit" if real else "Prévia com oito registros reais"),font=ImageFont.truetype(fonte,28),fill="#075e59")
        if i:
            grafico=Image.open(pasta/f"{prefixo}-{i-1}.png").convert("RGB")
            grafico.thumbnail((1180,490))
            tela.paste(grafico,((1280-grafico.width)//2,80))
        else:
            d.text((70,160),"Pipeline de dados com IoT e Docker",font=ImageFont.truetype(fonte,54),fill="#15373f")
            d.text((75,270),"CSV  →  Python  →  PostgreSQL  →  Streamlit",font=ImageFont.truetype(fonte,36),fill="#08796e")
            d.text((75,370),"Diogo Fuentes Pereira  |  UniFECAF",font=ImageFont.truetype(fonte,26),fill="#496467")
        d.rectangle((0,570,1280,800),fill="#173d45")
        d.multiline_text((40,595),"\n".join(textwrap.wrap(fala,91)),font=ImageFont.truetype(fonte,24),fill="white",spacing=8)
        frame=base/f"{i}.png"
        tela.save(frame)
        cmd=["ffmpeg","-loglevel","error","-loop","1","-framerate","10","-i",str(frame)]
        if shutil.which("espeak-ng"):
            wav=base/f"{i}.wav"
            executar("espeak-ng","-v","pt-br","-s","150","-w",str(wav),fala)
            cmd+=["-i",str(wav),"-shortest","-c:a","aac"]
        else:
            cmd+=["-t",str(max(8,len(fala.split())*.48))]
        clip=base/f"{i}.mp4"
        executar(*cmd,"-c:v","libx264","-threads","2","-pix_fmt","yuv420p",str(clip))
        partes.append(f"file '{clip}'")
    lista=base/"lista.txt"
    lista.write_text("\n".join(partes))
    executar("ffmpeg","-loglevel","error","-y","-f","concat","-safe","0","-i",str(lista),"-c","copy","-movflags","+faststart",str(pasta/"Pitch-IoT.mp4"))
