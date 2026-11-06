"""Panel de operador de la celda v05.

En la entrega se ejecuta embebido en la estación (Panel_Operador). Para desarrollo:
C:\\RoboDK\\Python-Embedded\\python.exe panel.py [--puerto 20501]

Requiere RoboDK abierto con la v05 y Coordinador_Panel iniciado desde RoboDK. El panel no lo
inicia ni abre RoboDK: solo calcula sensores, lee señales y escribe solicitudes.
"""
import argparse
import sys

from PySide2.QtWidgets import QApplication

from cuentas import Cuentas, ruta_datos
from enlace import Enlace, PUERTOS
from modos_nativos import CAUSAS
from procesador import Procesador
from ventana import Ventana


def crear(ruta=None, puertos=PUERTOS):
    enlace = Enlace(puertos)
    cuentas = Cuentas(ruta or ruta_datos())
    procesador = Procesador(cuentas, enlace.enviar, CAUSAS)
    ventana = Ventana(cuentas, procesador, CAUSAS)
    enlace.estado.connect(ventana.recibir_estado)
    return enlace, cuentas, procesador, ventana


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--puerto", type=int)
    args = parser.parse_args()
    app = QApplication(sys.argv)
    enlace, _, _, ventana = crear(puertos=(args.puerto,) if args.puerto else PUERTOS)
    app.installEventFilter(ventana)
    ventana.show()
    enlace.start()
    codigo = app.exec_()
    enlace.detener()
    sys.exit(codigo)


if __name__ == "__main__":
    main()
