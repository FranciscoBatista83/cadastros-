##################################################
#                navegador.py                    #
##################################################

# Arquivo responsável pela automação web.        #
##################################################
import os
from time import sleep
from playwright.sync_api import sync_playwright
from logger import logger
from monitor_utils import get_monitor_principal

# Esperas e contadores
PAUSA = 1
contador = 0

class SistemaEmissao:
    def __init__(self):
        logger.info("Inicializando SistemaEmissao com Playwright")
        
        # Detecção de monitor
        self.monitor = get_monitor_principal()
        w = self.monitor["width"]
        h = self.monitor["height"]
        logger.info(f"Monitor principal detectado: {w}x{h}")
        
        self.playwright = sync_playwright().start()
        
        # Lança navegador
        self.browser = self.playwright.chromium.launch(
            headless=False,
            args=[
                f"--window-position={self.monitor['left']},{self.monitor['top']}",
                f"--window-size={w},{h}"
            ]
        )
        
        self.context = self.browser.new_context(no_viewport=True)
        self.page = self.context.new_page()
        # Força maximização
        try:
            cdp = self.context.new_cdp_session(self.page)
            window_id = cdp.send("Browser.getWindowForTarget")["windowId"]
            cdp.send("Browser.setWindowBounds", {
                "windowId": window_id,
                "bounds": {"windowState": "maximized"}
            })
        except Exception as e:
            logger.warning(f"CDP maximização falhou (não crítico): {e}")
        
        self.processados = set()

    def abrir_sistema(self, url=None):
        """Abre o sistema FiadorWeb"""
        if not url:
            url = os.getenv("FIADOR_URL_JUNDIAI", "https://fiadorweb.com/emissao/docs_agger.php")
        logger.info(f"Abrindo sistema de emissão: {url}")
        self.page.goto(url)
        self.page.wait_for_load_state("networkidle")

    def login(self, usuario, senha):
        """Login no sistema"""
        logger.info(f"Realizando login com usuário: {usuario}")
        try:
            # Verifica se já está logado
            if not self.page.is_visible("//input[@placeholder='Usuário']"):
                logger.info("Campo de login não visível, verificando se já estamos logados...")
                if self.page.is_visible("//i[contains(@class, 'mdi-menu')]") or self.page.is_visible("(//i[contains(@class, 'fa-angle-down')])[2]"):
                    logger.info("Já logado, pulando preenchimento de credenciais.")
                    return

            self.page.wait_for_selector("//input[@placeholder='Usuário']", timeout=10000)
            self.page.fill("//input[@placeholder='Usuário']", usuario)
            self.page.fill("//input[@placeholder='Senha']", senha)
            self.page.click("//button[text()='Login']")
            self.page.wait_for_load_state("networkidle")
            logger.info("Login realizado com sucesso")
        except Exception as e:
            logger.error(f"Erro no processo de login: {e}")
            if "closed" in str(e).lower() or "connection" in str(e).lower() or "target" in str(e).lower():
                raise e
    def obter_usuarios_auditoria(self):
        """Extrai usuários do menu Auditoria"""
        logger.info("Extraindo lista de usuários do menu Auditoria...")
        try:
            # Abre menu Auditoria
            self.page.wait_for_selector("(//i[contains(@class, 'fa-angle-down')])[2]")
            self.page.click("(//i[contains(@class, 'fa-angle-down')])[2]")
            
            # Espera os itens do menu aparecerem
            self.page.wait_for_selector("//div[contains(@class, 'dropdown-menu')]//a")
            
            # Obtém links
            links = self.page.query_selector_all("//div[contains(@class, 'dropdown-menu')]//a")
            
            usuarios = []
            for link in links:
                texto = link.inner_text().strip()
                if texto and texto not in ["Auditoria", ""]: # Filtra textos vazios ou o próprio nome do menu
                    usuarios.append(texto)
            
            # Fecha menu
            self.page.click("(//i[contains(@class, 'fa-angle-down')])[2]")
            
            logger.info(f"Usuários encontrados: {usuarios}")
            return usuarios
        except Exception as e:
            logger.error(f"Erro ao obter usuários de auditoria: {e}")
            return []

    def selecionar_usuario_menu_auditoria(self, nome_usuario):
        """Seleciona auditor específico"""
        try:
            self.page.wait_for_selector("(//i[contains(@class, 'fa-angle-down')])[2]")
            self.page.click("(//i[contains(@class, 'fa-angle-down')])[2]")
            selector = f"//div[contains(@class, 'dropdown-menu')]//a[normalize-space()='{nome_usuario}']"
            self.page.wait_for_selector(selector)
            self.page.click(selector)
            self.page.wait_for_load_state("networkidle")
        except Exception as e:
            logger.error(f"Erro ao selecionar usuário {nome_usuario}: {e}")
            if "closed" in str(e).lower() or "connection" in str(e).lower() or "target" in str(e).lower():
                raise e

    def abrir_menu_cadastrar_no_agger(self):
        logger.info("Abrindo menu 'Cadastrar no Agger'")
        self.page.click("//span[contains(@class, 'hide-menu') and contains(text(), 'Cadastrar no Agger')]")
        self.page.wait_for_selector("//i[contains(@class, 'mdi-menu')]")
        self.page.click("//i[contains(@class, 'mdi-menu')]")
        self.page.wait_for_load_state("networkidle")

    def obter_proximo_cliente(self):
        """Busca cliente na tabela"""
        try:
            self.page.wait_for_selector('table.table')
            linhas = self.page.query_selector_all('table.table tr')[1:]
            for linha in linhas:
                colunas = linha.query_selector_all('td')
                if not colunas: continue
                
                # Captura ID Único
                id_unico = colunas[0].inner_text().strip()
                if not id_unico.startswith("#"):
                    # Fallback para o campo hidden se a coluna 0 não for o ID #
                    input_hidden = linha.query_selector("input[type='hidden']")
                    id_unico = input_hidden.get_attribute("value") if input_hidden else f"row_{linhas.index(linha)}"
                
                nome = colunas[2].inner_text().strip()
                texto_col_apolice = colunas[1].inner_text().strip()
                partes = texto_col_apolice.split('\n')
                apolice = partes[1] if len(partes) > 1 else partes[0]
                seguradora = colunas[3].inner_text().strip()
                select_element = linha.query_selector('select')
                valor = select_element.input_value() if select_element else ""
                
                # Processa pendentes não visitados
                if valor != "Sim" and id_unico not in self.processados:
                    self.processados.add(id_unico)
                    linha.scroll_into_view_if_needed()
                    logger.info(f"Cliente: {nome} | Apólice: {apolice} | Seg: {seguradora} | ID: {id_unico}")
                    return nome, apolice, seguradora, select_element, id_unico
        except Exception as e:
            logger.error(f"Erro ao obter cliente: {str(e)}")
            # Erro de timeout/sessão
            if "timeout" in str(e).lower() or "closed" in str(e).lower() or "connection" in str(e).lower() or "target" in str(e).lower():
                raise e
        return None, None, None, None, None

    def marcar_como_cadastrado(self, select_element, recarregar=True):
        """Marca 'Sim' no sistema"""
        if select_element:
            try:
                if recarregar:
                    logger.info("Marcando como 'Sim' e recarregando para salvar...")
                else:
                    logger.info("Marcando como 'Sim' (sem recarregar)...")
                
                select_element.select_option(label="Sim")
                sleep(1) # Espera o site processar a mudança
                
                if recarregar:
                    self.page.reload()
                    self.page.wait_for_load_state("networkidle")
                    # Restaura menu
                    try:
                        self.page.click("//i[contains(@class, 'mdi-menu')]", timeout=5000)
                        sleep(1)
                    except: pass
            except Exception as e:
                logger.error(f"Erro ao marcar como cadastrado: {e}")
                if "closed" in str(e).lower() or "connection" in str(e).lower() or "target" in str(e).lower():
                    raise e

    def marcar_como_nao_cadastrado(self, select_element, recarregar=True):
        """Marca 'Não' no sistema"""
        if select_element:
            try:
                if recarregar:
                    logger.info("Marcando como 'Não' e recarregando para salvar...")
                else:
                    logger.info("Marcando como 'Não' (sem recarregar)...")
                
                select_element.select_option(label="Não")
                sleep(1)
                
                if recarregar:
                    self.page.reload()
                    self.page.wait_for_load_state("networkidle")
                    # Restaura o menu após reload
                    try:
                        self.page.click("//i[contains(@class, 'mdi-menu')]", timeout=5000)
                        sleep(1)
                    except: pass
            except Exception as e:
                logger.error(f"Erro ao marcar como não cadastrado: {e}")
                if "closed" in str(e).lower() or "connection" in str(e).lower() or "target" in str(e).lower():
                    raise e

    def recarregar(self):
        """Limpa estado e garante menu"""
        logger.info("Verificando/Limpando estado da página web...")
        try:
            # Fecha modais
            for selector in ["button:has-text('Fechar')", ".close", ".modal-header button"]:
                if self.page.is_visible(selector):
                    logger.info(f"Fechando modal detectado: {selector}")
                    self.page.click(selector)
                    sleep(0.5)

            # Verifica se o menu principal sumiu ou se a página precisa de reload
            if not self.page.is_visible("//i[contains(@class, 'mdi-menu')]"):
                logger.info("Menu não detectado, recarregando página...")
                self.page.reload()
                self.page.wait_for_load_state("networkidle")
                sleep(2)
                
            # Garante que o menu de filtro lateral esteja aberto
            self.page.click("//i[contains(@class, 'mdi-menu')]")
            sleep(1)
            
        except Exception as e:
            logger.warning(f"Erro ao tentar recarregar/limpar página: {e}")
            # Em caso de erro crítico, tenta o reload forçado
            self.page.goto(self.page.url)
            self.page.wait_for_load_state("networkidle")

    def encerrar(self):
        logger.info("Encerrando navegador")
        self.browser.close()
        self.playwright.stop()
