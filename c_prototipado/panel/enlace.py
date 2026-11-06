"""Único hilo que habla con RoboDK: calcula sensores, lee señales y escribe solicitudes.

Solo usa setParam y lecturas. Las órdenes pendientes se descartan al perder la conexión:
no se reenvían al reconectar.
"""
import os
from pathlib import Path
import queue
import socket
import sys
import time

from PySide2.QtCore import QThread, Signal

sys.path.insert(0, r"C:\RoboDK\Python")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from robodk.robolink import Robolink, ITEM_TYPE_PROGRAM
from sensores_modos import SensoresModos

ESTACION = "Celda_Soldadura_Estator_Grupo4_v05"
COORDINADOR = "Coordinador_Panel"
PERIODO_S = 0.1
REINTENTO_S = 1.0
# RoboDK informa su puerto a los programas que ejecuta.
PUERTOS = ((int(os.environ["ROBODK_API_PORT"]),) if os.environ.get("ROBODK_API_PORT")
           else (20500, 20501))
SENALES = (
    "AUTO_ACTIVO", "ESTADO_CONTROL", "CAUSA_RECHAZO", "PROXIMA_PIEZA", "PIEZA_ACTIVA",
    "PIEZAS_COMPLETADAS", "LOTES_COMPLETADOS", "ARRANQUE_ACK", "PARADA_ACK", "PARADA_ID",
    "ARCO_TIG", "MODO_ACK", "MODO_CONFIRMADO", "MODO_EN_TRANSICION", "MODO_RESULTADO",
    "MODO_CAUSA", "PERMISO_OPERACION", "IRB_DISPONIBLE", "CRB_DISPONIBLE", "CINTA_DISPONIBLE",
    "SENSORES_VALIDOS", "IRB_EN_REPOSO", "CRB_EN_REPOSO", "IRB_EN_MANT", "CRB_EN_MANT",
    "CRB_EN_SERVICIO", "CINTA_DETENIDA", "PIEZA_SUJETA_SENSOR",
)


class RobolinkSinArranque(Robolink):
    """Robolink lanza RoboDK si no halla servidor; el panel nunca debe abrirlo por su cuenta."""

    def Connect(self):
        self.PORT = self.PORT_START
        self.NewLink()
        return 1


def puerto_abierto(puerto):
    with socket.socket() as s:
        s.settimeout(0.3)
        return s.connect_ex(("127.0.0.1", puerto)) == 0


def numero(valor):
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


class Enlace(QThread):
    estado = Signal(dict)

    def __init__(self, puertos=PUERTOS, parent=None):
        super().__init__(parent)
        self.puertos = puertos
        self.ordenes = queue.Queue()
        self.activo = True
        self.rdk = None
        self.puerto = None
        self.sensores = None
        self.estacion = None
        self.principal = None

    def enviar(self, orden):
        self.ordenes.put(orden)

    def detener(self):
        self.activo = False
        self.wait(3000)

    def _descartar_ordenes(self):
        while not self.ordenes.empty():
            self.ordenes.get_nowait()

    def _desconectar(self):
        self.rdk = self.sensores = self.estacion = self.principal = None
        self.puerto = None
        self._descartar_ordenes()

    def _conectar(self):
        for puerto in self.puertos:
            if puerto_abierto(puerto):
                self.rdk = RobolinkSinArranque(port=puerto)
                self.puerto = puerto
                return True
        return False

    def _preparar_estacion(self):
        """Devuelve True si la estación activa es la v05; rehace los ítems si fue reabierta."""
        activa = self.rdk.ActiveStation()
        if activa.Name() != ESTACION:
            self.sensores = self.estacion = self.principal = None
            self._descartar_ordenes()
            return False
        if self.estacion != activa or self.sensores is None:
            self.estacion = activa
            self.sensores = SensoresModos(self.rdk)
            self.principal = self.rdk.Item(COORDINADOR, ITEM_TYPE_PROGRAM)
        return True

    def _escribir(self, orden):
        r = self.rdk
        if orden[0] == "id":
            senal = orden[1]
            r.setParam(senal, int(numero(r.getParam(senal)) or 0) + 1)
        elif orden[0] == "modo":
            _, modo, restitucion = orden
            if restitucion:
                r.setParam("CONF_RESTITUCION", 1)
            r.setParam("MODO_SOLICITADO", modo)
            r.setParam("MODO_ID", int(numero(r.getParam("MODO_ID")) or 0) + 1)
        elif orden[0] == "entrada":
            r.setParam(orden[1], orden[2])

    def _ciclo(self):
        if not self._preparar_estacion():
            return {"conectado": True, "estacion_ok": False, "coordinador": False,
                    "puerto": self.puerto, "senales": {}}
        self.sensores.actualizar()
        while not self.ordenes.empty():
            self._escribir(self.ordenes.get_nowait())
        return {"conectado": True, "estacion_ok": True, "puerto": self.puerto,
                "coordinador": bool(self.principal.Busy()),
                "senales": {n: numero(self.rdk.getParam(n)) for n in SENALES}}

    def run(self):
        while self.activo:
            try:
                if self.rdk is None and not self._conectar():
                    self.estado.emit({"conectado": False, "senales": {}})
                    time.sleep(REINTENTO_S)
                    continue
                self.estado.emit(self._ciclo())
                time.sleep(PERIODO_S)
            except Exception:
                # Caída de RoboDK o estación cerrada a mitad de una consulta.
                self._desconectar()
                self.estado.emit({"conectado": False, "senales": {}})
                time.sleep(REINTENTO_S)
        try:
            if self.sensores is not None:
                # Cerrar el panel en producción encola una parada que debe salir antes de terminar.
                while not self.ordenes.empty():
                    self._escribir(self.ordenes.get_nowait())
                self.rdk.setParam("SENSORES_VALIDOS", 0)
        except Exception:
            pass
