"""Mide el tiempo de un lote ejecutando la simulación, sobre una copia de la v05.

Program.Update ignora los cambios de velocidad dentro del programa: hay que ejecutar y escalar.
A x10 el tiempo medido sale inflado; a x2 es fiel.
"""
import argparse
from pathlib import Path
import shutil
import socket
import sys
import tempfile
import time

sys.path.insert(0, r"C:\RoboDK\Python")
from robodk.robolink import Robolink, ITEM_TYPE_PROGRAM, COLLISION_ON

RAIZ = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--puerto", type=int, default=20500)
    parser.add_argument("--velocidad", type=float, default=2)
    parser.add_argument("--archivo", default=str(RAIZ / "Celda_Soldadura_Estator_Grupo4_v05.rdk"))
    args = parser.parse_args()
    with socket.create_connection(("localhost", args.puerto), timeout=3):
        pass
    r = Robolink(port=args.puerto)
    activa = r.ActiveStation()
    carpeta = Path(tempfile.mkdtemp(prefix="ciclo_"))
    copia = carpeta / "copia.rdk"
    shutil.copy2(args.archivo, copia)
    s = r.AddFile(str(copia))
    r.setActiveStation(s)
    try:
        r.setCollisionActive(COLLISION_ON)
        r.setSimulationSpeed(args.velocidad)
        p = r.Item("Programa_Principal", ITEM_TYPE_PROGRAM)
        ciclos = [r.Item(f"Ciclo_Pieza_{k}", ITEM_TYPE_PROGRAM) for k in range(1, 5)]
        t0 = time.monotonic()
        marcas = {}
        p.RunProgram()
        time.sleep(.1)
        while p.Busy():
            for k, c in enumerate(ciclos, 1):
                if c.Busy():
                    marcas.setdefault(k, time.monotonic() - t0)
            time.sleep(.1)  # Consultar más seguido alarga el tiempo medido.
        total = (time.monotonic() - t0) * args.velocidad
        piezas = [round((marcas[k + 1] - marcas[k]) * args.velocidad, 1) for k in (1, 2, 3)]
        print(f"lote {total:.1f} s | piezas 1 a 3: {piezas} s")
    finally:
        for x in r.ItemList(ITEM_TYPE_PROGRAM):
            if x.Busy():
                x.Stop()
        time.sleep(.2)
        s.Delete()
        r.setActiveStation(activa)
        r.setSimulationSpeed(1)
        shutil.rmtree(carpeta, ignore_errors=True)


if __name__ == "__main__":
    main()
