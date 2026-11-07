"""Imagen del proceso: planta de la celda con los dispositivos que se pueden accionar."""
from PySide2.QtCore import QPointF, QRectF, Qt, Signal
from PySide2.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PySide2.QtWidgets import QSizePolicy, QWidget

# Planta en mm, en Frame_Celda. Son valores de parametros_celda.py: el panel embebido no lo tiene.
X_MIN, X_MAX, Y_MIN, Y_MAX = -2150.0, 2200.0, -1250.0, 2150.0
CERRAMIENTO = (-1300.0, 850.0, -960.0, 1850.0)
BANDA = (-2000.0, 2100.0, -860.0, -260.0)
PUERTA_Y = (1000.0, 1700.0)
CORTINA_Y = (-960.0, -120.0)
IRB = (0.0, 0.0)
CRB = (0.0, 1150.0)
PULSADORES = ((930.0, 920.0), (-1420.0, -1060.0), (970.0, -1060.0), (1150.0, 250.0))

FONDO = QColor("#f8f9fa")
LINEA = QColor("#3a4651")
NORMAL = QColor("#1d6b45")
ALERTA = QColor("#b3261e")
BANDA_C = QColor("#55606a")
ROBOT = QColor("#dfe5ea")


class Sinoptico(QWidget):
    accionado = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.senales = {}
        self.zonas = {}
        self.setMinimumSize(420, 340)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setCursor(Qt.PointingHandCursor)

    def actualizar(self, senales):
        self.senales = senales
        self.update()

    def _escala(self):
        return min(self.width() / (X_MAX - X_MIN), self.height() / (Y_MAX - Y_MIN))

    def _punto(self, x, y):
        e = self._escala()
        margen_x = (self.width() - (X_MAX - X_MIN) * e) / 2
        margen_y = (self.height() - (Y_MAX - Y_MIN) * e) / 2
        return QPointF(margen_x + (x - X_MIN) * e, margen_y + (Y_MAX - y) * e)

    def _rect(self, x0, x1, y0, y1):
        return QRectF(self._punto(x0, y1), self._punto(x1, y0))

    def _activa(self, senal):
        return self.senales.get(senal) == 1

    def _texto(self, p, x, y, texto, color=LINEA, negrita=False):
        fuente = QFont("Segoe UI", 8)
        fuente.setBold(negrita)
        p.setFont(fuente)
        p.setPen(color)
        punto = self._punto(x, y)
        p.drawText(QRectF(punto.x() - 90, punto.y() - 10, 180, 20), Qt.AlignCenter, texto)

    def _cortina(self, p, nombre, senal, x, etiqueta, texto_x):
        cortada = self._activa(senal)
        color = ALERTA if cortada else NORMAL
        p.setPen(QPen(color, 4, Qt.DashLine))
        p.drawLine(self._punto(x, CORTINA_Y[0]), self._punto(x, CORTINA_Y[1]))
        self._texto(p, texto_x, CORTINA_Y[1] + 120, f"{etiqueta}: {'cortada' if cortada else 'libre'}", color, True)
        self.zonas[nombre] = self._rect(min(x, texto_x) - 500, max(x, texto_x) + 500 if texto_x > x else x + 170,
                                        CORTINA_Y[0], CORTINA_Y[1] + 240)

    def _robot(self, p, posicion, nombre, reposo, mantenimiento):
        centro = self._punto(*posicion)
        radio = 330 * self._escala()
        p.setPen(QPen(LINEA, 1.5))
        p.setBrush(QBrush(ROBOT))
        p.drawEllipse(centro, radio, radio)
        estado = "reposo" if self._activa(reposo) else "mantenimiento" if self._activa(mantenimiento) else "en ciclo"
        self._texto(p, posicion[0], posicion[1] + 50, nombre, LINEA, True)
        self._texto(p, posicion[0], posicion[1] - 90, estado)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), FONDO)
        self.zonas = {}
        x0, x1, y0, y1 = CERRAMIENTO
        p.setPen(QPen(LINEA, 2))
        p.setBrush(Qt.NoBrush)
        p.drawRect(self._rect(x0, x1, y0, y1))
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(BANDA_C))
        p.drawRect(self._rect(*BANDA))
        self._texto(p, -500, -560, "Cinta", QColor("#ffffff"), True)

        self._robot(p, IRB, "IRB 1200", "IRB_EN_REPOSO", "IRB_EN_MANT")
        self._robot(p, CRB, "CRB 1300", "CRB_EN_REPOSO", "CRB_EN_MANT")
        if self._activa("ARCO_TIG"):
            self._texto(p, 500, 650, "ARCO ENCENDIDO", ALERTA, True)

        self._cortina(p, "cortina_entrada", "CORTINA_ENTRADA_SIM", x0, "Cortina entrada", x0 - 620)
        self._cortina(p, "cortina_salida", "CORTINA_SALIDA_SIM", x1, "Cortina salida", x1 + 620)

        abierta = self._activa("PUERTA_ABIERTA_SIM")
        color = ALERTA if abierta else NORMAL
        p.setPen(QPen(color, 6))
        bisagra = self._punto(x1, PUERTA_Y[0])
        if abierta:
            p.drawLine(bisagra, self._punto(x1 + 620, PUERTA_Y[0] + 320))
        else:
            p.drawLine(bisagra, self._punto(x1, PUERTA_Y[1]))
        self._texto(p, x1 + 620, PUERTA_Y[1] + 110, f"Puerta: {'abierta' if abierta else 'cerrada'}", color, True)
        self.zonas["puerta"] = self._rect(x1 - 150, x1 + 800, PUERTA_Y[0] - 100, PUERTA_Y[1] + 200)

        pulsado = self._activa("EMERGENCIA_SIM")
        radio = 75 * self._escala() + 5
        for i, posicion in enumerate(PULSADORES):
            centro = self._punto(*posicion)
            p.setPen(QPen(QColor("#d9a400"), 3))
            p.setBrush(QBrush(ALERTA if pulsado else QColor("#d8453c")))
            p.drawEllipse(centro, radio, radio)
            self.zonas[f"emergencia_{i}"] = QRectF(centro.x() - radio - 4, centro.y() - radio - 4,
                                                   2 * radio + 8, 2 * radio + 8)
        p.end()

    def mousePressEvent(self, evento):
        # Las zonas de los pulsadores tienen prioridad: están dentro de otras.
        for nombre, zona in sorted(self.zonas.items(), key=lambda z: not z[0].startswith("emergencia")):
            if zona.contains(evento.pos()):
                self.accionado.emit("emergencia" if nombre.startswith("emergencia") else nombre)
                return
