# 🤖 CIABot Oráculo

Sistema de Inteligência Artificial para operações agrícolas de cana-de-açúcar, desenvolvido especificamente para executivos C-Level.

## 🎯 Visão Geral

O CIABot Oráculo é um chatbot para Telegram que utiliza Inteligência Artificial para responder perguntas sobre operações agrícolas com alto nível de confiança (mínimo 90%). O sistema analisa dados de operações (plantio, corte, carregamento e transporte) armazenados em arquivos Parquet e fornece respostas precisas e relatórios em PDF.

### Características Principais

✅ **Alta Confiança**: Só responde quando tem 90% ou mais de certeza
✅ **Transparência**: Sempre indica o percentual de confiança
✅ **Honestidade**: Admite quando não sabe ou não tem dados suficientes
✅ **Relatórios PDF**: Gera relatórios detalhados sob demanda
✅ **Interface Telegram**: Acesso fácil via mobile ou desktop
✅ **Análise Inteligente**: Processa linguagem natural para entender consultas

## 🏗️ Arquitetura

```
ciabot-oraculo/
├── config/                     # Configurações do sistema
│   ├── settings.py            # Configurações centralizadas
│   └── __init__.py
├── src/
│   ├── ai/                    # Motor de Inteligência Artificial
│   │   ├── intelligence_engine.py
│   │   └── __init__.py
│   ├── bot/                   # Bot do Telegram
│   │   ├── telegram_bot.py
│   │   └── __init__.py
│   ├── data/                  # Processamento de dados
│   │   ├── parquet_processor.py
│   │   └── __init__.py
│   ├── reports/               # Geração de relatórios
│   │   ├── pdf_generator.py
│   │   └── __init__.py
│   └── utils/                 # Utilitários
│       ├── logger.py
│       └── __init__.py
├── data/                      # Diretório de dados
│   ├── parquet/              # Arquivos Parquet (seus dados)
│   ├── reports/              # Relatórios gerados
│   └── temp/                 # Arquivos temporários
├── logs/                      # Logs do sistema
├── tests/                     # Testes (futuro)
├── main.py                    # Ponto de entrada
├── requirements.txt           # Dependências Python
├── .env.example              # Exemplo de configuração
└── README.md                 # Este arquivo
```

## 📋 Pré-requisitos

- Python 3.10 ou superior
- Conta no Telegram
- API Key da Anthropic (Claude) ou OpenAI (GPT)
- Arquivos Parquet com dados das operações

## 🚀 Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/ciabot-oraculo.git
cd ciabot-oraculo
```

### 2. Crie um ambiente virtual

```bash
python -m venv venv

# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

```bash
cp .env.example .env
```

Edite o arquivo `.env` e configure:

```env
# Token do bot do Telegram
TELEGRAM_TOKEN=seu_token_aqui

# IDs de usuários autorizados (opcional)
ALLOWED_USER_IDS=123456789,987654321

# API Key da Anthropic
ANTHROPIC_API_KEY=sua_api_key_aqui

# Data de início da safra
SAFRA_INICIO=2024-04-01
```

### 5. Prepare seus dados

Coloque seus arquivos Parquet no diretório `data/parquet/`.

**Importante**: Nomeie os arquivos de forma descritiva:
- `plantio_barra_2024.parquet`
- `corte_piacatu_maio.parquet`
- `transporte_univalem.parquet`

## 🎮 Como Usar

### Iniciar o Bot

```bash
python main.py
```

O bot ficará ativo e aguardando mensagens no Telegram.

### Obter Token do Telegram

1. Abra o Telegram e procure por `@BotFather`
2. Envie `/newbot` e siga as instruções
3. Copie o token fornecido
4. Cole no arquivo `.env` na variável `TELEGRAM_TOKEN`

### Obter seu User ID

1. Procure por `@userinfobot` no Telegram
2. Inicie uma conversa
3. Copie seu ID numérico
4. Adicione ao `.env` na variável `ALLOWED_USER_IDS`

### Obter API Key da Anthropic

1. Acesse https://console.anthropic.com/
2. Crie uma conta ou faça login
3. Vá em "API Keys"
4. Crie uma nova chave
5. Copie e cole no `.env`

## 💬 Exemplos de Uso

### Comandos Disponíveis

- `/start` - Inicia o bot e mostra boas-vindas
- `/ajuda` - Mostra exemplos de uso
- `/status` - Exibe status do sistema
- `/refresh` - Atualiza índice de arquivos Parquet

### Consultas de Métricas

```
Quantos hectares a unidade Barra plantou ontem?
```

```
Qual o total de corte da Piacatu nos últimos 7 dias?
```

```
Quantas toneladas foram transportadas do início da safra até agora?
```

### Solicitação de Relatórios

```
Me envie o relatório de plantio da Barra dos últimos 7 dias
```

```
Gerar relatório hora a hora do corte de ontem
```

```
Relatório completo da safra da Univalem
```

### Análises Comparativas

```
Compare o plantio da Barra e Piacatu este mês
```

```
Evolução do corte nos últimos 30 dias
```

## 📊 Formato dos Dados

Os arquivos Parquet devem conter pelo menos estas colunas:

### Colunas Recomendadas

- `data` - Data da operação (datetime)
- `unidade` - Nome da unidade (Barra, Piacatu, etc)
- `operacao` - Tipo de operação (plantio, corte, transporte, carregamento)
- `hectares` - Área em hectares (para plantio/corte)
- `toneladas` - Massa em toneladas (para transporte/carregamento)
- `horas` - Horas trabalhadas
- `equipamento` - ID do equipamento
- `turno` - Turno de trabalho
- `frente` - Frente de trabalho

### Exemplo de Estrutura

```python
import pandas as pd
from datetime import datetime

data = {
    'data': [datetime(2024, 5, 1, 8, 0)],
    'unidade': ['Barra'],
    'operacao': ['plantio'],
    'hectares': [45.2],
    'equipamento': ['PL-001'],
    'turno': ['diurno'],
    'frente': ['Frente A']
}

df = pd.DataFrame(data)
df.to_parquet('data/parquet/plantio_barra_2024.parquet')
```

## 🔧 Configurações Avançadas

### Ajustar Threshold de Confiança

No arquivo `.env`:

```env
CONFIDENCE_THRESHOLD=0.90  # 90%
MIN_CONFIDENCE_TO_RESPOND=0.90
```

### Escolher Modelo de IA

```env
# Anthropic
AI_PROVIDER=anthropic
AI_MODEL=claude-3-5-sonnet-20241022

# Ou OpenAI
AI_PROVIDER=openai
AI_MODEL=gpt-4-turbo
```

### Configurar Logging

```env
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

## 🎨 Personalização

### Adicionar Novas Unidades

Edite `config/settings.py`:

```python
UNIDADES = [
    "Barra",
    "Piacatu",
    "Univalem",
    "São José",
    "Sua Nova Unidade",  # Adicione aqui
]
```

### Adicionar Novas Operações

```python
OPERACOES = [
    "plantio",
    "corte",
    "carregamento",
    "transporte",
    "manutencao",  # Adicione aqui
]
```

## 📈 Roadmap

- [ ] Implementação de busca vetorial com embeddings
- [ ] Sistema de aprendizado contínuo
- [ ] Dashboard web
- [ ] Suporte a múltiplos idiomas
- [ ] Integração com WhatsApp
- [ ] Alertas proativos
- [ ] Previsões e tendências
- [ ] API REST

## 🔒 Segurança

- ✅ Controle de acesso por User ID
- ✅ Logs detalhados de todas as interações
- ✅ Variáveis sensíveis em `.env` (não versionado)
- ✅ Validação de entrada de dados

### Boas Práticas

1. **Nunca** commit arquivos `.env` no Git
2. Use `ALLOWED_USER_IDS` para restringir acesso
3. Mantenha logs em local seguro
4. Rotacione API keys periodicamente
5. Monitore o uso da API

## 🐛 Troubleshooting

### Bot não responde

1. Verifique se o `TELEGRAM_TOKEN` está correto
2. Confirme que o bot está rodando (`python main.py`)
3. Verifique logs em `logs/ciabot.log`

### Erro de API Key

1. Valide se a API key está correta
2. Verifique se tem créditos disponíveis
3. Confirme o nome do modelo

### Sem dados encontrados

1. Verifique se há arquivos `.parquet` em `data/parquet/`
2. Execute `/refresh` no bot
3. Confirme que os arquivos têm as colunas esperadas

### Baixa confiança

1. Seja mais específico na pergunta (unidade, período, operação)
2. Verifique se há dados para o período solicitado
3. Confirme que os nomes das unidades correspondem aos dados

## 📝 Logs

Logs são salvos em `logs/ciabot.log` com rotação automática (máximo 10MB por arquivo, 5 backups).

Para visualizar logs em tempo real:

```bash
tail -f logs/ciabot.log
```

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto é proprietário e confidencial.

## 👥 Suporte

Para suporte, entre em contato com a equipe de desenvolvimento.

---

**CIABot Oráculo** - Inteligência Artificial para o Agronegócio 🌱
