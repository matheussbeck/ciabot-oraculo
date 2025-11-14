"""
Processador de arquivos Parquet
"""
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import polars as pl
from config.settings import PARQUET_DIR

logger = logging.getLogger(__name__)


class ParquetProcessor:
    """Gerencia leitura e processamento de arquivos Parquet"""

    def __init__(self, data_dir: Path = PARQUET_DIR):
        self.data_dir = data_dir
        self.cache = {}
        self._index_files()

    def _index_files(self) -> None:
        """Indexa todos os arquivos Parquet disponíveis"""
        self.file_index = {}

        if not self.data_dir.exists():
            logger.warning(f"Diretório de dados não encontrado: {self.data_dir}")
            return

        for file_path in self.data_dir.rglob("*.parquet"):
            # Extrai metadados do nome do arquivo
            file_name = file_path.stem
            parts = file_name.lower().split("_")

            metadata = {
                "path": file_path,
                "size": file_path.stat().st_size,
                "modified": datetime.fromtimestamp(file_path.stat().st_mtime),
                "name": file_name,
                "keywords": parts
            }

            self.file_index[file_name] = metadata

        logger.info(f"Indexados {len(self.file_index)} arquivos Parquet")

    def find_relevant_files(self, query: str, operation: Optional[str] = None,
                           unit: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Encontra arquivos relevantes baseado na consulta

        Args:
            query: Consulta do usuário
            operation: Tipo de operação (plantio, corte, etc)
            unit: Unidade (Barra, Piacatu, etc)

        Returns:
            Lista de arquivos relevantes com score
        """
        query_lower = query.lower()
        query_terms = set(query_lower.split())

        relevant_files = []

        for file_name, metadata in self.file_index.items():
            score = 0
            keywords = set(metadata["keywords"])

            # Score baseado em termos da query
            common_terms = query_terms.intersection(keywords)
            score += len(common_terms) * 10

            # Bonus para operação específica
            if operation and operation.lower() in keywords:
                score += 20

            # Bonus para unidade específica
            if unit and unit.lower() in keywords:
                score += 20

            # Considera palavras-chave importantes
            important_terms = {"plantio", "corte", "carregamento", "transporte",
                             "barra", "piacatu", "hectares", "toneladas"}
            important_matches = query_terms.intersection(important_terms).intersection(keywords)
            score += len(important_matches) * 15

            if score > 0:
                relevant_files.append({
                    **metadata,
                    "score": score
                })

        # Ordena por score
        relevant_files.sort(key=lambda x: x["score"], reverse=True)

        logger.info(f"Encontrados {len(relevant_files)} arquivos relevantes para: {query}")
        return relevant_files

    def read_parquet(self, file_path: Path, use_polars: bool = True) -> Optional[Any]:
        """
        Lê arquivo Parquet

        Args:
            file_path: Caminho do arquivo
            use_polars: Usar Polars (mais rápido) ou Pandas

        Returns:
            DataFrame (Polars ou Pandas)
        """
        try:
            if use_polars:
                df = pl.read_parquet(file_path)
            else:
                df = pd.read_parquet(file_path)

            logger.info(f"Arquivo carregado: {file_path.name} - {len(df)} registros")
            return df

        except Exception as e:
            logger.error(f"Erro ao ler {file_path}: {e}")
            return None

    def query_data(self, files: List[Dict], filters: Dict[str, Any]) -> Optional[pl.DataFrame]:
        """
        Consulta dados com filtros específicos

        Args:
            files: Lista de arquivos para consultar
            filters: Filtros a aplicar (data_inicio, data_fim, unidade, etc)

        Returns:
            DataFrame consolidado
        """
        if not files:
            return None

        dfs = []

        for file_info in files[:5]:  # Limita a 5 arquivos mais relevantes
            df = self.read_parquet(file_info["path"], use_polars=True)

            if df is not None:
                # Aplica filtros
                df = self._apply_filters(df, filters)
                if df is not None and len(df) > 0:
                    dfs.append(df)

        if not dfs:
            return None

        # Consolida dataframes
        try:
            result = pl.concat(dfs, how="vertical_relaxed")
            logger.info(f"Dados consolidados: {len(result)} registros")
            return result
        except Exception as e:
            logger.error(f"Erro ao consolidar dados: {e}")
            return None

    def _apply_filters(self, df: pl.DataFrame, filters: Dict[str, Any]) -> Optional[pl.DataFrame]:
        """Aplica filtros ao DataFrame"""
        try:
            # Filtro de data
            if "data_inicio" in filters and "data" in df.columns:
                df = df.filter(pl.col("data") >= filters["data_inicio"])

            if "data_fim" in filters and "data" in df.columns:
                df = df.filter(pl.col("data") <= filters["data_fim"])

            # Filtro de unidade
            if "unidade" in filters and "unidade" in df.columns:
                df = df.filter(
                    pl.col("unidade").str.to_lowercase() == filters["unidade"].lower()
                )

            # Filtro de operação
            if "operacao" in filters and "operacao" in df.columns:
                df = df.filter(
                    pl.col("operacao").str.to_lowercase() == filters["operacao"].lower()
                )

            return df

        except Exception as e:
            logger.error(f"Erro ao aplicar filtros: {e}")
            return df

    def aggregate_data(self, df: pl.DataFrame, metric: str,
                       groupby: List[str] = None) -> Dict[str, Any]:
        """
        Agrega dados para responder perguntas

        Args:
            df: DataFrame com dados
            metric: Métrica a agregar (hectares, toneladas, etc)
            groupby: Colunas para agrupar

        Returns:
            Dicionário com resultados agregados
        """
        if df is None or len(df) == 0:
            return {}

        try:
            results = {}

            # Métricas disponíveis no DataFrame
            numeric_cols = [col for col in df.columns
                          if df[col].dtype in [pl.Float64, pl.Float32, pl.Int64, pl.Int32]]

            # Encontra coluna relevante para a métrica
            metric_col = None
            for col in numeric_cols:
                if metric.lower() in col.lower():
                    metric_col = col
                    break

            if metric_col:
                if groupby:
                    # Agregação com agrupamento
                    agg_df = df.group_by(groupby).agg([
                        pl.col(metric_col).sum().alias("total"),
                        pl.col(metric_col).mean().alias("media"),
                        pl.col(metric_col).count().alias("registros")
                    ])
                    results["grouped"] = agg_df.to_dicts()
                else:
                    # Agregação simples
                    results["total"] = df[metric_col].sum()
                    results["media"] = df[metric_col].mean()
                    results["registros"] = len(df)
            else:
                # Retorna estatísticas gerais
                results["registros"] = len(df)
                results["colunas"] = df.columns

            return results

        except Exception as e:
            logger.error(f"Erro ao agregar dados: {e}")
            return {}

    def get_available_metrics(self) -> List[str]:
        """Retorna métricas disponíveis nos arquivos"""
        metrics = set()

        for file_info in list(self.file_index.values())[:10]:  # Amostra
            try:
                df = self.read_parquet(file_info["path"], use_polars=True)
                if df is not None:
                    numeric_cols = [col for col in df.columns
                                  if df[col].dtype in [pl.Float64, pl.Float32, pl.Int64, pl.Int32]]
                    metrics.update(numeric_cols)
            except:
                continue

        return sorted(list(metrics))

    def refresh_index(self) -> None:
        """Recarrega índice de arquivos"""
        logger.info("Recarregando índice de arquivos...")
        self._index_files()
