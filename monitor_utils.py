# monitor_utils.py
"""
Detecta automaticamente os monitores conectados usando mss.
Funciona em qualquer resolução e quantidade de monitores.
"""
import mss
from logger import logger

def detectar_monitores():
    """
    Retorna uma lista de dicionários com as info de cada monitor.
    O índice 0 do mss é a tela "combinada", os monitores reais começam no índice 1.
    """
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
    """Retorna o monitor principal (geralmente o da esquerda / posição 0,0)"""
    monitores = detectar_monitores()
    # O monitor principal é o que tem left=0 e top=0
    for m in monitores:
        if m["left"] == 0 and m["top"] == 0:
            return m
    # Fallback: retorna o primeiro
    return monitores[0] if monitores else {"left": 0, "top": 0, "width": 1600, "height": 900}

def get_monitor_secundario():
    """Retorna o monitor secundário (o que não é o principal)"""
    monitores = detectar_monitores()
    principal = get_monitor_principal()
    for m in monitores:
        if m["indice"] != principal["indice"]:
            return m
    # Se só tem um monitor, retorna ele mesmo
    return principal
