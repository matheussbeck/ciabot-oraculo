"""
API REST para o CIABot Oráculo
Permite integração via HTTP
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from src.ai.intelligence_engine import IntelligenceEngine
from src.ai.vector_search import VectorSearch
from src.ai.continuous_learning import ContinuousLearning
from src.data.parquet_processor import ParquetProcessor
from src.reports.report_finder import ReportFinder
from src.analytics.predictions import PredictionsEngine
from config.settings import REPORTS_DIR

logger = logging.getLogger(__name__)

# Modelos Pydantic
class QueryRequest(BaseModel):
    """Modelo de requisição de consulta"""
    query: str = Field(..., description="Consulta do usuário")
    user_id: Optional[int] = Field(None, description="ID do usuário")
    context: Optional[Dict[str, Any]] = Field(None, description="Contexto adicional")


class QueryResponse(BaseModel):
    """Modelo de resposta de consulta"""
    success: bool
    response: str
    confidence: float
    intent: str
    data_available: bool
    timestamp: str


class StatusResponse(BaseModel):
    """Modelo de resposta de status"""
    status: str
    version: str
    parquet_files: int
    powerbi_reports: int
    uptime: str


class PredictionRequest(BaseModel):
    """Modelo de requisição de previsão"""
    metric: str = Field(..., description="Métrica a prever")
    unidade: Optional[str] = Field(None, description="Unidade")
    operacao: Optional[str] = Field(None, description="Operação")
    periods: int = Field(7, description="Períodos para prever")


# Segurança (básica com Bearer Token)
security = HTTPBearer()


class CIABotAPI:
    """API REST do CIABot Oráculo"""

    def __init__(self, api_key: Optional[str] = None, enable_vector_search: bool = False,
                 enable_learning: bool = True):
        self.app = FastAPI(
            title="CIABot Oráculo API",
            description="API REST para consultas agrícolas com IA",
            version="1.0.0"
        )

        self.api_key = api_key or "ciabot-api-key-change-me"

        # Componentes
        self.parquet_processor = ParquetProcessor()

        # Módulos avançados (opcionais)
        self.vector_search = None
        self.continuous_learning = None

        if enable_vector_search:
            try:
                self.vector_search = VectorSearch()
            except Exception as e:
                logger.warning(f"VectorSearch não disponível: {e}")

        if enable_learning:
            try:
                self.continuous_learning = ContinuousLearning()
            except Exception as e:
                logger.warning(f"ContinuousLearning não disponível: {e}")

        self.intelligence_engine = IntelligenceEngine(
            self.parquet_processor,
            vector_search=self.vector_search,
            continuous_learning=self.continuous_learning
        )
        self.report_finder = ReportFinder()
        self.predictions_engine = PredictionsEngine()

        # Tempo de início
        self.start_time = datetime.now()

        # Configurar CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Em produção, especifique domínios
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Registrar rotas
        self._register_routes()

        logger.info("API REST inicializada")

    def _verify_token(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> bool:
        """Verifica token de autenticação"""
        if credentials.credentials != self.api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido"
            )
        return True

    def _register_routes(self):
        """Registra todas as rotas da API"""

        @self.app.get("/", tags=["Root"])
        async def root():
            """Endpoint raiz"""
            return {
                "service": "CIABot Oráculo API",
                "version": "1.0.0",
                "status": "online",
                "docs": "/docs"
            }

        @self.app.get("/status", response_model=StatusResponse, tags=["Status"])
        async def get_status():
            """Retorna status do sistema"""
            uptime = datetime.now() - self.start_time

            return StatusResponse(
                status="online",
                version="1.0.0",
                parquet_files=len(self.parquet_processor.file_index),
                powerbi_reports=len(self.report_finder.report_index),
                uptime=str(uptime)
            )

        @self.app.post("/query", response_model=QueryResponse, tags=["Queries"])
        async def process_query(
            request: QueryRequest,
            authenticated: bool = Depends(self._verify_token)
        ):
            """
            Processa uma consulta do usuário

            Args:
                request: Dados da consulta

            Returns:
                Resposta da IA
            """
            try:
                result = self.intelligence_engine.process_query(
                    request.query,
                    user_context={"user_id": request.user_id, **(request.context or {})}
                )

                return QueryResponse(
                    success=result.get("success", False),
                    response=result.get("response", ""),
                    confidence=result.get("confidence", 0.0),
                    intent=result.get("intent", "unknown"),
                    data_available=result.get("data_available", False),
                    timestamp=datetime.now().isoformat()
                )

            except Exception as e:
                logger.error(f"Erro ao processar query: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Erro ao processar consulta: {str(e)}"
                )

        @self.app.get("/reports", tags=["Reports"])
        async def list_reports(
            categoria: Optional[str] = None,
            authenticated: bool = Depends(self._verify_token)
        ):
            """Lista relatórios disponíveis"""
            try:
                reports = self.report_finder.list_all_reports(categoria)

                return {
                    "total": len(reports),
                    "reports": [
                        {
                            "name": r["name"],
                            "category": r["category"],
                            "size_kb": round(r["size"] / 1024, 2),
                            "modified": r["modified"].isoformat()
                        }
                        for r in reports
                    ]
                }

            except Exception as e:
                logger.error(f"Erro ao listar relatórios: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/reports/search", tags=["Reports"])
        async def search_reports(
            query: str,
            unidade: Optional[str] = None,
            operacao: Optional[str] = None,
            authenticated: bool = Depends(self._verify_token)
        ):
            """Busca relatórios por query"""
            try:
                reports = self.report_finder.find_reports(
                    query=query,
                    unidade=unidade,
                    operacao=operacao,
                    limite=10
                )

                return {
                    "query": query,
                    "results": len(reports),
                    "reports": [
                        {
                            "name": r["name"],
                            "score": r["score"],
                            "category": r["category"],
                            "path": str(r["path"])
                        }
                        for r in reports
                    ]
                }

            except Exception as e:
                logger.error(f"Erro ao buscar relatórios: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/predictions/forecast", tags=["Predictions"])
        async def forecast(
            request: PredictionRequest,
            authenticated: bool = Depends(self._verify_token)
        ):
            """Gera previsão de métrica"""
            try:
                # Busca dados
                files = self.parquet_processor.find_relevant_files(
                    query=request.metric,
                    operation=request.operacao,
                    unit=request.unidade
                )

                if not files:
                    raise HTTPException(
                        status_code=404,
                        detail="Dados não encontrados"
                    )

                filters = {}
                if request.unidade:
                    filters["unidade"] = request.unidade
                if request.operacao:
                    filters["operacao"] = request.operacao

                df = self.parquet_processor.query_data(files, filters)

                if df is None or len(df) == 0:
                    raise HTTPException(
                        status_code=404,
                        detail="Sem dados suficientes"
                    )

                # Gera previsão
                prediction = self.predictions_engine.predict_next_values(
                    df=df,
                    metric_column=request.metric,
                    periods=request.periods
                )

                return prediction

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Erro ao gerar previsão: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/analytics/trend", tags=["Analytics"])
        async def analyze_trend(
            metric: str,
            unidade: Optional[str] = None,
            operacao: Optional[str] = None,
            authenticated: bool = Depends(self._verify_token)
        ):
            """Analisa tendência de métrica"""
            try:
                files = self.parquet_processor.find_relevant_files(
                    query=metric,
                    operation=operacao,
                    unit=unidade
                )

                if not files:
                    raise HTTPException(status_code=404, detail="Dados não encontrados")

                filters = {}
                if unidade:
                    filters["unidade"] = unidade
                if operacao:
                    filters["operacao"] = operacao

                df = self.parquet_processor.query_data(files, filters)

                if df is None or len(df) == 0:
                    raise HTTPException(status_code=404, detail="Sem dados")

                trend = self.predictions_engine.analyze_trend(df, metric)

                return trend

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Erro ao analisar tendência: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/data/metrics", tags=["Data"])
        async def get_available_metrics(
            authenticated: bool = Depends(self._verify_token)
        ):
            """Retorna métricas disponíveis"""
            try:
                metrics = self.parquet_processor.get_available_metrics()

                return {
                    "total": len(metrics),
                    "metrics": metrics
                }

            except Exception as e:
                logger.error(f"Erro ao obter métricas: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/data/refresh", tags=["Data"])
        async def refresh_data(
            authenticated: bool = Depends(self._verify_token)
        ):
            """Atualiza índices de dados"""
            try:
                self.parquet_processor.refresh_index()
                self.report_finder.refresh_index()

                return {
                    "status": "success",
                    "parquet_files": len(self.parquet_processor.file_index),
                    "powerbi_reports": len(self.report_finder.report_index),
                    "timestamp": datetime.now().isoformat()
                }

            except Exception as e:
                logger.error(f"Erro ao atualizar dados: {e}")
                raise HTTPException(status_code=500, detail=str(e))

    def run(self, host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
        """Inicia o servidor da API"""
        logger.info(f"Iniciando API REST em {host}:{port}")
        uvicorn.run(self.app, host=host, port=port, reload=reload)


# Para execução direta
if __name__ == "__main__":
    api = CIABotAPI()
    api.run()
