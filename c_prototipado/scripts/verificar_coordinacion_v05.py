"""Banco de integración del coordinador nativo v05: inyecta señales y observa.

Las ejecuciones API son exclusivas del banco, no del panel de operación.
Reabre el archivo nominal al terminar; nunca guarda el estado de los ensayos.
"""
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, r"C:\RoboDK\Python")
from robodk.robolink import Robolink, ITEM_TYPE_PROGRAM, COLLISION_ON
from sensores_modos import SensoresModos


def main():
    puerto = int(sys.argv[sys.argv.index("--puerto") + 1]) if "--puerto" in sys.argv else 20500
    r = Robolink(port=puerto)
    raiz = Path(__file__).resolve().parent.parent
    estacion = r.ActiveStation()
    assert estacion.Name() == "Celda_Soldadura_Estator_Grupo4_v05"
    p = r.Item("Programa_Principal", ITEM_TYPE_PROGRAM)
    sensores = SensoresModos(r)
    pruebas = []
    inicio = time.monotonic()

    def valor(n):
        return float(r.getParam(n))

    def esperar(condicion, limite=40):
        t = time.monotonic()
        while time.monotonic() - t < limite:
            sensores.actualizar()
            if r.Collisions():
                raise AssertionError("Colisión en prueba de coordinación")
            if condicion():
                return
            time.sleep(.025)
        raise AssertionError("Tiempo máximo de espera: " + str(
            {n: valor(n) for n in ("ARRANQUE_ID", "ARRANQUE_ACK", "CAUSA_RECHAZO", "AUTO_ACTIVO",
                                   "ESTADO_CONTROL", "PIEZA_ACTIVA", "PROXIMA_PIEZA", "MODO_CAUSA",
                                   "MODO_CONFIRMADO", "IRB_EN_REPOSO", "CRB_EN_REPOSO",
                                   "CINTA_DETENIDA", "PIEZA_SUJETA_SENSOR")}))

    def registrar(nombre, **datos):
        fila = {"prueba": nombre, **datos}
        pruebas.append(fila)
        print(json.dumps(fila, ensure_ascii=False), flush=True)

    solicitudes_modo = 0

    def pedir_modo(modo):
        nonlocal solicitudes_modo
        solicitudes_modo += 1
        r.setParam("MODO_SOLICITADO", modo)
        r.setParam("MODO_ID", solicitudes_modo)
        esperar(lambda: valor("MODO_ACK") == solicitudes_modo, limite=70)

    def intervenir(modo):
        pedir_modo(modo)
        esperar(lambda: valor("MODO_CONFIRMADO") == modo and valor("MODO_EN_TRANSICION") == 0)
        r.setParam("CONF_RESTITUCION", 1)
        pedir_modo(0)
        esperar(lambda: valor("MODO_CONFIRMADO") == 0 and valor("MODO_EN_TRANSICION") == 0)
        assert valor("AUTO_ACTIVO") == 0

    try:
        r.setCollisionActive(COLLISION_ON)
        r.setSimulationSpeed(10)
        for n in ("IRB_DISPONIBLE", "CRB_DISPONIBLE", "CINTA_DISPONIBLE"):
            r.setParam(n, 1)
        esperar(lambda: valor("CINTA_DETENIDA") == 1)
        p.RunProgram()
        time.sleep(.2)
        r.setParam("ARRANQUE_ID", 1)
        esperar(lambda: valor("ARRANQUE_ACK") == 1)
        assert valor("AUTO_ACTIVO") == 0 and valor("CAUSA_RECHAZO") == 1
        registrar("Arranque sin permiso rechazado", causa=1, siguiente=valor("PROXIMA_PIEZA"))
        r.setParam("PERMISO_OPERACION", 1)
        time.sleep(.3)
        assert valor("AUTO_ACTIVO") == 0
        registrar("Restaurar permiso no arranca", auto=valor("AUTO_ACTIVO"))

        # Parar durante soldadura, toma de la siguiente pieza y cuarta pieza.
        for orden, pieza, fase in ((2, 1, "soldadura"), (3, 2, "toma"), (4, 4, "soldadura"),
                                   (5, 4, "segundo lote")):
            r.setParam("ARRANQUE_ID", orden)
            if orden == 4:
                # Las solicitudes inválidas se atienden entre piezas y no detienen el lote.
                esperar(lambda: valor("PIEZA_ACTIVA") == 3)
                pedir_modo(99)
                assert valor("AUTO_ACTIVO") == 1 and valor("MODO_RESULTADO") == 2
                assert valor("MODO_CAUSA") == 11
                registrar("Modo desconocido no detiene producción", causa=11)
            if orden == 5:
                esperar(lambda: valor("PIEZA_ACTIVA") == 1, limite=70)
                pedir_modo(0)
                assert valor("AUTO_ACTIVO") == 1 and valor("MODO_RESULTADO") == 2
                assert valor("MODO_CAUSA") == 9
                registrar("Regreso sin modo activo no detiene producción", causa=9)
            esperar(lambda: valor("PIEZA_ACTIVA") == pieza and
                    (valor("ARCO_TIG") == 1 if fase != "toma" else
                     r.Item("Estator_2").Parent().Name() == "TCP_Pinza"), limite=70)
            if fase == "segundo lote":
                pedir_modo(1)
                esperar(lambda: valor("AUTO_ACTIVO") == 0)
                assert valor("MODO_RESULTADO") == 3
            else:
                r.setParam("PARADA_ID", orden)
                esperar(lambda: valor("PARADA_ACK") == orden and valor("AUTO_ACTIVO") == 0)
            assert valor("PROXIMA_PIEZA") == pieza + 1
            assert valor("PIEZA_ACTIVA") == 0 and valor("ARCO_TIG") == 0
            assert all(r.Item("Estator_" + str(k)).Parent().Name() != "TCP_Pinza" for k in range(1,5))
            registrar("Parada durante " + fase, pieza=pieza, siguiente=valor("PROXIMA_PIEZA"),
                      completadas=valor("PIEZAS_COMPLETADAS"), lotes=valor("LOTES_COMPLETADOS"))
            antes = valor("PIEZAS_COMPLETADAS")
            time.sleep(.25)
            assert valor("PIEZAS_COMPLETADAS") == antes
            if orden == 3:
                # Lote parcial real: faltan las piezas 3 y 4; la fase siguiente debe retomarlas.
                intervenir(2)
                assert valor("PROXIMA_PIEZA") == 3 and valor("PIEZAS_COMPLETADAS") == 2
                assert valor("LOTES_COMPLETADOS") == 0
                registrar("Mantenimiento con lote parcial conserva el índice", siguiente=3,
                          completadas=2)
        assert valor("PIEZAS_COMPLETADAS") == 8
        assert valor("LOTES_COMPLETADOS") == 1
        registrar("Dos lotes soldados sin repetir piezas", completadas=8,
                  fin_segundo_lote_diferido=True, colisiones=0)
        intervenir(1)
        assert valor("PROXIMA_PIEZA") == 5 and valor("PIEZAS_COMPLETADAS") == 8
        registrar("Mantenimiento con fin de lote pendiente conserva el estado", siguiente=5,
                  completadas=8, solicitud_desde_auto_requiere_repeticion=True)

        r.setParam("ARRANQUE_ID", 6)
        esperar(lambda: valor("LOTES_COMPLETADOS") == 2 and valor("PIEZA_ACTIVA") == 1, limite=70)
        registrar("Arranque posterior ejecuta el fin de lote diferido", lotes=2)

        # La falla se atiende entre piezas y deja la intervención sin movimiento como salida.
        r.setParam("CRB_DISPONIBLE", 0)
        esperar(lambda: valor("AUTO_ACTIVO") == 0 and valor("ESTADO_CONTROL") == 3, limite=70)
        assert valor("PROXIMA_PIEZA") == 2 and valor("PIEZAS_COMPLETADAS") == 9
        pedir_modo(6)
        esperar(lambda: valor("MODO_CONFIRMADO") == 6)
        r.setParam("CONF_RESTITUCION", 1)
        pedir_modo(0)
        assert valor("MODO_CAUSA") == 7 and valor("MODO_CONFIRMADO") == 6
        r.setParam("CRB_DISPONIBLE", 1)
        pedir_modo(0)
        esperar(lambda: valor("MODO_CONFIRMADO") == 0 and valor("MODO_EN_TRANSICION") == 0)
        assert valor("AUTO_ACTIVO") == 0 and valor("PROXIMA_PIEZA") == 2
        registrar("Falla en producción, correctivo y retorno", siguiente=2, completadas=9)
    finally:
        r.setParam("COORDINADOR_ACTIVO", 0)
        r.setParam("SENSORES_VALIDOS", 0)
        time.sleep(.25)
        if p.Busy():
            p.Stop()
        for sub in r.ItemList(ITEM_TYPE_PROGRAM):
            if sub.Busy():
                sub.Stop()
        resultado = {"version": r.Version(), "segundos_reales": time.monotonic()-inicio,
                     "pruebas": pruebas}
        with (raiz / "verificaciones" / "coordinacion_v05.json").open("w", encoding="utf-8", newline="\n") as f:
            json.dump(resultado, f, ensure_ascii=False, indent=2)
            f.write("\n")
        estacion.Delete()
        s = r.AddFile(str(raiz / "Celda_Soldadura_Estator_Grupo4_v05.rdk"))
        r.setActiveStation(s)
        r.setSimulationSpeed(1)


if __name__ == "__main__":
    main()
