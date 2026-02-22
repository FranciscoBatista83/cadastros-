##################################################
#                 relatorios.py                  #
##################################################

# Arquivo responsável pela gestão de relatórios.  #
##################################################
import csv
import os
from datetime import datetime
from logger import logger

class Relatorio:
    def __init__(self, filename="relatorio_final.csv"):
        self.filename = filename
        self.headers = ["Horário", "Cliente", "Apólice", "Status", "Motivo da Falha"]
        self._inicializar()

    def _inicializar(self):
        """Cria o arquivo com cabeçalhos se não existir"""
        if not os.path.exists(self.filename):
            with open(self.filename, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(self.headers)

    def adicionar_registro(self, cliente, apolice, status, motivo=""):
        """Adiciona registro ao relatório"""
        horario = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(self.filename, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([horario, cliente, apolice, status, motivo])
            logger.info(f"Registro adicionado ao relatório: {cliente} - {status}")
        except Exception as e:
            logger.error(f"Erro ao escrever no relatório: {e}")

class RelatorioPendentes:
    def __init__(self, filename="pendentes_emissao.csv"):
        self.filename = filename
        self.headers = ["Nome", "Número Apólice", "Seguradora", "Vendedor"]
        self._inicializar()

    def _inicializar(self):
        """Cria o arquivo com cabeçalhos se não existir"""
        if not os.path.exists(self.filename):
            with open(self.filename, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(self.headers)

    def ja_existe(self, nome, apolice):
        """Evita duplicatas em pendentes"""
        if not os.path.exists(self.filename):
            return False
        
        try:
            with open(self.filename, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Verifica as colunas principais
                    if row.get('Nome') == nome and row.get('Número Apólice') == apolice:
                        return True
        except Exception as e:
            logger.error(f"Erro ao ler planilha de pendentes: {e}")
        return False

    def adicionar_pendente(self, nome, apolice, seguradora, vendedor):
        """Adiciona pendente sem duplicar"""
        if self.ja_existe(nome, apolice):
            logger.info(f"Pendente já registrado anteriormente: {nome}")
            return False

        try:
            with open(self.filename, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([nome, apolice, seguradora, vendedor])
            logger.info(f"Salvo em Pendentes de Emissão: {nome} | Seg: {seguradora} | Vendedor: {vendedor}")
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar em pendentes: {e}")
            return False
