# 🚀 Features Avançadas - CIABot Oráculo

Documentação das funcionalidades avançadas implementadas no CIABot Oráculo.

## 📑 Índice

1. [API REST](#api-rest)
2. [Busca Vetorial com Embeddings](#busca-vetorial)
3. [Sistema de Aprendizado Contínuo](#aprendizado-continuo)
4. [Previsões e Análise de Tendências](#previsoes)
5. [Integração com Dashboard](#dashboard) ⚠️ **EM DESENVOLVIMENTO**
6. [Integração com WhatsApp](#whatsapp) ⚠️ **EM DESENVOLVIMENTO**
7. [Alertas Proativos](#alertas-proativos) ⚠️ **EM DESENVOLVIMENTO**

---

## 🌐 API REST

A API REST permite integração HTTP com o CIABot Oráculo.

### Iniciar API

```bash
# Método 1: Usando arquivo dedicado
python api_server.py

# Método 2: Diretamente
python -m uvicorn src.api.rest_api:app --host 0.0.0.0 --port 8000
```

### Configuração

Adicione ao `.env`:

```env
API_KEY=sua-api-key-secreta
API_PORT=8000
API_HOST=0.0.0.0
```

### Documentação Interativa

Acesse: `http://localhost:8000/docs`

### Endpoints Principais

#### POST /query
Processa consulta do usuário

```bash
curl -X POST "http://localhost:8000/query" \
  -H "Authorization: Bearer sua-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Quantos hectares a Barra plantou ontem?",
    "user_id": 123
  }'
```

**Resposta:**
```json
{
  "success": true,
  "response": "✅ Confiança: 95%\n\nA unidade Barra plantou 45.2 hectares ontem.",
  "confidence": 0.95,
  "intent": "metric_query",
  "data_available": true,
  "timestamp": "2024-05-15T10:30:00"
}
```

#### GET /status
Status do sistema

```bash
curl -X GET "http://localhost:8000/status" \
  -H "Authorization: Bearer sua-api-key"
```

#### POST /predictions/forecast
Gera previsão

```bash
curl -X POST "http://localhost:8000/predictions/forecast" \
  -H "Authorization: Bearer sua-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "metric": "hectares",
    "unidade": "Barra",
    "operacao": "plantio",
    "periods": 7
  }'
```

#### GET /analytics/trend
Analisa tendência

```bash
curl -X GET "http://localhost:8000/analytics/trend?metric=hectares&unidade=Barra" \
  -H "Authorization: Bearer sua-api-key"
```

### Exemplos de Integração

#### Python
```python
import requests

API_URL = "http://localhost:8000"
API_KEY = "sua-api-key"

headers = {"Authorization": f"Bearer {API_KEY}"}

# Query
response = requests.post(
    f"{API_URL}/query",
    json={"query": "Quantos hectares a Barra plantou ontem?"},
    headers=headers
)

result = response.json()
print(f"Resposta: {result['response']}")
print(f"Confiança: {result['confidence']*100}%")
```

#### JavaScript
```javascript
const API_URL = "http://localhost:8000";
const API_KEY = "sua-api-key";

async function query(text) {
    const response = await fetch(`${API_URL}/query`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${API_KEY}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query: text })
    });

    return await response.json();
}

// Uso
query("Quantos hectares a Barra plantou ontem?")
    .then(result => console.log(result));
```

---

## 🔍 Busca Vetorial com Embeddings

Sistema de busca semântica usando embeddings.

### Instalação

Descomente no `requirements.txt`:
```bash
pip install chromadb sentence-transformers
```

### Uso

```python
from src.ai.vector_search import VectorSearch

# Inicializa
vector_search = VectorSearch()

# Indexa dados históricos
historical_data = [
    {
        "unidade": "Barra",
        "operacao": "plantio",
        "data": "2024-05-15",
        "hectares": 45.2
    },
    # ... mais dados
]

vector_search.index_historical_data(historical_data)

# Busca queries similares
similar = vector_search.search_similar_queries(
    "quantos hectares foram plantados?"
)

# Busca conhecimento
knowledge = vector_search.search_knowledge(
    "plantio barra",
    category="plantio"
)
```

### Funcionalidades

- **Busca semântica**: Encontra consultas similares mesmo com palavras diferentes
- **Histórico de queries**: Armazena e busca queries anteriores
- **Base de conhecimento**: Indexa e busca conhecimento específico do domínio
- **Multilíngue**: Suporta português e outros idiomas

---

## 🧠 Sistema de Aprendizado Contínuo

O sistema aprende com cada interação e melhora ao longo do tempo.

### Funcionalidades

1. **Aprende padrões** de consultas bem-sucedidas
2. **Identifica falhas** recorrentes
3. **Mapeia terminologia** específica do usuário
4. **Rastreia métricas** de desempenho

### Uso

```python
from src.ai.continuous_learning import ContinuousLearning

# Inicializa
learning = ContinuousLearning()

# Registra interação
learning.record_interaction(
    query="Quantos hectares a Barra plantou?",
    response={
        "success": True,
        "confidence": 0.95,
        "intent": "metric_query"
    },
    params={
        "unidade": "Barra",
        "operacao": "plantio"
    },
    user_id=123
)

# Obtém insights
insights = learning.get_learned_insights()
print(f"Taxa de sucesso: {insights['success_rate']}%")
print(f"Consultas mais comuns: {insights['common_queries']}")

# Sugestões para query
suggestions = learning.get_suggestions_for_query(
    "quantos hectares foram plantados?"
)

# Exporta dados de aprendizado
learning.export_learning_data()
```

### Métricas Rastreadas

- Total de interações
- Taxa de sucesso
- Confiança média
- Intents mais comuns
- Unidades mais consultadas
- Operações mais consultadas
- Consultas problemáticas

---

## 📈 Previsões e Análise de Tendências

Motor avançado de análise preditiva.

### Funcionalidades

#### 1. Análise de Tendência

```python
from src.analytics.predictions import PredictionsEngine
import polars as pl

predictions = PredictionsEngine()

# Carrega dados
df = pl.read_parquet("data/parquet/plantio_barra.parquet")

# Analisa tendência
trend = predictions.analyze_trend(df, metric_column="hectares")

print(f"Direção: {trend['direction']}")  # crescente/decrescente/estável
print(f"Variação: {trend['percent_change']}%")
print(f"Volatilidade: {trend['volatility']}")
```

#### 2. Previsões

```python
# Prevê próximos 7 dias
forecast = predictions.predict_next_values(
    df=df,
    metric_column="hectares",
    periods=7
)

for day in forecast['forecast']:
    print(f"Data: {day['date']}")
    print(f"Valor previsto: {day['predicted_value']}")
    print(f"Confiança: {day['confidence']*100}%")
```

#### 3. Comparação de Períodos

```python
from datetime import datetime

comparison = predictions.compare_periods(
    df=df,
    metric_column="hectares",
    period1_start=datetime(2024, 4, 1),
    period1_end=datetime(2024, 4, 30),
    period2_start=datetime(2024, 5, 1),
    period2_end=datetime(2024, 5, 31)
)

print(f"Diferença: {comparison['comparison']['total_difference']}")
print(f"Variação: {comparison['comparison']['total_percent_change']}%")
```

#### 4. Detecção de Anomalias

```python
anomalies = predictions.detect_anomalies(
    df=df,
    metric_column="hectares",
    threshold=2.0  # desvios padrão
)

for anomaly in anomalies:
    print(f"Valor anômalo: {anomaly['value']}")
    print(f"Tipo: {anomaly['type']}")  # alto/baixo
    print(f"Z-Score: {anomaly['z_score']}")
```

#### 5. Análise Sazonal

```python
seasonal = predictions.seasonal_analysis(
    df=df,
    metric_column="hectares"
)

print(f"Melhor dia da semana: {seasonal['best_weekday']}")
print(f"Melhor hora: {seasonal['best_hour']}")
print(f"Melhor mês: {seasonal['best_month']}")
```

---

## 📊 Integração com Dashboard

⚠️ **STATUS: EM DESENVOLVIMENTO**

Módulo preparado para integração com dashboard de monitoramento.

### Configuração Futura

```python
from src.integrations.dashboard_connector import DashboardConnector

# Inicializa
dashboard = DashboardConnector(
    api_url="http://seu-dashboard.com/api",
    api_key="dashboard-api-key"
)

# Envia alerta
dashboard.send_alert(
    alert_type="threshold",
    title="Produção Acima do Esperado",
    message="Unidade Barra ultrapassou meta em 15%",
    severity="warning",
    metadata={"unidade": "Barra", "metrica": "hectares"}
)

# Atualiza métrica
dashboard.update_metric(
    metric_name="hectares_plantados",
    value=45.2,
    unit="hectares",
    tags={"unidade": "Barra"}
)

# Registra evento
dashboard.log_event(
    event_type="milestone",
    description="Meta mensal atingida",
    metadata={"unidade": "Barra", "mes": "maio"}
)
```

### Pendências

- [ ] Configurar endpoint da API do dashboard
- [ ] Implementar autenticação
- [ ] Testar envio de alertas
- [ ] Configurar webhook de retorno

### Alertas Temporários

Enquanto não configurado, alertas são salvos em `data/dashboard_alerts/` para processamento posterior.

---

## 💬 Integração com WhatsApp

⚠️ **STATUS: EM DESENVOLVIMENTO**

Módulo preparado para envio de mensagens via WhatsApp.

### Uso Atual

```python
from src.integrations.whatsapp_connector import WhatsAppConnector

# Inicializa
whatsapp = WhatsAppConnector()

# Salva mensagem para envio
message_id = whatsapp.send_message(
    phone_number="+5511999999999",
    message="Alerta: Produção acima do esperado na unidade Barra",
    priority=1  # 0=normal, 1=alta, 2=urgente
)

# Envia alerta para múltiplos números
whatsapp.send_alert(
    phone_numbers=["+5511999999999", "+5511888888888"],
    alert_title="Produção Alta",
    alert_message="Unidade Barra ultrapassou meta em 15%",
    severity="warning"
)

# Mensagens pendentes
pending = whatsapp.get_pending_messages(limit=50)

# Marca como enviada (após integração real)
whatsapp.mark_as_sent(message_id)

# Estatísticas
stats = whatsapp.get_statistics()
print(f"Pendentes: {stats['pending']}")
print(f"Enviadas: {stats['sent']}")
```

### Banco de Dados

Mensagens são armazenadas em SQLite em `data/whatsapp_messages.db`

### Pendências

- [ ] Integrar com sistema de envio WhatsApp
- [ ] Configurar callbacks de status
- [ ] Implementar fila de processamento
- [ ] Adicionar rate limiting

---

## 🚨 Alertas Proativos

⚠️ **STATUS: EM DESENVOLVIMENTO**

Sistema de monitoramento contínuo com alertas automáticos.

### Configuração

```python
from src.integrations.proactive_alerts import ProactiveAlerts
from src.data.parquet_processor import ParquetProcessor

# Inicializa
processor = ParquetProcessor()
alerts = ProactiveAlerts(parquet_processor=processor)

# Adiciona regra de threshold
alerts.add_threshold_rule(
    metric="hectares",
    threshold_value=50.0,
    condition="above",
    unidade="Barra",
    operacao="plantio",
    alert_title="Produção Alta - Barra",
    severity="warning"
)

# Adiciona regra de anomalia
alerts.add_anomaly_detection_rule(
    metric="toneladas",
    sensitivity=2.0,  # desvios padrão
    unidade="Piacatu",
    alert_title="Anomalia Detectada - Piacatu"
)

# Adiciona regra preditiva
alerts.add_prediction_rule(
    metric="hectares",
    days_ahead=7,
    threshold_value=300.0,
    condition="below",
    alert_title="Alerta: Produção pode cair"
)

# Inicia monitoramento (roda em background)
alerts.start_monitoring(interval=300)  # 5 minutos

# Para monitoramento
# alerts.stop_monitoring()

# Status
status = alerts.get_status()
print(f"Monitorando: {status['monitoring']}")
print(f"Regras ativas: {status['active_rules']}")
```

### Tipos de Alertas

1. **Threshold**: Alerta quando métrica ultrapassa limite
2. **Anomalia**: Detecta comportamentos anômalos
3. **Preditivo**: Alerta baseado em previsões

### Pendências

- [ ] Configurar destinatários por tipo de alerta
- [ ] Implementar scheduler robusto (APScheduler)
- [ ] Adicionar filtros de horário
- [ ] Criar dashboard de alertas

---

## 🎯 Roadmap de Integração

### Curto Prazo
- [ ] Testar API REST em produção
- [ ] Configurar dashboard connector
- [ ] Integrar WhatsApp connector

### Médio Prazo
- [ ] Implementar autenticação OAuth2 na API
- [ ] Adicionar cache Redis
- [ ] Criar interface web para configuração de alertas

### Longo Prazo
- [ ] Machine Learning avançado para previsões
- [ ] Integração com mais canais (Slack, Teams)
- [ ] Dashboard próprio do CIABot

---

## 📚 Recursos Adicionais

- [README Principal](../README.md)
- [Quick Start](../QUICKSTART.md)
- [Relatórios Power BI](POWERBI_REPORTS.md)

---

**CIABot Oráculo** - Sempre evoluindo 🚀
