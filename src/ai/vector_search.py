"""
Sistema de Busca Vetorial com Embeddings
Permite busca semântica nos dados históricos
"""
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
from datetime import datetime

try:
    import chromadb
    from chromadb.config import Settings
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    chromadb = None
    SentenceTransformer = None

from config.settings import VECTOR_DB_PATH, EMBEDDING_MODEL

logger = logging.getLogger(__name__)


class VectorSearch:
    """Sistema de busca vetorial para dados históricos"""

    def __init__(self, db_path: Path = VECTOR_DB_PATH):
        if not EMBEDDINGS_AVAILABLE:
            logger.warning(
                "Bibliotecas de embeddings não disponíveis. "
                "Instale: pip install chromadb sentence-transformers"
            )
            self.enabled = False
            return

        self.enabled = True
        self.db_path = db_path
        self.db_path.mkdir(parents=True, exist_ok=True)

        # Inicializa ChromaDB
        try:
            self.client = chromadb.PersistentClient(
                path=str(self.db_path),
                settings=Settings(anonymized_telemetry=False)
            )
            logger.info("ChromaDB inicializado")
        except Exception as e:
            logger.error(f"Erro ao inicializar ChromaDB: {e}")
            self.enabled = False
            return

        # Carrega modelo de embeddings
        try:
            self.model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
            logger.info("Modelo de embeddings carregado")
        except Exception as e:
            logger.error(f"Erro ao carregar modelo de embeddings: {e}")
            self.enabled = False
            return

        # Coleções
        self.queries_collection = self._get_or_create_collection("user_queries")
        self.knowledge_collection = self._get_or_create_collection("knowledge_base")

        logger.info("VectorSearch inicializado com sucesso")

    def _get_or_create_collection(self, name: str):
        """Obtém ou cria uma coleção"""
        if not self.enabled:
            return None

        try:
            return self.client.get_or_create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            logger.error(f"Erro ao criar coleção {name}: {e}")
            return None

    def add_query(self, query: str, response: Dict[str, Any],
                  metadata: Optional[Dict] = None) -> None:
        """
        Adiciona uma consulta ao histórico vetorial

        Args:
            query: Consulta do usuário
            response: Resposta gerada
            metadata: Metadados adicionais
        """
        if not self.enabled or not self.queries_collection:
            return

        try:
            # Gera ID único
            doc_id = f"query_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

            # Prepara metadados
            meta = {
                "timestamp": datetime.now().isoformat(),
                "confidence": response.get("confidence", 0.0),
                "intent": response.get("intent", "unknown"),
                "success": response.get("success", False),
            }

            if metadata:
                meta.update(metadata)

            # Adiciona à coleção
            self.queries_collection.add(
                documents=[query],
                metadatas=[meta],
                ids=[doc_id]
            )

            logger.debug(f"Query adicionada ao vetor DB: {doc_id}")

        except Exception as e:
            logger.error(f"Erro ao adicionar query ao vetor DB: {e}")

    def add_knowledge(self, text: str, category: str,
                     metadata: Optional[Dict] = None) -> None:
        """
        Adiciona conhecimento à base vetorial

        Args:
            text: Texto do conhecimento
            category: Categoria (operacao, unidade, etc)
            metadata: Metadados adicionais
        """
        if not self.enabled or not self.knowledge_collection:
            return

        try:
            doc_id = f"knowledge_{category}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

            meta = {
                "category": category,
                "timestamp": datetime.now().isoformat(),
            }

            if metadata:
                meta.update(metadata)

            self.knowledge_collection.add(
                documents=[text],
                metadatas=[meta],
                ids=[doc_id]
            )

            logger.debug(f"Conhecimento adicionado: {doc_id}")

        except Exception as e:
            logger.error(f"Erro ao adicionar conhecimento: {e}")

    def search_similar_queries(self, query: str, n_results: int = 5) -> List[Dict]:
        """
        Busca consultas similares no histórico

        Args:
            query: Consulta para buscar similares
            n_results: Número de resultados

        Returns:
            Lista de consultas similares com metadados
        """
        if not self.enabled or not self.queries_collection:
            return []

        try:
            results = self.queries_collection.query(
                query_texts=[query],
                n_results=n_results
            )

            similar = []
            if results and results['documents']:
                for i, doc in enumerate(results['documents'][0]):
                    similar.append({
                        "query": doc,
                        "distance": results['distances'][0][i] if 'distances' in results else None,
                        "metadata": results['metadatas'][0][i] if 'metadatas' in results else {}
                    })

            return similar

        except Exception as e:
            logger.error(f"Erro ao buscar queries similares: {e}")
            return []

    def search_knowledge(self, query: str, category: Optional[str] = None,
                        n_results: int = 5) -> List[Dict]:
        """
        Busca conhecimento relevante na base

        Args:
            query: Consulta
            category: Filtro por categoria (opcional)
            n_results: Número de resultados

        Returns:
            Lista de conhecimentos relevantes
        """
        if not self.enabled or not self.knowledge_collection:
            return []

        try:
            where = {"category": category} if category else None

            results = self.knowledge_collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where
            )

            knowledge = []
            if results and results['documents']:
                for i, doc in enumerate(results['documents'][0]):
                    knowledge.append({
                        "text": doc,
                        "distance": results['distances'][0][i] if 'distances' in results else None,
                        "metadata": results['metadatas'][0][i] if 'metadatas' in results else {}
                    })

            return knowledge

        except Exception as e:
            logger.error(f"Erro ao buscar conhecimento: {e}")
            return []

    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas do banco vetorial"""
        if not self.enabled:
            return {"enabled": False}

        stats = {"enabled": True}

        try:
            if self.queries_collection:
                stats["total_queries"] = self.queries_collection.count()

            if self.knowledge_collection:
                stats["total_knowledge"] = self.knowledge_collection.count()

        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")

        return stats

    def index_historical_data(self, data: List[Dict[str, Any]]) -> int:
        """
        Indexa dados históricos para busca vetorial

        Args:
            data: Lista de dicionários com dados

        Returns:
            Número de itens indexados
        """
        if not self.enabled:
            return 0

        indexed = 0

        for item in data:
            try:
                # Cria texto descritivo do item
                text_parts = []

                if 'unidade' in item:
                    text_parts.append(f"Unidade: {item['unidade']}")

                if 'operacao' in item:
                    text_parts.append(f"Operação: {item['operacao']}")

                if 'data' in item:
                    text_parts.append(f"Data: {item['data']}")

                # Adiciona métricas
                for key, value in item.items():
                    if key not in ['unidade', 'operacao', 'data'] and isinstance(value, (int, float)):
                        text_parts.append(f"{key}: {value}")

                text = " | ".join(text_parts)

                # Adiciona ao knowledge base
                self.add_knowledge(
                    text=text,
                    category=item.get('operacao', 'geral'),
                    metadata={
                        'unidade': item.get('unidade'),
                        'data': str(item.get('data'))
                    }
                )

                indexed += 1

            except Exception as e:
                logger.error(f"Erro ao indexar item: {e}")
                continue

        logger.info(f"{indexed} itens indexados no banco vetorial")
        return indexed

    def clear_collection(self, collection_name: str) -> bool:
        """Limpa uma coleção"""
        if not self.enabled:
            return False

        try:
            self.client.delete_collection(collection_name)
            logger.info(f"Coleção {collection_name} limpa")
            return True
        except Exception as e:
            logger.error(f"Erro ao limpar coleção: {e}")
            return False
