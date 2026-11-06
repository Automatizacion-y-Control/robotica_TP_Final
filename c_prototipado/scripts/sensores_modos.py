"""Lecturas geométricas para confirmar modos. No mueve elementos ni lanza programas.

La disponibilidad de los equipos y PERMISO_OPERACION son entradas externas.
Esta etapa no implementa detección nativa de vencimiento de una señal congelada.
"""
import argparse
import math
import sys
import time

sys.path.insert(0, r"C:\RoboDK\Python")
from robodk.robolink import Robolink, ITEM_TYPE_ROBOT, ITEM_TYPE_TOOL, ITEM_TYPE_TARGET


class SensoresModos:
    def __init__(self, rdk):
        self.r = rdk
        self.irb = rdk.Item("ABB IRB 1200-7/0.7", ITEM_TYPE_ROBOT)
        self.crb = rdk.Item("ABB CRB 1300-10/1.15", ITEM_TYPE_ROBOT)
        self.cinta = rdk.Item("Cinta_Pasante", ITEM_TYPE_ROBOT)
        self.tcp = rdk.Item("TCP_Pinza", ITEM_TYPE_TOOL)
        self.antorcha = rdk.Item("Antorcha_TIG", ITEM_TYPE_TOOL)
        self.targets = {n: rdk.Item(n, ITEM_TYPE_TARGET) for n in
                        ("Man_Reposo", "Sold_Reposo", "Man_Mantenimiento", "Sold_Mantenimiento",
                         "Serv_Cambio_Tungsteno")}
        self.previa = None
        self.estable_desde = time.monotonic()

    @staticmethod
    def cerca(q, t):
        return len(q) == len(t) and max(abs(a-b) for a,b in zip(q,t)) <= .5

    def actualizar(self):
        q = self.cinta.Joints().list()[0]
        ahora = time.monotonic()
        if self.previa is None or abs(q-self.previa) > .1:
            self.estable_desde = ahora
        self.previa = q
        # Pose real del TCP: base absoluta * cinemática directa * herramienta.
        pose = self.crb.PoseAbs() * self.crb.SolveFK(self.crb.Joints()) * self.antorcha.PoseTool()
        error = self.targets["Serv_Cambio_Tungsteno"].PoseAbs().inv() * pose
        distancia = math.sqrt(sum(v*v for v in error.Pos()))
        coseno = max(-1, min(1, (error[0,0]+error[1,1]+error[2,2]-1)/2))
        angulo = math.degrees(math.acos(coseno))
        sujeta = False
        for k in range(1,5):
            padre = self.r.Item("Estator_"+str(k)).Parent()
            while padre.Valid():
                if padre == self.tcp:
                    sujeta = True
                    break
                padre = padre.Parent()
        datos = {
            "IRB_EN_REPOSO": self.cerca(self.irb.Joints().list(), self.targets["Man_Reposo"].Joints().list()),
            "CRB_EN_REPOSO": self.cerca(self.crb.Joints().list(), self.targets["Sold_Reposo"].Joints().list()),
            "IRB_EN_MANT": self.cerca(self.irb.Joints().list(), self.targets["Man_Mantenimiento"].Joints().list()),
            "CRB_EN_MANT": self.cerca(self.crb.Joints().list(), self.targets["Sold_Mantenimiento"].Joints().list()),
            "CRB_EN_SERVICIO": distancia <= 1 and angulo <= 1,
            "CINTA_DETENIDA": ahora-self.estable_desde >= .2,
            "PIEZA_SUJETA_SENSOR": sujeta,
            "SENSORES_VALIDOS": True,
        }
        for n,v in datos.items():
            self.r.setParam(n, int(v))
        return datos


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--puerto", type=int, default=20500)
    args = parser.parse_args()
    r = Robolink(port=args.puerto)
    assert r.ActiveStation().Name() == "Celda_Soldadura_Estator_Grupo4_v05"
    sensores = SensoresModos(r)
    try:
        while True:
            sensores.actualizar()
            time.sleep(.05)
    finally:
        r.setParam("SENSORES_VALIDOS", 0)


if __name__ == "__main__":
    main()
