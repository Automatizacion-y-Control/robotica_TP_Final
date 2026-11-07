"""Une el panel en un solo script para embeberlo en el .rdk.

Se entrega únicamente la estación, sin el repositorio: Panel_Operador no puede depender de
archivos externos. Lo generado no se edita a mano; se cambia panel/ y se regenera la v05.
"""
import ast
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
PANEL = SCRIPTS.parent / "panel"
MODULOS = (PANEL / "permisos.py", PANEL / "cuentas.py", PANEL / "procesador.py",
           SCRIPTS / "sensores_modos.py", PANEL / "enlace.py", PANEL / "sinoptico.py", PANEL / "ventana.py",
           PANEL / "panel.py")
LOCALES = {"permisos", "cuentas", "procesador", "sensores_modos", "enlace", "sinoptico", "ventana", "modos_nativos"}
CABECERA = '''"""Panel de operador de la celda. Generado por empaquetar_panel.py: no editar aquí.

Se ejecuta con doble clic en RoboDK. Solo lee y escribe señales: no mueve robots ni la cinta.
"""
import os
import subprocess
import sys

# RoboDK puede tener configurado otro Python; PySide2 viene con el que trae la instalación.
PYTHON_ROBODK = r"C:\\RoboDK\\Python-Embedded\\python.exe"
try:
    import PySide2
except ImportError:
    if os.path.exists(PYTHON_ROBODK) and os.path.normcase(sys.executable) != os.path.normcase(PYTHON_ROBODK):
        sys.exit(subprocess.call([PYTHON_ROBODK, __file__]))
    from robodk.robolink import Robolink
    Robolink().ShowMessage("El panel necesita PySide2, incluido en el Python de RoboDK 6.1.1.")
    sys.exit(1)
'''


def _es_prescindible(nodo, ruta):
    if isinstance(nodo, ast.Expr):
        if isinstance(nodo.value, ast.Constant):
            return True  # Docstring del módulo.
        return ast.unparse(nodo).startswith("sys.path.insert")
    if isinstance(nodo, ast.If) and ast.unparse(nodo.test) == "__name__ == '__main__'":
        return True
    # main de los sensores es para ejecutarlos solos; en el panel corren dentro del enlace.
    return isinstance(nodo, ast.FunctionDef) and nodo.name == "main" and ruta.stem == "sensores_modos"


def _inicio(nodo):
    return min([nodo.lineno] + [d.lineno for d in getattr(nodo, "decorator_list", [])])


def _causas():
    fuente = (SCRIPTS / "modos_nativos.py").read_text(encoding="utf-8")
    for nodo in ast.parse(fuente).body:
        if isinstance(nodo, ast.Assign) and nodo.targets[0].id == "CAUSAS":
            return ast.get_source_segment(fuente, nodo)
    raise RuntimeError("Falta CAUSAS en modos_nativos.py")


def generar(destino):
    importaciones = []
    cuerpo = [_causas()]
    for ruta in MODULOS:
        fuente = ruta.read_text(encoding="utf-8")
        lineas = fuente.splitlines()
        anterior = 0
        partes = []
        for nodo in ast.parse(fuente).body:
            if isinstance(nodo, (ast.Import, ast.ImportFrom)):
                modulo = nodo.module if isinstance(nodo, ast.ImportFrom) else nodo.names[0].name
                if modulo not in LOCALES:
                    texto = ast.get_source_segment(fuente, nodo)
                    if texto not in importaciones:
                        importaciones.append(texto)
            elif not _es_prescindible(nodo, ruta):
                # Desde el final del nodo anterior: conserva los comentarios que lo preceden.
                partes.append("\n".join(lineas[max(anterior, _inicio(nodo) - 1):nodo.end_lineno]))
                partes[-1] = partes[-1].lstrip("\n")
            anterior = nodo.end_lineno
        cuerpo.append(f"# --- {ruta.name} ---\n\n" + "\n\n".join(partes))
    texto = "\n\n".join([CABECERA.rstrip(), "\n".join(importaciones), *cuerpo,
                         'if __name__ == "__main__":\n    main()']) + "\n"
    compile(texto, "Panel_Operador.py", "exec")
    Path(destino).write_text(texto, encoding="utf-8", newline="\n")
    return destino
