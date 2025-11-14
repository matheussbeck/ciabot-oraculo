"""
Exportador de Dados
Exporta dados em múltiplos formatos (CSV, Excel, JSON)
"""
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import pandas as pd
import polars as pl
import json

from config.settings import DATA_DIR

logger = logging.getLogger(__name__)


class DataExporter:
    """Exportador de dados em vários formatos"""

    def __init__(self, export_dir: Optional[Path] = None):
        """
        Inicializa exportador

        Args:
            export_dir: Diretório para salvar exports
        """
        self.export_dir = export_dir or (DATA_DIR / "exports")
        self.export_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"DataExporter inicializado: {self.export_dir}")

    def export_to_csv(self, data: Any, filename: str,
                     include_timestamp: bool = True) -> Optional[Path]:
        """
        Exporta dados para CSV

        Args:
            data: DataFrame (Polars ou Pandas) ou lista de dicionários
            filename: Nome do arquivo (sem extensão)
            include_timestamp: Adicionar timestamp ao nome

        Returns:
            Caminho do arquivo criado
        """
        try:
            # Converte para Pandas
            if isinstance(data, pl.DataFrame):
                df = data.to_pandas()
            elif isinstance(data, list):
                df = pd.DataFrame(data)
            else:
                df = data

            # Nome do arquivo
            if include_timestamp:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{filename}_{timestamp}"

            filepath = self.export_dir / f"{filename}.csv"

            # Exporta
            df.to_csv(filepath, index=False, encoding='utf-8-sig')

            size_kb = filepath.stat().st_size / 1024
            logger.info(f"CSV exportado: {filepath.name} ({size_kb:.2f} KB)")

            return filepath

        except Exception as e:
            logger.error(f"Erro ao exportar CSV: {e}")
            return None

    def export_to_excel(self, data: Any, filename: str,
                       sheet_name: str = "Dados",
                       include_timestamp: bool = True) -> Optional[Path]:
        """
        Exporta dados para Excel (.xlsx)

        Args:
            data: DataFrame ou dict de DataFrames (múltiplas sheets)
            filename: Nome do arquivo
            sheet_name: Nome da planilha (se data for DataFrame único)
            include_timestamp: Adicionar timestamp

        Returns:
            Caminho do arquivo criado
        """
        try:
            if include_timestamp:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{filename}_{timestamp}"

            filepath = self.export_dir / f"{filename}.xlsx"

            # Se é dicionário, múltiplas sheets
            if isinstance(data, dict):
                with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                    for sheet, df in data.items():
                        if isinstance(df, pl.DataFrame):
                            df = df.to_pandas()
                        df.to_excel(writer, sheet_name=sheet, index=False)

            else:
                # Sheet única
                if isinstance(data, pl.DataFrame):
                    df = data.to_pandas()
                elif isinstance(data, list):
                    df = pd.DataFrame(data)
                else:
                    df = data

                df.to_excel(filepath, sheet_name=sheet_name, index=False,
                           engine='openpyxl')

            size_kb = filepath.stat().st_size / 1024
            logger.info(f"Excel exportado: {filepath.name} ({size_kb:.2f} KB)")

            return filepath

        except Exception as e:
            logger.error(f"Erro ao exportar Excel: {e}")
            return None

    def export_to_json(self, data: Any, filename: str,
                      include_timestamp: bool = True,
                      pretty: bool = True) -> Optional[Path]:
        """
        Exporta dados para JSON

        Args:
            data: DataFrame, lista ou dicionário
            filename: Nome do arquivo
            include_timestamp: Adicionar timestamp
            pretty: JSON formatado (indentado)

        Returns:
            Caminho do arquivo criado
        """
        try:
            if include_timestamp:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{filename}_{timestamp}"

            filepath = self.export_dir / f"{filename}.json"

            # Converte DataFrame para dict/list
            if isinstance(data, (pd.DataFrame, pl.DataFrame)):
                if isinstance(data, pl.DataFrame):
                    data = data.to_pandas()
                json_data = data.to_dict(orient='records')
            else:
                json_data = data

            # Exporta
            with open(filepath, 'w', encoding='utf-8') as f:
                if pretty:
                    json.dump(json_data, f, indent=2, ensure_ascii=False,
                             default=str)
                else:
                    json.dump(json_data, f, ensure_ascii=False, default=str)

            size_kb = filepath.stat().st_size / 1024
            logger.info(f"JSON exportado: {filepath.name} ({size_kb:.2f} KB)")

            return filepath

        except Exception as e:
            logger.error(f"Erro ao exportar JSON: {e}")
            return None

    def export_query_results(self, query: str, results: Dict[str, Any],
                            format: str = "excel") -> Optional[Path]:
        """
        Exporta resultados de uma query

        Args:
            query: Query original
            results: Resultados da query
            format: Formato de exportação (csv, excel, json)

        Returns:
            Caminho do arquivo exportado
        """
        filename = f"query_result_{query[:30].replace(' ', '_')}"

        export_data = {
            "metadata": {
                "query": query,
                "exported_at": datetime.now().isoformat(),
                "confidence": results.get("confidence"),
                "intent": results.get("intent")
            },
            "response": results.get("response"),
            "params": results.get("params", {})
        }

        if format == "csv":
            # Para CSV, só exporta params como tabela
            if "params" in results and results["params"]:
                return self.export_to_csv(
                    [results["params"]],
                    filename
                )

        elif format == "excel":
            # Excel com múltiplas sheets
            sheets = {
                "Metadata": pd.DataFrame([export_data["metadata"]]),
                "Response": pd.DataFrame([{"response": export_data["response"]}])
            }

            if export_data["params"]:
                sheets["Parameters"] = pd.DataFrame([export_data["params"]])

            return self.export_to_excel(sheets, filename)

        elif format == "json":
            return self.export_to_json(export_data, filename)

        return None

    def export_learning_insights(self, insights: Dict[str, Any]) -> Optional[Path]:
        """
        Exporta insights de aprendizado

        Args:
            insights: Insights do ContinuousLearning

        Returns:
            Caminho do arquivo Excel exportado
        """
        try:
            filename = "learning_insights"

            sheets = {}

            # Sheet de estatísticas gerais
            stats = {
                "total_interactions": [insights["total_interactions"]],
                "success_rate": [insights["success_rate"]],
                "average_confidence": [insights["average_confidence"]]
            }
            sheets["Statistics"] = pd.DataFrame(stats)

            # Top intents
            if insights["top_intents"]:
                sheets["Top Intents"] = pd.DataFrame(insights["top_intents"])

            # Top unidades
            if insights["top_units"]:
                sheets["Top Units"] = pd.DataFrame(insights["top_units"])

            # Top operações
            if insights["top_operations"]:
                sheets["Top Operations"] = pd.DataFrame(insights["top_operations"])

            # Queries comuns
            if insights["common_queries"]:
                sheets["Common Queries"] = pd.DataFrame(insights["common_queries"])

            # Queries problemáticas
            if insights["problematic_queries"]:
                sheets["Problematic Queries"] = pd.DataFrame(
                    insights["problematic_queries"]
                )

            return self.export_to_excel(sheets, filename, include_timestamp=True)

        except Exception as e:
            logger.error(f"Erro ao exportar insights: {e}")
            return None

    def list_exports(self) -> List[Dict[str, Any]]:
        """Lista todos os exports disponíveis"""
        exports = []

        for ext in ['*.csv', '*.xlsx', '*.json']:
            for file_path in self.export_dir.glob(ext):
                stat = file_path.stat()

                exports.append({
                    "name": file_path.name,
                    "format": file_path.suffix[1:],
                    "size_kb": round(stat.st_size / 1024, 2),
                    "created": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })

        return sorted(exports, key=lambda x: x['created'], reverse=True)

    def clear_old_exports(self, days: int = 30) -> int:
        """
        Remove exports antigos

        Args:
            days: Remover exports mais antigos que N dias

        Returns:
            Número de arquivos removidos
        """
        cutoff = datetime.now().timestamp() - (days * 86400)
        deleted = 0

        for ext in ['*.csv', '*.xlsx', '*.json']:
            for file_path in self.export_dir.glob(ext):
                if file_path.stat().st_mtime < cutoff:
                    file_path.unlink()
                    deleted += 1
                    logger.info(f"Export antigo removido: {file_path.name}")

        return deleted
