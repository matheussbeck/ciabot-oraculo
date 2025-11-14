"""
Sistema de Aprendizado Contínuo
Aprende com interações e melhora respostas ao longo do tempo
"""
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
from collections import defaultdict

from config.settings import DATA_DIR

logger = logging.getLogger(__name__)


class ContinuousLearning:
    """Sistema que aprende com interações do usuário"""

    def __init__(self, learning_dir: Path = None):
        self.learning_dir = learning_dir or (DATA_DIR / "learning")
        self.learning_dir.mkdir(parents=True, exist_ok=True)

        # Arquivos de persistência
        self.feedback_file = self.learning_dir / "user_feedback.jsonl"
        self.patterns_file = self.learning_dir / "learned_patterns.json"
        self.metrics_file = self.learning_dir / "metrics.json"

        # Cache de padrões aprendidos
        self.patterns = self._load_patterns()
        self.metrics = self._load_metrics()

        logger.info("Sistema de aprendizado contínuo inicializado")

    def _load_patterns(self) -> Dict[str, Any]:
        """Carrega padrões aprendidos"""
        if self.patterns_file.exists():
            try:
                with open(self.patterns_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Erro ao carregar padrões: {e}")

        return {
            "common_queries": {},  # Consultas comuns
            "query_mappings": {},  # Mapeamentos de variações
            "successful_patterns": {},  # Padrões bem-sucedidos
            "failed_patterns": {},  # Padrões que falharam
            "terminology": {},  # Terminologia específica do usuário
        }

    def _save_patterns(self) -> None:
        """Salva padrões aprendidos"""
        try:
            with open(self.patterns_file, 'w', encoding='utf-8') as f:
                json.dump(self.patterns, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erro ao salvar padrões: {e}")

    def _load_metrics(self) -> Dict[str, Any]:
        """Carrega métricas de aprendizado"""
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Erro ao carregar métricas: {e}")

        return {
            "total_interactions": 0,
            "successful_responses": 0,
            "failed_responses": 0,
            "average_confidence": 0.0,
            "most_common_intents": {},
            "most_requested_units": {},
            "most_requested_operations": {},
            "last_updated": datetime.now().isoformat()
        }

    def _save_metrics(self) -> None:
        """Salva métricas"""
        self.metrics["last_updated"] = datetime.now().isoformat()

        try:
            with open(self.metrics_file, 'w', encoding='utf-8') as f:
                json.dump(self.metrics, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erro ao salvar métricas: {e}")

    def record_interaction(self, query: str, response: Dict[str, Any],
                          params: Dict[str, Any], user_id: Optional[int] = None) -> None:
        """
        Registra uma interação para aprendizado

        Args:
            query: Consulta do usuário
            response: Resposta gerada
            params: Parâmetros extraídos
            user_id: ID do usuário
        """
        try:
            # Atualiza métricas
            self.metrics["total_interactions"] += 1

            if response.get("success", False):
                self.metrics["successful_responses"] += 1
            else:
                self.metrics["failed_responses"] += 1

            # Atualiza média de confiança
            confidence = response.get("confidence", 0.0)
            total = self.metrics["total_interactions"]
            current_avg = self.metrics["average_confidence"]
            self.metrics["average_confidence"] = (
                (current_avg * (total - 1) + confidence) / total
            )

            # Registra intent
            intent = response.get("intent", "unknown")
            self.metrics["most_common_intents"][intent] = \
                self.metrics["most_common_intents"].get(intent, 0) + 1

            # Registra unidade e operação
            if params.get("unidade"):
                unit = params["unidade"]
                self.metrics["most_requested_units"][unit] = \
                    self.metrics["most_requested_units"].get(unit, 0) + 1

            if params.get("operacao"):
                op = params["operacao"]
                self.metrics["most_requested_operations"][op] = \
                    self.metrics["most_requested_operations"].get(op, 0) + 1

            # Aprende padrões
            self._learn_from_interaction(query, response, params)

            # Salva feedback
            self._save_feedback({
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "query": query,
                "success": response.get("success", False),
                "confidence": confidence,
                "intent": intent,
                "params": params
            })

            self._save_metrics()

        except Exception as e:
            logger.error(f"Erro ao registrar interação: {e}")

    def _learn_from_interaction(self, query: str, response: Dict[str, Any],
                                params: Dict[str, Any]) -> None:
        """Aprende padrões da interação"""

        query_lower = query.lower()

        # Aprende consultas comuns
        if response.get("success", False):
            self.patterns["common_queries"][query_lower] = \
                self.patterns["common_queries"].get(query_lower, 0) + 1

            # Aprende padrões bem-sucedidos
            intent = response.get("intent")
            if intent:
                if intent not in self.patterns["successful_patterns"]:
                    self.patterns["successful_patterns"][intent] = []

                pattern = {
                    "query_template": self._extract_template(query, params),
                    "params": params,
                    "count": 1
                }

                # Verifica se padrão similar já existe
                found = False
                for existing in self.patterns["successful_patterns"][intent]:
                    if existing["query_template"] == pattern["query_template"]:
                        existing["count"] += 1
                        found = True
                        break

                if not found:
                    self.patterns["successful_patterns"][intent].append(pattern)

        else:
            # Registra padrões que falharam
            if query_lower not in self.patterns["failed_patterns"]:
                self.patterns["failed_patterns"][query_lower] = {
                    "count": 0,
                    "last_seen": None
                }

            self.patterns["failed_patterns"][query_lower]["count"] += 1
            self.patterns["failed_patterns"][query_lower]["last_seen"] = \
                datetime.now().isoformat()

        # Aprende terminologia
        self._learn_terminology(query, params)

        self._save_patterns()

    def _extract_template(self, query: str, params: Dict[str, Any]) -> str:
        """Extrai template genérico da consulta"""
        template = query.lower()

        # Substitui valores específicos por placeholders
        if params.get("unidade"):
            template = template.replace(params["unidade"].lower(), "{unidade}")

        if params.get("operacao"):
            template = template.replace(params["operacao"].lower(), "{operacao}")

        # Substitui datas
        date_words = ["ontem", "hoje", "últimos", "ultimos", "dias", "semana", "mês"]
        for word in date_words:
            if word in template:
                template = template.replace(word, "{periodo}")

        return template

    def _learn_terminology(self, query: str, params: Dict[str, Any]) -> None:
        """Aprende terminologia específica do usuário"""

        words = query.lower().split()

        # Aprende sinônimos
        if params.get("operacao"):
            op = params["operacao"]
            if op not in self.patterns["terminology"]:
                self.patterns["terminology"][op] = set()

            # Procura palavras que possam ser sinônimos
            for word in words:
                if len(word) > 3 and word not in ["para", "sobre", "como", "qual", "quanto"]:
                    self.patterns["terminology"][op].add(word)

        # Converte sets para listas para JSON
        for key in self.patterns["terminology"]:
            if isinstance(self.patterns["terminology"][key], set):
                self.patterns["terminology"][key] = list(self.patterns["terminology"][key])

    def _save_feedback(self, feedback: Dict[str, Any]) -> None:
        """Salva feedback em arquivo JSONL"""
        try:
            with open(self.feedback_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(feedback, ensure_ascii=False) + '\n')
        except Exception as e:
            logger.error(f"Erro ao salvar feedback: {e}")

    def get_suggestions_for_query(self, query: str) -> List[str]:
        """
        Sugere melhorias ou alternativas para uma consulta

        Args:
            query: Consulta do usuário

        Returns:
            Lista de sugestões
        """
        suggestions = []

        query_lower = query.lower()

        # Verifica se é uma consulta comum
        if query_lower in self.patterns["common_queries"]:
            count = self.patterns["common_queries"][query_lower]
            if count > 5:
                suggestions.append(
                    f"Esta é uma consulta frequente (já feita {count}x)"
                )

        # Verifica se já falhou antes
        if query_lower in self.patterns["failed_patterns"]:
            fail_info = self.patterns["failed_patterns"][query_lower]
            if fail_info["count"] > 2:
                suggestions.append(
                    "⚠️ Esta consulta falhou anteriormente. "
                    "Tente ser mais específico com unidade, período e operação."
                )

        return suggestions

    def get_learned_insights(self) -> Dict[str, Any]:
        """Retorna insights aprendidos"""
        insights = {
            "total_interactions": self.metrics["total_interactions"],
            "success_rate": 0.0,
            "average_confidence": self.metrics["average_confidence"],
            "top_intents": [],
            "top_units": [],
            "top_operations": [],
            "common_queries": [],
            "problematic_queries": []
        }

        # Taxa de sucesso
        if self.metrics["total_interactions"] > 0:
            insights["success_rate"] = (
                self.metrics["successful_responses"] /
                self.metrics["total_interactions"]
            ) * 100

        # Top intents
        intents = sorted(
            self.metrics["most_common_intents"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        insights["top_intents"] = [{"intent": i[0], "count": i[1]} for i in intents]

        # Top unidades
        units = sorted(
            self.metrics["most_requested_units"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        insights["top_units"] = [{"unit": u[0], "count": u[1]} for u in units]

        # Top operações
        ops = sorted(
            self.metrics["most_requested_operations"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        insights["top_operations"] = [{"operation": o[0], "count": o[1]} for o in ops]

        # Consultas comuns
        common = sorted(
            self.patterns["common_queries"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        insights["common_queries"] = [
            {"query": c[0], "count": c[1]} for c in common
        ]

        # Consultas problemáticas
        problems = sorted(
            self.patterns["failed_patterns"].items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )[:10]
        insights["problematic_queries"] = [
            {"query": p[0], "failures": p[1]["count"]} for p in problems
        ]

        return insights

    def export_learning_data(self, output_path: Optional[Path] = None) -> Path:
        """Exporta dados de aprendizado para análise"""
        if not output_path:
            output_path = self.learning_dir / f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        export_data = {
            "exported_at": datetime.now().isoformat(),
            "metrics": self.metrics,
            "patterns": self.patterns,
            "insights": self.get_learned_insights()
        }

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Dados de aprendizado exportados: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Erro ao exportar dados: {e}")
            return None

    def reset_learning(self) -> None:
        """Reseta todo o aprendizado (use com cuidado!)"""
        logger.warning("Resetando sistema de aprendizado...")

        self.patterns = {
            "common_queries": {},
            "query_mappings": {},
            "successful_patterns": {},
            "failed_patterns": {},
            "terminology": {},
        }

        self.metrics = {
            "total_interactions": 0,
            "successful_responses": 0,
            "failed_responses": 0,
            "average_confidence": 0.0,
            "most_common_intents": {},
            "most_requested_units": {},
            "most_requested_operations": {},
            "last_updated": datetime.now().isoformat()
        }

        self._save_patterns()
        self._save_metrics()

        logger.info("Sistema de aprendizado resetado")
