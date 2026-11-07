"""Valida cada orden antes de pasarla al enlace. Ocultar botones no reemplaza esta comprobación.

Las condiciones de ejecución las decide el coordinador nativo: aquí solo se controla sesión,
permiso y que haya quien atienda la solicitud. Ninguna orden mueve equipos desde Python.
"""
from dataclasses import dataclass

from cuentas import ErrorCuenta
from permisos import (ENTRADAS_SIMULADAS, MODOS, OBJETIVO_MAXIMO, PRODUCCION, RESGUARDOS,
                      TIPOS_INTERVENCION, Op, permitido)

SIN_SESION = "sin sesión"
# La emergencia física no depende de un inicio de sesión.
SIN_SESION_PERMITIDAS = (Op.PARADA, Op.EMERGENCIA)


@dataclass
class Resultado:
    aceptada: bool
    mensaje: str


def operativo(estado):
    return bool(estado.get("conectado") and estado.get("estacion_ok") and estado.get("coordinador"))


class Procesador:
    def __init__(self, cuentas, enviar, causas):
        self.cuentas = cuentas
        self.enviar = enviar
        self.causas = causas
        self.estado = {}
        self.pendientes = {}
        self.acks = {}

    def _registrar(self, sesion, op, detalle, resultado):
        usuario, perfil = (sesion.usuario, sesion.perfil) if sesion else (SIN_SESION, "-")
        self.cuentas.registrar(usuario, perfil, op.value, detalle, resultado)

    def _rechazar(self, sesion, op, detalle, motivo):
        self._registrar(sesion, op, detalle, "Rechazado: " + motivo)
        return Resultado(False, motivo)

    def _autorizar(self, sesion, op, detalle):
        if sesion is None and op not in SIN_SESION_PERMITIDAS:
            return self._rechazar(sesion, op, detalle, "Hace falta iniciar sesión.")
        if sesion is not None:
            if not self.cuentas.sesion_valida(sesion):
                return self._rechazar(sesion, op, detalle, "La sesión ya no es válida.")
            if not permitido(sesion.perfil, op):
                return self._rechazar(sesion, op, detalle, "El perfil no tiene este permiso.")
        return None

    def solicitar(self, sesion, op, modo=None, tipo="", senal=None, valor=None):
        detalle = self._detalle(op, modo, tipo, senal, valor)
        rechazo = self._autorizar(sesion, op, detalle)
        if rechazo:
            return rechazo
        if op in (Op.EMERGENCIA, Op.RESGUARDO, Op.REARME, Op.OBJETIVO):
            return self._seguridad(sesion, op, detalle, senal, valor)
        if op is Op.ENTRADA_SIMULADA:
            if senal not in ENTRADAS_SIMULADAS or valor not in (0, 1):
                return self._rechazar(sesion, op, detalle, "Entrada no admitida.")
            if not (self.estado.get("conectado") and self.estado.get("estacion_ok")):
                return self._rechazar(sesion, op, detalle, "Sin conexión con la estación.")
            self.enviar(("entrada", senal, valor))
            self._registrar(sesion, op, detalle, "Escrita")
            return Resultado(True, "Entrada actualizada.")
        if not operativo(self.estado):
            return self._rechazar(sesion, op, detalle, "Sin conexión con el coordinador.")
        if op is Op.ARRANQUE:
            orden, clave = ("id", "ARRANQUE_ID"), "ARRANQUE_ACK"
        elif op is Op.PARADA:
            orden, clave = ("id", "PARADA_ID"), "PARADA_ACK"
        elif op is Op.RECUPERAR:
            orden, clave = ("id", "RECUPERAR_ID"), "RECUPERAR_ACK"
        elif op is Op.REINICIAR:
            orden, clave = ("id", "REINICIAR_ID"), "REINICIAR_ACK"
        elif op is Op.PREPARAR_MODO:
            if modo not in MODOS or tipo not in TIPOS_INTERVENCION:
                return self._rechazar(sesion, op, detalle, "Selección no admitida.")
            orden, clave = ("modo", modo, False), "MODO_ACK"
        else:
            orden, clave = ("modo", 0, True), "MODO_ACK"
        self.enviar(orden)
        self.pendientes[clave] = (sesion, op, detalle)
        self._registrar(sesion, op, detalle, "Enviada")
        return Resultado(True, "Solicitud enviada; se espera la confirmación del coordinador.")

    def _seguridad(self, sesion, op, detalle, senal, valor):
        """No exige coordinador: justamente después de una parada está detenido."""
        if not (self.estado.get("conectado") and self.estado.get("estacion_ok")):
            return self._rechazar(sesion, op, detalle, "Sin conexión con la estación.")
        s = self.estado.get("senales", {})
        if op is Op.EMERGENCIA:
            if valor not in (0, 1):
                return self._rechazar(sesion, op, detalle, "Entrada no admitida.")
            self.enviar(("entrada", "EMERGENCIA_SIM", valor))
            if valor:
                self.enviar(("paro", 1))
        elif op is Op.RESGUARDO:
            if senal not in RESGUARDOS or valor not in (0, 1):
                return self._rechazar(sesion, op, detalle, "Entrada no admitida.")
            self.enviar(("entrada", senal, valor))
            # Con un modo confirmado el acceso está previsto; con equipos en marcha, detiene.
            if valor and (s.get("AUTO_ACTIVO") == 1 or s.get("MODO_EN_TRANSICION") == 1
                          or s.get("ESTADO_CONTROL") == 8):
                self.enviar(("paro", RESGUARDOS[senal]))
        elif op is Op.REARME:
            causa = s.get("PARO_CAUSA") or 0
            if not causa:
                return self._rechazar(sesion, op, detalle, "No hay una parada para rearmar.")
            if causa == 1 and sesion.perfil == PRODUCCION:
                return self._rechazar(sesion, op, detalle, "Después de una emergencia rearma mantenimiento.")
            if s.get("EMERGENCIA_SIM") == 1 or any(s.get(n) == 1 for n in RESGUARDOS):
                return self._rechazar(sesion, op, detalle, "La causa de la parada sigue presente.")
            self.enviar(("entrada", "PARO_CAUSA", 0))
        else:
            if not isinstance(valor, int) or not 0 <= valor <= OBJETIVO_MAXIMO:
                return self._rechazar(sesion, op, detalle, "Cantidad no admitida.")
            self.enviar(("entrada", "OBJETIVO_PIEZAS", valor))
        self._registrar(sesion, op, detalle, "Hecho")
        return Resultado(True, "Hecho.")

    @staticmethod
    def _detalle(op, modo, tipo, senal, valor):
        if op is Op.PREPARAR_MODO:
            return f"{tipo}: {MODOS.get(modo, modo)}"
        if op in (Op.ENTRADA_SIMULADA, Op.RESGUARDO):
            return f"{senal} = {valor}"
        if op in (Op.EMERGENCIA, Op.OBJETIVO):
            return str(valor)
        return "-"

    def actualizar(self, estado):
        """Registra la confirmación nativa, separada de la hora de la solicitud."""
        anterior, self.estado = self.estado, estado
        senales = estado.get("senales", {})
        if not operativo(estado):
            # Una orden sin confirmar no se retoma al reconectar.
            self.pendientes.clear()
            self.acks.clear()
            return
        for clave in list(self.pendientes):
            valor = senales.get(clave)
            if clave not in self.acks:
                self.acks[clave] = (anterior.get("senales", {}).get(clave, valor), False)
            base, visto = self.acks[clave]
            if visto:
                sesion, op, detalle = self.pendientes.pop(clave)
                del self.acks[clave]
                self._registrar(sesion, op, detalle, self._resultado(clave, senales))
            elif valor != base:
                self.acks[clave] = (base, True)

    def _resultado(self, clave, s):
        if clave in ("ARRANQUE_ACK", "RECUPERAR_ACK", "REINICIAR_ACK"):
            causa = int(s.get("CAUSA_RECHAZO") or 0)
            return "Confirmada" if causa == 0 else "Rechazada: " + self.causas.get(causa, str(causa))
        if clave == "MODO_ACK":
            resultado = int(s.get("MODO_RESULTADO") or 0)
            if resultado == 1:
                return "Confirmada"
            if resultado == 3:
                return "Producción detenida: reenviar la solicitud"
            causa = int(s.get("MODO_CAUSA") or 0)
            return "Rechazada: " + self.causas.get(causa, str(causa))
        return "Confirmada"

    def cerrar_sesion(self, sesion, motivo):
        """Cerrar sesión no abre la pinza ni reinicia el lote: solo pide la parada normal."""
        if sesion is None or sesion.cerrada:
            return
        sesion.cerrada = True
        detalle = motivo
        if operativo(self.estado) and self.estado.get("senales", {}).get("AUTO_ACTIVO") == 1:
            self.enviar(("id", "PARADA_ID"))
            detalle += "; parada normal solicitada"
        self.cuentas.registrar(sesion.usuario, sesion.perfil, "Cierre de sesión", detalle, "Hecho")

    def administrar(self, sesion, accion, usuario, *argumentos):
        detalle = f"{accion} {usuario}"
        rechazo = self._autorizar(sesion, Op.ADMINISTRAR, detalle)
        if rechazo:
            return rechazo
        if usuario == sesion.usuario and accion in ("cambiar_perfil", "habilitar"):
            return self._rechazar(sesion, Op.ADMINISTRAR, detalle,
                                  "Una cuenta no puede cambiar sus propios privilegios.")
        if accion not in ("crear", "cambiar_perfil", "habilitar", "fijar_clave"):
            return self._rechazar(sesion, Op.ADMINISTRAR, detalle, "Acción desconocida.")
        try:
            getattr(self.cuentas, accion)(usuario, *argumentos)
        except ErrorCuenta as error:
            return self._rechazar(sesion, Op.ADMINISTRAR, detalle, str(error))
        self._registrar(sesion, Op.ADMINISTRAR, detalle, "Hecho")
        return Resultado(True, "Cuenta actualizada.")
