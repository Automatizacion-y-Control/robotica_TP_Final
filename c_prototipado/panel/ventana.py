"""Interfaz del panel. Muestra estados confirmados y pasa toda orden por el procesador."""
from datetime import datetime

from PySide2.QtCore import QEvent, Qt, QTimer
from PySide2.QtWidgets import (QAbstractItemView, QCheckBox, QComboBox, QDialog, QFormLayout, QFrame,
                               QGridLayout, QGroupBox, QHBoxLayout, QHeaderView, QInputDialog,
                               QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton,
                               QStackedWidget, QTableWidget, QTableWidgetItem, QTabWidget,
                               QTextBrowser, QVBoxLayout, QWidget)

from cuentas import ErrorCuenta, FALLO_ACCESO
from permisos import (ADMINISTRADOR, ENTRADAS_SIMULADAS, MANTENIMIENTO, MODOS, PERFILES, PRODUCCION,
                      TIPOS_INTERVENCION, Op, permitido)
from procesador import operativo

ESTADOS = {0: "Inicial", 1: "Automático", 2: "Parada normal", 3: "Detenida por condición perdida",
           4: "Preparando modo", 5: "Regresando de modo", 6: "Modo confirmado"}
RESULTADOS_MODO = {1: "Aceptada", 2: "Rechazada", 3: "Producción detenida: reenviar la solicitud"}
SENSORES = (("IRB_EN_REPOSO", "IRB en reposo"), ("CRB_EN_REPOSO", "CRB en reposo"),
            ("IRB_EN_MANT", "IRB en mantenimiento"), ("CRB_EN_MANT", "CRB en mantenimiento"),
            ("CRB_EN_SERVICIO", "CRB en servicio"), ("CINTA_DETENIDA", "Cinta detenida"),
            ("PIEZA_SUJETA_SENSOR", "Pieza sujeta"), ("SENSORES_VALIDOS", "Sensores en ejecución"))
ETIQUETAS_ENTRADA = {"PERMISO_OPERACION": "Permiso de operación", "IRB_DISPONIBLE": "IRB disponible",
                     "CRB_DISPONIBLE": "CRB disponible", "CINTA_DISPONIBLE": "Cinta disponible"}

AYUDA = """
<h3>Cómo usar la celda</h3>
<p><b>Ciclo completo sin panel:</b> doble clic en <code>Programa_Principal</code>. Suelda un lote de
cuatro estatores y termina.</p>
<p><b>Con el panel:</b></p>
<ol>
<li>Doble clic en <code>Coordinador_Panel</code>: queda esperando órdenes y nada se mueve.</li>
<li>Doble clic en <code>Panel_Operador</code>, si no está abierto.</li>
<li>Entrar como mantenimiento y marcar las cuatro entradas de simulación.</li>
<li>Cerrar sesión, entrar como producción y pulsar Arranque.</li>
</ol>
<p>No mezclar: para pasar de un programa a otro, reabrir la estación sin guardar.</p>
<h3>Cuentas de puesta en marcha</h3>
{cuentas}
<h3>Perfiles</h3>
<ul>
<li><b>Producción:</b> arranque y parada normal.</li>
<li><b>Mantenimiento:</b> preparar modos, regresar, entradas de simulación y parada normal.</li>
<li><b>Administrador:</b> cuentas y parada normal; no opera la celda.</li>
</ul>
<h3>Mantenimiento</h3>
<p>Elegir equipo y pulsar Preparar. Si había producción, se detiene al terminar la pieza: pulsar
Preparar otra vez. Al terminar, Confirmar restitución y regresar; la celda no arranca sola.</p>
<h3>Límites</h3>
<ul>
<li>Parada normal termina la pieza en curso: no es una parada de emergencia.</li>
<li>Las entradas de simulación no son protecciones.</li>
<li>El panel solo envía solicitudes: los movimientos son programas nativos de RoboDK.</li>
<li>Al cerrar RoboDK, no guardar: se conservaría el estado de la simulación.</li>
</ul>
"""

ESTILO = """
QMainWindow, QWidget#fondo { background: #eef0f2; }
QWidget { color: #1c2329; font-family: "Segoe UI"; font-size: 14px; }
QFrame#banda { background: #1f2d3a; }
QFrame#banda QLabel { color: #ffffff; }
QLabel#titulo { font-size: 17px; font-weight: 600; }
QFrame#tarjeta, QGroupBox { background: #ffffff; border: 1px solid #cfd5da; border-radius: 6px; }
QGroupBox { margin-top: 14px; padding-top: 12px; font-weight: 600; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }
QLabel#rotulo { color: #56626c; font-size: 12px; }
QLabel#valor { font-size: 17px; font-weight: 600; }
QLabel#aviso { background: #fff3cd; border: 1px solid #d9b64a; border-radius: 4px; padding: 6px 10px; }
QLabel#mensaje { color: #1c2329; padding: 2px; }
QPushButton { background: #ffffff; border: 1px solid #8b98a3; border-radius: 4px; padding: 7px 14px; }
QPushButton:hover { background: #e4e9ed; }
QPushButton:disabled { color: #8f99a1; border-color: #cfd5da; background: #f2f4f5; }
QPushButton#primario, QPushButton#crear_cuenta { background: #1d6b45; border-color: #1d6b45; color: #ffffff; font-weight: 600; }
QPushButton#primario:disabled { background: #c9d6cf; border-color: #c9d6cf; color: #ffffff; }
QPushButton#parada { background: #b3261e; border-color: #b3261e; color: #ffffff; font-weight: 600; }
QPushButton#parada:disabled { background: #dcbcba; border-color: #dcbcba; color: #ffffff; }
QTabWidget::pane { border: 1px solid #cfd5da; background: #f8f9fa; }
QTabBar::tab { padding: 8px 18px; background: #dfe3e7; border: 1px solid #cfd5da; }
QTabBar::tab:selected { background: #f8f9fa; color: #1d6b45; }
QTableWidget { background: #ffffff; gridline-color: #e1e5e8; }
QLineEdit, QComboBox { background: #ffffff; border: 1px solid #8b98a3; border-radius: 4px; padding: 5px; }
"""


def rotulo(texto):
    etiqueta = QLabel(texto)
    etiqueta.setObjectName("rotulo")
    etiqueta.setWordWrap(True)
    return etiqueta


def tarjeta(titulo):
    marco = QFrame()
    marco.setObjectName("tarjeta")
    capa = QVBoxLayout(marco)
    capa.setContentsMargins(12, 8, 12, 8)
    capa.addWidget(rotulo(titulo))
    valor = QLabel("—")
    valor.setObjectName("valor")
    valor.setWordWrap(True)
    valor.setMinimumHeight(48)
    valor.setAlignment(Qt.AlignLeft | Qt.AlignTop)
    capa.addWidget(valor)
    return marco, valor


def tabla(columnas):
    t = QTableWidget(0, len(columnas))
    t.setHorizontalHeaderLabels(columnas)
    t.verticalHeader().hide()
    t.setEditTriggers(QAbstractItemView.NoEditTriggers)
    t.setSelectionBehavior(QAbstractItemView.SelectRows)
    t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    return t


def llenar(t, filas):
    t.setRowCount(len(filas))
    for i, fila in enumerate(filas):
        for j, valor in enumerate(fila):
            t.setItem(i, j, QTableWidgetItem(str(valor)))


def condiciones_arranque(s):
    """Solo para mostrar; quien decide es el coordinador nativo."""
    igual = lambda n, v: s.get(n) == v
    return (("Permiso de operación", igual("PERMISO_OPERACION", 1)),
            ("Sensores en ejecución", igual("SENSORES_VALIDOS", 1)),
            ("Sin modo activo", igual("MODO_CONFIRMADO", 0) and igual("MODO_EN_TRANSICION", 0)),
            ("Robots en reposo", igual("IRB_EN_REPOSO", 1) and igual("CRB_EN_REPOSO", 1)),
            ("Sin pieza sujeta", igual("PIEZA_SUJETA_SENSOR", 0)),
            ("Cinta detenida", igual("CINTA_DETENIDA", 1)),
            ("Equipos disponibles", igual("IRB_DISPONIBLE", 1) and igual("CRB_DISPONIBLE", 1)
             and igual("CINTA_DISPONIBLE", 1)))


class Ventana(QMainWindow):
    def __init__(self, cuentas, procesador, causas, version="v05"):
        super().__init__()
        self.cuentas = cuentas
        self.procesador = procesador
        self.causas = causas
        self.sesion = None
        self.estado = {}
        self.setWindowTitle(f"Panel de operador · Celda de soldadura TIG {version}")
        self.resize(1040, 720)
        self.setStyleSheet(ESTILO)
        fondo = QWidget()
        fondo.setObjectName("fondo")
        self.setCentralWidget(fondo)
        capa = QVBoxLayout(fondo)
        capa.setContentsMargins(0, 0, 0, 0)
        capa.addWidget(self._banda())
        cuerpo = QVBoxLayout()
        cuerpo.setContentsMargins(14, 10, 14, 12)
        cuerpo.addLayout(self._resumen())
        self.aviso = QLabel()
        self.aviso.setObjectName("aviso")
        self.aviso.setWordWrap(True)
        self.aviso.hide()
        cuerpo.addWidget(self.aviso)
        self.paginas = QStackedWidget()
        self.paginas.addWidget(self._pagina_login())
        self.pestanas = QTabWidget()
        self.paginas.addWidget(self.pestanas)
        cuerpo.addWidget(self.paginas, 1)
        capa.addLayout(cuerpo, 1)
        self._construir_pestanas()
        self.reloj = QTimer(self)
        self.reloj.timeout.connect(self._vigilar_sesion)
        self.reloj.start(1000)
        self._refrescar_sesion()

    # Construcción

    def _banda(self):
        banda = QFrame()
        banda.setObjectName("banda")
        capa = QHBoxLayout(banda)
        capa.setContentsMargins(14, 8, 14, 8)
        titulo = QLabel("Panel de operador")
        titulo.setObjectName("titulo")
        capa.addWidget(titulo)
        capa.addStretch(1)
        self.et_conexion = QLabel()
        capa.addWidget(self.et_conexion)
        capa.addSpacing(18)
        self.et_usuario = QLabel()
        capa.addWidget(self.et_usuario)
        self.bt_ayuda = QPushButton("Ayuda")
        self.bt_ayuda.clicked.connect(self._ayuda)
        capa.addWidget(self.bt_ayuda)
        self.bt_clave = QPushButton("Cambiar contraseña")
        self.bt_clave.clicked.connect(self._cambiar_clave)
        capa.addWidget(self.bt_clave)
        self.bt_salir = QPushButton("Cerrar sesión")
        self.bt_salir.clicked.connect(lambda: self._cerrar_sesion("Cierre por el usuario"))
        capa.addWidget(self.bt_salir)
        self.bt_parada = QPushButton("Parada normal")
        self.bt_parada.setObjectName("parada")
        self.bt_parada.clicked.connect(lambda: self._orden(Op.PARADA))
        capa.addWidget(self.bt_parada)
        return banda

    def _resumen(self):
        fila = QHBoxLayout()
        self.valores = {}
        for clave, titulo in (("estado", "Estado de la celda"), ("modo", "Modo confirmado"),
                              ("pieza", "Pieza y lote"), ("causa", "Último rechazo")):
            marco, valor = tarjeta(titulo)
            self.valores[clave] = valor
            fila.addWidget(marco, 1)
        return fila

    def _pagina_login(self):
        pagina = QWidget()
        externa = QGridLayout(pagina)
        caja = QGroupBox("Inicio de sesión")
        caja.setMinimumWidth(360)
        formulario = QFormLayout(caja)
        self.in_usuario = QLineEdit()
        self.in_clave = QLineEdit()
        self.in_clave.setEchoMode(QLineEdit.Password)
        self.in_clave.returnPressed.connect(self._entrar)
        formulario.addRow("Usuario", self.in_usuario)
        formulario.addRow("Contraseña", self.in_clave)
        self.bt_entrar = QPushButton("Entrar")
        self.bt_entrar.setObjectName("primario")
        self.bt_entrar.clicked.connect(self._entrar)
        formulario.addRow(self.bt_entrar)
        self.et_login = QLabel()
        self.et_login.setWordWrap(True)
        formulario.addRow(self.et_login)
        externa.addWidget(caja, 0, 0, Qt.AlignCenter)
        return pagina

    def _pestana_produccion(self):
        pagina = QWidget()
        capa = QHBoxLayout(pagina)
        mandos = QGroupBox("Mandos")
        columna = QVBoxLayout(mandos)
        self.bt_arranque = QPushButton("Arranque")
        self.bt_arranque.setObjectName("primario")
        self.bt_arranque.clicked.connect(lambda: self._orden(Op.ARRANQUE))
        columna.addWidget(self.bt_arranque)
        self.et_arranque = QLabel()
        self.et_arranque.setWordWrap(True)
        columna.addWidget(self.et_arranque)
        columna.addWidget(rotulo("La parada normal termina y deposita la pieza en curso. "
                                 "No es una parada de emergencia."))
        columna.addStretch(1)
        capa.addWidget(mandos, 1)
        caja = QGroupBox("Condiciones de arranque")
        lista = QVBoxLayout(caja)
        self.et_condiciones = QLabel()
        self.et_condiciones.setTextFormat(Qt.PlainText)
        lista.addWidget(self.et_condiciones)
        lista.addStretch(1)
        capa.addWidget(caja, 1)
        return pagina

    def _pestana_mantenimiento(self):
        pagina = QWidget()
        capa = QHBoxLayout(pagina)
        caja = QGroupBox("Preparación")
        formulario = QFormLayout(caja)
        self.cb_modo = QComboBox()
        for modo, nombre in MODOS.items():
            self.cb_modo.addItem(nombre, modo)
        self.cb_tipo = QComboBox()
        self.cb_tipo.addItems(TIPOS_INTERVENCION)
        formulario.addRow("Equipo o tarea", self.cb_modo)
        formulario.addRow("Intervención", self.cb_tipo)
        self.bt_preparar = QPushButton("Preparar")
        self.bt_preparar.setObjectName("primario")
        self.bt_preparar.clicked.connect(self._preparar)
        formulario.addRow(self.bt_preparar)
        self.bt_regresar = QPushButton("Confirmar restitución y regresar")
        self.bt_regresar.clicked.connect(self._regresar)
        formulario.addRow(self.bt_regresar)
        self.et_modo = QLabel()
        self.et_modo.setWordWrap(True)
        formulario.addRow(self.et_modo)
        formulario.addRow(rotulo("La preparación posiciona los equipos. El aislamiento y el bloqueo "
                                 "se hacen por procedimiento, fuera del panel; esta confirmación "
                                 "no es una medición de energía cero."))
        capa.addWidget(caja, 3)
        simuladas = QGroupBox("Entradas de simulación")
        columna = QVBoxLayout(simuladas)
        columna.addWidget(rotulo("Representan señales externas de la celda. No son protecciones."))
        self.entradas = {}
        for senal in ENTRADAS_SIMULADAS:
            casilla = QCheckBox(ETIQUETAS_ENTRADA[senal])
            # PySide2 no pasa el argumento de clicked a una lambda con valores por defecto.
            casilla.clicked.connect(lambda _=False, s=senal, c=casilla: self._entrada(s, c.isChecked()))
            self.entradas[senal] = casilla
            columna.addWidget(casilla)
        columna.addStretch(1)
        capa.addWidget(simuladas, 2)
        return pagina

    def _pestana_sensores(self):
        pagina = QWidget()
        capa = QVBoxLayout(pagina)
        self.tb_sensores = tabla(("Sensor", "Valor", "Procedencia"))
        capa.addWidget(self.tb_sensores)
        return pagina

    def _pestana_registro(self):
        pagina = QWidget()
        capa = QVBoxLayout(pagina)
        self.tb_registro = tabla(("Fecha", "Usuario", "Perfil", "Operación", "Detalle", "Resultado"))
        capa.addWidget(self.tb_registro)
        return pagina

    def _pestana_administracion(self):
        pagina = QWidget()
        capa = QHBoxLayout(pagina)
        izquierda = QVBoxLayout()
        self.tb_cuentas = tabla(("Usuario", "Nombre", "Perfil", "Activa", "Clave de fábrica"))
        izquierda.addWidget(self.tb_cuentas)
        acciones = QHBoxLayout()
        for texto, funcion in (("Habilitar o inhabilitar", self._alternar_cuenta),
                               ("Cambiar perfil", self._cambiar_perfil),
                               ("Restablecer contraseña", self._restablecer)):
            boton = QPushButton(texto)
            boton.clicked.connect(funcion)
            acciones.addWidget(boton)
        izquierda.addLayout(acciones)
        capa.addLayout(izquierda, 3)
        caja = QGroupBox("Nueva cuenta")
        formulario = QFormLayout(caja)
        self.in_nuevo = QLineEdit()
        self.in_nombre = QLineEdit()
        self.cb_perfil = QComboBox()
        self.cb_perfil.addItems(PERFILES)
        self.in_inicial = QLineEdit()
        self.in_inicial.setEchoMode(QLineEdit.Password)
        formulario.addRow("Usuario", self.in_nuevo)
        formulario.addRow("Nombre", self.in_nombre)
        formulario.addRow("Perfil", self.cb_perfil)
        formulario.addRow("Contraseña", self.in_inicial)
        crear = QPushButton("Crear cuenta")
        crear.setObjectName("crear_cuenta")
        crear.clicked.connect(self._crear_cuenta)
        formulario.addRow(crear)
        self.et_admin = QLabel()
        self.et_admin.setWordWrap(True)
        formulario.addRow(self.et_admin)
        capa.addWidget(caja, 2)
        return pagina

    def _construir_pestanas(self):
        self.pag_produccion = self._pestana_produccion()
        self.pag_mantenimiento = self._pestana_mantenimiento()
        self.pag_sensores = self._pestana_sensores()
        self.pag_registro = self._pestana_registro()
        self.pag_administracion = self._pestana_administracion()

    def _ayuda(self):
        # Solo lista las claves que siguen vigentes: al actualizarlas dejan de mostrarse.
        vigentes = [c["usuario"] for c in self.cuentas.listar()
                    if c["clave_por_defecto"] and c["activo"]]
        cuentas = ("<ul>" + "".join(f"<li><code>{u}</code> / <code>{u}</code></li>" for u in vigentes)
                   + "</ul><p>Actualizarlas al pasar la celda a operación.</p>") if vigentes else \
            "<p>Las contraseñas de fábrica ya fueron actualizadas.</p>"
        self.dialogo_ayuda = QDialog(self)
        self.dialogo_ayuda.setWindowTitle("Ayuda")
        self.dialogo_ayuda.resize(620, 620)
        capa = QVBoxLayout(self.dialogo_ayuda)
        texto = QTextBrowser()
        texto.setHtml(AYUDA.format(cuentas=cuentas))
        capa.addWidget(texto)
        self.dialogo_ayuda.show()

    # Sesión

    def _entrar(self):
        sesion = self.cuentas.autenticar(self.in_usuario.text().strip(), self.in_clave.text())
        self.in_clave.clear()
        if sesion is None:
            self.et_login.setText(FALLO_ACCESO)
            return
        self.sesion = sesion
        self.et_login.clear()
        self.in_usuario.clear()
        self._refrescar_sesion()

    def _cerrar_sesion(self, motivo):
        self.procesador.cerrar_sesion(self.sesion, motivo)
        self.sesion = None
        self.et_login.setText(motivo + ".")
        self._refrescar_sesion()

    def _vigilar_sesion(self):
        if self.sesion is not None and not self.cuentas.sesion_valida(self.sesion):
            self._cerrar_sesion("Sesión cerrada por inactividad o cambio de la cuenta")

    def eventFilter(self, objeto, evento):
        if evento.type() in (QEvent.MouseButtonPress, QEvent.KeyPress):
            self.cuentas.actividad(self.sesion)
        return False

    def _refrescar_sesion(self):
        self.pestanas.clear()
        hay = self.sesion is not None
        self.paginas.setCurrentIndex(1 if hay else 0)
        self.bt_salir.setVisible(hay)
        self.bt_clave.setVisible(hay)
        self.et_usuario.setText(f"{self.sesion.nombre} · {self.sesion.perfil}" if hay else "Sin sesión")
        if hay:
            perfil = self.sesion.perfil
            if permitido(perfil, Op.ARRANQUE):
                self.pestanas.addTab(self.pag_produccion, "Producción")
            if permitido(perfil, Op.PREPARAR_MODO):
                self.pestanas.addTab(self.pag_mantenimiento, "Mantenimiento")
            if permitido(perfil, Op.ADMINISTRAR):
                self.pestanas.addTab(self.pag_administracion, "Administración")
            self.pestanas.addTab(self.pag_sensores, "Sensores")
            self.pestanas.addTab(self.pag_registro, "Registro")
            self._refrescar_tablas()
        self._refrescar_aviso()

    def _refrescar_aviso(self):
        texto = ""
        if not self.estado.get("conectado"):
            texto = "Sin conexión con RoboDK: los mandos están bloqueados."
        elif not self.estado.get("estacion_ok"):
            texto = "La estación activa de RoboDK no es la v05: los mandos están bloqueados."
        elif not self.estado.get("coordinador"):
            texto = "El coordinador está detenido: doble clic en Coordinador_Panel, en RoboDK."
        elif self.sesion is not None and self.sesion.clave_por_defecto:
            texto = "Esta cuenta usa la contraseña de fábrica: actualizarla al pasar la celda a operación."
        elif self.sesion is not None and self.sesion.perfil == ADMINISTRADOR \
                and self.cuentas.hay_claves_por_defecto():
            texto = "Hay cuentas con la contraseña de fábrica: actualizarlas al pasar la celda a operación."
        self.aviso.setText(texto)
        self.aviso.setVisible(bool(texto))

    def _refrescar_tablas(self):
        filas = []
        for f in self.cuentas.leer_registro():
            fecha = datetime.fromtimestamp(f["fecha"]).strftime("%d/%m %H:%M:%S")
            filas.append((fecha, f["usuario"], f["perfil"], f["operacion"], f["detalle"], f["resultado"]))
        llenar(self.tb_registro, filas)
        if self.sesion is not None and self.sesion.perfil == ADMINISTRADOR:
            llenar(self.tb_cuentas, [(c["usuario"], c["nombre"], c["perfil"],
                                      "Sí" if c["activo"] else "No",
                                      "Sí" if c["clave_por_defecto"] else "No")
                                     for c in self.cuentas.listar()])

    # Órdenes

    def confirmar(self, texto):
        respuesta = QMessageBox.question(self, "Confirmar", texto, QMessageBox.Yes | QMessageBox.No,
                                         QMessageBox.No)
        return respuesta == QMessageBox.Yes

    def _orden(self, op, etiqueta=None, **datos):
        resultado = self.procesador.solicitar(self.sesion, op, **datos)
        if etiqueta is not None:
            etiqueta.setText(resultado.mensaje)
        elif not resultado.aceptada:
            self.et_login.setText(resultado.mensaje)
        self.cuentas.actividad(self.sesion)
        if self.sesion is not None:
            self._refrescar_tablas()
        return resultado

    def _preparar(self):
        modo = self.cb_modo.currentData()
        if self.confirmar(f"¿Preparar «{MODOS[modo]}»? Si hay producción, se detendrá al terminar "
                          "la pieza. Nadie debe estar dentro de la zona de robots."):
            self._orden(Op.PREPARAR_MODO, self.et_modo, modo=modo, tipo=self.cb_tipo.currentText())

    def _regresar(self):
        if self.confirmar("¿Confirmás la restitución? Se declara terminada la intervención, con "
                          "resguardos cerrados y nadie dentro. No arranca la producción."):
            self._orden(Op.REGRESAR_MODO, self.et_modo)

    def _entrada(self, senal, marcada):
        self._orden(Op.ENTRADA_SIMULADA, self.et_modo, senal=senal, valor=int(marcada))

    def _cuenta_seleccionada(self):
        fila = self.tb_cuentas.currentRow()
        if fila < 0:
            self.et_admin.setText("Seleccioná una cuenta.")
            return None
        return self.tb_cuentas.item(fila, 0).text()

    def _administrar(self, accion, usuario, *argumentos):
        self.et_admin.setText(self.procesador.administrar(self.sesion, accion, usuario, *argumentos).mensaje)
        self._refrescar_tablas()

    def _crear_cuenta(self):
        self._administrar("crear", self.in_nuevo.text().strip(), self.in_nombre.text().strip(),
                          self.cb_perfil.currentText(), self.in_inicial.text())
        self.in_inicial.clear()

    def _alternar_cuenta(self):
        usuario = self._cuenta_seleccionada()
        if usuario:
            activa = self.tb_cuentas.item(self.tb_cuentas.currentRow(), 3).text() == "Sí"
            self._administrar("habilitar", usuario, not activa)

    def _cambiar_perfil(self):
        usuario = self._cuenta_seleccionada()
        if usuario:
            perfil, ok = QInputDialog.getItem(self, "Cambiar perfil", usuario, PERFILES, 0, False)
            if ok:
                self._administrar("cambiar_perfil", usuario, perfil)

    def _restablecer(self):
        usuario = self._cuenta_seleccionada()
        if usuario:
            clave, ok = QInputDialog.getText(self, "Restablecer contraseña", usuario, QLineEdit.Password)
            if ok:
                self._administrar("fijar_clave", usuario, clave)

    def _cambiar_clave(self):
        actual, ok = QInputDialog.getText(self, "Cambiar contraseña", "Contraseña actual",
                                          QLineEdit.Password)
        if not ok:
            return
        nueva, ok = QInputDialog.getText(self, "Cambiar contraseña", "Contraseña nueva",
                                         QLineEdit.Password)
        if not ok:
            return
        try:
            self.cuentas.cambiar_clave_propia(self.sesion, actual, nueva)
            self.cuentas.registrar(self.sesion.usuario, self.sesion.perfil, "Cambio de contraseña",
                                   "-", "Hecho")
            QMessageBox.information(self, "Contraseña", "Contraseña actualizada.")
        except ErrorCuenta as error:
            QMessageBox.warning(self, "Contraseña", str(error))
        self._refrescar_aviso()

    # Estado

    def recibir_estado(self, estado):
        conectado_antes = self.estado.get("conectado")
        self.estado = estado
        self.procesador.actualizar(estado)
        if conectado_antes and not estado.get("conectado") and self.sesion is not None:
            self._cerrar_sesion("Sesión cerrada por pérdida de conexión")
        s = estado.get("senales", {})
        puerto = estado.get("puerto")
        self.et_conexion.setText(f"RoboDK conectado · puerto {puerto}" if estado.get("conectado")
                                 else "Sin conexión con RoboDK")
        listo = operativo(estado)
        self.bt_parada.setEnabled(listo)
        self.valores["estado"].setText(ESTADOS.get(int(s.get("ESTADO_CONTROL") or 0), "—") if s else "—")
        if not s:
            self.valores["modo"].setText("—")
            self.valores["pieza"].setText("—")
            self.valores["causa"].setText("—")
        else:
            confirmado = int(s.get("MODO_CONFIRMADO") or 0)
            en_transicion = s.get("MODO_EN_TRANSICION") == 1
            self.valores["modo"].setText("Cambiando…" if en_transicion else
                                         MODOS.get(confirmado, "Producción"))
            activa = int(s.get("PIEZA_ACTIVA") or 0)
            proxima = int(s.get("PROXIMA_PIEZA") or 1)
            texto = f"Soldando pieza {activa}" if activa else (
                "Fin de lote pendiente" if proxima == 5 else f"Próxima pieza {proxima}")
            hechas = int(s.get("PIEZAS_COMPLETADAS") or 0)
            lotes = int(s.get("LOTES_COMPLETADOS") or 0)
            self.valores["pieza"].setText(texto + "\n" + f"{hechas} hechas · {lotes} lotes")
            causa = int(s.get("CAUSA_RECHAZO") or 0) or int(s.get("MODO_CAUSA") or 0)
            self.valores["causa"].setText(self.causas.get(causa, str(causa)) if causa else "Ninguno")
        self._actualizar_mandos(s, listo)
        self._refrescar_aviso()

    def _actualizar_mandos(self, s, listo):
        if self.sesion is None:
            return
        condiciones = condiciones_arranque(s)
        faltan = [nombre for nombre, ok in condiciones if not ok]
        automatico = s.get("AUTO_ACTIVO") == 1
        self.et_condiciones.setText("\n".join(f"{'Cumple' if ok else 'Falta '}  ·  {nombre}"
                                              for nombre, ok in condiciones))
        self.bt_arranque.setEnabled(listo and not automatico and not faltan)
        if automatico:
            self.et_arranque.setText("Producción en curso.")
        elif not listo:
            self.et_arranque.setText("Sin conexión con el coordinador.")
        elif faltan:
            self.et_arranque.setText("Falta: " + ", ".join(faltan).lower() + ".")
        else:
            self.et_arranque.setText("Listo para arrancar.")
        confirmado = int(s.get("MODO_CONFIRMADO") or 0)
        libre = listo and s.get("MODO_EN_TRANSICION") == 0
        self.bt_preparar.setEnabled(bool(libre and confirmado == 0))
        self.bt_regresar.setEnabled(bool(libre and confirmado != 0))
        resultado = int(s.get("MODO_RESULTADO") or 0)
        if resultado:
            causa = int(s.get("MODO_CAUSA") or 0)
            texto = RESULTADOS_MODO.get(resultado, "—")
            self.et_modo.setText(f"Última solicitud: {texto}" +
                                 (f" · {self.causas.get(causa, causa)}" if causa else ""))
        for senal, casilla in self.entradas.items():
            casilla.setEnabled(bool(self.estado.get("conectado") and self.estado.get("estacion_ok")))
            casilla.setChecked(s.get(senal) == 1)
        llenar(self.tb_sensores, [(nombre, "Sí" if s.get(senal) == 1 else "No",
                                   "Calculado por Python") for senal, nombre in SENSORES] +
               [(ETIQUETAS_ENTRADA[e], "Sí" if s.get(e) == 1 else "No", "Entrada simulada")
                for e in ENTRADAS_SIMULADAS])

    def closeEvent(self, evento):
        self.procesador.cerrar_sesion(self.sesion, "Cierre del panel")
        evento.accept()
