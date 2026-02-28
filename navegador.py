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
        """Busca o próximo cliente válido filtrando IDs já processados no navegador (O(1) com Set)"""
        try:
            self.page.wait_for_selector('table.table')
            
            # Converte o set de processados em lista para o JS
            lista_processados = list(self.processados)
            
            # Extração e Filtragem em Lote via JavaScript
            # O JS filtrará os IDs usando um Set para performance instantânea
            cliente_alvo = self.page.evaluate("""(processadosArray) => {
                const linhas = Array.from(document.querySelectorAll('table.table tr')).slice(1);
                const processadosSet = new Set(processadosArray);
                
                for (let i = 0; i < linhas.length; i++) {
                    const linha = linhas[i];
                    const colunas = linha.querySelectorAll('td');
                    if (colunas.length < 4) continue;
                    
                    // Captura ID
                    let id_unico = colunas[0].innerText.trim();
                    if (!id_unico.startsWith("#")) {
                        const inputHidden = linha.querySelector("input[type='hidden']");
                        id_unico = inputHidden ? inputHidden.value : 'row_' + i;
                    }
                    
                    // Busca instantânea no Set (O(1))
                    if (processadosSet.has(id_unico)) continue;
                    
                    const select = linha.querySelector('select');
                    const valor = select ? select.value : "";
                    
                    // Se já estiver marcado como "Sim", pulamos (já processado no sistema)
                    if (valor === "Sim") continue;
                    
                    const nome = colunas[2].innerText.trim();
                    const textoApolice = colunas[1].innerText.trim();
                    const partes = textoApolice.split('\\n');
                    const apolice = partes.length > 1 ? partes[1] : partes[0];
                    const seguradora = colunas[3].innerText.trim();
                    
                    return { id_unico, nome, apolice, seguradora, index: i };
                }
                return null;
            }""", lista_processados)

            if cliente_alvo:
                id_unico = cliente_alvo['id_unico']
                self.processados.add(id_unico)
                
                # Localizador otimizado (nth) para o select
                select_element = self.page.locator('table.table select').nth(cliente_alvo['index'])
                
                # Sincroniza o scroll
                try:
                    select_element.scroll_into_view_if_needed()
                except:
                    pass
                
                logger.info(f"Cliente: {cliente_alvo['nome']} | Apólice: {cliente_alvo['apolice']} | Seg: {cliente_alvo['seguradora']} | ID: {id_unico}")
                return cliente_alvo['nome'], cliente_alvo['apolice'], cliente_alvo['seguradora'], select_element, id_unico
                    
        except Exception as e:
            logger.error(f"Erro ao obter cliente: {str(e)}")
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
                
                # Tempo reduzido se não for recarregar (apenas para o select registrar)
                sleep(0.3 if not recarregar else 1)
                
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
