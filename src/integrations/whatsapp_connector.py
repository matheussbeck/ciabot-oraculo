"""
Conector para WhatsApp
Status: EM DESENVOLVIMENTO - Aguardando integração com sistema de mensagens

Funcionalidades:
- Salvar mensagens no banco para envio via WhatsApp
- Enfileirar mensagens
- Marcar mensagens como enviadas/falhadas
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import json
import sqlite3

from config.settings import DATA_DIR

logger = logging.getLogger(__name__)


class WhatsAppConnector:
    """
    Conector para integração com WhatsApp

    STATUS: EM DESENVOLVIMENTO

    TODO: Integrar com sistema de envio de mensagens WhatsApp
    - Configurar conexão com banco de mensagens
    - Implementar fila de envio
    - Adicionar callbacks de status
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Inicializa conector do WhatsApp

        Args:
            db_path: Caminho do banco de dados de mensagens
        """
        self.db_path = db_path or (DATA_DIR / "whatsapp_messages.db")
        self.enabled = False  # Desabilitado até configuração completa

        # Inicializa banco de dados SQLite
        self._init_database()

        logger.info("WhatsAppConnector inicializado [EM DESENVOLVIMENTO]")
        logger.warning(
            "WhatsApp integration is not yet configured. "
            "Messages will be queued in local database."
        )

    def _init_database(self) -> None:
        """Inicializa banco de dados de mensagens"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Tabela de mensagens
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    phone_number TEXT NOT NULL,
                    message TEXT NOT NULL,
                    message_type TEXT DEFAULT 'text',
                    priority INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'pending',
                    sent_at TIMESTAMP,
                    error_message TEXT,
                    retry_count INTEGER DEFAULT 0,
                    metadata TEXT
                )
            """)

            # Índices
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_status
                ON messages(status)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_created_at
                ON messages(created_at)
            """)

            conn.commit()
            conn.close()

            logger.info(f"Banco de mensagens WhatsApp inicializado: {self.db_path}")

        except Exception as e:
            logger.error(f"Erro ao inicializar banco de dados: {e}")

    def send_message(self, phone_number: str, message: str,
                    message_type: str = "text", priority: int = 0,
                    metadata: Optional[Dict] = None) -> Optional[int]:
        """
        Salva mensagem no banco para envio posterior

        Args:
            phone_number: Número do WhatsApp (formato: +5511999999999)
            message: Conteúdo da mensagem
            message_type: Tipo da mensagem (text, image, document, etc)
            priority: Prioridade (0=normal, 1=alta, 2=urgente)
            metadata: Metadados adicionais

        Returns:
            ID da mensagem salva, ou None em caso de erro

        TODO: Implementar envio real via API WhatsApp
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            metadata_json = json.dumps(metadata) if metadata else None

            cursor.execute("""
                INSERT INTO messages
                (phone_number, message, message_type, priority, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (phone_number, message, message_type, priority, metadata_json))

            message_id = cursor.lastrowid

            conn.commit()
            conn.close()

            logger.info(
                f"Mensagem salva para envio WhatsApp: "
                f"ID={message_id}, Phone={phone_number}, Priority={priority}"
            )

            return message_id

        except Exception as e:
            logger.error(f"Erro ao salvar mensagem WhatsApp: {e}")
            return None

    def send_alert(self, phone_numbers: List[str], alert_title: str,
                  alert_message: str, severity: str = "info") -> List[int]:
        """
        Envia alerta para múltiplos números

        Args:
            phone_numbers: Lista de números
            alert_title: Título do alerta
            alert_message: Mensagem do alerta
            severity: Severidade (info, warning, error, critical)

        Returns:
            Lista de IDs das mensagens criadas
        """
        # Define prioridade baseado na severidade
        priority_map = {
            "info": 0,
            "warning": 1,
            "error": 2,
            "critical": 2
        }
        priority = priority_map.get(severity, 0)

        # Formata mensagem
        emoji_map = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
            "critical": "🚨"
        }
        emoji = emoji_map.get(severity, "📢")

        formatted_message = f"{emoji} *{alert_title}*\n\n{alert_message}"

        message_ids = []

        for phone in phone_numbers:
            msg_id = self.send_message(
                phone_number=phone,
                message=formatted_message,
                message_type="text",
                priority=priority,
                metadata={
                    "alert_type": "system_alert",
                    "severity": severity,
                    "title": alert_title
                }
            )

            if msg_id:
                message_ids.append(msg_id)

        logger.info(f"Alerta salvo para {len(message_ids)} destinatários")

        return message_ids

    def get_pending_messages(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retorna mensagens pendentes de envio

        Args:
            limit: Número máximo de mensagens

        Returns:
            Lista de mensagens pendentes
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    id, created_at, phone_number, message, message_type,
                    priority, status, retry_count, metadata
                FROM messages
                WHERE status = 'pending'
                ORDER BY priority DESC, created_at ASC
                LIMIT ?
            """, (limit,))

            rows = cursor.fetchall()
            conn.close()

            messages = []
            for row in rows:
                metadata = json.loads(row[8]) if row[8] else {}

                messages.append({
                    "id": row[0],
                    "created_at": row[1],
                    "phone_number": row[2],
                    "message": row[3],
                    "message_type": row[4],
                    "priority": row[5],
                    "status": row[6],
                    "retry_count": row[7],
                    "metadata": metadata
                })

            return messages

        except Exception as e:
            logger.error(f"Erro ao buscar mensagens pendentes: {e}")
            return []

    def mark_as_sent(self, message_id: int) -> bool:
        """
        Marca mensagem como enviada

        Args:
            message_id: ID da mensagem

        Returns:
            True se atualizado com sucesso
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE messages
                SET status = 'sent', sent_at = ?
                WHERE id = ?
            """, (datetime.now().isoformat(), message_id))

            conn.commit()
            conn.close()

            logger.debug(f"Mensagem {message_id} marcada como enviada")

            return True

        except Exception as e:
            logger.error(f"Erro ao marcar mensagem como enviada: {e}")
            return False

    def mark_as_failed(self, message_id: int, error_message: str) -> bool:
        """
        Marca mensagem como falhada

        Args:
            message_id: ID da mensagem
            error_message: Mensagem de erro

        Returns:
            True se atualizado com sucesso
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE messages
                SET status = 'failed',
                    error_message = ?,
                    retry_count = retry_count + 1
                WHERE id = ?
            """, (error_message, message_id))

            conn.commit()
            conn.close()

            logger.warning(f"Mensagem {message_id} marcada como falhada: {error_message}")

            return True

        except Exception as e:
            logger.error(f"Erro ao marcar mensagem como falhada: {e}")
            return False

    def retry_failed_messages(self, max_retries: int = 3) -> int:
        """
        Marca mensagens falhadas para retry

        Args:
            max_retries: Número máximo de tentativas

        Returns:
            Número de mensagens marcadas para retry
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE messages
                SET status = 'pending'
                WHERE status = 'failed' AND retry_count < ?
            """, (max_retries,))

            updated = cursor.rowcount

            conn.commit()
            conn.close()

            logger.info(f"{updated} mensagens falhadas marcadas para retry")

            return updated

        except Exception as e:
            logger.error(f"Erro ao processar retry de mensagens: {e}")
            return 0

    def get_statistics(self) -> Dict[str, Any]:
        """
        Retorna estatísticas de mensagens

        Returns:
            Dicionário com estatísticas
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Total de mensagens
            cursor.execute("SELECT COUNT(*) FROM messages")
            total = cursor.fetchone()[0]

            # Por status
            cursor.execute("""
                SELECT status, COUNT(*)
                FROM messages
                GROUP BY status
            """)
            by_status = dict(cursor.fetchall())

            # Mensagens das últimas 24h
            cursor.execute("""
                SELECT COUNT(*)
                FROM messages
                WHERE created_at >= datetime('now', '-1 day')
            """)
            last_24h = cursor.fetchone()[0]

            conn.close()

            return {
                "total_messages": total,
                "by_status": by_status,
                "last_24h": last_24h,
                "pending": by_status.get("pending", 0),
                "sent": by_status.get("sent", 0),
                "failed": by_status.get("failed", 0)
            }

        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return {}

    def clear_old_messages(self, days: int = 30) -> int:
        """
        Remove mensagens antigas já enviadas

        Args:
            days: Número de dias para manter

        Returns:
            Número de mensagens removidas
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                DELETE FROM messages
                WHERE status = 'sent'
                AND sent_at < datetime('now', ? || ' days')
            """, (f'-{days}',))

            deleted = cursor.rowcount

            conn.commit()
            conn.close()

            logger.info(f"{deleted} mensagens antigas removidas")

            return deleted

        except Exception as e:
            logger.error(f"Erro ao limpar mensagens antigas: {e}")
            return 0

    def get_status(self) -> Dict[str, Any]:
        """
        Retorna status do conector

        Returns:
            Dicionário com informações de status
        """
        stats = self.get_statistics()

        return {
            "enabled": self.enabled,
            "database": str(self.db_path),
            "status": "development" if not self.enabled else "connected",
            "statistics": stats,
            "note": "Integration pending - Messages queued in local database"
        }
