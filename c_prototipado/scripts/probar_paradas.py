"""Ensayo de mecanismos de parada sobre una copia descartable de la v05.

No guarda ni modifica el archivo nominal. Las ejecuciones y detenciones son del banco.
"""
import argparse
import json
from pathlib import Path
import shutil
import socket
import sys
import tempfile
import time

sys.path.insert(0, r"C:\RoboDK\Python")
from robodk.robolink import Robolink, ITEM_TYPE_PROGRAM, ITEM_TYPE_ROBOT, COLLISION_ON
from sensores_modos import SensoresModos

RAIZ = Path(__file__).resolve().parent.parent
NOMINAL = RAIZ / "Celda_Soldadura_Estator_Grupo4_v05.rdk"
EQUIPOS = ("ABB IRB 1200-7/0.7", "ABB CRB 1300-10/1.15", "Cinta_Pasante")
VELOCIDAD = 5
RESULTADOS = []


def registrar(nombre, **datos):
    fila = {"prueba": nombre, **datos}
    RESULTADOS.append(fila)
    print(json.dumps(fila, ensure_ascii=False, default=str), flush=True)


class Banco:
    def __init__(self, r, copia):
        self.r = r
        self.copia = copia
        self.s = None

    def __enter__(self):
        self.s = self.r.AddFile(str(self.copia))
        self.r.setActiveStation(self.s)
        self.r.setCollisionActive(COLLISION_ON)
        self.r.setSimulationSpeed(VELOCIDAD)
        self.equipos = [self.r.Item(n, ITEM_TYPE_ROBOT) for n in EQUIPOS]
        return self

    def __exit__(self, *_):
        for p in self.r.ItemList(ITEM_TYPE_PROGRAM):
            if p.Busy():
                p.Stop()
        for e in self.equipos:
            e.Stop()
        self.r.setSimulationSpeed(VELOCIDAD)
        time.sleep(.3)
        self.s.Delete()

    def programa(self, nombre):
        return self.r.Item(nombre, ITEM_TYPE_PROGRAM)

    def valor(self, n):
        try:
            return float(self.r.getParam(n))
        except (TypeError, ValueError):
            return None

    def ocupados(self):
        return [p.Name() for p in self.r.ItemList(ITEM_TYPE_PROGRAM) if p.Busy()]

    def articulaciones(self):
        return [e.Joints().list() for e in self.equipos]

    def esperar(self, condicion, limite=60):
        t = time.monotonic()
        while time.monotonic() - t < limite:
            if condicion():
                return True
            time.sleep(.02)
        return False

    def padre(self, k):
        return self.r.Item(f"Estator_{k}").Parent().Name()

    def en_movimiento(self):
        a = self.articulaciones()
        time.sleep(.05)
        return desplazamiento(a, self.articulaciones()) > .02

    def correr(self, nombre, limite=90):
        p = self.programa(nombre)
        p.RunProgram()
        time.sleep(.2)
        return self.esperar(lambda: not p.Busy(), limite)

    def llevar_a_pieza_sujeta(self):
        p = self.programa("Programa_Principal")
        p.RunProgram()
        assert self.esperar(lambda: self.padre(1) == "TCP_Pinza"), "No tomó la pieza"
        assert self.esperar(self.en_movimiento, 20), "Sin movimiento"
        return p

    def seguir(self, segundos=2.0):
        """Mayor desplazamiento posterior a la orden y momento en que dejó de moverse."""
        inicio = self.articulaciones()
        t0 = time.monotonic()
        ultimo = 0.0
        total = 0.0
        previa = inicio
        while time.monotonic() - t0 < segundos:
            actual = self.articulaciones()
            d = desplazamiento(previa, actual)
            if d > .01:
                ultimo = time.monotonic() - t0
            total = max(total, desplazamiento(inicio, actual))
            previa = actual
            time.sleep(.02)
        return {"desplazamiento_max": round(total, 3), "ultimo_movimiento_s": round(ultimo, 3)}


def desplazamiento(a, b):
    return max(abs(x - y) for p, q in zip(a, b) for x, y in zip(p, q))


def probar_stop(banco_nuevo):
    for nombre, accion in (
        ("Stop al programa principal", lambda b, p: p.Stop()),
        ("Stop a los robots y la cinta", lambda b, p: [e.Stop() for e in b.equipos]),
        ("Stop a todos los programas y equipos", lambda b, p: (
            [x.Stop() for x in b.r.ItemList(ITEM_TYPE_PROGRAM) if x.Busy()],
            [e.Stop() for e in b.equipos])),
    ):
        with banco_nuevo() as b:
            p = b.llevar_a_pieza_sujeta()
            antes = b.ocupados()
            t = time.monotonic()
            accion(b, p)
            llamada = time.monotonic() - t
            datos = b.seguir()
            registrar(nombre, ocupados_antes=antes, ocupados_despues=b.ocupados(),
                      llamada_s=round(llamada, 3), pieza=b.padre(1),
                      arco=b.valor("ARCO_TIG"), colisiones=b.r.Collisions(), **datos)


def probar_pausa(banco_nuevo):
    with banco_nuevo() as b:
        p = b.llevar_a_pieza_sujeta()
        b.r.setSimulationSpeed(.001)
        congelado = b.seguir(1.5)
        ocupados = b.ocupados()
        b.r.setSimulationSpeed(VELOCIDAD)
        retoma = b.seguir(1.5)
        p_termina = b.esperar(lambda: b.padre(1) == "Frame_Banda", 60)
        registrar("Velocidad mínima como pausa", congelado=congelado, ocupados=ocupados,
                  retoma=retoma, deposito_la_pieza=p_termina, colisiones=b.r.Collisions())


def probar_parada_coordinador(banco_nuevo):
    """Detener solo los equipos: ¿el coordinador sigue, se traba o avanza sin movimiento?"""
    with banco_nuevo() as b:
        sensores = SensoresModos(b.r)
        for n in ("PERMISO_OPERACION", "IRB_DISPONIBLE", "CRB_DISPONIBLE", "CINTA_DISPONIBLE"):
            b.r.setParam(n, 1)
        t = time.monotonic()
        while time.monotonic() - t < .6:
            sensores.actualizar()
            time.sleep(.05)
        c = b.programa("Coordinador_Panel")
        c.RunProgram()
        time.sleep(.5)
        sensores.actualizar()
        b.r.setParam("ARRANQUE_ID", 1)

        def tomada():
            sensores.actualizar()
            return b.padre(1) == "TCP_Pinza"
        assert b.esperar(tomada), "No tomó la pieza"
        b.esperar(b.en_movimiento, 20)
        antes = b.ocupados()
        for e in b.equipos:
            e.Stop()
        datos = b.seguir(4)
        registrar("Stop a equipos con el coordinador corriendo", ocupados_antes=antes,
                  ocupados_despues=b.ocupados(), pieza_activa=b.valor("PIEZA_ACTIVA"),
                  auto=b.valor("AUTO_ACTIVO"), completadas=b.valor("PIEZAS_COMPLETADAS"),
                  pieza=b.padre(1), **datos)


def probar_linea(banco_nuevo):
    with banco_nuevo() as b:
        x, y, z = b.r.Item("Estator_1").PoseAbs().Pos()
        tiempos = []
        for _ in range(20):
            t = time.monotonic()
            cruce = b.r.Collision_Line([x, y - 500, z], [x, y + 500, z])
            tiempos.append(time.monotonic() - t)
        libre = b.r.Collision_Line([x, y - 100, z + 1500], [x, y + 100, z + 1500])
        registrar("Collision_Line como sensor", cruza=bool(cruce[0]),
                  objeto=cruce[1].Name() if cruce[0] else None, libre=bool(libre[0]),
                  ms=round(1000 * sum(tiempos) / len(tiempos), 2), ocupados=b.ocupados())


def poses(b):
    return {k: (b.padre(k), [round(v, 2) for v in b.r.Item(f"Estator_{k}").PoseAbs().Pos()])
            for k in range(1, 5)}


def probar_reinicio(banco_nuevo):
    with banco_nuevo() as b:
        b.r.setSimulationSpeed(10)
        inicial = poses(b)
        assert b.correr("Inicio_Celda") and b.correr("Ciclo_Pieza_1", 120)
        parcial = poses(b)
        ok = b.correr("Fin_Lote", 120)
        final = poses(b)
        registrar("Fin_Lote con lote parcial restituye las piezas", termino=ok,
                  iguales=final == inicial, inicial=inicial, parcial=parcial, final=final,
                  eje_cinta=b.equipos[2].Joints().list(), colisiones=b.r.Collisions())

    with banco_nuevo() as b:
        inicial = poses(b)
        p = b.llevar_a_pieza_sujeta()
        p.Stop()
        for x in b.r.ItemList(ITEM_TYPE_PROGRAM):
            if x.Busy():
                x.Stop()
        for e in b.equipos:
            e.Stop()
        time.sleep(.3)
        b.r.setSimulationSpeed(10)
        sujeta = b.padre(1)
        reposo = b.correr("Man_Ir_Reposo", 40)
        col_reposo = b.r.Collisions()
        ok = b.correr("Fin_Lote", 120)
        final = poses(b)
        registrar("Recuperación con pieza en la pinza", pieza_al_detener=sujeta, reposo=reposo,
                  colisiones_reposo=col_reposo, fin_lote=ok, iguales=final == inicial,
                  final=final, colisiones=b.r.Collisions())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--puerto", type=int, default=20500)
    args = parser.parse_args()
    with socket.create_connection(("localhost", args.puerto), timeout=3):
        pass
    r = Robolink(port=args.puerto)
    activa = r.ActiveStation()
    velocidad = r.SimulationSpeed()
    carpeta = Path(tempfile.mkdtemp(prefix="paradas_"))
    copia = carpeta / "copia_v05.rdk"
    shutil.copy2(NOMINAL, copia)
    error = None
    try:
        crear = lambda: Banco(r, copia)
        for prueba in (probar_stop, probar_pausa, probar_parada_coordinador, probar_linea,
                       probar_reinicio):
            try:
                prueba(crear)
            except Exception as e:
                error = f"{prueba.__name__}: {e!r}"
                registrar("ERROR", detalle=error)
    finally:
        r.setActiveStation(activa)
        r.setSimulationSpeed(velocidad)
        shutil.rmtree(carpeta, ignore_errors=True)
        with (RAIZ / "verificaciones" / "paradas_v05.json").open("w", encoding="utf-8", newline="\n") as f:
            json.dump({"version": r.Version(), "error": error, "pruebas": RESULTADOS}, f,
                      ensure_ascii=False, indent=2, default=str)
            f.write("\n")


if __name__ == "__main__":
    main()
