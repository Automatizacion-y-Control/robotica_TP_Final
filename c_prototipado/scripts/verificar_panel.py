"""Banco del panel. Sin argumentos prueba cuentas, permisos y código; con --puerto, la integración.

La integración inicia Programa_Principal porque el panel no debe hacerlo, y reabre el archivo
nominal al terminar sin guardar. Usa una base temporal: no toca panel.db.
"""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import socket
import sys
import tempfile
import time

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "panel"))
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, r"C:\RoboDK\Python")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
# La plataforma offscreen no ve las fuentes del sistema si no se le indica la carpeta.
os.environ.setdefault("QT_QPA_FONTDIR", r"C:\Windows\Fonts")

from cuentas import BLOQUEO_S, INACTIVIDAD_S, INTENTOS_MAXIMOS, Cuentas, ErrorCuenta
from permisos import ADMINISTRADOR, MANTENIMIENTO, PERFILES, PRODUCCION, Op, permitido
from procesador import Procesador

PRUEBAS = []
ESPERADA = {
    PRODUCCION: {Op.ARRANQUE, Op.PARADA},
    MANTENIMIENTO: {Op.PARADA, Op.PREPARAR_MODO, Op.REGRESAR_MODO, Op.ENTRADA_SIMULADA},
    ADMINISTRADOR: {Op.PARADA, Op.ADMINISTRAR},
}
OPERATIVO = {"conectado": True, "estacion_ok": True, "coordinador": True, "senales": {"AUTO_ACTIVO": 0}}


def registrar(nombre, **datos):
    fila = {"prueba": nombre, **datos}
    PRUEBAS.append(fila)
    print(json.dumps(fila, ensure_ascii=False), flush=True)


class Reloj:
    ahora = 1000.0

    def __call__(self):
        return self.ahora


def argumentos(op):
    if op is Op.PREPARAR_MODO:
        return {"modo": 1, "tipo": "Preventivo"}
    if op is Op.ENTRADA_SIMULADA:
        return {"senal": "PERMISO_OPERACION", "valor": 1}
    return {}


def probar_cuentas(carpeta):
    reloj = Reloj()
    ordenes = []
    c = Cuentas(carpeta / "unidad.db", reloj)
    p = Procesador(c, ordenes.append, {})
    p.estado = OPERATIVO

    crudo = (carpeta / "unidad.db").read_bytes()
    filas = c.db.execute("SELECT clave FROM usuarios").fetchall()
    assert all(f["clave"].startswith("scrypt$") for f in filas)
    assert len({f["clave"].split("$")[4] for f in filas}) == 3
    assert b"scrypt$" in crudo
    registrar("Contraseñas guardadas como hash con salt individual", cuentas=len(filas))

    sesiones = {perfil: c.autenticar(u, u) for u, perfil in
                (("produccion", PRODUCCION), ("mantenimiento", MANTENIMIENTO), ("admin", ADMINISTRADOR))}
    assert all(s and s.clave_por_defecto for s in sesiones.values())
    registrar("Cuentas iniciales ingresan y se identifican como de fábrica", cuentas=3)

    casillas = 0
    for perfil, sesion in sesiones.items():
        for op in Op:
            assert permitido(perfil, op) == (op in ESPERADA[perfil]), (perfil, op)
            if op is Op.ADMINISTRAR:
                continue
            ordenes.clear()
            aceptada = p.solicitar(sesion, op, **argumentos(op)).aceptada
            assert aceptada == (op in ESPERADA[perfil]) and bool(ordenes) == aceptada, (perfil, op)
            casillas += 1
    assert not p.administrar(sesiones[PRODUCCION], "crear", "x", "x", PRODUCCION, "clave1234").aceptada
    assert not p.administrar(sesiones[MANTENIMIENTO], "fijar_clave", "admin", "clave1234").aceptada
    registrar("Matriz de permisos en el procesador", casillas=casillas)

    ordenes.clear()
    assert p.solicitar(None, Op.PARADA).aceptada and ordenes == [("id", "PARADA_ID")]
    for op in Op:
        if op is not Op.PARADA:
            assert not p.solicitar(None, op, **argumentos(op)).aceptada
    assert c.leer_registro(50)[-1] is not None
    assert any(f["usuario"] == "sin sesión" for f in c.leer_registro(50))
    registrar("Sin sesión solo se admite la parada normal, registrada como tal")

    ordenes.clear()
    sesion = c.autenticar("produccion", "produccion")
    p.estado = {"conectado": False, "senales": {}}
    assert not p.solicitar(sesion, Op.ARRANQUE).aceptada and not ordenes
    p.estado = {**OPERATIVO, "coordinador": False}
    assert not p.solicitar(sesion, Op.ARRANQUE).aceptada and not ordenes
    p.estado = OPERATIVO
    registrar("Sin conexión o sin coordinador no se envían órdenes")

    reloj.ahora += INACTIVIDAD_S + 1
    assert not p.solicitar(sesion, Op.ARRANQUE).aceptada and not ordenes
    registrar("Sesión vencida por inactividad rechaza órdenes", segundos=INACTIVIDAD_S)

    sesion = c.autenticar("produccion", "produccion")
    admin = c.autenticar("admin", "admin")
    assert p.administrar(admin, "habilitar", "produccion", False).aceptada
    assert not p.solicitar(sesion, Op.ARRANQUE).aceptada and not ordenes
    assert c.autenticar("produccion", "produccion") is None
    assert p.administrar(admin, "habilitar", "produccion", True).aceptada
    assert p.administrar(admin, "cambiar_perfil", "produccion", MANTENIMIENTO).aceptada
    assert not p.solicitar(sesion, Op.ARRANQUE).aceptada and not ordenes
    assert p.administrar(admin, "cambiar_perfil", "produccion", PRODUCCION).aceptada
    registrar("Baja o cambio de perfil invalidan la sesión abierta")

    assert not p.administrar(admin, "habilitar", "admin", False).aceptada
    assert not p.administrar(admin, "cambiar_perfil", "admin", PRODUCCION).aceptada
    try:
        c.habilitar("admin", False)
        raise AssertionError("Se inhabilitó la última cuenta administradora")
    except ErrorCuenta:
        pass
    assert p.administrar(admin, "crear", "admin2", "Otro", ADMINISTRADOR, "clave1234").aceptada
    assert p.administrar(admin, "habilitar", "admin2", False).aceptada
    assert not p.administrar(admin, "crear", "corta", "x", PRODUCCION, "1234").aceptada
    registrar("Última cuenta administradora protegida; sin cambio de privilegios propios")

    for _ in range(INTENTOS_MAXIMOS):
        assert c.autenticar("mantenimiento", "incorrecta") is None
    assert c.autenticar("mantenimiento", "mantenimiento") is None
    reloj.ahora += BLOQUEO_S + 1
    assert c.autenticar("mantenimiento", "mantenimiento") is not None
    assert c.autenticar("no_existe", "x") is None
    registrar("Bloqueo temporal tras intentos fallidos", intentos=INTENTOS_MAXIMOS, segundos=BLOQUEO_S)

    sesion = c.autenticar("produccion", "produccion")
    c.cambiar_clave_propia(sesion, "produccion", "clave-nueva")
    assert not sesion.clave_por_defecto and c.autenticar("produccion", "produccion") is None
    assert c.autenticar("produccion", "clave-nueva") is not None
    registrar("Cambio de contraseña propia quita el aviso de clave de fábrica")

    ordenes.clear()
    sesion = c.autenticar("mantenimiento", "mantenimiento")
    p.estado = {**OPERATIVO, "senales": {"AUTO_ACTIVO": 1}}
    p.cerrar_sesion(sesion, "Prueba")
    assert ordenes == [("id", "PARADA_ID")]
    assert not p.solicitar(sesion, Op.PARADA).aceptada
    ordenes.clear()
    sesion = c.autenticar("mantenimiento", "mantenimiento")
    p.estado = OPERATIVO
    p.cerrar_sesion(sesion, "Prueba")
    assert not ordenes
    registrar("Cerrar sesión pide parada solo si hay producción")

    p.estado = OPERATIVO
    sesion = c.autenticar("mantenimiento", "mantenimiento")
    p.solicitar(sesion, Op.REGRESAR_MODO)
    assert p.pendientes
    p.actualizar({"conectado": False, "senales": {}})
    assert not p.pendientes
    registrar("Órdenes sin confirmar se descartan al perder la conexión")

    registro = " ".join(" ".join(str(v) for v in tuple(f)) for f in c.leer_registro(500))
    assert "clave-nueva" not in registro and "clave1234" not in registro
    registrar("El registro no contiene contraseñas")
    c.db.close()


def auditar_codigo():
    prohibido = re.compile(r"\.(RunProgram|RunCode|Stop|MoveJ|MoveL|MoveC|setJoints|setPose|"
                           r"setPoseAbs|setParent\w*|AddProgram|addMoveJ|addMoveL|Pause)\(")
    hallazgos = []
    archivos = sorted((RAIZ / "panel").glob("*.py")) + [RAIZ / "scripts" / "sensores_modos.py"]
    for ruta in archivos:
        for numero, linea in enumerate(ruta.read_text(encoding="utf-8").splitlines(), 1):
            if prohibido.search(linea):
                hallazgos.append(f"{ruta.name}:{numero}")
    assert not hallazgos, hallazgos
    registrar("El panel y los sensores no ejecutan ni mueven nada", archivos=len(archivos))


def probar_arranque_prohibido():
    """Con el puerto cerrado el enlace debe fallar sin lanzar RoboDK."""
    from enlace import RobolinkSinArranque, puerto_abierto
    libre = 20599
    assert not puerto_abierto(libre)
    try:
        r = RobolinkSinArranque(port=libre)
        r.ActiveStation()
    except Exception:
        pass
    assert not puerto_abierto(libre)
    registrar("Sin servidor el enlace no abre RoboDK", puerto=libre)


def probar_interfaz(carpeta):
    """Pulsa los controles reales: llamar a los métodos no prueba las conexiones de las señales."""
    from PySide2.QtWidgets import QApplication, QPushButton, QTextBrowser
    from permisos import ENTRADAS_SIMULADAS
    from ventana import Ventana

    app = QApplication.instance() or QApplication(sys.argv)
    errores = []
    anterior = sys.excepthook
    sys.excepthook = lambda tipo, valor, traza: errores.append(f"{tipo.__name__}: {valor}")
    ordenes = []
    c = Cuentas(carpeta / "interfaz.db")
    p = Procesador(c, ordenes.append, {})
    v = Ventana(c, p, {})
    v.confirmar = lambda texto: True
    senales = {"AUTO_ACTIVO": 0, "MODO_CONFIRMADO": 0, "MODO_EN_TRANSICION": 0,
               "PERMISO_OPERACION": 1, "SENSORES_VALIDOS": 1, "IRB_EN_REPOSO": 1, "CRB_EN_REPOSO": 1,
               "PIEZA_SUJETA_SENSOR": 0, "CINTA_DETENIDA": 1, "IRB_DISPONIBLE": 1,
               "CRB_DISPONIBLE": 1, "CINTA_DISPONIBLE": 1}
    estado = {**OPERATIVO, "puerto": 1, "senales": senales}

    def entrar(usuario):
        v.in_usuario.setText(usuario)
        v.in_clave.setText(usuario)
        v.bt_entrar.click()
        assert v.sesion is not None
        v.recibir_estado(estado)
        app.processEvents()

    try:
        entrar("mantenimiento")
        for senal in ENTRADAS_SIMULADAS:
            v.entradas[senal].click()
            app.processEvents()
        assert ordenes == [("entrada", s, 0) for s in ENTRADAS_SIMULADAS], ordenes
        ordenes.clear()
        v.bt_preparar.click()
        assert ordenes == [("modo", 1, False)], ordenes
        ordenes.clear()
        v.recibir_estado({**estado, "senales": {**senales, "MODO_CONFIRMADO": 1}})
        v.bt_regresar.click()
        assert ordenes == [("modo", 0, True)], ordenes
        ordenes.clear()
        v.bt_parada.click()
        assert ordenes == [("id", "PARADA_ID")], ordenes
        ordenes.clear()
        v.bt_salir.click()
        assert v.sesion is None
        entrar("produccion")
        v.bt_arranque.click()
        assert ordenes == [("id", "ARRANQUE_ID")], ordenes
        v.bt_salir.click()
        v.bt_ayuda.click()
        texto = v.dialogo_ayuda.findChild(QTextBrowser).toPlainText()
        assert "Coordinador_Panel" in texto and "mantenimiento / mantenimiento" in texto
        v.dialogo_ayuda.close()
        entrar("admin")
        v.in_nuevo.setText("operario")
        v.in_inicial.setText("clave1234")
        v.findChild(QPushButton, "crear_cuenta").click()
        assert any(f["usuario"] == "operario" for f in c.listar())
        assert not errores, errores
        registrar("Clics reales en casillas y botones", controles=len(ENTRADAS_SIMULADAS) + 7)
    finally:
        sys.excepthook = anterior
        v.close()
        c.db.close()


def probar_paquete(carpeta):
    """El script embebido no puede depender del repositorio."""
    from empaquetar_panel import LOCALES, generar
    ruta = generar(carpeta / "Panel_Operador.py")
    texto = ruta.read_text(encoding="utf-8")
    assert "c_prototipado" not in texto and "sys.path.insert" not in texto
    assert not [m for m in LOCALES if f"import {m}" in texto or f"from {m} import" in texto]
    registrar("El panel empaquetado no depende de archivos del repositorio", kb=len(texto) // 1024)


def probar_embebido(puerto):
    """Ejecuta Panel_Operador como un doble clic: los sensores deben empezar a escribir."""
    from robodk.robolink import ITEM_TYPE_PROGRAM, ITEM_TYPE_PROGRAM_PYTHON, Robolink
    r = Robolink(port=puerto)
    estacion = r.ActiveStation()
    item = r.Item("Panel_Operador", ITEM_TYPE_PROGRAM_PYTHON)
    assert item.Valid() and estacion.Name() == "Celda_Soldadura_Estator_Grupo4_v05"
    assert float(r.getParam("SENSORES_VALIDOS")) == 0
    item.RunProgram()
    try:
        t = time.monotonic()
        while float(r.getParam("SENSORES_VALIDOS")) != 1:
            assert time.monotonic() - t < 25, "El panel embebido no arrancó"
            time.sleep(.2)
        assert float(r.getParam("AUTO_ACTIVO")) == 0
        registrar("Panel_Operador arranca desde el .rdk y conecta", segundos=round(time.monotonic() - t, 1))
    finally:
        item.Stop()
        time.sleep(.5)
        ruta = RAIZ / "Celda_Soldadura_Estator_Grupo4_v05.rdk"
        estacion.Delete()
        r.setActiveStation(r.AddFile(str(ruta)))


def probar_integracion(puerto, carpeta):
    from PySide2.QtCore import QCoreApplication
    from PySide2.QtWidgets import QApplication
    from robodk.robolink import ITEM_TYPE_PROGRAM, COLLISION_ON, Robolink
    import panel as modulo
    from permisos import ENTRADAS_SIMULADAS

    with socket.create_connection(("localhost", puerto), timeout=3):
        pass
    capturas = RAIZ / "imagenes" / "panel"
    capturas.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication(sys.argv)
    r = Robolink(port=puerto)
    estacion = r.ActiveStation()
    assert estacion.Name() == "Celda_Soldadura_Estator_Grupo4_v05"
    enlace, cuentas, _, v = modulo.crear(carpeta / "integracion.db", (puerto,))
    v.confirmar = lambda texto: True
    principal = r.Item("Coordinador_Panel", ITEM_TYPE_PROGRAM)

    def val(n):
        return float(r.getParam(n))

    def esperar(condicion, limite=70):
        t = time.monotonic()
        while time.monotonic() - t < limite:
            app.processEvents()
            if r.Collisions():
                raise AssertionError("Colisión durante la integración")
            if condicion():
                return
            time.sleep(.03)
        raise AssertionError("Tiempo máximo; " + str(v.estado.get("senales")))

    def entrar(usuario):
        v.in_usuario.setText(usuario)
        v.in_clave.setText(usuario)
        v._entrar()
        assert v.sesion is not None
        app.processEvents()

    def captura(nombre):
        app.processEvents()
        assert v.grab().save(str(capturas / (nombre + ".png")))

    try:
        v.resize(1040, 720)
        v.show()
        enlace.start()
        r.setCollisionActive(COLLISION_ON)
        r.setSimulationSpeed(10)
        esperar(lambda: v.estado.get("estacion_ok"), 10)
        assert not v.estado["coordinador"]
        captura("login")
        registrar("Sin coordinador iniciado el panel lo indica y no lo inicia", aviso=v.aviso.text())

        principal.RunProgram()
        esperar(lambda: v.estado.get("coordinador"), 10)

        entrar("mantenimiento")
        assert [v.pestanas.tabText(i) for i in range(v.pestanas.count())] == \
            ["Mantenimiento", "Sensores", "Registro"]
        for senal in ENTRADAS_SIMULADAS:
            v.entradas[senal].click()
        esperar(lambda: v.estado["senales"]["IRB_DISPONIBLE"] == 1 and
                v.estado["senales"]["PERMISO_OPERACION"] == 1 and
                v.estado["senales"]["CINTA_DISPONIBLE"] == 1, 10)
        esperar(lambda: v.bt_preparar.isEnabled(), 10)
        captura("mantenimiento")
        assert val("AUTO_ACTIVO") == 0
        v._cerrar_sesion("Prueba")
        assert val("AUTO_ACTIVO") == 0
        registrar("Inicio y cierre de sesión no arrancan ni mueven")

        entrar("produccion")
        assert [v.pestanas.tabText(i) for i in range(v.pestanas.count())] == \
            ["Producción", "Sensores", "Registro"]
        esperar(lambda: v.bt_arranque.isEnabled(), 10)
        captura("produccion")
        v.bt_arranque.click()
        esperar(lambda: v.estado["senales"]["PIEZA_ACTIVA"] == 1)
        captura("produccion_ciclo")
        v.bt_parada.click()
        esperar(lambda: v.estado["senales"]["AUTO_ACTIVO"] == 0)
        assert val("PROXIMA_PIEZA") == 2 and val("PIEZAS_COMPLETADAS") == 1
        registrar("Arranque y parada desde los botones", siguiente=2, completadas=1)

        esperar(lambda: v.bt_arranque.isEnabled(), 10)
        v.bt_arranque.click()
        esperar(lambda: v.estado["senales"]["PIEZA_ACTIVA"] == 2)
        v._cerrar_sesion("Prueba")
        esperar(lambda: v.estado["senales"]["AUTO_ACTIVO"] == 0)
        assert val("PROXIMA_PIEZA") == 3 and val("PIEZAS_COMPLETADAS") == 2
        registrar("Cerrar sesión en producción completa la pieza y no reinicia el lote", siguiente=3)

        entrar("mantenimiento")
        v.cb_modo.setCurrentIndex(v.cb_modo.findData(2))
        esperar(lambda: v.bt_preparar.isEnabled(), 10)
        v.bt_preparar.click()
        esperar(lambda: v.estado["senales"]["MODO_CONFIRMADO"] == 2)
        esperar(lambda: v.bt_regresar.isEnabled(), 10)
        captura("mantenimiento_modo")
        v.bt_regresar.click()
        esperar(lambda: v.estado["senales"]["MODO_CONFIRMADO"] == 0 and
                v.estado["senales"]["MODO_EN_TRANSICION"] == 0)
        assert val("AUTO_ACTIVO") == 0 and val("PROXIMA_PIEZA") == 3
        registrar("Preparar y regresar desde el panel sin autoarranque", modo=2, siguiente=3)

        v.entradas["CRB_DISPONIBLE"].click()
        esperar(lambda: v.estado["senales"]["CRB_DISPONIBLE"] == 0, 10)
        v.cb_modo.setCurrentIndex(v.cb_modo.findData(2))
        v.bt_preparar.click()
        esperar(lambda: v.estado["senales"]["MODO_ACK"] >= 3 and "no disponible" in v.et_modo.text(), 10)
        assert v.estado["senales"]["MODO_CONFIRMADO"] == 0
        registrar("El panel muestra la causa de rechazo nativa", causa=v.et_modo.text())
        v.entradas["CRB_DISPONIBLE"].click()
        esperar(lambda: v.estado["senales"]["CRB_DISPONIBLE"] == 1, 10)

        v.pestanas.setCurrentIndex(1)
        captura("sensores")
        v.pestanas.setCurrentIndex(2)
        v._refrescar_tablas()
        captura("registro")
        v._cerrar_sesion("Prueba")
        entrar("admin")
        assert [v.pestanas.tabText(i) for i in range(v.pestanas.count())] == \
            ["Administración", "Sensores", "Registro"]
        captura("administracion")
        resultados = [f["resultado"] for f in cuentas.leer_registro(500)]
        assert "Confirmada" in resultados and any(x.startswith("Rechazada") for x in resultados)
        registrar("El registro distingue solicitud y confirmación nativa",
                  entradas=len(resultados))

        # Cerrar la ventana en producción debe dejar salir la parada antes de terminar el hilo.
        v._cerrar_sesion("Prueba")
        entrar("produccion")
        esperar(lambda: v.bt_arranque.isEnabled(), 10)
        v.bt_arranque.click()
        esperar(lambda: v.estado["senales"]["PIEZA_ACTIVA"] == 3)
        parada = val("PARADA_ID")
        v.close()
        enlace.detener()
        assert val("PARADA_ID") == parada + 1
        t = time.monotonic()
        while val("AUTO_ACTIVO") != 0 and time.monotonic() - t < 70:
            time.sleep(.05)
        assert val("AUTO_ACTIVO") == 0 and val("PROXIMA_PIEZA") == 4
        registrar("Cerrar el panel en producción completa la pieza", siguiente=4)
    finally:
        r.setParam("COORDINADOR_ACTIVO", 0)
        time.sleep(.5)
        enlace.detener()
        for programa in r.ItemList(ITEM_TYPE_PROGRAM):
            if programa.Busy():
                programa.Stop()
        v.close()
        cuentas.db.close()
        estacion.Delete()
        s = r.AddFile(str(RAIZ / "Celda_Soldadura_Estator_Grupo4_v05.rdk"))
        r.setActiveStation(s)
        r.setSimulationSpeed(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--puerto", type=int)
    args = parser.parse_args()
    carpeta = Path(tempfile.mkdtemp(prefix="panel_"))
    exito = False
    try:
        probar_cuentas(carpeta)
        auditar_codigo()
        probar_arranque_prohibido()
        probar_interfaz(carpeta)
        probar_paquete(carpeta)
        if args.puerto:
            probar_integracion(args.puerto, carpeta)
            probar_embebido(args.puerto)
        exito = True
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)
        ruta = RAIZ / "verificaciones" / "panel_v05.json"
        with ruta.open("w", encoding="utf-8", newline="\n") as f:
            json.dump({"exito": exito, "integracion": bool(args.puerto), "pruebas": PRUEBAS}, f,
                      ensure_ascii=False, indent=2)
            f.write("\n")


if __name__ == "__main__":
    main()
