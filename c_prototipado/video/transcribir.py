# Transcripción local (faster-whisper, CPU int8) con tiempos por palabra; mismo formato que Oriana/tools/transcribir_video.py.
import json, sys, time
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
import av, faster_whisper.audio as fwa
from faster_whisper import WhisperModel
_o = av.open
def _abrir(*a, **k):
    k.pop("metadata_errors", None); return _o(*a, **k)
fwa.av.open = _abrir
video, salida = Path(sys.argv[1]), Path(sys.argv[2])
modelo = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")
t0 = time.time()
segs, info = modelo.transcribe(str(video), language="es", word_timestamps=True, vad_filter=False,
                               condition_on_previous_text=False,
                               initial_prompt="RoboDK, MoveJ, MoveL, MoveC, TIG, IRB 1200, CRB 1300, Robotiq, TCP, Frame_Soldadura, Coordinador_Panel, estator.")
datos = {"video": video.name, "modelo": "large-v3-turbo", "duracion": round(info.duration, 2), "segmentos": []}
lineas = []
for s in segs:
    pal = [{"inicio": round(w.start, 2), "fin": round(w.end, 2), "texto": w.word.strip(), "prob": round(w.probability, 2)} for w in (s.words or [])]
    datos["segmentos"].append({"inicio": round(s.start, 2), "fin": round(s.end, 2), "texto": s.text.strip(), "palabras": pal})
    m, x = divmod(s.start, 60); m2, x2 = divmod(s.end, 60)
    lineas.append(f"[{int(m):02d}:{x:05.2f} → {int(m2):02d}:{x2:05.2f}] {s.text.strip()}")
    print(lineas[-1], flush=True)
(salida / "transcripcion.json").write_text(json.dumps(datos, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
(salida / "transcripcion.txt").write_text("\n".join(lineas) + "\n", encoding="utf-8", newline="\n")
print(f"listo en {time.time()-t0:.0f} s", flush=True)
