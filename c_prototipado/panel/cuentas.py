"""Cuentas, sesiones y registro del panel sobre SQLite.

La base se usa solo desde el hilo de la interfaz. Autentica a quien usa el panel: no protege
los parámetros de RoboDK de otro cliente de la API ni equivale al UAS del controlador.
"""
from dataclasses import dataclass
import hashlib
import hmac
import os
import sqlite3
import time

from permisos import ADMINISTRADOR, MANTENIMIENTO, PERFILES, PRODUCCION

INACTIVIDAD_S = 15 * 60
INTENTOS_MAXIMOS = 5
BLOQUEO_S = 5 * 60
CLAVE_MINIMA = 8
# Coste guardado con cada hash: se puede subir sin invalidar las cuentas existentes.
SCRYPT_N, SCRYPT_R, SCRYPT_P = 2 ** 15, 8, 3
CUENTAS_INICIALES = (
    ("admin", "Administrador", ADMINISTRADOR, "admin"),
    ("mantenimiento", "Mantenimiento", MANTENIMIENTO, "mantenimiento"),
    ("produccion", "Producción", PRODUCCION, "produccion"),
)
FALLO_ACCESO = "Usuario o contraseña incorrectos, o acceso bloqueado temporalmente."


class ErrorCuenta(Exception):
    pass


@dataclass
class Sesion:
    usuario: str
    nombre: str
    perfil: str
    ultima_actividad: float
    clave_por_defecto: bool
    cerrada: bool = False


def _derivar(clave, sal, n, r, p):
    return hashlib.scrypt(clave.encode("utf-8"), salt=sal, n=n, r=r, p=p,
                          maxmem=128 * r * n * 2, dklen=32)


def generar_hash(clave):
    sal = os.urandom(16)
    derivada = _derivar(clave, sal, SCRYPT_N, SCRYPT_R, SCRYPT_P)
    return f"scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}${sal.hex()}${derivada.hex()}"


def comprobar_hash(clave, guardado):
    _, n, r, p, sal, derivada = guardado.split("$")
    calculada = _derivar(clave, bytes.fromhex(sal), int(n), int(r), int(p))
    return hmac.compare_digest(calculada, bytes.fromhex(derivada))


class Cuentas:
    def __init__(self, ruta, reloj=time.time):
        self.reloj = reloj
        self.db = sqlite3.connect(str(ruta))
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS usuarios (
                usuario TEXT PRIMARY KEY, nombre TEXT NOT NULL, perfil TEXT NOT NULL,
                clave TEXT NOT NULL, activo INTEGER NOT NULL DEFAULT 1,
                clave_por_defecto INTEGER NOT NULL DEFAULT 0,
                intentos INTEGER NOT NULL DEFAULT 0, bloqueado_hasta REAL NOT NULL DEFAULT 0,
                creado REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS registro (
                id INTEGER PRIMARY KEY AUTOINCREMENT, fecha REAL NOT NULL, usuario TEXT NOT NULL,
                perfil TEXT NOT NULL, operacion TEXT NOT NULL, detalle TEXT NOT NULL,
                resultado TEXT NOT NULL);
        """)
        if not self.db.execute("SELECT 1 FROM usuarios LIMIT 1").fetchone():
            for usuario, nombre, perfil, clave in CUENTAS_INICIALES:
                self._insertar(usuario, nombre, perfil, clave, por_defecto=1)
            self.registrar("sistema", "-", "Crear base", "Cuentas iniciales", "Hecho")
        self._hash_ficticio = generar_hash(os.urandom(8).hex())

    def _insertar(self, usuario, nombre, perfil, clave, por_defecto=0):
        self.db.execute("INSERT INTO usuarios (usuario, nombre, perfil, clave, clave_por_defecto, "
                        "creado) VALUES (?, ?, ?, ?, ?, ?)",
                        (usuario, nombre, perfil, generar_hash(clave), por_defecto, self.reloj()))
        self.db.commit()

    def _fila(self, usuario):
        return self.db.execute("SELECT * FROM usuarios WHERE usuario = ?", (usuario,)).fetchone()

    def registrar(self, usuario, perfil, operacion, detalle, resultado):
        self.db.execute("INSERT INTO registro (fecha, usuario, perfil, operacion, detalle, resultado)"
                        " VALUES (?, ?, ?, ?, ?, ?)",
                        (self.reloj(), usuario, perfil, operacion, detalle, resultado))
        self.db.commit()

    def leer_registro(self, limite=200):
        return self.db.execute("SELECT * FROM registro ORDER BY id DESC LIMIT ?", (limite,)).fetchall()

    def autenticar(self, usuario, clave):
        """Devuelve una Sesion o None; el motivo del fallo no se revela a quien intenta entrar."""
        fila = self._fila(usuario)
        ahora = self.reloj()
        # Una cuenta inexistente cuesta lo mismo que una real: el tiempo no delata su existencia.
        correcta = comprobar_hash(clave, fila["clave"] if fila else self._hash_ficticio)
        if fila is None:
            self.registrar(usuario, "-", "Inicio de sesión", "Cuenta inexistente", "Rechazado")
            return None
        if not fila["activo"] or fila["bloqueado_hasta"] > ahora:
            self.registrar(usuario, fila["perfil"], "Inicio de sesión", "Cuenta inhabilitada o bloqueada",
                           "Rechazado")
            return None
        if not correcta:
            intentos = fila["intentos"] + 1
            bloqueo = ahora + BLOQUEO_S if intentos >= INTENTOS_MAXIMOS else 0
            self.db.execute("UPDATE usuarios SET intentos = ?, bloqueado_hasta = ? WHERE usuario = ?",
                            (0 if bloqueo else intentos, bloqueo, usuario))
            self.db.commit()
            self.registrar(usuario, fila["perfil"], "Inicio de sesión",
                           "Bloqueo temporal" if bloqueo else "Contraseña incorrecta", "Rechazado")
            return None
        self.db.execute("UPDATE usuarios SET intentos = 0, bloqueado_hasta = 0 WHERE usuario = ?",
                        (usuario,))
        self.db.commit()
        self.registrar(usuario, fila["perfil"], "Inicio de sesión", "-", "Aceptado")
        return Sesion(usuario, fila["nombre"], fila["perfil"], ahora, bool(fila["clave_por_defecto"]))

    def sesion_valida(self, sesion):
        if sesion is None or sesion.cerrada:
            return False
        fila = self._fila(sesion.usuario)
        return bool(fila and fila["activo"] and fila["perfil"] == sesion.perfil
                    and self.reloj() - sesion.ultima_actividad < INACTIVIDAD_S)

    def actividad(self, sesion):
        if sesion is not None:
            sesion.ultima_actividad = self.reloj()

    def listar(self):
        return self.db.execute("SELECT usuario, nombre, perfil, activo, clave_por_defecto "
                               "FROM usuarios ORDER BY usuario").fetchall()

    def hay_claves_por_defecto(self):
        return bool(self.db.execute("SELECT 1 FROM usuarios WHERE clave_por_defecto = 1 AND activo = 1"
                                    " LIMIT 1").fetchone())

    def _administradores_activos(self):
        return self.db.execute("SELECT COUNT(*) FROM usuarios WHERE perfil = ? AND activo = 1",
                               (ADMINISTRADOR,)).fetchone()[0]

    def _protege_ultimo_admin(self, fila):
        if fila["perfil"] == ADMINISTRADOR and fila["activo"] and self._administradores_activos() <= 1:
            raise ErrorCuenta("No se puede dejar la celda sin una cuenta administradora activa.")

    def _exigir(self, usuario):
        fila = self._fila(usuario)
        if fila is None:
            raise ErrorCuenta("La cuenta no existe.")
        return fila

    @staticmethod
    def _validar_clave(clave):
        if len(clave) < CLAVE_MINIMA:
            raise ErrorCuenta(f"La contraseña debe tener al menos {CLAVE_MINIMA} caracteres.")

    def crear(self, usuario, nombre, perfil, clave):
        if not usuario or self._fila(usuario):
            raise ErrorCuenta("El identificador está vacío o ya existe.")
        if perfil not in PERFILES:
            raise ErrorCuenta("Perfil desconocido.")
        self._validar_clave(clave)
        self._insertar(usuario, nombre or usuario, perfil, clave)

    def cambiar_perfil(self, usuario, perfil):
        fila = self._exigir(usuario)
        if perfil not in PERFILES:
            raise ErrorCuenta("Perfil desconocido.")
        if perfil != ADMINISTRADOR:
            self._protege_ultimo_admin(fila)
        self.db.execute("UPDATE usuarios SET perfil = ? WHERE usuario = ?", (perfil, usuario))
        self.db.commit()

    def habilitar(self, usuario, activo):
        fila = self._exigir(usuario)
        if not activo:
            self._protege_ultimo_admin(fila)
        self.db.execute("UPDATE usuarios SET activo = ?, intentos = 0, bloqueado_hasta = 0 "
                        "WHERE usuario = ?", (int(activo), usuario))
        self.db.commit()

    def fijar_clave(self, usuario, clave):
        self._exigir(usuario)
        self._validar_clave(clave)
        self.db.execute("UPDATE usuarios SET clave = ?, clave_por_defecto = 0, intentos = 0, "
                        "bloqueado_hasta = 0 WHERE usuario = ?", (generar_hash(clave), usuario))
        self.db.commit()

    def cambiar_clave_propia(self, sesion, actual, nueva):
        if not comprobar_hash(actual, self._exigir(sesion.usuario)["clave"]):
            raise ErrorCuenta("La contraseña actual no es correcta.")
        self.fijar_clave(sesion.usuario, nueva)
        sesion.clave_por_defecto = False
