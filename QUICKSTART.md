# 🚀 Quick Start Guide - CIABot Oráculo

Guia rápido para colocar o CIABot Oráculo em funcionamento em **menos de 10 minutos**.

## ⚡ Passo a Passo Rápido

### 1️⃣ Instalar Dependências (2 min)

```bash
# Clone o repositório (se ainda não fez)
cd ciabot-oraculo

# Crie e ative ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instale dependências
pip install -r requirements.txt
```

### 2️⃣ Criar Bot no Telegram (2 min)

1. Abra o Telegram
2. Procure por: `@BotFather`
3. Envie: `/newbot`
4. Escolha um nome: `MeuOraculoBot`
5. Escolha um username: `meuciabot_bot`
6. **Copie o token** fornecido (algo como: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)

### 3️⃣ Obter API Key da Anthropic (2 min)

1. Acesse: https://console.anthropic.com/
2. Crie uma conta (ou faça login)
3. Vá em "API Keys"
4. Clique em "Create Key"
5. **Copie a API key**

### 4️⃣ Configurar (1 min)

```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite o arquivo .env
nano .env  # ou use seu editor favorito
```

**Edite apenas estas linhas:**

```env
TELEGRAM_TOKEN=cole_seu_token_aqui
ANTHROPIC_API_KEY=cole_sua_api_key_aqui
```

Salve e feche o arquivo.

### 5️⃣ Gerar Dados de Exemplo (1 min)

```bash
python scripts/generate_sample_data.py
```

Isso criará arquivos Parquet de exemplo com 60 dias de dados para 4 unidades.

### 6️⃣ Iniciar o Bot (10 seg)

```bash
python main.py
```

Você verá:

```
==================================================
CIABot Oráculo - Iniciando sistema
==================================================
...
Bot iniciado e aguardando mensagens...
```

### 7️⃣ Testar no Telegram (1 min)

1. Abra o Telegram
2. Procure pelo username do seu bot (ex: `@meuciabot_bot`)
3. Clique em "Iniciar" ou envie: `/start`
4. Experimente:

```
Quantos hectares a Barra plantou nos últimos 7 dias?
```

```
Me envie o relatório de plantio da Piacatu
```

## ✅ Pronto!

Seu CIABot Oráculo está funcionando!

---

## 🔧 Resolução de Problemas Rápida

### Bot não responde?

```bash
# Verifique se está rodando
# Veja logs:
tail -f logs/ciabot.log
```

### Erro de autenticação?

- Confirme que copiou o token corretamente (sem espaços)
- Verifique se a API key está correta

### "Sem dados encontrados"?

```bash
# Rode novamente o gerador:
python scripts/generate_sample_data.py

# No bot, envie:
/refresh
```

---

## 📱 Comandos Úteis

| Comando | Descrição |
|---------|-----------|
| `/start` | Inicia o bot |
| `/ajuda` | Mostra exemplos |
| `/status` | Status do sistema |
| `/refresh` | Atualiza dados |

---

## 💡 Exemplos de Perguntas

**Métricas:**
- `Quantos hectares a Barra plantou ontem?`
- `Qual o total de corte da Piacatu nos últimos 7 dias?`
- `Quantas toneladas a Univalem transportou este mês?`

**Relatórios:**
- `Me envie o relatório de plantio da Barra`
- `Gerar relatório hora a hora do corte de ontem`
- `Relatório completo da safra`

---

## 📊 Usando Seus Próprios Dados

Para usar seus dados reais:

1. Coloque arquivos `.parquet` em: `data/parquet/`
2. Nomeie descritivamente: `operacao_unidade_periodo.parquet`
3. Exemplo: `plantio_barra_2024.parquet`
4. No bot, envie: `/refresh`

### Colunas Necessárias

Seus arquivos Parquet devem ter:

- `data` - Data/hora (datetime)
- `unidade` - Nome da unidade (str)
- `operacao` - Tipo de operação (str)
- `hectares` ou `toneladas` - Métricas (float)

---

## 🎯 Próximos Passos

1. ✅ Bot funcionando
2. 📊 Adicione seus dados reais
3. 👥 Configure usuários autorizados no `.env`
4. 🔒 Adicione restrições de acesso
5. 📈 Explore análises avançadas

---

## 📚 Documentação Completa

Para mais detalhes, consulte: [README.md](README.md)

---

**Precisando de ajuda?** Entre em contato com a equipe de desenvolvimento.

---

**CIABot Oráculo** 🤖🌱
