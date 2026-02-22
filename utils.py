##################################################
#                   utils.py                     #
##################################################

# Arquivo responsável por funções utilitárias.   #
##################################################

import re
from datetime import datetime
from logger import logger
import json
import os

class Utils:
    
    def __init__(self):
        logger.info("Inicializando Utils")
        
        # Regras por seguradora
        self.REGRAS_SEGURADORAS = {
            'ALLIANZ': lambda v: re.sub(r'[\-–—]', '', v),
            'HDI': lambda v: re.sub(r'\D', '', v)[:14],
            'YELUM': lambda v: re.sub(r'\D', '', v),
            'ALIRO': lambda v: re.sub(r'\D', '', v),
            'PORTO': lambda v: re.sub(r'\D', '', v),
            'ITAU': lambda v: re.sub(r'\D', '', v),
            'ITAÚ': lambda v: re.sub(r'\D', '', v),
            'BRADESCO': lambda v: re.sub(r'\D', '', v),
            'TOKIO': lambda v: re.sub(r'\D', '', v),
            'ZURICH': lambda v: re.sub(r'\D', '', v),
            'ALFA': lambda v: re.sub(r'\D', '', v),
            'MAPFRE': lambda v: re.sub(r'\D', '', v),
            'SUHAI': lambda v: re.sub(r'\D', '', v),
            'MITSUI': lambda v: re.sub(r'\D', '', v),
            'AZUL': lambda v: re.sub(r'\D', '', v),
        }
    
    def extrair_apolice(self, valor, seguradora):
        """Extrai número da apólice"""
        logger.info(f"Extraindo apólice: valor='{valor}', seguradora='{seguradora}'")
        try:
            valor_str = str(valor).strip()
            # Verifica se é endosso
            if re.search(r'[a-zA-Z_]', valor_str):
                logger.warning(f"Apólice contém caracteres inválidos ou é endosso: '{valor_str}'.")
                return "endosso"
            
            seguradora_upper = seguradora.upper()
            
            # Aplica regra da seguradora
            if seguradora_upper in self.REGRAS_SEGURADORAS:
                regra = self.REGRAS_SEGURADORAS[seguradora_upper]
                valor_limpo = regra(valor_str)
                logger.info(f"Apólice {seguradora_upper} tratada: '{valor_limpo}'")
                return valor_limpo
            
            logger.warning(f"Seguradora '{seguradora_upper}' sem regra definida.")
            return None
                
        except Exception as e:
            logger.error(f"Erro ao extrair apólice: {str(e)}")
            return None
   
    def data_hoje(self):
        """Data hoje (DD/MM/YYYY)"""
        return datetime.now().strftime("%d/%m/%Y")

    def limpar_nome(self, nome):
        """Limpa e formata nome do cliente"""
        logger.info(f"Limpando nome: '{nome}'")
        nome = nome.upper()
        
        PALAVRAS_REMOVER = [
            # === DOCUMENTOS/ARQUIVOS ===
            '(12.PDF', 'ARQUIVO', 'PDF', '.PDF.PDF', '.PDFF', 'PDFF', 'DOCUMENTO', 'CERTIFICADO', 'NOTA FISCAL', 'RECIBO', 'BOLETO', 'COMPROVANTE', 
            'DECLARAÇÃO', 'APÓLICE', 'PROPOSTA', 'CONTRATO', 'FATURA', 'PROCESSAMENTO', 'Nº', 'PROPOS', 'FILE', '(C)', 'SCAN', 'SCANEADO', 'ARQUIV',
            'RECONSTITUIÇÃO', 'RECONSTITUICAO',

            # === MARCAS DE CARROS ===
            'ACURA', 'ALFA', 'ALFA ROMEO', 'ASTON MARTIN', 'AUDI', 'BMW', 'BUGATTI', 'BUICK', 'CADILLAC', 'CHERY', 'CHEVROLET', 'CHRYSLER', 'CITROËN', 'DODGE', 'FERRARI', 'FIAT', 'FORD', 'GMC', 'HONDA', 'HYUNDAI', 'JAGUAR', 'JEEP', 'KIA', 'LAMBORGHINI', 'LAND ROVER', 'LEXUS', 'MASERATI', 'MAZDA', 'MCLAREN', 'MERCEDES-BENZ', 'MINI', 'MITSUBISHI', 'NISSAN', 'PEUGEOT', 'PORSCHE', 'RENAULT', 'ROLLS-ROYCE', 'SUBARU', 'SUZUKI', 'TESLA', 'TOYOTA', 'VOLKSWAGEN', 'VOLVO', 'GREAT WALL', 'HAVAL', 'TATA', 'MAHINDRA',

            # === MODELOS DE CARROS ===
            '1UNO', '2008', '206', '207', '208', 'TERA', '3008', '320I', '330E', '407', '408', '500', '508', '911', 'A3', 'A4', 'A5', 'A6', 'ACCENT', 'ADVENTURE', 'AGGER', 'ALIRO', 'ALLROAD', 'AMAROK', 'ARCO', 'ARGGO', 'ARGO', 'ARGU', 'ARRIZO 5', 'ARRIZO 6', 'ARRIZO 8', 'ASTRA', 'ASX', 'ATOS', 'AZERA', 'BERLINGO', 'BLAZER', 'C0MPASS', 'C0RSA', 'C180', 'C200', 'C3', 'C3 AIRCROSS', 'C300', 'C4', 'C4 CACTUS', 'C4 PALLAS', 'C6', 'CAMRY', 'CAPTIVA', 'CAPTUR', 'CAROLA', 'CAYENNE', 'CELTA', 'CELTTA', 'CERETA', 'CHEROKEE', 'CITY', 'CIVIC', 'CLA', 'CLIO', 'COBALT', 'COMMANDER', 'COMPAS', 'COMPASS', 'COMPPAS', 'COMPPASS', 'CORCEL', 'COROLA', 'COROLA CROS', 'COROLA CROSS', 'COROLAA', 'COROLLA', 'COROLLA CROS', 'COROLLA CROSS', 'CORR0LA', 'CORSA', 'CORSSA', 'CORZA', 'CR-V', 'CR3TA', 'CREITA', 'CRETA', 'CRON0S', 'CRONOS', 'CRONOSS', 'CRONUS', 'CROSS', 'CROSS PLUS', 'CROSSFOX', 'CRUSE', 'CRUZE', 'CRUZE SPORT6', 'CRUZEI', 'CRUZEZ', 'CUP', 'CÉLTA', 'DEFENDER', 'DISCOVERY', 'DISCOVERY SPORT', 'DOBLÒ', 'DUSTER', 'ECLIPSE CROSS', 'ECO SPORT', 'ECOSPOR', 'ECOSPORT', 'ECOSPORTT', 'EDGE', 'ESCORT', 'ETIOS', 'ETIOSS', 'ETIUS', 'ETYOS', 'FIESTA', 'FIESTA CAR', 'FIESTAA', 'FIORINO', 'FIT', 'FIÉSTA', 'FOCUS', 'FOX', 'FRONTIER', 'FUSION', 'G0L', 'GLA', 'GLC', 'GLE', 'GLS', 'GOL', 'GOLF', 'GOLL', 'GRAND CHEROKEE', 'GRAND VITARA', 'GT', 'GT LINE', 'GT PERFORMANCE', 'GT PREMIUM', 'GT SPORT', 'GTE', 'GTI', 'H B20', 'HB 20', 'HB-20', 'HB20', 'HB20S', 'HB20X', 'HB2O', 'HB2O', 'HD20', 'HI-LUX', 'HILUX', 'HILUXE', 'HR-V', 'HYLUX', 'IDEA', 'IX35', 'JETA', 'JETAO', 'JETTA', 'JETTAA', 'JIMNY', 'JUMPY', 'KA', 'KA SEDAN', 'KA+', 'KAA', 'KICKS', 'KWID', 'KÁ', 'L200', 'LANCER', 'LIBERTY', 'LINEA', 'LIVINA', 'LOGAN', 'LX', 'LX PLUS', 'LXS', 'M0BI', 'M3', 'M5', 'MACAN', 'MARCH', 'MAVERIC', 'MAVERICK', 'MEGANE', 'MERIVA', 'MOBBI', 'MOBY', 'MONDEO', 'MONTANA', 'NIVUS', 'NOMAD', 'ONIX', 'ONIX PLUS', 'ONIX PLUSS', 'ONIX PLUUS', 'ONIX+', 'ONIXE', 'ONIXX', 'ONYX', 'OROCH', 'OUTLANDER', 'PAJERO FULL', 'PAJERO SPORT', 'PAJERO TR4', 'PALIO', 'PALIO WEEKEND', 'PANAMERA', 'PARATI', 'PASSAT', 'PICASSO', 'POLO', 'POLOO', 'POLOU', 'PRISMA', 'PRIUS', 'PUNTO', 'Q3', 'Q5', 'Q7', 'QQ', 'R', 'R-LINE', 'R-LINE BLACK', 'RANGE ROVER', 'RANGE ROVER EVOQUE', 'RANGE ROVER SPORT', 'RANGE ROVER VELAR', 'RANGER', 'RANGR', 'RANGUER', 'RANJER', 'RAV4', 'RCZ', 'RENAGADE', 'RENEGADE', 'RENEGAID', 'RENEGATE', 'S', 'S-10', 'S.10', 'S10', 'S1O', 'S60', 'S90', 'SANDERO', 'SANDERO STEPWAY', 'SANTA FÉ', 'SAVEIRO', 'SAVEIROS', 'SAVERIO', 'SAVERO', 'SCÉNIC', 'SELTA', 'SENTRA', 'SIENA', 'SONATA', 'SPIN', 'STILO', 'STRAD', 'STRADA', 'STRADDA', 'SUHAI', 'SW4', 'SWIFT', 'SX4', 'SYMBOL', 'T CROSS', 'T-CROS', 'T-CROSS', 'TAOS', 'TAYCAN', 'TCR0SS', 'TCROSS', 'TIGGO 2', 'TIGGO 3X', 'TIGGO 5X', 'TIGGO 7', 'TIGGO 8', 'TIGUAN', 'TIIDA', 'TITANIUM', 'TOR0', 'TORO', 'TORRO', 'TOURO', 'TRACKER', 'TRAIL', 'TRAIL PLUS', 'TRAILBLAZER', 'TRAILHAWK', 'TROCSS', 'TT', 'TUCSON', 'TUCSSON', 'TUCÇON', 'TUKSON', 'URBAN', 'V6', 'V8', 'VECTRA', 'VELOSTER', 'VERONA', 'VERSA', 'VERSA NOTE', 'VIRTUS', 'VIRTUSS', 'VIRTUUS', 'VOIAGE', 'VOYAG', 'VOYAGE', 'VOYAJE', 'VXR', 'WR-V', 'WRANGLER', 'X', 'X-TRAIL', 'X1', 'X2', 'X3', 'X4', 'X5', 'X6', 'X7', 'XC40', 'XC60', 'XC90', 'XLT', 'XSARA', 'YARIS', 'YARISS', 'YARISSE', 'YARIZ', 'ZAFIRA', 'ÔNIX',

            # === BANCOS ===
            'BANCO', 'BANCO DO BRASIL', 'BANCO VOLKSWAGEN', 'BANCO TOYOTA', 'BANCO HONDA', 'BTG PACTUAL', 'VOTORANTIM', 
            'PAGSEGURO', 'PAGBANK', 'SICREDI', 'SICOOB', 'DAYCOVAL', 'BANRISUL', 'SANTANDER', 'BRADESCO', 'BRADES', 'NUBANK', 
            'ORIGINAL', 'C6 BANK', 'BCO DO', 'BANCO DA', 'FINANCIAMENTO', 'VOLKSWAGEN', 'TOYOTA', 'HONDA', 'ITAÚ', 'ITAU', 
            'CAIXA', 'SAFRA', 'C6', 'BV', 'CEF', 'BCO', 'BB', 'PAN', 'BMG', 'NEON', 'INTER', 'RCI', 'CAIXA ECONÔMICA FEDERAL', 
            'ITAÚ UNIBANCO', 'BRAD', 'BTG',

            # === SEGURADORAS ===
            'ALLIANZ', 'ASSIM SEGURADORA', 'AXA', 'BRADESCO SEGUROS', 'CNA', 'GENERALI', 'HDI', 'ICATU', 'LIBERTY SEGUROS',
            'MAPFRE', 'METLIFE', 'MONGERAL AEGON', 'PORTO', 'PRUDENTIAL', 'QUALITAS', 'SAFRA SEGUROS', 'SUL AMERICA', 
            'TOKIO', 'ZURICH', 'YELUM', 'ALIRO', 'SUHAI', 'AZUL', 'MITSUI', 'CNA SEGUROS', 'HDI SEGUROS', 'ICATU SEGUROS', 
            'PORTO SEGURO', 'SUL AMÉRICA', 'TOKIO MARINE', 'ZURICH SEGUROS', 'AMIL', 'SAUDE', 'CONSORCIO', 'AINZ', 'ALIZ', 'LIBER', 'POR',

            # === TERMOS DE SEGUROS ===
            'APROVAÇÃO', 'CANC', 'CANCELADA', 'CANCELAMENTO', 'CONDIÇÃO', 'DESCONTO', 'ENDOSSO', 'INDENIZAÇÃO', 'PRAZO', 
            'PRODUTO', 'RENOVAÇÃO', 'RENOVAÇÃO AUTOMÁTICA', 'SEG', 'SEG.', 'SEGURADORA', 'SEGURO', 'TIPO DE SEGURO', 
            'VIGÊNCIA', 'VALOR', 'VALOR TOTAL', 'RENOV', 'RENOVACAO', 'SINISTRO', 'PRIMEIRA', 'PARCELA', 'RESTIUIAO',

            # === CATEGORIAS/VERSÕES DE CARROS ===
            'ACTIVE', 'ACTIVE PLUS', 'ADVANCE', 'ADVENTURE PACK', 'AMBIENTE', 'BLACK EDITION', 'CLASSIC', 'COMFORT', 
            'CONNECT', 'DESIGN', 'DIAMOND', 'DYNAMIC', 'DYNAMIC PLUS', 'DYNAMIC SPORT', 'EDITION', 'EDITION ONE', 
            'ELEGANCE', 'ELITE', 'ELITE PLUS', 'EMOTION', 'EXCLUSIVE', 'EXECUTIVE', 'EXECUTIVE PACK', 'EXL', 'GL', 'GLX', 
            'GLX PLUS', 'HIGHLINE', 'HYBRID', 'HYBRID AWD', 'LIMITED', 'LIMITED EDITION', 'LUXURY', 'LUXURY LINE', 
            'OFFROAD', 'PLATINUM', 'PLUS', 'POWER', 'PREMIUM', 'PRESTIGE', 'RACING', 'RS', 'RS LINE', 'RS TURBO', 
            'S-LINE', 'SE', 'SE PLUS', 'SEL', 'SEL PREMIUM', 'SIGNATURE', 'SPORT', 'SPORT DESIGN', 'SPORT LINE', 
            'SPORT PLUS', 'SPORTBACK', 'SPORTING', 'STYLE', 'TOP', 'TURBO', 'TURBO PLUS', 'ULTIMATE',

            # === TERMOS FINANCEIROS/ADMINISTRATIVOS ===
            'ACRESCIMO', 'ALTERAÇÃO', 'ANÁLISE', 'APL', 'AUTORIZAÇÃO', 'BENEFICIÁRIO', 'CADASTRAL', 'CADASTRO', 'CADASTROU', 
            'CATEGORIA', 'CLIENTE', 'CNPJ', 'CONTA', 'CPF', 'CTPJ', 'DATA', 'DESCRIÇÃO', 'DETALHE', 'EIREL', 'EIRELI', 
            'EIRELI ME', 'EMAIL', 'EMPRESARIAL', 'END', 'END DE CORREÇÃO', 'ENDERECO', 'ENDEREÇO', 'EPP', 'FORMA DE PAGAMENTO', 
            'HORA', 'INCLUSÃO', 'INFORMAÇÃO', 'ITEM', 'JUROS', 'LIQUIDAÇÃO', 'LTD', 'LTDA', 'ME', 'NOME', 'NÃO', 'OBSERVAÇÃO', 
            'OBSERVAÇÕES', 'PESSOAIS', 'PLANO', 'PROP', 'PROP.', 'REF', 'REFEITA', 'REJEIÇÃO', 'RENV', 'RESD', 'RESIDENCIAL', 
            'RETIFIAÇÃO', 'RETIFIAÇÃO PLACA', 'RETIFICA', 'RETIFICADA', 'SOCIAL', 'STATUS', 'SUBST', 'SUBS', 'SUBSTITUIÇÃO', 'SUBSTITUICAO', 
            'INCLUSAO', 'SUBCATEGORIA', 'TAXA', 'TELEFONE', 'TIPO', 'TRANSFERÊNCIA', 'TROCA', 'VALIDAÇÃO', 'VENCIMENTO', 
            'VERIFICAÇÃO', 'VIAGEM', 'VIDA', 'MERCUSUL', 'VENCTO', 'ESTADO CIVIL', 'COBRANÇA', 'COBRANA', 'SEGURADO', 
            'SOLTEIRO', 'PEDIDO', 'PLACA', 'VENDA', 'MOTO', 'COM', 'PRA', 'PRO', 'SUBS', 'UNO', 'AP', 'A PEDIDO', 'PARA',
            'ACEITOU', 'ACEITA', 'RECUSADA', 'PEND', 'PENDENCIA', 'ALT', 'VLD', 'BANCARIA', 'BANC', 'CARTAO', 'CART', 
            'DADOS', 'NASC', 'ESPOLIO', 'CONDUTOR', 'RETIF', 'RETI', 'RET', 'RETIFICAÇÃO', 'RETIFICACAO',
            'ALTERAÇAO', 'ALTERAAO', 'ALTE', 'ALTER',

            # === CORES ===
            'AZUL', 'BRANCO',

            # === OUTROS / DATAS ===
            '2023', '2024', '2025', '2026', 'JANEIRO', 'FEVEREIRO', 'MARÇO', 'ABRIL', 'MAIO', 'JUNHO', 'JULHO', 'AGOSTO', 
            'SETEMBRO', 'OUTUBRO', 'NOVEMBRO', 'DEZEMBRO', 'ACID', 'AGÊNCIA', 'AMÉRICA', 'CARTÃO', 'DE TELEFONEGOL', 
            'CEL', 'CARTA VERDE', 'RCF', 'FXJ', 'NOVOC', 'UGBD', 
            'EX', 'EXS', 'EXCLUSÃO', 'EXECUÇÃO', 'NOVA', 'NOVO', 'OCEAN', 'PERFORMANCE', 'S.A.', 'S.A. EIRELI', 'S.A. EPP', 
            'S.A. LTDA ME', 'S/A', 'S/A EIRELI', 'S/A EPP', 'S/A LTDA', 'SERVIÇO', 'SL', 'SLT', 'TREKKING', 'UN0', 'UNNO', 
            'UP', 'ALT', 'ALT.', 'PERFIL', 'GARAGEM', 'REBOQUE', 'GUINCHO', 'CARRO', 'CAMINHÃO', 'CAMINHAO', 'AUTO', 
            'PICKUP', 'CAMIONETE', 'ESTRADA', 'VLD', 'CASADO', 'CASADA', 'DIVORCIADO', 'DIVORCIADA', 'VIÚVO', 'VIUVO', 
            'VIÚVA', 'VIUVA', 'PRIMEIRA', 'PERNOITE', 'JOVEM', 'INCLUIR', 'VINCULO', 'FOTO', 
            'RESTAURADO', 'RECUPERADO', 'ROUBO', 'FURTO', 'PERDA', 'SINISTRADO', 'TOTAL', 'PLACA', 'PERFIL', 'VENDA', 'SEM'
        ]
        
        # Ordena por tamanho para precisão
        palavras_ordenadas = sorted(PALAVRAS_REMOVER, key=len, reverse=True)
        
        for palavra in palavras_ordenadas:
            nome = re.sub(rf"\b{re.escape(palavra)}\b", "", nome)
        
        # Remove especiais e espaços
        nome = re.sub(r"[^A-Z ]", "", nome)
        nome = re.sub(r"\s+", " ", nome).strip()
        
        logger.info(f"Nome limpo: '{nome}'")
        return nome

    def salvar_progresso(self, start_index, passos_concluidos, ids_processados, arquivo="progresso_geral.json"):
        """Salva progresso circular e IDs"""
        try:
            dados = {
                "start_index": start_index,
                "passos_concluidos": passos_concluidos,
                "ids_processados": list(ids_processados)
            }
            with open(arquivo, 'w', encoding='utf-8') as f:
                json.dump(dados, f, indent=4)
            logger.info(f"Progresso salvo no arquivo: {arquivo} (Passos: {passos_concluidos})")
        except Exception as e:
            logger.error(f"Erro ao salvar progresso: {e}")

    def carregar_progresso(self, arquivo="progresso_geral.json"):
        """Carrega progresso salvo"""
        if not os.path.exists(arquivo):
            return 0, 0, set()
        
        try:
            with open(arquivo, 'r', encoding='utf-8') as f:
                dados = json.load(f)
            
            # Suporta formatos antigo e novo
            start_index = dados.get("start_index", dados.get("index_geral", 0))
            passos = dados.get("passos_concluidos", 0)
            ids = set(dados.get("ids_processados", []))
            
            logger.info(f"Progresso carregado: Inicial={start_index}, Concluídos={passos}, Histórico={len(ids)} IDs")
            return start_index, passos, ids
        except Exception as e:
            logger.error(f"Erro ao carregar progresso: {e}")
            return 0, 0, set()

    def limpar_progresso(self, arquivo="progresso_geral.json"):
        """Deleta arquivo de progresso ao concluir"""
        if os.path.exists(arquivo):
            try:
                os.remove(arquivo)
                logger.info(f"Arquivo de progresso {arquivo} removido (ciclo concluído).")
            except Exception as e:
                logger.error(f"Erro ao remover arquivo de progresso: {e}")