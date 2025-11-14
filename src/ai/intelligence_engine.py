"""
Motor de Inteligência com cálculo de confiança
"""
import logging
import json
import re
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import anthropic
from openai import OpenAI

from config.settings import (
    AI_PROVIDER, ANTHROPIC_API_KEY, OPENAI_API_KEY,
    AI_MODEL, MIN_CONFIDENCE_TO_RESPOND, SAFRA_INICIO
)
from src.data.parquet_processor import ParquetProcessor

logger = logging.getLogger(__name__)


class IntelligenceEngine:
    """Motor de IA com cálculo de confiança para respostas"""

    def __init__(self, parquet_processor: ParquetProcessor,
                 vector_search=None, continuous_learning=None):
        self.processor = parquet_processor
        self.ai_provider = AI_PROVIDER.lower()

        # Módulos opcionais
        self.vector_search = vector_search
        self.learning = continuous_learning

        # Inicializa cliente de IA
        if self.ai_provider == "anthropic":
            self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            self.model = AI_MODEL
        elif self.ai_provider == "openai":
            self.client = OpenAI(api_key=OPENAI_API_KEY)
            self.model = AI_MODEL
        else:
            raise ValueError(f"Provedor de IA não suportado: {AI_PROVIDER}")

        logger.info(f"Intelligence Engine inicializado com {AI_PROVIDER}")
        if self.vector_search:
            logger.info("VectorSearch habilitado")
        if self.learning:
            logger.info("ContinuousLearning habilitado")

    def process_query(self, user_query: str, user_context: Dict = None) -> Dict[str, Any]:
        """
        Processa consulta do usuário

        Args:
            user_query: Pergunta do usuário
            user_context: Contexto adicional do usuário

        Returns:
            Dicionário com resposta, confiança e metadados
        """
        logger.info(f"Processando query: {user_query}")

        # 1. Busca queries similares (se VectorSearch habilitado)
        if self.vector_search and self.vector_search.enabled:
            similar_queries = self.vector_search.search_similar_queries(user_query, n_results=3)
            if similar_queries:
                logger.info(f"Queries similares encontradas: {len(similar_queries)}")

        # 2. Analisa a intenção da consulta
        intent = self._analyze_intent(user_query)
        logger.info(f"Intenção detectada: {intent}")

        # 3. Extrai parâmetros da consulta
        params = self._extract_parameters(user_query, intent)
        logger.info(f"Parâmetros extraídos: {params}")

        # 4. Busca dados relevantes
        data_context = self._get_data_context(params)

        # 5. Calcula se há dados suficientes
        data_confidence = self._calculate_data_confidence(data_context, params)

        # 6. Gera resposta com IA
        if data_confidence >= MIN_CONFIDENCE_TO_RESPOND:
            response = self._generate_response(
                user_query, intent, params, data_context, data_confidence
            )
        else:
            response = self._generate_low_confidence_response(
                user_query, params, data_confidence
            )

        # 7. Registra interação para aprendizado (se habilitado)
        if self.learning:
            try:
                self.learning.record_interaction(
                    query=user_query,
                    response=response,
                    params=params,
                    user_id=user_context.get("user_id") if user_context else None
                )
            except Exception as e:
                logger.error(f"Erro ao registrar aprendizado: {e}")

        # 8. Adiciona query ao histórico vetorial (se habilitado)
        if self.vector_search and self.vector_search.enabled:
            try:
                self.vector_search.add_query(user_query, response, user_context)
            except Exception as e:
                logger.error(f"Erro ao adicionar query ao vetor DB: {e}")

        return response

    def _analyze_intent(self, query: str) -> str:
        """Analisa a intenção da consulta"""
        query_lower = query.lower()

        # Padrões de intenção
        if any(word in query_lower for word in ["quantos", "quanto", "qual", "hectares", "toneladas", "total"]):
            return "metric_query"
        elif any(word in query_lower for word in ["relatório", "relatorio", "envie", "gerar", "pdf"]):
            return "report_request"
        elif any(word in query_lower for word in ["comparar", "diferença", "versus", "vs"]):
            return "comparison"
        elif any(word in query_lower for word in ["tendência", "evolução", "progressão", "histórico"]):
            return "trend_analysis"
        else:
            return "general_query"

    def _extract_parameters(self, query: str, intent: str) -> Dict[str, Any]:
        """Extrai parâmetros estruturados da consulta"""
        params = {
            "query": query,
            "intent": intent,
            "unidade": None,
            "operacao": None,
            "periodo": None,
            "data_inicio": None,
            "data_fim": None,
            "metrica": None
        }

        query_lower = query.lower()

        # Extrai unidade
        from config.settings import UNIDADES
        for unidade in UNIDADES:
            if unidade.lower() in query_lower:
                params["unidade"] = unidade
                break

        # Extrai operação
        from config.settings import OPERACOES
        for operacao in OPERACOES:
            if operacao.lower() in query_lower:
                params["operacao"] = operacao
                break

        # Extrai métrica
        metricas = ["hectares", "toneladas", "viagens", "horas"]
        for metrica in metricas:
            if metrica in query_lower:
                params["metrica"] = metrica
                break

        # Extrai período temporal
        hoje = datetime.now().date()

        if "ontem" in query_lower:
            params["periodo"] = "ontem"
            params["data_inicio"] = hoje - timedelta(days=1)
            params["data_fim"] = hoje - timedelta(days=1)

        elif "hoje" in query_lower:
            params["periodo"] = "hoje"
            params["data_inicio"] = hoje
            params["data_fim"] = hoje

        elif "últimos 7 dias" in query_lower or "ultimos 7 dias" in query_lower:
            params["periodo"] = "ultimos_7_dias"
            params["data_inicio"] = hoje - timedelta(days=7)
            params["data_fim"] = hoje

        elif "início da safra" in query_lower or "inicio da safra" in query_lower:
            params["periodo"] = "safra"
            params["data_inicio"] = datetime.strptime(SAFRA_INICIO, "%Y-%m-%d").date()
            params["data_fim"] = hoje

        elif "mês" in query_lower or "mes" in query_lower:
            params["periodo"] = "mes"
            params["data_inicio"] = hoje.replace(day=1)
            params["data_fim"] = hoje

        return params

    def _get_data_context(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Busca contexto de dados relevantes"""
        context = {
            "has_data": False,
            "files_found": [],
            "data": None,
            "aggregated": {},
            "row_count": 0
        }

        # Busca arquivos relevantes
        files = self.processor.find_relevant_files(
            query=params["query"],
            operation=params["operacao"],
            unit=params["unidade"]
        )

        context["files_found"] = files

        if not files:
            return context

        # Monta filtros
        filters = {}
        if params["data_inicio"]:
            filters["data_inicio"] = params["data_inicio"]
        if params["data_fim"]:
            filters["data_fim"] = params["data_fim"]
        if params["unidade"]:
            filters["unidade"] = params["unidade"]
        if params["operacao"]:
            filters["operacao"] = params["operacao"]

        # Consulta dados
        df = self.processor.query_data(files, filters)

        if df is not None and len(df) > 0:
            context["has_data"] = True
            context["data"] = df
            context["row_count"] = len(df)

            # Agrega dados se métrica especificada
            if params["metrica"]:
                context["aggregated"] = self.processor.aggregate_data(
                    df, params["metrica"]
                )

        return context

    def _calculate_data_confidence(self, data_context: Dict, params: Dict) -> float:
        """
        Calcula confiança baseado na disponibilidade e qualidade dos dados

        Retorna valor entre 0 e 1
        """
        confidence = 0.0

        # Tem dados?
        if not data_context["has_data"]:
            return 0.1  # Confiança mínima

        # Score baseado em quantidade de registros
        row_count = data_context["row_count"]
        if row_count > 100:
            confidence += 0.4
        elif row_count > 10:
            confidence += 0.3
        elif row_count > 0:
            confidence += 0.2

        # Score baseado em arquivos encontrados
        files_count = len(data_context["files_found"])
        if files_count >= 3:
            confidence += 0.2
        elif files_count >= 1:
            confidence += 0.15

        # Score baseado em dados agregados
        if data_context["aggregated"]:
            if "total" in data_context["aggregated"]:
                confidence += 0.2
            if "grouped" in data_context["aggregated"]:
                confidence += 0.1

        # Bonus se todos os parâmetros foram atendidos
        if all([
            params["unidade"] is not None,
            params["operacao"] is not None,
            params["data_inicio"] is not None
        ]):
            confidence += 0.1

        return min(confidence, 1.0)

    def _generate_response(self, query: str, intent: str, params: Dict,
                          data_context: Dict, confidence: float) -> Dict[str, Any]:
        """Gera resposta usando IA"""

        # Prepara contexto para a IA
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(query, intent, params, data_context, confidence)

        try:
            if self.ai_provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    system=system_prompt,
                    messages=[
                        {"role": "user", "content": user_prompt}
                    ]
                )
                ai_response = response.content[0].text

            elif self.ai_provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ]
                )
                ai_response = response.choices[0].message.content

            return {
                "success": True,
                "response": ai_response,
                "confidence": confidence,
                "intent": intent,
                "params": params,
                "data_available": True,
                "requires_report": intent == "report_request"
            }

        except Exception as e:
            logger.error(f"Erro ao gerar resposta com IA: {e}")
            return {
                "success": False,
                "response": "Desculpe, ocorreu um erro ao processar sua consulta.",
                "confidence": 0.0,
                "error": str(e)
            }

    def _generate_low_confidence_response(self, query: str, params: Dict,
                                         confidence: float) -> Dict[str, Any]:
        """Gera resposta quando a confiança é baixa"""

        missing_info = []

        if not params["unidade"]:
            missing_info.append("unidade")
        if not params["operacao"]:
            missing_info.append("tipo de operação")
        if not params["data_inicio"]:
            missing_info.append("período")

        response = f"⚠️ **Confiança: {confidence*100:.0f}%**\n\n"
        response += "Não possuo dados suficientes para responder com a confiança mínima de 90%.\n\n"

        if missing_info:
            response += f"Informações que podem ajudar: {', '.join(missing_info)}\n\n"

        response += "Sugestões:\n"
        response += "- Verifique se especificou a unidade (ex: Barra, Piacatu)\n"
        response += "- Indique o tipo de operação (plantio, corte, carregamento, transporte)\n"
        response += "- Especifique o período (ontem, últimos 7 dias, etc)\n"

        return {
            "success": False,
            "response": response,
            "confidence": confidence,
            "data_available": False,
            "requires_report": False
        }

    def _build_system_prompt(self) -> str:
        """Constrói prompt do sistema"""
        return """Você é o Oráculo, um assistente de IA especializado em operações agrícolas de cana-de-açúcar.

Sua função é responder perguntas de executivos C-Level com PRECISÃO e CLAREZA.

REGRAS FUNDAMENTAIS:
1. Baseie-se APENAS nos dados fornecidos
2. Nunca invente ou estime números
3. Sempre indique o nível de confiança da resposta
4. Seja direto e objetivo
5. Use formatação clara (negrito, listas quando apropriado)
6. Se não souber, admita claramente

FORMATO DAS RESPOSTAS:
- Comece com o percentual de confiança em destaque
- Responda a pergunta de forma direta
- Apresente números com clareza
- Use unidades apropriadas (hectares, toneladas, etc)
- Se relevante, adicione contexto breve

EXEMPLO:
✅ **Confiança: 95%**

A unidade Barra plantou:
- **Ontem**: 45,2 hectares
- **Últimos 7 dias**: 312,8 hectares
- **Safra até agora**: 1.847,5 hectares

Baseado em 156 registros de operação."""

    def _build_user_prompt(self, query: str, intent: str, params: Dict,
                           data_context: Dict, confidence: float) -> str:
        """Constrói prompt do usuário"""

        prompt = f"**PERGUNTA DO USUÁRIO:**\n{query}\n\n"
        prompt += f"**INTENÇÃO:** {intent}\n\n"
        prompt += f"**CONFIANÇA DOS DADOS:** {confidence*100:.0f}%\n\n"

        # Adiciona parâmetros extraídos
        prompt += "**PARÂMETROS IDENTIFICADOS:**\n"
        for key, value in params.items():
            if value:
                prompt += f"- {key}: {value}\n"
        prompt += "\n"

        # Adiciona dados agregados
        if data_context["aggregated"]:
            prompt += "**DADOS DISPONÍVEIS:**\n"
            prompt += f"```json\n{json.dumps(data_context['aggregated'], indent=2, default=str)}\n```\n\n"

        # Adiciona amostra dos dados
        if data_context["data"] is not None:
            prompt += f"**REGISTROS ENCONTRADOS:** {data_context['row_count']}\n\n"

            # Mostra amostra
            sample = data_context["data"].head(5)
            prompt += "**AMOSTRA DOS DADOS:**\n"
            prompt += f"```\n{sample}\n```\n\n"

        prompt += f"Responda a pergunta do usuário com confiança de {confidence*100:.0f}%."

        return prompt
