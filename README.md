# 🤖 Sistema de Automação de Cadastro de Apólices (Modernizado)

Sistema robusto de automação para cadastro de apólices de seguros no **Agger Desktop**, utilizando dados extraídos do **FiadorWeb**.

---

## 📋 Descrição do Projeto

Este sistema automatiza o fluxo completo de cadastro, desde a extração na web até a inserção no sistema desktop, com foco em **estabilidade e performance**.

1. **Acessa o FiadorWeb** (Playwright - Alta Performance)
2. **Extrai dados de clientes** (Tabelas dinâmicas)
3. **Mecanismo de OCR Moderno** (EasyOCR - Modo CPU para Estabilidade)
4. **Cadastra no Agger Desktop** (PyAutoGUI + Visão Computacional)
5. **Relatórios Automáticos** (Geração de logs e arquivos CSV/Excel)
6. **Sistema de Autocura** (Detecção de travamentos e pausas preventivas)

---

## 🏗️ Estrutura do Projeto

```
Projeto_apolices/
│
├── main.py                 # Orquestrador com tratamento de erros global
├── navegador.py            # Automação Web (Playwright)
├── agger_bot.py            # Automação Desktop (PyAutoGUI)
├── reconhecimento.py       # Motor OCR (EasyOCR) e Visão Computacional
├── utils.py                # Limpeza de nomes e regras de apólices
├── relatorios.py           # Geração de relatórios de sucesso/pendência
├── logger.py               # Sistema de log rotativo (preserva histórico)
├── .env                    # Configurações sensíveis (usuário/senha)
│
├── imagens/                # Templates para reconhecimento visual
└── logs/                   # Histórico de execução e debug
```

---

## 🔧 Tecnologias Utilizadas

- **Playwright** - Automação web moderna (substituiu o Selenium)
- **EasyOCR** - Reconhecimento de texto (substituiu o Tesseract para maior precisão)
- **PyAutoGUI** - Controle de periféricos (mouse/teclado)
- **OpenCV** - Comparação de templates de imagem
- **MSS** - Capturas de tela ultra rápidas

---

## 🛡️ Estabilidade e Modernização

O sistema foi atualizado para suportar execuções de longa duração (24/7):

### 1. OCR em Modo CPU
O motor EasyOCR foi configurado para rodar em modo **CPU**. Isso garante que o bot não apresente instabilidade em máquinas sem placa de vídeo dedicada ou com múltiplos monitores.

### 2. Timeout e Autocura
Cada operação de OCR possui um **limite de 60 segundos**. Caso o sistema trave (excesso de carga ou congelamento da aplicação desktop), o bot:
- Fecha o navegador automaticamente.
- Aguarda **5 minutos** para descompressão da CPU.
- Realiza o login novamente e retoma o trabalho sem perder o progresso.

### 3. Ciclo de Descanso de 3 Horas
A cada 3 horas de trabalho ininterrupto, o bot realiza uma **pausa preventiva de 5 minutos**. Isso limpa cache, memória e evita lentidão acumulada no sistema operacional.

### 4. Otimização de Performance
O sistema detecta "Endossos" e dados inválidos antes de iniciar a automação desktop. Nesses casos, o status é atualizado no FiadorWeb **sem recarregar a página**, economizando até 40% de tempo por ciclo.

---

## 📦 Instalação

1. **Dependências**:
```bash
pip install playwright easyocr pyautogui opencv-python mss python-dotenv
playwright install chromium
```

2. **Configuração**:
Crie um arquivo `.env` na raiz:
```env
FIADOR_URL_JUNDIAI=https://...
FIADOR_USER_JUNDIAI=seu_usuario
FIADOR_PASS_JUNDIAI=sua_senha
```

---

## 🚀 Como Usar

1. Execute o `main.py`.
2. Informe o limite de erros para a sessão.
3. Escolha o usuário para auditoria.
4. O bot assumirá o controle. **Mantenha as mãos longe do mouse durante a execução no Agger.**

---

## 📝 Regras de Negócio

- **Nomes**: O sistema limpa automaticamente nomes de montadoras, modelos de carros e seguradoras antes de pesquisar no Agger.
- **Apólices**: Cada seguradora possui uma regra específica de limpeza (ex: Allianz remove hífens, HDI limita tamanho).
- **Status**: Clientes marcados como "Pendente de Emissão" pelo OCR são registrados em um relatório separado para verificação manual posterior.

---

## 👨‍💻 Observações Técnicas
As coordenadas de clique são baseadas no monitor principal. Para ajustes em resoluções diferentes, verifique as configurações em `get_monitor_principal()` no arquivo de utilitários de monitor.
