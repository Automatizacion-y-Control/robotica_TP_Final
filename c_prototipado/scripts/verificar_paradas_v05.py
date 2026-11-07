"""Parada inmediata y recuperación en cada fase del ciclo, sobre una copia de la v05.

Inyecta señales y aplica la misma detención que el panel. Reiniciar el coordinador desde aquí
reemplaza al doble clic de quien opera la celda.
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
EQUIPOS = ("ABB IRB 1200-7/0.7", "ABB CRB 1300-10/1.15", "Cinta_Pasante", "Pinza_2F85")
Y_NORMAL, Y_RETRABAJO = -560.0, -620.0
VELOCIDAD = 5  # Con el perfil rápido, a x10 las fases más cortas duran menos que una lectura.
RESULTADOS = []


def registrar(nombre, **datos):
    fila = {"prueba": nombre, **datos}
    RESULTADOS.append(fila)
    print(json.dumps(fila, ensure_ascii=False, default=str), flush=True)


class Celda:
    def __init__(self, r, copia):
        self.r = r
        self.s = r.AddFile(str(copia))
        r.setActiveStation(self.s)
        r.setCollisionActive(COLLISION_ON)
        r.setSimulationSpeed(VELOCIDAD)
        self.sensores = SensoresModos(r)
        self.coordinador = r.Item("Coordinador_Panel", ITEM_TYPE_PROGRAM)
        for n in ("PERMISO_OPERACION", "IRB_DISPONIBLE", "CRB_DISPONIBLE", "CINTA_DISPONIBLE"):
            r.setParam(n, 1)
        self.esperar(lambda: self.v("CINTA_DETENIDA") == 1, "cinta detenida", 5)
        self.coordinador.RunProgram()
        self.sensores.actualizar()
        self.ids = 0

    def v(self, n):
        return float(self.r.getParam(n))

    def esperar(self, condicion, que, limite=60):
        t = time.monotonic()
        lectura = 0.0
        while time.monotonic() - t < limite:
            # Consultar muy seguido frena la simulación: RoboDK atiende la API en el mismo ciclo.
            if time.monotonic() - lectura > .25:
                self.sensores.actualizar()
                lectura = time.monotonic()
                if self.r.Collisions():
                    pares = [(a.Name(), b.Name()) for a, b, *_ in self.r.CollisionPairs()]
                    raise AssertionError(f"Colisión esperando {que}: {pares}")
            if condicion():
                return
            time.sleep(.03)
        estado = {n: self.v(n) for n in ("FASE_PIEZA", "PIEZA_ACTIVA", "AUTO_ACTIVO", "ARCO_TIG",
                                         "PIEZA_PRESENTADA", "SOLDADURA_TERMINADA", "CAUSA_RECHAZO",
                                         "RECUP_PENDIENTE")}
        ocupados = [p.Name() for p in self.r.ItemList(ITEM_TYPE_PROGRAM) if p.Busy()]
        crb = self.r.Item(EQUIPOS[1], ITEM_TYPE_ROBOT)
        q0 = crb.Joints().list()
        time.sleep(1)
        movimiento = max(abs(a - b) for a, b in zip(q0, crb.Joints().list()))
        sold = self.r.Item("Sold_Par_Cordones", ITEM_TYPE_PROGRAM)
        instruccion = sold.InstructionSelect(-1)
        detalle = sold.Instruction(instruccion)[0] if instruccion >= 0 else None
        pares = [(a.Name(), b.Name()) for a, b, *_ in self.r.CollisionPairs()] if self.r.Collisions() else []
        raise AssertionError(f"Sin {que}: {ocupados} crb_se_mueve={movimiento:.2f} "
                             f"crb_busy={crb.Busy()} instruccion={instruccion}:{detalle} colisiones={pares} "
                             f"velocidad={self.r.SimulationSpeed()} {estado}")

    def arrancar(self):
        self.ids += 1
        self.r.setParam("ARRANQUE_ID", self.ids)

    def parar(self, causa=1):
        """Lo mismo que hace el enlace del panel."""
        r = self.r
        for p in r.ItemList(ITEM_TYPE_PROGRAM):
            if p.Busy():
                p.Stop()
        for n in EQUIPOS:
            r.Item(n, ITEM_TYPE_ROBOT).Stop()
        r.setParam("ARCO_TIG", 0)
        r.setParam("PARO_CAUSA", causa)

    def instruccion(self):
        for n in ("Sold_Retirar", "Sold_Ir_Reposo", "Sold_Par_Cordones"):
            p = self.r.Item(n, ITEM_TYPE_PROGRAM)
            if p.Busy():
                return n
        return None

    def padre(self, k):
        return self.r.Item(f"Estator_{k}").Parent().Name()

    def y(self, k):
        return self.r.Item(f"Estator_{k}").PoseAbs().Pos()[1]

    def cerrar(self):
        for p in self.r.ItemList(ITEM_TYPE_PROGRAM):
            if p.Busy():
                p.Stop()
        time.sleep(.2)
        self.s.Delete()


def probar_fase(r, copia, fase):
    """Pieza 2, con el lote avanzado. La fase 8 solo existe en la pieza 4, antes del fin de lote."""
    pieza = 4 if fase == 8 else 2
    c = Celda(r, copia)
    try:
        c.arrancar()
        c.esperar(lambda: c.v("PIEZA_ACTIVA") == pieza and c.v("FASE_PIEZA") == fase and
                  (fase not in (4, 6) or c.v("ARCO_TIG") == 1), f"fase {fase}", 120)
        c.parar()
        fase_real = c.v("FASE_PIEZA")
        time.sleep(.3)
        c.sensores.actualizar()
        sujeta = c.v("PIEZA_SUJETA_SENSOR")
        assert c.v("ARCO_TIG") == 0
        assert not [p.Name() for p in r.ItemList(ITEM_TYPE_PROGRAM) if p.Busy()]
        c.r.setParam("PARO_CAUSA", 0)
        c.coordinador.RunProgram()
        c.esperar(lambda: c.v("RECUP_PENDIENTE") == 1, "recuperación pendiente", 5)
        assert c.v("AUTO_ACTIVO") == 0
        c.arrancar()
        c.esperar(lambda: c.v("ARRANQUE_ACK") == c.ids, "acuse de arranque", 5)
        assert c.v("CAUSA_RECHAZO") == 16 and c.v("AUTO_ACTIVO") == 0
        c.r.setParam("RECUPERAR_ID", 1)
        c.esperar(lambda: c.v("RECUPERAR_ACK") == 1 and c.v("RECUP_PENDIENTE") == 0, "recuperación", 150)
        assert c.v("CAUSA_RECHAZO") == 0, c.v("CAUSA_RECHAZO")
        c.esperar(lambda: c.v("IRB_EN_REPOSO") == 1 and c.v("CRB_EN_REPOSO") == 1, "reposo", 10)
        retrabajo = c.v("PIEZAS_RETRABAJO")
        esperado = 1 if fase_real in (4, 6) else 0
        assert retrabajo == esperado, retrabajo
        resuelta = fase >= 3
        siguiente = pieza + 1 if resuelta else pieza
        assert c.v("PROXIMA_PIEZA") == siguiente, c.v("PROXIMA_PIEZA")
        y = c.y(pieza)
        if resuelta:
            assert abs(y - (Y_RETRABAJO if esperado else Y_NORMAL)) < 1, y
        # El lote debe poder seguir hasta el final con la pieza corrida en la banda.
        c.arrancar()
        # PROXIMA_PIEZA se escribe antes que el contador: hay que esperar el contador.
        c.esperar(lambda: c.v("PIEZAS_COMPLETADAS") == 4, "fin de las piezas", 240)
        c.esperar(lambda: c.v("LOTES_COMPLETADOS") == 1, "fin de lote", 120)
        registrar("Parada y recuperación", fase=fase_real, pieza_en_pinza=bool(sujeta), retrabajo=retrabajo,
                  y_pieza=round(y, 1), siguiente=siguiente, lote_completo=True, colisiones=0)
    finally:
        c.cerrar()


def probar_corte(r, copia, fase, demora):
    """Corta a distintos tiempos dentro de la soldadura: el choque depende del punto del corte."""
    c = Celda(r, copia)
    try:
        c.arrancar()
        c.esperar(lambda: c.v("PIEZA_ACTIVA") == 2 and c.v("FASE_PIEZA") == fase, f"fase {fase}", 120)
        time.sleep(demora)
        c.parar()
        fase_real = c.v("FASE_PIEZA")
        arco = c.v("ARCO_TIG")
        time.sleep(.3)
        c.r.setParam("PARO_CAUSA", 0)
        c.coordinador.RunProgram()
        c.esperar(lambda: c.v("RECUP_PENDIENTE") == 1, "recuperación pendiente", 5)
        c.r.setParam("RECUPERAR_ID", 1)

        def termino():
            # RoboDK frena todo ante una colisión: el coordinador deja de correr.
            assert c.coordinador.Busy(), f"Colisión al recuperar: coordinador detenido, instr {c.instruccion()}"
            return c.v("RECUP_PENDIENTE") == 0
        c.esperar(termino, "recuperación", 120)
        assert c.v("PIEZA_ACTIVA") == 0 and c.v("PROXIMA_PIEZA") == 3
        registrar("Corte en la soldadura", fase=fase_real, demora=demora, y=round(c.y(2), 1),
                  retrabajo=c.v("PIEZAS_RETRABAJO"), colisiones=0)
    finally:
        c.cerrar()


def probar_pedido(r, copia):
    """Objetivo de dos piezas buenas con una de retrabajo: se fabrican tres."""
    c = Celda(r, copia)
    try:
        inicial = {k: [round(v, 1) for v in r.Item(f"Estator_{k}").PoseAbs().Pos()] for k in range(1, 5)}
        r.setParam("OBJETIVO_PIEZAS", 2)
        c.arrancar()
        c.esperar(lambda: c.v("PIEZA_ACTIVA") == 2 and c.v("ARCO_TIG") == 1, "soldadura", 150)
        c.parar()
        assert c.v("FASE_PIEZA") in (4, 6)
        r.setParam("PARO_CAUSA", 0)
        c.coordinador.RunProgram()
        c.esperar(lambda: c.v("RECUP_PENDIENTE") == 1, "recuperación pendiente", 5)
        r.setParam("RECUPERAR_ID", 1)
        c.esperar(lambda: c.v("RECUP_PENDIENTE") == 0, "recuperación", 150)
        assert c.v("PIEZAS_RETRABAJO") == 1 and c.v("PIEZAS_COMPLETADAS") == 2
        c.arrancar()
        c.esperar(lambda: c.v("PEDIDOS_TERMINADOS") == 1, "pedido terminado", 200)
        assert c.v("ESTADO_CONTROL") == 9 and c.v("AUTO_ACTIVO") == 0 and c.v("PROXIMA_PIEZA") == 1
        assert c.v("PIEZAS_COMPLETADAS") == 0 and c.v("PIEZAS_RETRABAJO") == 0
        final = {k: [round(v, 1) for v in r.Item(f"Estator_{k}").PoseAbs().Pos()] for k in range(1, 5)}
        assert final == inicial, final
        registrar("Pedido de 2 buenas con 1 retrabajo: se detiene, repone y queda en cero", fabricadas=3)

        c.arrancar()
        c.esperar(lambda: c.v("PIEZA_ACTIVA") == 1, "nueva orden", 30)
        r.setParam("PARADA_ID", 90)
        c.esperar(lambda: c.v("PARADA_ACK") == 90 and c.v("AUTO_ACTIVO") == 0, "parada", 90)
        assert c.v("PIEZAS_COMPLETADAS") == 1
        c.esperar(lambda: c.v("IRB_EN_REPOSO") == 1 and c.v("CRB_EN_REPOSO") == 1, "reposo", 10)
        r.setParam("REINICIAR_ID", 1)
        c.esperar(lambda: c.v("REINICIAR_ACK") == 1 and c.v("PIEZAS_COMPLETADAS") == 0, "reinicio", 90)
        assert c.v("CAUSA_RECHAZO") == 0 and c.v("PROXIMA_PIEZA") == 1
        final = {k: [round(v, 1) for v in r.Item(f"Estator_{k}").PoseAbs().Pos()] for k in range(1, 5)}
        assert final == inicial, final
        registrar("Reinicio manual con lote parcial: piezas en su lugar y contadores en cero")
    finally:
        c.cerrar()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--puerto", type=int, default=20500)
    parser.add_argument("--fases", default="1,2,3,4,5,6,7,8")
    parser.add_argument("--sin-pedido", dest="pedido", action="store_false")
    parser.add_argument("--cortes", action="store_true")
    args = parser.parse_args()
    with socket.create_connection(("localhost", args.puerto), timeout=3):
        pass
    r = Robolink(port=args.puerto)
    activa = r.ActiveStation()
    carpeta = Path(tempfile.mkdtemp(prefix="paradas_"))
    copia = carpeta / "copia_v05.rdk"
    shutil.copy2(NOMINAL, copia)
    fallos = []
    try:
        if args.pedido:
            try:
                probar_pedido(r, copia)
            except AssertionError as e:
                fallos.append({"prueba": "pedido", "error": str(e)[:700]})
                registrar("FALLA", prueba="pedido", error=str(e)[:700])
        if args.cortes:
            for fase in (4, 6):
                for demora in (.3, 1.0, 1.8, 2.6, 3.4, 4.2, 5.0):
                    try:
                        probar_corte(r, copia, fase, demora)
                    except AssertionError as e:
                        fallos.append({"fase": fase, "demora": demora, "error": str(e)[:400]})
                        registrar("FALLA", fase=fase, demora=demora, error=str(e)[:400])
        for fase in (int(f) for f in args.fases.split(",") if f):
            try:
                probar_fase(r, copia, fase)
            except AssertionError as e:
                fallos.append({"fase": fase, "error": str(e)[:700]})
                registrar("FALLA", fase=fase, error=str(e)[:700])
    finally:
        r.setActiveStation(activa)
        r.setSimulationSpeed(1)
        shutil.rmtree(carpeta, ignore_errors=True)
        with (RAIZ / "verificaciones" / "recuperacion_v05.json").open("w", encoding="utf-8", newline="\n") as f:
            json.dump({"version": r.Version(), "exito": not fallos, "pruebas": RESULTADOS}, f,
                      ensure_ascii=False, indent=2, default=str)
            f.write("\n")


if __name__ == "__main__":
    main()
