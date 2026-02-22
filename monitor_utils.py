##################################################
#               monitor_utils.py                 #
##################################################

# Arquivo responsável pela detecção de monitores. #
##################################################
import mss
from logger import logger

def detectar_monitores():
    """Lista info de cada monitor"""
    with mss.mss() as sct:
        monitores = []
        for i, m in enumerate(sct.monitors):
            if i == 0:
                continue  # Pula o monitor virtual (combinação de todos)
            info = {
                "indice": i,
                "left": m["left"],
                "top": m["top"],
                "width": m["width"],
                "height": m["height"]
            }
            monitores.append(info)
            logger.info(f"Monitor {i}: {info['width']}x{info['height']} em ({info['left']}, {info['top']})")
        return monitores

def get_monitor_principal():
    """Monitor principal (posicao 0,0)"""
    monitores = detectar_monitores()
    # Monitor principal tem left=0 e top=0
    for m in monitores:
        if m["left"] == 0 and m["top"] == 0:
            return m
    # Fallback: retorna o primeiro
    return monitores[0] if monitores else {"left": 0, "top": 0, "width": 1600, "height": 900}

def get_monitor_secundario():
    """Monitor secundário"""
    monitores = detectar_monitores()
    principal = get_monitor_principal()
    for m in monitores:
        if m["indice"] != principal["indice"]:
            return m
    # Se só tem um monitor, retorna ele mesmo
    return principal
