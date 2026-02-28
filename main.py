##################################################
#                   main.py                      #
##################################################

# Arquivo responsável por orquestração do bot.   #
##################################################

from navegador import SistemaEmissao
from agger_bot import AggerDesktop
from reconhecimento import OCRTimeoutError
from utils import Utils
from relatorios import Relatorio, RelatorioPendentes
from time import sleep
from logger import logger
import os
import math
import time
from dotenv import load_dotenv

# Carrega ambiente
load_dotenv()
def escolher_unidade():
    print("\nEscolha a unidade:")
    print("1. Jundiaí")
    print("2. Indaiatuba")
    
    try:
        unidade_escolha = int(input("\nDigite o número da unidade: "))
        if unidade_escolha == 1:
            return "JUNDIAI"
        elif unidade_escolha == 2:
            return "INDAIATUBA"
        else:
            print("Opção inválida!")
            exit()
    except Exception:
        print("Entrada inválida!")
        exit()

if __name__ == "__main__":
    logger.info("==== INÍCIO DA EXECUÇÃO ====")
    
    # Seleção da unidade
    PREFIXO = escolher_unidade()
    
    # Carrega credenciais
    usuario_login = os.getenv(f"FIADOR_USER_{PREFIXO}")
    senha_login = os.getenv(f"FIADOR_PASS_{PREFIXO}")
    url_sistema = os.getenv(f"FIADOR_URL_{PREFIXO}")

    # Define usuário de auditoria
    modo_geral = False
    lista_geral = []
    index_geral = 0

    if PREFIXO == "INDAIATUBA":
        usuario_a_cadastrar = "Edite"
        print(f"\nUnidade selecionada: {PREFIXO}")
        print(f"Usuário de auditoria definido automaticamente: {usuario_a_cadastrar}")
    else:
        # Lista de nomes fixa para Auditoria (Jundiaí)
        nomes = [
            "Claudia",
            "Claudia Fw",
            "Claudia Regina",
            "Gabriel",
            "Giovanna",
            "Lilian Vieira",
            "Luiz",
            "Marechal 41",
            "Geral"
        ]

        print(f"\nUnidade selecionada: {PREFIXO}")
        print("Escolha um nome da lista de auditoria:")
        for i, nome in enumerate(nomes):
            print(f"{i+1}. {nome}")

        try:
            escolha = int(input("\nDigite o número correspondente: "))
            usuario_a_cadastrar = nomes[escolha - 1]
            if usuario_a_cadastrar == "Geral":
                modo_geral = True
                lista_geral = nomes[:-1] # Pega todos exceto o 'Geral'
                
                # Lógica de Inicialização (Sempre do zero)
                passos_concluidos = 0
                print("\nEscolha em qual auditor deseja INICIAR o ciclo:")
                for idx, n in enumerate(lista_geral):
                    print(f"{idx+1}. {n}")
                try:
                    start_index = int(input("Número: ")) - 1
                    usuario_a_cadastrar = lista_geral[start_index % len(lista_geral)]
                except:
                    start_index = 0
                    usuario_a_cadastrar = lista_geral[0]
                
                logger.info(f"Modo GERAL iniciado em: {usuario_a_cadastrar} (Índice {start_index})")
                logger.info("Modo GERAL ativado: o bot irá percorrer todos os usuários da lista.")
        except Exception:
            print("Escolha inválida!")
            exit()

    # Sem limite de erros consecutivos
    erros_limit = math.inf

    # Configuração inicial (Login + Auditoria)
    def configurar_sistema_fiador(instancia_sistema, auditor):
        logger.info(f"Configurando acesso para auditor: {auditor}...")
        instancia_sistema.abrir_sistema(url=url_sistema)
        instancia_sistema.login(usuario_login, senha_login)
        instancia_sistema.selecionar_usuario_menu_auditoria(auditor)
        instancia_sistema.abrir_menu_cadastrar_no_agger()

    # Inicialização dos módulos
    logger.info(f"Iniciando módulos para {PREFIXO}...")
    sistema = SistemaEmissao()
    utilitarios = Utils()
    relatorio = Relatorio()
    relatorio_pendentes = RelatorioPendentes()
    agger = AggerDesktop()
    
    # Setup inicial
    historico_sucesso = utilitarios.carregar_historico()
    if modo_geral:
        sistema.processados = historico_sucesso
    
    configurar_sistema_fiador(sistema, usuario_a_cadastrar)

    erros_consecutivos = 0
    contador_nao = 0 # Contador para restauração
    
    # Ciclo de 3 horas
    tempo_inicio_trabalho = time.time()
    LIMITE_TRABALHO_SEGUNDOS = 3 * 3600
    
    # Loop principal
    while True:
        try:
            # Verifica limite de 3 horas
            tempo_atual = time.time()
            if (tempo_atual - tempo_inicio_trabalho) >= LIMITE_TRABALHO_SEGUNDOS:
                logger.info("==== CICLO DE DESCANSO PREVENTIVO (3H) ====")
                logger.info("Encerrando navegador e aguardando 5 minutos para preservação do sistema...")
                
                try:
                    sistema.encerrar()
                except:
                    pass
                
                # Pausa de 5 minutos
                time.sleep(300)
                
                logger.info("Retomando após descanso...")
                tempo_inicio_trabalho = time.time()
                
                try:
                    processados_antigos = sistema.processados.copy()
                    sistema = SistemaEmissao()
                    sistema.processados = processados_antigos
                    configurar_sistema_fiador(sistema, usuario_a_cadastrar)
                except Exception as e_descanso:
                    logger.critical(f"Falha ao retomar após descanso: {e_descanso}")
                    time.sleep(30)
                    continue

            logger.info(f"Buscando cliente para: {usuario_a_cadastrar}...")
            nome, apolice, seguradora, select_element, id_unico = sistema.obter_proximo_cliente()
            
            if not nome or not apolice:
                if modo_geral:
                    # Incrementa passos no ciclo circular
                    passos_concluidos += 1
                    
                    # Se completou toda a lista de usuários (ciclo 360º)
                    if passos_concluidos >= len(lista_geral):
                        logger.info("Ciclo GERAL de 360º concluído por completo!")
                        break 
                    
                    usuario_a_cadastrar = lista_geral[(start_index + passos_concluidos) % len(lista_geral)]
                    logger.info(f"Sem clientes para o usuário anterior. Mudando para próximo: {usuario_a_cadastrar} ({passos_concluidos}/{len(lista_geral)})")
                    
                    # IMPORTANTE: NÃO limpamos sistema.processados.clear() para manter a persistência global
                    sistema.selecionar_usuario_menu_auditoria(usuario_a_cadastrar)
                    sistema.abrir_menu_cadastrar_no_agger()
                    continue
                else:
                    logger.info("Sem clientes pendentes na lista atual. Recarregando...")
                    sistema.processados.clear()  # Limpa para re-checar todos
                    try:
                        sistema.page.reload()
                        sistema.page.wait_for_load_state("networkidle")
                        # Tenta reabrir o menu se necessário
                        try:
                            sistema.page.click("//i[contains(@class, 'mdi-menu')]", timeout=5000)
                        except Exception:
                            pass
                        sleep(5)
                    except Exception as e:
                        logger.error(f"Erro ao recarregar página: {e}")
                        # Se o erro for de fechamento de browser ou timeout (sessão expirada), levantamos para o catch externo
                        if "timeout" in str(e).lower() or "closed" in str(e).lower() or "connection" in str(e).lower():
                            raise e
                        sleep(10)
                    continue
                
            # Controle de reload
            precisa_recarregar = True
            
            # Pré-processamento
            nome_limpo = utilitarios.limpar_nome(nome)
            apolice_tratada = utilitarios.extrair_apolice(apolice, seguradora)
            
            # Validação Pré-Bot
            if apolice_tratada == 'endosso':
                sistema.marcar_como_nao_cadastrado(select_element, recarregar=False)
                relatorio.adicionar_registro(nome, apolice, "Pulado", "Endosso detectado")
                precisa_recarregar = False

                contador_nao += 1
                if contador_nao >= 3:
                    logger.info("Executando restauração preventiva do Agger (3 marcações de 'Não')...")
                    agger.restaurar()
                    contador_nao = 0
                continue

            if not nome_limpo or not apolice_tratada:
                logger.warning("Dados incompletos após limpeza.")
                sistema.marcar_como_nao_cadastrado(select_element, recarregar=False)
                relatorio.adicionar_registro(nome, apolice, "Falha", "Dados incompletos após limpeza")
                erros_consecutivos += 1
                precisa_recarregar = False
                
                # Registra tentativa no histórico se for válida (não endosso)
                utilitarios.adicionar_ao_historico(id_unico)

                contador_nao += 1
                if contador_nao >= 3:
                    logger.info("Executando restauração preventiva do Agger (3 marcações de 'Não')...")
                    agger.restaurar()
                    contador_nao = 0
                continue
                
            # Execução no Agger
            logger.info(f"Processando: {nome_limpo} | Apólice: {apolice_tratada}")
            sucesso = agger.processar_cliente(nome_limpo, apolice_tratada, seguradora)
            
            if sucesso == "pendente":
                logger.info("Cliente com emissão pendente. Registrando...")
                relatorio_pendentes.adicionar_pendente(nome, apolice, seguradora, usuario_a_cadastrar)
                sistema.marcar_como_nao_cadastrado(select_element)
                relatorio.adicionar_registro(nome, apolice, "Pendente", "Pendente de Emissão no Agger")
                erros_consecutivos = 0
                
                # Registra sucesso/tentativa no histórico
                utilitarios.adicionar_ao_historico(id_unico)

                contador_nao += 1
                if contador_nao >= 3:
                    logger.info("Executando restauração preventiva do Agger (3 marcações de 'Não')...")
                    agger.restaurar()
                    contador_nao = 0
                continue

            if sucesso:
                logger.info("Sucesso!")
                sistema.marcar_como_cadastrado(select_element)
                relatorio.adicionar_registro(nome, apolice, "Sucesso")
                erros_consecutivos = 0
                contador_nao = 0 # Reset se sucesso
                
                # Registra sucesso no histórico
                utilitarios.adicionar_ao_historico(id_unico)
            else:
                logger.error("Falha no Agger Desktop")
                sistema.marcar_como_nao_cadastrado(select_element)
                relatorio.adicionar_registro(nome, apolice, "Falha", "Erro no Agger Desktop")
                erros_consecutivos += 1
                
                # Registra tentativa no histórico
                utilitarios.adicionar_ao_historico(id_unico)

                contador_nao += 1
                if contador_nao >= 3:
                    logger.info("Executando restauração preventiva do Agger (3 marcações de 'Não')...")
                    agger.restaurar()
                    contador_nao = 0

            if precisa_recarregar:
                try:
                    sistema.recarregar()
                except Exception as e:
                    logger.warning(f"Erro ao limpar página: {e}. Continuando...")
                    if "closed" in str(e).lower() or "connection" in str(e).lower():
                        raise e
                    
            if erros_consecutivos >= erros_limit:
                logger.error(f"Limite de erros ({erros_limit}) atingido.")
                break
                
        except Exception as e:
            msg_erro = str(e).lower()
            if "closed" in msg_erro or "connection" in msg_erro or "target" in msg_erro or "timeout" in msg_erro:
                logger.error(f"CONEXÃO PERDIDA COM O NAVEGADOR: {e}")
                logger.info("Reconexão automática...")
                
                try:
                    # Tenta encerrar o que sobrou
                    try: sistema.encerrar()
                    except: pass
                    
                    sleep(5)
                    # Reinicia a instância preservando os clientes já processados nesta rodada
                    processados_antigos = sistema.processados.copy()
                    sistema = SistemaEmissao()
                    sistema.processados = processados_antigos
                    
                    # Loga e retoma
                    configurar_sistema_fiador(sistema, usuario_a_cadastrar)
                    logger.info("Reconexão concluída com sucesso. Retomando processamento.")
                except Exception as e2:
                    logger.critical(f"Falha ao tentar reconectar: {e2}")
                    sleep(30) # Espera mais tempo antes de tentar novamente
            else:
                logger.error(f"Erro inesperado no loop principal: {e}")
                sleep(10)
        except OCRTimeoutError as e:
            logger.error(f"CPU TRAVADA (OCR TIMEOUT): {e}")
            logger.info("Aguardando 5 min para CPU...")
            
            try:
                sistema.encerrar()
            except:
                pass
            
            # Pausa de 5 minutos (300 segundos)
            sleep(300)
            
            logger.info("Retomando após pausa preventiva. Reiniciando conexão...")
            try:
                # Reinicia preservando processados
                processados_antigos = sistema.processados.copy()
                sistema = SistemaEmissao()
                sistema.processados = processados_antigos
                configurar_sistema_fiador(sistema, usuario_a_cadastrar)
            except Exception as e2:
                logger.critical(f"Falha ao tentar recompor sistema após timeout: {e2}")
                sleep(30)

    
    # Finalização
    sistema.encerrar()
    logger.info("==== FIM DA EXECUÇÃO ====")
