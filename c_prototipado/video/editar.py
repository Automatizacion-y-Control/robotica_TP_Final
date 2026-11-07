"""Edición del video final según guion-edicion.md. Requiere FFmpeg y haber corrido graficos.py.

Un solo grafo de FFmpeg: el crudo se recorta una vez (silencio inicial y final) y la voz corre continua; en los
tramos de pantalla dividida se superpone el fondo con el programa y la grabación achicada. Portada y placa en silencio.
Uso: python editar.py               vista previa a 540p en trabajo/vista-previa.mp4
     python editar.py --final       video final en d_presentacion/ (no se versiona: se publica en Drive) y miniatura
     python editar.py --miniatura   solo la miniatura para los README, a partir del video final
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
MINIATURA = AQUI.parents[1] / "d_presentacion" / "miniatura_video.jpg"
CUADRO_MINIATURA = 350.0  # segundo del crudo: soldadura en pantalla dividida, con Sold_Par_Cordones al costado

# Presentación sobre la portada, reordenada y sin «Nosotros somos el grupo 10» (Whisper oyó mal; se dice 4):
# «Bueno, ¿qué tal?» + «Nuestro grupo está conformado por…» + «Vamos a presentar ahora… paquete de estator».
# Bordes en segundos del crudo, en los huecos entre palabras de la transcripción.
INTRO = [(1.40, 2.60), (15.82, 21.60), (4.70, 15.70)]
PAUSA_INICIAL, ENTRE_FRASES, COLA = 1.0, 0.35, 0.6
INICIO, FIN = 22.2, 531.6     # desde «Bueno, la idea es…» hasta «nos estamos viendo»
PLACA, FUNDIDO = 3.0, 0.5
PORTADA = round(PAUSA_INICIAL + sum(b - a for a, b in INTRO) + ENTRE_FRASES * (len(INTRO) - 1) + COLA, 2)
# Tramos de pantalla dividida, en segundos del crudo (ver la tabla «Propuesta» del guion).
DIVIDIDA = [
    (22.2, 50.2, "d_producto"),       # qué se fabrica (desde «Bueno, la idea es…»)
    (50.2, 80.8, "d_versiones"),      # «Comenzamos construyendo una celda sencilla…»
    (80.8, 117.3, "d_equipos"),       # robots, pinza, antorcha, argón y fuente
    (117.3, 157.3, "d_seguridad"),    # «Como elemento de seguridad…»
    (157.3, 194.9, "d_principal"),
    (194.9, 248.9, "d_ciclo"),
    (302.7, 327.4, "d_pedido"),       # producción define el pedido de 12 piezas
    (337.6, 382.8, "d_soldadura"),
    (382.8, 406.3, "d_deposito"),
    (429.6, 449.6, "d_giro"),         # reposo, cordón y giro; después pasa al bobinado
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
        f"[0:a]highpass=f=80,asplit={len(INTRO) + 1}[a0]" + "".join(f"[a{i + 1}]" for i in range(len(INTRO))),
        f"[a0]atrim={INICIO}:{FIN},asetpts=PTS-STARTPTS,afade=t=in:d=0.05,afade=t=out:st={dur - 0.4:.2f}:d=0.4[voz]",
    ]
    # Audio de la portada: pausa, frases separadas por silencios cortos y una cola antes del fundido.
    trozos = [f"anullsrc=r=48000:cl=stereo,atrim=0:{PAUSA_INICIAL}[s0]"]
    for i, (a, b) in enumerate(INTRO):
        trozos.append(f"[a{i + 1}]atrim={a}:{b},asetpts=PTS-STARTPTS,"
                      f"afade=t=in:d=0.02,afade=t=out:st={b - a - 0.03:.2f}:d=0.03[p{i}]")
        silencio = COLA if i == len(INTRO) - 1 else ENTRE_FRASES
        trozos.append(f"anullsrc=r=48000:cl=stereo,atrim=0:{silencio}[s{i + 1}]")
    orden = "[s0]" + "".join(f"[p{i}][s{i + 1}]" for i in range(len(INTRO)))
    trozos.append(f"{orden}concat=n={2 * len(INTRO) + 1}:v=0:a=1[sp]")
    partes += trozos + [
        f"[1:v]fps=30,format=yuv420p,fade=t=out:st={PORTADA - FUNDIDO}:d={FUNDIDO}[portada]",
        f"[2:v]fps=30,format=yuv420p,fade=t=in:d={FUNDIDO}[placa]",
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


def miniatura():
    """Cuadro del video final con un botón de reproducción, para enlazar el video de Drive desde los README."""
    from PIL import Image, ImageDraw
    from graficos import ACENTO, SANS_B, fuente
    t = PORTADA + CUADRO_MINIATURA - INICIO
    cuadro = AQUI / "trabajo" / "cuadro_miniatura.png"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", str(FINAL), "-frames:v", "1", str(cuadro)],
                   check=True)
    im = Image.open(cuadro).convert("RGB").resize((1280, 720), Image.LANCZOS)
    capa = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(capa)
    cx, cy, radio = 640, 360, 90
    d.ellipse((cx - radio, cy - radio, cx + radio, cy + radio), fill=(14, 27, 44, 210), outline=ACENTO, width=6)
    d.polygon([(cx - 30, cy - 48), (cx - 30, cy + 48), (cx + 52, cy)], fill="white")
    minutos, segundos = divmod(round(PORTADA + FIN - INICIO + PLACA), 60)
    texto = f"Ver el video · {minutos}:{segundos:02d}"
    f = fuente(SANS_B, 34)
    ancho = d.textlength(texto, font=f)
    d.rounded_rectangle((cx - ancho / 2 - 24, cy + 118, cx + ancho / 2 + 24, cy + 176), radius=12, fill=(14, 27, 44, 220))
    d.text((cx - ancho / 2, cy + 124), texto, font=f, fill="white")
    Image.alpha_composite(im.convert("RGBA"), capa).convert("RGB").save(MINIATURA, quality=85, optimize=True)
    print(f"{MINIATURA} ({MINIATURA.stat().st_size / 1e3:.0f} kB)")


if __name__ == "__main__":
    if "--miniatura" in sys.argv:
        miniatura()
    elif "--final" in sys.argv:
        render(FINAL, "1920:1080", ["-c:v", "libx264", "-preset", "slow", "-tune", "animation", "-crf", str(CRF),
                                    "-pix_fmt", "yuv420p", "-g", "300"], 96)
        miniatura()
    else:
        render(PREVIA, "960:540", ["-c:v", "libx264", "-preset", "veryfast", "-crf", "28", "-pix_fmt", "yuv420p"], 96)
