"""Parámetros geométricos y de proceso de la celda de soldadura de estatores.

Fuente única de cotas para generar_modelos.py (geometría) y construir_celda.py
(disposición, targets y programas). Unidades: mm, grados, mm/s.

Sistema de referencia de la celda (Frame_Celda):
    origen en el piso, en el centro de la base del robot manipulador;
    +X hacia la ventana del pallet y la puerta; +Y hacia el robot soldador;
    +Z hacia arriba.
"""

# ---------------------------------------------------------------------------
# Pieza: paquete de estator (medidas estimadas, ver componentesRDK.md §6)
# ---------------------------------------------------------------------------
ESTATOR_LADO = 105.0          # lado exterior de la sección cuadrada
ESTATOR_LARGO = 55.0          # largo de apilado (eje del paquete)
ESTATOR_D_AGUJERO = 55.0      # diámetro del agujero central
ESTATOR_ESCALON = 4.0         # escalón en cada arista, alojamiento del cordón

# Punto de soldadura: vértice interior del escalón, medido desde el eje.
CORDON_XY = ESTATOR_LADO / 2.0 - ESTATOR_ESCALON          # 47,5 mm

# ---------------------------------------------------------------------------
# Proceso TIG sin aporte
# ---------------------------------------------------------------------------
TIG_TCP_Z = 207.0             # punta del tungsteno respecto de la brida
DIST_ARCO = 2.0               # distancia punta-pieza durante el cordón
DIST_APROX_SOLD = 40.0        # retiro radial para aproximación y salida
# Radio (desde el eje del estator) de la transición en arco entre aristas.
# Tiene que superar el de los bordes del escalón, sqrt(47,5^2 + 52,5^2) = 70,8 mm,
# más el radio del electrodo y un margen; con 80 mm la punta pasa a 27,5 mm de la cara.
R_TRANSICION = 80.0
V_SOLDADURA = 8.0             # velocidad de avance del cordón (TIG manual: 2-10 mm/s)
V_APROX = 100.0               # aproximación y retiro lineal
V_TRASLADO_LIN = 500.0        # traslados lineales largos
V_ARTICULAR = 60.0            # velocidad articular de los MoveJ (°/s)

# ---------------------------------------------------------------------------
# Pinza Robotiq 2F-85 (agarre interior en el agujero del estator)
# ---------------------------------------------------------------------------
PINZA_TCP_Z = 150.0           # centro de las almohadillas respecto de la brida
PINZA_PROF_AGARRE = 20.0      # profundidad del TCP dentro del agujero, desde la cara
PINZA_CERRADA = 0.0           # apertura para entrar en el agujero (dedos juntos)
PINZA_SUJETA = 35.0           # apertura con la que los dedos apoyan en el agujero
PINZA_ABIERTA = 85.0          # apertura máxima (reposo)
DIST_APROX_PINZA = 80.0       # altura de aproximación sobre la cara del estator

# ---------------------------------------------------------------------------
# Disposición en planta (Frame_Celda)
# ---------------------------------------------------------------------------
# Robot manipulador ABB IRB 1200-7/0.7, apoyado en el piso.
IRB_BASE = (0.0, 0.0, 0.0, 0.0)          # x, y, z, giro en Z

# Robot soldador ABB CRB 1300-10/1.15, enfrentado al manipulador.
CRB_BASE = (0.0, 1150.0, 0.0, -90.0)

# Zona de soldadura: centro del estator mientras el manipulador lo presenta.
# El eje del estator queda paralelo a +Y (apuntando al soldador).
SOLD_CENTRO = (0.0, 500.0, 620.0)

# Cinta de entrada (modelo ConveyorA del ejemplo 17 de RoboDK).
# El modelo tiene la base en un extremo, la banda hacia +X y la cara
# superior a 366,5 mm del piso.
CINTA_ALTURA_BANDA = 366.5
CINTA_LARGO = 2200.0           # largo aproximado del modelo
CINTA_EJE_Y_REL = 300.0        # línea central de la banda respecto de la base
CINTA_TOMA = (120.0, -560.0)   # posición (x, y) del centro del estator al tomarlo
CINTA_PASO = 300.0             # separación entre estatores sobre la banda
LOTE = 4                       # estatores por lote (= posiciones del pallet)

# Pallet de salida de 2 x 2 posiciones sobre un soporte bajo.
PALLET_CENTRO = (480.0, 0.0)   # centro del pallet en planta
PALLET_LADO = 400.0
PALLET_ESPESOR = 20.0
PALLET_PASO = 200.0
SOPORTE_PALLET_ALTURA = 350.0

# Estación de servicio de la antorcha (pedestal de 900 mm, ver generar_modelos).
SERVICIO_BASE = (520.0, 1300.0)
SERVICIO_PUNTO = (0.0, 60.0, 970.0)   # punto de verificación del TCP, relativo a la base

# ---------------------------------------------------------------------------
# Cerramiento (protección de nivel 1)
# ---------------------------------------------------------------------------
CERR_X = (-1300.0, 850.0)      # caras oeste y este
CERR_Y = (-1150.0, 1850.0)     # caras sur y norte
CERR_ALTO = 2000.0
CERR_POSTE = 60.0
CERR_PANEL = 4.0
# Abertura en la cara oeste por donde entra la cinta (túnel).
CERR_ABERTURA_CINTA_Y = (-1000.0, -120.0)
CERR_ABERTURA_CINTA_Z = 700.0
# Ventana de descarga del pallet en la cara este, protegida por cortina de luz.
CERR_VENTANA_PALLET_Y = (-300.0, 300.0)
CERR_VENTANA_PALLET_Z = (300.0, 1000.0)
# Puerta de acceso en la cara este, frente a la estación de servicio.
CERR_PUERTA_Y = (1000.0, 1700.0)

# ---------------------------------------------------------------------------
# Posiciones de reposo (valores articulares)
# ---------------------------------------------------------------------------
IRB_REPOSO = [0.0, -20.0, 30.0, 0.0, 80.0, 0.0]
CRB_REPOSO = [0.0, -10.0, 10.0, 0.0, 60.0, 0.0]

# ---------------------------------------------------------------------------
# Mejora 01 (v03): cinta pasante, entrada y salida por la misma cinta
# ---------------------------------------------------------------------------
# El modelo ConveyorA termina a ~2050 mm de su base; se prolonga con un tramo
# propio que atraviesa la cara este del cerramiento. Todo lo que está sobre la
# banda (Frame_Banda) avanza con el mismo eje del mecanismo.
CINTA_BANDA_FIN_REL = 2050.0      # final de la banda del modelo, desde su base
CINTA_ANCHO_BANDA = 600.0         # ancho útil de la banda (medido sobre el modelo)
CINTA_EXT_FIN_X = 2100.0          # final del tramo de salida, en Frame_Celda (afuera del cerramiento)
# Toma y depósito sobre la misma banda, simétricos respecto de la base del manipulador.
V3_TOMA_X = -150.0
V3_DEPOSITO_X = 150.0             # = toma + CINTA_PASO: cada avance deja libre el depósito
# Avance final del lote: lleva el último estator soldado afuera del cerramiento.
V3_AVANCE_EVACUACION = 1750.0     # posición del eje de la cinta al terminar el lote
# Abertura de salida en la cara este, igual a la de entrada en la cara oeste.
CERR_ABERTURA_SALIDA_Y = CERR_ABERTURA_CINTA_Y
CERR_ABERTURA_SALIDA_Z = CERR_ABERTURA_CINTA_Z
