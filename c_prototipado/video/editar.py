"""Edición del video final según guion-edicion.md. Requiere FFmpeg y haber corrido graficos.py.

Un solo grafo de FFmpeg: el crudo se recorta una vez (silencio inicial y final) y la voz corre continua; en los
tramos de pantalla dividida se superpone el fondo con el programa y la grabación achicada. Portada y placa en silencio.
Uso: python editar.py            vista previa a 540p en trabajo/vista-previa.mp4
     python editar.py --final    video final en d_presentacion/
"""
import subprocess
import sys
from pathlib import Path

from graficos import VIDEO

AQUI = Path(__file__).resolve().parent
CRUDO = AQUI / "crudo_2026-11-07.mp4"
G = AQUI / "g"
PREVIA = AQUI / "trabajo" / "vista-previa.mp4"
FINAL = AQUI.parents[1] / "d_presentacion" / "Video_Celda_Soldadura_Grupo4.mp4"

INICIO, FIN = 1.2, 531.6      # silencio inicial y todo lo que sigue a «nos estamos viendo»
PORTADA, PLACA, FUNDIDO = 5.0, 3.0, 0.5
# Tramos de pantalla dividida, en segundos del crudo (ver la tabla «Propuesta» del guion).
DIVIDIDA = [
    (157.3, 194.9, "d_principal"),
    (194.9, 248.9, "d_ciclo"),
    (337.6, 382.8, "d_soldadura"),
    (382.8, 406.3, "d_deposito"),
    (476.4, 493.8, "d_recuperacion"),
]
CRF = 30  # contenido de pantalla con poco movimiento: CRF alto y -tune animation alcanzan


def grafo(escala):
    vx, vy, vw, vh = VIDEO
    n = len(DIVIDIDA)
    partes = [
        f"[0:v]trim={INICIO}:{FIN},setpts=PTS-STARTPTS,fps=30,format=yuv420p,split=2[full][chico0]",
        f"[chico0]scale={vw}:{vh}:flags=lanczos,split={n}" + "".join(f"[c{i}]" for i in range(n)),
    ]
    base = "full"
    for i, (a, b, _) in enumerate(DIVIDIDA):
        en = f"enable='between(t,{a - INICIO:.2f},{b - INICIO:.2f})'"
        partes.append(f"[{base}][{3 + i}:v]overlay=0:0:{en}[f{i}]")
        partes.append(f"[f{i}][c{i}]overlay={vx}:{vy}:{en}[o{i}]")
        base = f"o{i}"
    dur = FIN - INICIO
    partes += [
        f"[{base}]null[principal]",
        f"[0:a]atrim={INICIO}:{FIN},asetpts=PTS-STARTPTS,highpass=f=80,"
        f"afade=t=in:d=0.2,afade=t=out:st={dur - 0.4:.2f}:d=0.4[voz]",
        f"[1:v]fps=30,format=yuv420p,fade=t=out:st={PORTADA - FUNDIDO}:d={FUNDIDO}[portada]",
        f"[2:v]fps=30,format=yuv420p,fade=t=in:d={FUNDIDO}[placa]",
        f"anullsrc=r=48000:cl=stereo,atrim=0:{PORTADA}[sp]",
        f"anullsrc=r=48000:cl=stereo,atrim=0:{PLACA}[sf]",
        "[portada][sp][principal][voz][placa][sf]concat=n=3:v=1:a=1[v][a0]",
        f"[v]scale={escala}:flags=lanczos,setsar=1[vout]",
        "[a0]loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000[aout]",
    ]
    return ";".join(partes)


def render(salida, escala, video_args, audio_k):
    entradas = ["-i", str(CRUDO),
                "-loop", "1", "-framerate", "30", "-t", str(PORTADA), "-i", str(G / "portada.png"),
                "-loop", "1", "-framerate", "30", "-t", str(PLACA), "-i", str(G / "placa.png")]
    for _, _, g in DIVIDIDA:
        # Un solo cuadro: overlay repite el último (eof_action=repeat) y el PNG se decodifica una vez.
        entradas += ["-i", str(G / f"{g}.png")]
    salida.parent.mkdir(exist_ok=True)
    cmd = ["ffmpeg", "-y", "-v", "error", "-stats", *entradas, "-filter_complex", grafo(escala),
           "-map", "[vout]", "-map", "[aout]", *video_args,
           "-c:a", "aac", "-b:a", f"{audio_k}k", "-movflags", "+faststart", str(salida)]
    subprocess.run(cmd, check=True)
    print(f"{salida} ({salida.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    if "--final" in sys.argv:
        render(FINAL, "1920:1080", ["-c:v", "libx264", "-preset", "slow", "-tune", "animation", "-crf", str(CRF),
                                    "-pix_fmt", "yuv420p", "-g", "300"], 96)
    else:
        render(PREVIA, "960:540", ["-c:v", "libx264", "-preset", "veryfast", "-crf", "28", "-pix_fmt", "yuv420p"], 96)
