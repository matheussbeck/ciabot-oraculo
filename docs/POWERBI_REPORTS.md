# 📊 Configuração de Relatórios Power BI

Este guia explica como organizar seus relatórios existentes do Power BI para que o CIABot Oráculo possa encontrá-los e enviá-los automaticamente.

## 📁 Diretório de Relatórios

Coloque todos os seus relatórios Power BI exportados em PDF no diretório:

```
data/powerbi_reports/
```

## 📝 Nomenclatura de Arquivos

Para que a IA encontre os relatórios corretamente, use nomes descritivos que incluam:

1. **Tipo de operação**: plantio, corte, transporte, carregamento
2. **Unidade** (se aplicável): barra, piacatu, univalem, etc
3. **Período** (se aplicável): diario, semanal, mensal, safra
4. **Data** (opcional): YYYY-MM-DD ou YYYYMMDD

### Exemplos de Nomes Bons

```
plantio_barra_diario_2024-05-15.pdf
corte_piacatu_semanal.pdf
transporte_consolidado_mensal.pdf
relatorio_operacional_barra_hora_a_hora.pdf
producao_safra_2024.pdf
plantio_detalhado_univalem.pdf
```

### Exemplos de Nomes Ruins (evitar)

```
relatorio1.pdf
dados.pdf
arquivo_final_v3.pdf
power_bi_export.pdf
```

## 🗂️ Organização por Subdiretórios

Você pode organizar os relatórios em subdiretórios por categoria:

```
data/powerbi_reports/
├── plantio/
│   ├── plantio_barra_diario.pdf
│   ├── plantio_piacatu_diario.pdf
│   └── plantio_consolidado_semanal.pdf
├── corte/
│   ├── corte_barra_diario.pdf
│   ├── corte_hora_a_hora.pdf
│   └── corte_mensal_todas_unidades.pdf
├── transporte/
│   └── transporte_logistica_diario.pdf
└── gerenciais/
    ├── consolidado_mensal.pdf
    └── safra_completo.pdf
```

O sistema busca em todos os subdiretórios automaticamente.

## 🔍 Como a IA Encontra Relatórios

A IA usa as seguintes estratégias para encontrar o relatório certo:

### 1. Correspondência de Palavras-chave

Extrai palavras do nome do arquivo e compara com a consulta do usuário.

**Exemplo:**
- Usuário: "me envie o relatório de plantio da Barra"
- Busca por: arquivos contendo "plantio" E "barra"
- Encontra: `plantio_barra_diario.pdf`

### 2. Detecção de Período

Identifica período específico na consulta:

- "hora a hora", "hourly" → busca "hora", "hourly", "detalhado"
- "diário", "daily" → busca "diario", "daily"
- "semanal", "weekly" → busca "semanal", "weekly"
- "mensal", "monthly" → busca "mensal", "monthly"

### 3. Priorização

Relatórios são priorizados por:
- Relevância (mais palavras em comum)
- Data de modificação (mais recentes primeiro)
- Correspondência exata de unidade e operação

## 💡 Dicas de Nomenclatura

### Use Palavras-chave Consistentes

**Operações:**
- `plantio`
- `corte` ou `colheita`
- `transporte` ou `logistica`
- `carregamento` ou `carga`

**Períodos:**
- `diario` ou `daily`
- `semanal` ou `weekly`
- `mensal` ou `monthly`
- `safra` ou `anual`
- `hora_a_hora` ou `hourly`

**Tipos:**
- `consolidado`
- `detalhado`
- `resumo` ou `summary`
- `gerencial` ou `executivo`

### Inclua a Data (quando relevante)

Para relatórios diários ou específicos:
```
plantio_barra_2024-05-15.pdf
corte_diario_2024-05-20.pdf
```

### Use Underscores ou Hífens

Evite espaços, use `_` ou `-`:
```
✅ plantio_barra_diario.pdf
✅ plantio-barra-diario.pdf
❌ plantio barra diario.pdf
```

## 🔄 Atualização Automática

### Substituir Relatórios

Para atualizar um relatório:

1. Exporte o novo PDF do Power BI
2. Salve com o **mesmo nome** do anterior
3. Substitua o arquivo em `data/powerbi_reports/`
4. No Telegram, envie: `/refresh`

### Adicionar Novos Relatórios

1. Exporte o PDF do Power BI
2. Renomeie seguindo as convenções acima
3. Salve em `data/powerbi_reports/`
4. No Telegram, envie: `/refresh`

## 📋 Exemplo de Consultas

Veja como o usuário pode solicitar relatórios:

| Consulta do Usuário | Relatório Encontrado |
|---------------------|---------------------|
| "me envie o relatório de plantio da Barra" | `plantio_barra_diario.pdf` |
| "relatório hora a hora do corte" | `corte_hora_a_hora.pdf` |
| "relatório semanal de transporte" | `transporte_semanal.pdf` |
| "consolidado mensal" | `consolidado_mensal.pdf` |
| "relatório da safra" | `producao_safra_2024.pdf` |

## 🔧 Configuração Avançada

### Múltiplas Versões do Mesmo Relatório

Se você tem diferentes versões (ex: completo e resumido):

```
plantio_barra_resumo.pdf
plantio_barra_detalhado.pdf
plantio_barra_executivo.pdf
```

A IA mostrará opções e enviará a mais relevante.

### Relatórios por Data

Para histórico de relatórios diários:

```
data/powerbi_reports/historico/
├── 2024-05/
│   ├── plantio_barra_2024-05-01.pdf
│   ├── plantio_barra_2024-05-02.pdf
│   └── ...
└── 2024-06/
    └── ...
```

## ⚠️ Limitações

1. **Tamanho dos Arquivos**: PDFs muito grandes (>50MB) podem demorar para enviar
2. **Formato**: Apenas PDFs são suportados
3. **Busca**: A busca é baseada em nomes de arquivos, não no conteúdo

## 📊 Monitoramento

Para ver estatísticas dos relatórios indexados, envie no Telegram:

```
/status
```

Isso mostrará:
- Total de relatórios Power BI encontrados
- Categorias disponíveis
- Unidades com relatórios

## 🆘 Troubleshooting

### Relatório não encontrado

1. Verifique o nome do arquivo
2. Confirme que está em `data/powerbi_reports/`
3. Execute `/refresh` no bot
4. Tente ser mais específico na consulta

### Relatório errado enviado

Seja mais específico na consulta:
- Inclua a unidade: "Barra", "Piacatu"
- Inclua o período: "diário", "semanal"
- Inclua o tipo: "detalhado", "resumo"

### Múltiplos relatórios enviados

Isso acontece quando a busca encontra vários candidatos. O bot enviará o mais relevante. Para evitar:
- Use nomes mais específicos
- Faça consultas mais precisas

## 📝 Checklist de Implementação

- [ ] Criar diretório `data/powerbi_reports/`
- [ ] Exportar relatórios do Power BI em PDF
- [ ] Renomear arquivos seguindo convenções
- [ ] Copiar PDFs para o diretório
- [ ] Executar `/refresh` no bot
- [ ] Testar consultas no Telegram
- [ ] Documentar lista de relatórios disponíveis

## 📚 Recursos Adicionais

- [README.md](../README.md) - Documentação completa
- [QUICKSTART.md](../QUICKSTART.md) - Guia de início rápido

---

**CIABot Oráculo** - Simplificando o acesso aos seus dados 📊
