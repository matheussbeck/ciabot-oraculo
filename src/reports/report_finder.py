"""
Gerenciador de Relatórios Existentes (Power BI)
"""
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import re

from config.settings import REPORTS_DIR

logger = logging.getLogger(__name__)


class ReportFinder:
    """Encontra e gerencia relatórios já existentes (Power BI)"""

    def __init__(self, powerbi_reports_dir: Path = None):
        """
        Args:
            powerbi_reports_dir: Diretório onde estão os relatórios do Power BI
        """
        if powerbi_reports_dir:
            self.powerbi_dir = powerbi_reports_dir
        else:
            # Diretório padrão para relatórios Power BI
            self.powerbi_dir = REPORTS_DIR.parent / "powerbi_reports"

        self.powerbi_dir.mkdir(parents=True, exist_ok=True)
        self.report_index = {}
        self._index_reports()

        logger.info(f"ReportFinder inicializado. Diretório: {self.powerbi_dir}")

    def _index_reports(self) -> None:
        """Indexa todos os relatórios PDF disponíveis"""
        self.report_index = {}

        if not self.powerbi_dir.exists():
            logger.warning(f"Diretório de relatórios não encontrado: {self.powerbi_dir}")
            return

        # Busca todos os PDFs no diretório e subdiretórios
        pdf_files = list(self.powerbi_dir.rglob("*.pdf"))

        for pdf_path in pdf_files:
            # Extrai metadados do nome do arquivo
            file_name = pdf_path.stem
            file_name_lower = file_name.lower()

            # Extrai palavras-chave do nome
            keywords = self._extract_keywords(file_name_lower)

            # Tenta extrair data do nome do arquivo
            file_date = self._extract_date_from_filename(file_name)

            metadata = {
                "path": pdf_path,
                "name": file_name,
                "size": pdf_path.stat().st_size,
                "modified": datetime.fromtimestamp(pdf_path.stat().st_mtime),
                "keywords": keywords,
                "file_date": file_date,
                "category": self._categorize_report(file_name_lower)
            }

            self.report_index[file_name] = metadata

        logger.info(f"Indexados {len(self.report_index)} relatórios PDF")

    def _extract_keywords(self, filename: str) -> set:
        """Extrai palavras-chave do nome do arquivo"""
        # Remove extensão e caracteres especiais
        clean_name = re.sub(r'[_\-.]', ' ', filename)

        # Divide em palavras
        words = clean_name.lower().split()

        # Remove palavras muito curtas e números isolados
        keywords = {w for w in words if len(w) > 2 and not w.isdigit()}

        return keywords

    def _extract_date_from_filename(self, filename: str) -> Optional[datetime]:
        """Tenta extrair data do nome do arquivo"""
        # Padrões comuns de data: 2024-05-15, 20240515, 15-05-2024, etc
        patterns = [
            r'(\d{4})[_-]?(\d{2})[_-]?(\d{2})',  # YYYY-MM-DD ou YYYYMMDD
            r'(\d{2})[_-]?(\d{2})[_-]?(\d{4})',  # DD-MM-YYYY
        ]

        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                groups = match.groups()
                try:
                    if len(groups[0]) == 4:  # YYYY-MM-DD
                        return datetime(int(groups[0]), int(groups[1]), int(groups[2]))
                    else:  # DD-MM-YYYY
                        return datetime(int(groups[2]), int(groups[1]), int(groups[0]))
                except ValueError:
                    continue

        return None

    def _categorize_report(self, filename: str) -> str:
        """Categoriza o relatório baseado no nome"""
        categories = {
            'plantio': ['plantio', 'planting', 'plant'],
            'corte': ['corte', 'colheita', 'harvest', 'cutting'],
            'transporte': ['transporte', 'transport', 'logistica', 'logistics'],
            'carregamento': ['carregamento', 'loading', 'carga'],
            'producao': ['producao', 'production', 'produtividade'],
            'operacional': ['operacional', 'operational', 'operacao'],
            'gerencial': ['gerencial', 'management', 'executive'],
            'consolidado': ['consolidado', 'consolidated', 'resumo', 'summary'],
            'diario': ['diario', 'daily', 'dia'],
            'semanal': ['semanal', 'weekly', 'semana'],
            'mensal': ['mensal', 'monthly', 'mes', 'month'],
            'safra': ['safra', 'season', 'anual'],
        }

        detected_categories = []

        for category, keywords in categories.items():
            if any(keyword in filename for keyword in keywords):
                detected_categories.append(category)

        return ', '.join(detected_categories) if detected_categories else 'geral'

    def find_reports(self, query: str, unidade: Optional[str] = None,
                    operacao: Optional[str] = None, limite: int = 10) -> List[Dict[str, Any]]:
        """
        Busca relatórios relevantes

        Args:
            query: Consulta do usuário
            unidade: Filtro por unidade
            operacao: Filtro por operação
            limite: Número máximo de resultados

        Returns:
            Lista de relatórios encontrados com score de relevância
        """
        if not self.report_index:
            logger.warning("Nenhum relatório indexado")
            return []

        query_lower = query.lower()
        query_terms = set(query_lower.split())

        results = []

        for file_name, metadata in self.report_index.items():
            score = 0
            keywords = metadata["keywords"]

            # Score baseado em palavras da query
            common_terms = query_terms.intersection(keywords)
            score += len(common_terms) * 10

            # Bonus para operação específica
            if operacao and operacao.lower() in metadata["category"]:
                score += 25

            # Bonus para unidade específica
            if unidade:
                unidade_variations = [
                    unidade.lower(),
                    unidade.lower().replace(" ", ""),
                    unidade.lower().replace(" ", "_")
                ]
                if any(var in file_name.lower() for var in unidade_variations):
                    score += 25

            # Bonus para termos importantes
            important_terms = {
                'relatorio', 'report', 'plantio', 'corte', 'transporte',
                'carregamento', 'diario', 'semanal', 'mensal', 'consolidado',
                'hora', 'hourly', 'detalhado'
            }

            important_matches = query_terms.intersection(important_terms).intersection(keywords)
            score += len(important_matches) * 15

            # Detecta período específico na query
            if any(term in query_lower for term in ['hora a hora', 'hourly', 'detalhado']):
                if any(term in file_name.lower() for term in ['hora', 'hourly', 'detalhado', 'detailed']):
                    score += 20

            if any(term in query_lower for term in ['diario', 'daily', 'dia']):
                if 'diario' in metadata["category"] or 'daily' in file_name.lower():
                    score += 20

            if any(term in query_lower for term in ['semanal', 'weekly', 'semana']):
                if 'semanal' in metadata["category"] or 'weekly' in file_name.lower():
                    score += 20

            # Bonus para relatórios recentes (modificados recentemente)
            days_old = (datetime.now() - metadata["modified"]).days
            if days_old <= 7:
                score += 10
            elif days_old <= 30:
                score += 5

            if score > 0:
                results.append({
                    **metadata,
                    "score": score
                })

        # Ordena por score
        results.sort(key=lambda x: x["score"], reverse=True)

        # Limita resultados
        return results[:limite]

    def get_report_by_name(self, report_name: str) -> Optional[Dict[str, Any]]:
        """Busca relatório pelo nome exato ou parcial"""
        report_name_lower = report_name.lower()

        # Busca exata
        if report_name in self.report_index:
            return self.report_index[report_name]

        # Busca parcial
        for name, metadata in self.report_index.items():
            if report_name_lower in name.lower():
                return metadata

        return None

    def list_all_reports(self, categoria: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lista todos os relatórios, opcionalmente filtrados por categoria"""
        reports = list(self.report_index.values())

        if categoria:
            reports = [r for r in reports if categoria.lower() in r["category"]]

        # Ordena por data de modificação (mais recentes primeiro)
        reports.sort(key=lambda x: x["modified"], reverse=True)

        return reports

    def get_categories(self) -> Dict[str, int]:
        """Retorna categorias disponíveis e quantidade de relatórios em cada"""
        categories = {}

        for metadata in self.report_index.values():
            cats = metadata["category"].split(", ")
            for cat in cats:
                if cat:
                    categories[cat] = categories.get(cat, 0) + 1

        return dict(sorted(categories.items(), key=lambda x: x[1], reverse=True))

    def get_units(self) -> List[str]:
        """Retorna lista de unidades encontradas nos relatórios"""
        from config.settings import UNIDADES

        units_found = set()

        for file_name in self.report_index.keys():
            file_name_lower = file_name.lower()
            for unidade in UNIDADES:
                if unidade.lower() in file_name_lower:
                    units_found.add(unidade)

        return sorted(list(units_found))

    def refresh_index(self) -> None:
        """Recarrega índice de relatórios"""
        logger.info("Recarregando índice de relatórios...")
        self._index_reports()

    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas sobre os relatórios"""
        if not self.report_index:
            return {"total": 0}

        total_size = sum(r["size"] for r in self.report_index.values())

        return {
            "total": len(self.report_index),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "categories": self.get_categories(),
            "units": self.get_units(),
            "oldest": min(r["modified"] for r in self.report_index.values()),
            "newest": max(r["modified"] for r in self.report_index.values())
        }
