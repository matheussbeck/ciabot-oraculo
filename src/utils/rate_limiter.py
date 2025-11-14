"""
Sistema de Rate Limiting
Previne abuso e garante uso justo dos recursos
"""
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter com sliding window"""

    def __init__(self, requests_per_minute: int = 30, requests_per_hour: int = 500):
        """
        Inicializa rate limiter

        Args:
            requests_per_minute: Máximo de requisições por minuto
            requests_per_hour: Máximo de requisições por hora
        """
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour

        # Armazena timestamps de requisições por usuário
        self.user_requests: Dict[str, deque] = defaultdict(lambda: deque())

        logger.info(
            f"RateLimiter inicializado "
            f"(rpm={requests_per_minute}, rph={requests_per_hour})"
        )

    def is_allowed(self, user_id: str) -> bool:
        """
        Verifica se usuário pode fazer requisição

        Args:
            user_id: ID do usuário (pode ser int, string, etc)

        Returns:
            True se permitido, False se excedeu limite
        """
        user_key = str(user_id)
        now = datetime.now()

        # Limpa requisições antigas
        self._cleanup_old_requests(user_key, now)

        # Obtém requisições do último minuto e hora
        requests = self.user_requests[user_key]

        one_minute_ago = now - timedelta(minutes=1)
        one_hour_ago = now - timedelta(hours=1)

        recent_minute = sum(1 for ts in requests if ts > one_minute_ago)
        recent_hour = sum(1 for ts in requests if ts > one_hour_ago)

        # Verifica limites
        if recent_minute >= self.requests_per_minute:
            logger.warning(
                f"Rate limit EXCEEDED (minute): user={user_key}, "
                f"requests={recent_minute}/{self.requests_per_minute}"
            )
            return False

        if recent_hour >= self.requests_per_hour:
            logger.warning(
                f"Rate limit EXCEEDED (hour): user={user_key}, "
                f"requests={recent_hour}/{self.requests_per_hour}"
            )
            return False

        # Registra requisição
        requests.append(now)

        logger.debug(
            f"Rate limit OK: user={user_key}, "
            f"rpm={recent_minute}/{self.requests_per_minute}, "
            f"rph={recent_hour}/{self.requests_per_hour}"
        )

        return True

    def _cleanup_old_requests(self, user_key: str, now: datetime) -> None:
        """Remove requisições antigas (mais de 1 hora)"""
        one_hour_ago = now - timedelta(hours=1)

        requests = self.user_requests[user_key]

        # Remove requisições antigas do início da fila
        while requests and requests[0] < one_hour_ago:
            requests.popleft()

    def get_remaining_requests(self, user_id: str) -> Dict[str, int]:
        """
        Retorna número de requisições restantes

        Args:
            user_id: ID do usuário

        Returns:
            Dicionário com requisições restantes por minuto e hora
        """
        user_key = str(user_id)
        now = datetime.now()

        self._cleanup_old_requests(user_key, now)

        requests = self.user_requests[user_key]

        one_minute_ago = now - timedelta(minutes=1)
        one_hour_ago = now - timedelta(hours=1)

        recent_minute = sum(1 for ts in requests if ts > one_minute_ago)
        recent_hour = sum(1 for ts in requests if ts > one_hour_ago)

        return {
            "remaining_per_minute": max(0, self.requests_per_minute - recent_minute),
            "remaining_per_hour": max(0, self.requests_per_hour - recent_hour),
            "limit_per_minute": self.requests_per_minute,
            "limit_per_hour": self.requests_per_hour
        }

    def reset_user(self, user_id: str) -> None:
        """Reseta limites de um usuário"""
        user_key = str(user_id)
        if user_key in self.user_requests:
            del self.user_requests[user_key]
            logger.info(f"Rate limits reset for user: {user_key}")

    def get_stats(self) -> Dict[str, any]:
        """Retorna estatísticas do rate limiter"""
        return {
            "total_users": len(self.user_requests),
            "requests_per_minute": self.requests_per_minute,
            "requests_per_hour": self.requests_per_hour,
            "active_users": sum(1 for reqs in self.user_requests.values() if len(reqs) > 0)
        }


# Instância global
_global_rate_limiter = None


def get_rate_limiter() -> RateLimiter:
    """Obtém instância global do rate limiter"""
    global _global_rate_limiter
    if _global_rate_limiter is None:
        _global_rate_limiter = RateLimiter()
    return _global_rate_limiter
