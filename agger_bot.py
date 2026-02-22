##################################################
#                 agger_bot.py                   #
##################################################

# Arquivo responsável pela automação do Agger.   #
##################################################
import pyautogui
import pygetwindow as gw
from time import sleep
from reconhecimento import localizar_texto_na_tela, encontrar_botao, validar_data_preenchida, validar_emissao_preenchida, restaurar_agger
from logger import logger

class AggerDesktop:
    def __init__(self):
        logger.info("Inicializando AggerDesktop")
        self.window = self._localizar_janela()

    def _localizar_janela(self):
        titulos = ["AGGER GESTOR", "Agger"]
        for t in titulos:
            wins = gw.getWindowsWithTitle(t)
            if wins:
                win = wins[0]
                logger.info(f"Janela '{win.title}' em X={win.left}, Y={win.top}, {win.width}x{win.height}")
                return win
        return None

    def get_regiao(self):
        if not self.window: return None
        return {
            "left": self.window.left,
            "top": self.window.top,
            "width": self.window.width,
            "height": self.window.height
        }

    def focar(self):
        if not self.window:
            self.window = self._localizar_janela()
        if self.window:
            try:
                if self.window.isMinimized: self.window.restore()
                pyautogui.click(self.window.left + 150, self.window.top + 10)
                sleep(0.5)
                try:
                    self.window.activate()
                except:
                    pass
                sleep(0.5)
            except:
                pass
        return True

    def clicar_relativo(self, x_rel, y_rel, clicks=1):
        if self.window:
            abs_x = self.window.left + x_rel
            abs_y = self.window.top + y_rel
            pyautogui.click(abs_x, abs_y, clicks=clicks, duration=0.3)
            logger.debug(f"Clique relativo ({x_rel},{y_rel}) -> absoluto ({abs_x},{abs_y})")

    def clicar_botao_com_retry(self, nome_imagem, regiao, tentativas=3, espera=5):
        """Clica em botão com tentativas"""
        for i in range(tentativas):
            enc, x, y = encontrar_botao(nome_imagem, regiao=regiao)
            if enc:
                pyautogui.click(x, y, duration=0.3)
                logger.info(f"Botão '{nome_imagem}' clicado (tentativa {i+1})")
                return True
            logger.warning(f"Tentativa {i+1}/{tentativas}: '{nome_imagem}' não encontrado")
            sleep(espera)
        logger.error(f"Botão '{nome_imagem}' não encontrado após {tentativas} tentativas")
        return False

    def restaurar(self):
        regiao = self.get_regiao()
        if regiao:
            restaurar_agger(regiao)

    def processar_cliente(self, nome, apolice, seguradora):
        """Fluxo principal de processamento no Agger"""
        logger.info(f"Iniciando Agger: {nome} | Apólice: {apolice}")
        self.focar()
        regiao = self.get_regiao()

        try:
            # Pesquisa cliente
            self.clicar_relativo(1231, 65, clicks=1)
            sleep(0.5)
            self.clicar_relativo(1231, 65, clicks=1)
            sleep(0.5)

            pyautogui.press('backspace', presses=100, interval=0.1)
            sleep(1)
            pyautogui.write(nome, interval=0.1)
            logger.debug(f"Digitado: {nome}")
            sleep(5)

            # Seleciona na lista
            self.clicar_relativo(463, 108, clicks=2)
            sleep(7)

            # Localiza apólice via OCR
            scroll_x = self.window.left + 400
            scroll_y = self.window.top + 300
            
            status_busca = localizar_texto_na_tela(apolice, regiao=regiao, scroll_pos=(scroll_x, scroll_y))
            
            if status_busca == "pendente":
                logger.info("Status pendente detectado no Agger.")
                restaurar_agger(regiao)
                return "pendente"

            if not status_busca:
                logger.error(f"Apólice '{apolice}' não localizada")
                restaurar_agger(regiao)
                return False

            # Clica na apólice
            pyautogui.doubleClick(duration=0.3)
            logger.debug("Clicou na apólice")
            sleep(1)

            # Alterar (Retry)
            if not self.clicar_botao_com_retry("alterar.png", regiao, tentativas=3, espera=5):
                restaurar_agger(regiao)
                return False
            sleep(7)

            # Fecha modal OK
            enc, x, y = encontrar_botao("ok_modal.png", regiao=regiao)
            if enc:
                pyautogui.click(x, y, duration=0.3)
                sleep(2)

            # Validação de Datas
            valido_trans, _, _ = validar_data_preenchida(regiao)
            if not valido_trans:
                logger.error("Data de transmissão não validada")
                restaurar_agger(regiao)
                return False
            
            valido_emiss, _, _ = validar_emissao_preenchida(regiao)
            if not valido_emiss:
                logger.error("Data de emissão não validada")
                restaurar_agger(regiao)
                return False

            # Botão Check
            enc, x, y = None, None, None
            for i in range(3):
                enc, x, y = encontrar_botao("check_apolice.png", regiao=regiao)
                if enc:
                    pyautogui.click(x, y + 15, duration=0.3)
                    logger.info(f"Botão 'check_apolice.png' clicado com offset +15px (tentativa {i+1})")
                    break
                sleep(3)
            if not enc:
                logger.error("Botão 'check_apolice.png' não encontrado")
                restaurar_agger(regiao)
                return False
            sleep(1)

            # Salvar (Retry)
            if not self.clicar_botao_com_retry("salvar.png", regiao, tentativas=3, espera=3):
                restaurar_agger(regiao)
                return False
            sleep(10)

            # Confirmar Salvar
            enc, x, y = encontrar_botao("sim_modal.png", regiao=regiao)
            if enc:
                pyautogui.click(x, y, duration=0.3)
                sleep(1)

            # Voltar (Retry)
            if not self.clicar_botao_com_retry("voltar.png", regiao, tentativas=3, espera=5):
                restaurar_agger(regiao)
                return False
            sleep(5)

            logger.info(f"Cliente {nome} processado com sucesso!")
            return True

        except Exception as e:
            logger.error(f"Erro no bot: {e}")
            restaurar_agger(regiao)
            return False