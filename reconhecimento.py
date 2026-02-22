##################################################
#               reconhecimento.py                #
##################################################

# Arquivo responsável pelo processamento de OCR.  #
##################################################
import cv2
import numpy as np
import easyocr
import pyautogui
import mss
import mss as mss_lib
from time import sleep
import re
from datetime import datetime
from logger import logger
import os
import concurrent.futures

# Exceção de timeout OCR
class OCRTimeoutError(Exception):
    pass

# Inicializa EasyOCR (CPU)
logger.info("Inicializando EasyOCR Reader (CPU Mode)...")
reader = easyocr.Reader(['pt', 'en'], gpu=False)

PAUSA = 2

def ler_com_timeout(imagem, timeout=60, **kwargs):
    """OCR com thread e timeout"""
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(reader.readtext, imagem, **kwargs)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            raise OCRTimeoutError("O processo de OCR excedeu o limite de 60 segundos.")

def limpar_string_comparacao(s):
    """Mantém apenas números"""
    return re.sub(r'\D', '', str(s))

def textos_compativeis(alvo, detectado, min_len=5):
    """Verifica compatibilidade de números"""
    if len(detectado) < min_len:
        return False
    return alvo in detectado or detectado in alvo

def localizar_texto_na_tela(texto_alvo, regiao=None, scroll_pos=None):
    """Localiza texto na tela com scroll"""
    logger.info(f"Tentando localizar texto: '{texto_alvo}'")
    
    if regiao is None:
        with mss_lib.mss() as sct:
            full = sct.monitors[0]
        regiao = {"left": full["left"], "top": full["top"], "width": full["width"], "height": full["height"]}

    alvo_numerico = limpar_string_comparacao(texto_alvo)
    logger.debug(f"Alvo numérico: {alvo_numerico}")

    pendente_encontrado = False
    
    # Passo 1: Busca sem scroll
    logger.info("Tentativa inicial sem scroll...")
    try:
        with mss.mss() as sct:
            screenshot = np.array(sct.grab(regiao))
            img = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)
        
        resultados = ler_com_timeout(img)
        for (bbox, text, prob) in resultados:
            text_upper = text.upper()
            if "PENDENTE" in text_upper and "EMISS" in text_upper:
                logger.info(f"Pendente visto na tela inicial.")
                pendente_encontrado = True

            if textos_compativeis(alvo_numerico, limpar_string_comparacao(text)):
                x_min, y_min = bbox[0]
                x_max, y_max = bbox[2]
                centro_x = regiao['left'] + int((x_min + x_max) / 2)
                centro_y = regiao['top'] + int((y_min + y_max) / 2)
                logger.info(f"Apólice encontrada sem scroll: '{text}'")
                pyautogui.moveTo(centro_x, centro_y, duration=0.5)
                return True
    except Exception as e:
        logger.error(f"Erro na busca inicial: {e}")

    # Passo 2: Scroll para o final
    if scroll_pos:
        logger.info("Apólice não visível. Indo para o final da lista...")
        pyautogui.moveTo(scroll_pos[0], scroll_pos[1], duration=0.5)
        pyautogui.click() 
        sleep(0.5)
        pyautogui.press('end')
        # Reforço de scroll
        for _ in range(20):
            pyautogui.scroll(-3000) 
            sleep(0.3)
        sleep(1.5)

    # Passo 3: Busca subindo
    tentativas_max = 30 
    textos_anteriores = []
    repeticoes_sem_mudanca = 0

    for tentativa in range(1, tentativas_max + 1):
        logger.info(f"Tentativa {tentativa} de {tentativas_max} (Subindo...)")
        try:
            with mss.mss() as sct:
                screenshot = np.array(sct.grab(regiao))
                img = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)

            if tentativa == 1:
                if not os.path.exists('debug'): os.makedirs('debug')
                cv2.imwrite('debug/ultima_busca.png', img)

            resultados = ler_com_timeout(img)
            textos_lidos = [r[1].upper() for r in resultados]
            
            # Verifica pendência
            for txt in textos_lidos:
                if "PENDENTE" in txt and "EMISS" in txt:
                    if not pendente_encontrado:
                        logger.info(f"Visto status pendente durante scroll.")
                        pendente_encontrado = True
            # -------------------------------

            # Otimização de scroll
            if textos_lidos == textos_anteriores and len(textos_lidos) > 0:
                repeticoes_sem_mudanca += 1
                logger.debug(f"Lista estagnada (Repetição {repeticoes_sem_mudanca}/2)")
                if repeticoes_sem_mudanca >= 2:
                    logger.info("Topo da lista atingido (sem mudanças no scroll). Encerrando busca.")
                    break
            else:
                repeticoes_sem_mudanca = 0
            
            textos_anteriores = textos_lidos
            # -----------------------------------------------------

            melhor_match = None
            melhor_len = 0

            for (bbox, text, prob) in resultados:
                text_numerico = limpar_string_comparacao(text)
                if textos_compativeis(alvo_numerico, text_numerico):
                    if len(text_numerico) > melhor_len:
                        melhor_match = (bbox, text, prob)
                        melhor_len = len(text_numerico)

            if melhor_match:
                bbox, text, prob = melhor_match
                # ... restante do cálculo do centro ...
                x_min = min([p[0] for p in bbox])
                x_max = max([p[0] for p in bbox])
                y_min = min([p[1] for p in bbox])
                y_max = max([p[1] for p in bbox])

                centro_x = regiao['left'] + int((x_min + x_max) / 2)
                centro_y = regiao['top'] + int((y_min + y_max) / 2)

                logger.info(f"Apólice encontrada subindo: '{text}' em ({centro_x}, {centro_y})")
                pyautogui.moveTo(centro_x, centro_y, duration=0.5)
                return True

        except Exception as e:
            logger.error(f"Erro no OCR: {str(e)}")

        pyautogui.scroll(12) 
        sleep(1.2)

    # Conclusão
    if pendente_encontrado:
        logger.warning(f"Número '{texto_alvo}' NÃO encontrado, mas status PENDENTE foi visto.")
        return "pendente"

    logger.warning(f"Texto '{texto_alvo}' não encontrado após busca completa.")
    return False
    
def encontrar_botao(nome_imagem, regiao=None):
    """Localiza botão por imagem"""
    if regiao is None:
        with mss_lib.mss() as sct:
            full = sct.monitors[0]
        regiao = {"left": full["left"], "top": full["top"], "width": full["width"], "height": full["height"]}

    try:
        with mss.mss() as sct:
            screenshot = np.array(sct.grab(regiao))
            screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)

        modelo = cv2.imread(f"imagens/{nome_imagem}")
        if modelo is None:
            logger.error(f"Imagem 'imagens/{nome_imagem}' não encontrada")
            return False, None, None

        resultado = cv2.matchTemplate(screenshot, modelo, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(resultado)

        if max_val >= 0.70:
            x = regiao['left'] + max_loc[0] + modelo.shape[1] // 2
            y = regiao['top'] + max_loc[1] + modelo.shape[0] // 2
            logger.info(f"Botão '{nome_imagem}' encontrado (Confiança: {max_val:.2f})")
            return True, x, y

        logger.debug(f"Botão '{nome_imagem}' não encontrado (melhor: {max_val:.2f})")
        return False, None, None
    except Exception as e:
        logger.error(f"Erro ao buscar botão: {str(e)}")
        return False, None, None

def validar_data_preenchida(regiao_janela):
    """Valida se data está preenchida"""
    encontrado, x, y = encontrar_botao("transmissao.png", regiao=regiao_janela)
    if not encontrado:
        return (False, None, None)

    monitor = {"top": y - 30, "left": x - 180, "width": 150, "height": 60}
    try:
        with mss.mss() as sct:
            img = cv2.cvtColor(np.array(sct.grab(monitor)), cv2.COLOR_BGRA2BGR)
            if not os.path.exists('debug'): os.makedirs('debug')
            cv2.imwrite('debug/campo_data.png', img)

        resultados = ler_com_timeout(img)
        for (bbox, text, prob) in resultados:
            if re.search(r'\d{2}/\d{2}/\d{4}', text):
                logger.info(f"Data validada: {text}")
                return (True, x, y)
        return (False, None, None)
    except Exception as e:
        logger.error(f"Erro validar data: {e}")
        return (False, None, None)

def validar_emissao_preenchida(regiao_janela):
    """Valida data de emissão"""
    logger.info("Validando data de emissão preenchida")
    
    def checar_status():
        # Tentativa por imagem de preenchida
        if encontrar_botao("data_emissao_preenchida.png", regiao=regiao_janela)[0]:
            return True, "Imagem"
        
        # Tentativa por OCR
        enc_ref, x_r, y_r = encontrar_botao("data.png", regiao=regiao_janela)
        if enc_ref:
            monitor = {"top": y_r - 30, "left": x_r - 180, "width": 150, "height": 60}
            with mss.mss() as sct:
                img = cv2.cvtColor(np.array(sct.grab(monitor)), cv2.COLOR_BGRA2BGR)
                resultados = ler_com_timeout(img)
                for (_, text, _) in resultados:
                    if re.search(r'\d{2}/\d{2}/\d{4}', text):
                        return True, f"OCR ({text})"
        return False, None

    # 1. Primeira verificação
    valido, metodo = checar_status()
    if valido:
        logger.info(f"Data de emissão validada de primeira ({metodo})")
        _, x, y = encontrar_botao("data.png", regiao=regiao_janela)
        return True, x, y

    # Tenta carregar se vazio
    logger.warning("Campo de data vazio ou não reconhecido. Tentando duplo clique para carregar...")
    enc_vazia, x_v, y_v = encontrar_botao("data_emissao_vazia.png", regiao=regiao_janela)
    if not enc_vazia:
        # Se não achou a imagem de vazia, tenta usar o ponto de referência do rótulo
        _, x_v, y_v = encontrar_botao("data.png", regiao=regiao_janela)
        if x_v: x_v -= 100 # Move para a esquerda do rótulo onde fica o campo

    if x_v and y_v:
        pyautogui.doubleClick(x_v, y_v, duration=0.3)
        sleep(2.5) # Espera carregar após o clique
        
        # 3. Segunda verificação após o clique
        valido_pos, metodo_pos = checar_status()
        if valido_pos:
            logger.info(f"Data de emissão validada APÓS CLIQUE ({metodo_pos})")
            return True, x_v, y_v

    logger.error("Data de emissão permanece vazia após tentativa de correção.")
    return False, None, None

def restaurar_agger(regiao_janela):
    """Restauração sequencial: OK -> NÃO -> Cancelar -> Voltar"""
    
    # 1. Tenta fechar modais de erro/info
    encontrado, x, y = encontrar_botao('ok_modal.png', regiao=regiao_janela)
    if encontrado:
        logger.info("Clicando em 'ok_modal.png'")
        pyautogui.click(x, y)
        sleep(2)

    # 1.1 Tenta fechar modais de confirmação negativa (Não)
    encontrado, x, y = encontrar_botao('nao_modal.png', regiao=regiao_janela)
    if encontrado:
        logger.info("Clicando em 'nao_modal.png'")
        pyautogui.moveTo(x, y)
        sleep(1)
        pyautogui.doubleClick()
        sleep(2)

    # 2. Tenta Cancelar (sai do cadastro)
    encontrado, x, y = encontrar_botao('cancelar.png', regiao=regiao_janela)
    if encontrado:
        logger.info("Clicando em 'cancelar.png'")
        pyautogui.click(x, y)
        sleep(3) 
    
    # 3. Tenta Voltar (sai da listagem)
    encontrado, x, y = encontrar_botao('voltar.png', regiao=regiao_janela)
    if encontrado:
        logger.info("Clicando em 'voltar.png'")
        pyautogui.click(x, y)
        sleep(2)
        return True 
            
    return False
