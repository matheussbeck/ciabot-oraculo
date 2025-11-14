"""
Sistema de Cache em Memória
Melhora performance cacheando resultados de queries e dados
"""
import logging
from typing import Any, Optional, Dict
from datetime import datetime, timedelta
from collections import OrderedDict
import hashlib
import json

logger = logging.getLogger(__name__)


class CacheManager:
    """Gerenciador de cache em memória com TTL e LRU"""

    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """
        Inicializa cache manager

        Args:
            max_size: Tamanho máximo do cache (número de itens)
            default_ttl: TTL padrão em segundos (5 minutos)
        """
        self.cache = OrderedDict()
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.hits = 0
        self.misses = 0

        logger.info(f"CacheManager inicializado (max_size={max_size}, ttl={default_ttl}s)")

    def _generate_key(self, key_data: Any) -> str:
        """Gera chave única para cache"""
        if isinstance(key_data, str):
            key_str = key_data
        else:
            key_str = json.dumps(key_data, sort_keys=True, default=str)

        return hashlib.md5(key_str.encode()).hexdigest()

    def get(self, key: Any) -> Optional[Any]:
        """
        Obtém valor do cache

        Args:
            key: Chave (pode ser string, dict, etc)

        Returns:
            Valor cacheado ou None se não encontrado/expirado
        """
        cache_key = self._generate_key(key)

        if cache_key not in self.cache:
            self.misses += 1
            return None

        cached_item = self.cache[cache_key]

        # Verifica expiração
        if datetime.now() > cached_item['expires_at']:
            del self.cache[cache_key]
            self.misses += 1
            return None

        # Move para o final (LRU)
        self.cache.move_to_end(cache_key)

        self.hits += 1
        logger.debug(f"Cache HIT: {cache_key[:8]}...")
        return cached_item['value']

    def set(self, key: Any, value: Any, ttl: Optional[int] = None) -> None:
        """
        Define valor no cache

        Args:
            key: Chave
            value: Valor a cachear
            ttl: TTL em segundos (usa default se não especificado)
        """
        cache_key = self._generate_key(key)
        ttl = ttl or self.default_ttl

        # Remove item mais antigo se cache está cheio
        if len(self.cache) >= self.max_size and cache_key not in self.cache:
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
            logger.debug(f"Cache EVICT: {oldest_key[:8]}... (LRU)")

        self.cache[cache_key] = {
            'value': value,
            'expires_at': datetime.now() + timedelta(seconds=ttl),
            'created_at': datetime.now()
        }

        # Move para o final
        self.cache.move_to_end(cache_key)

        logger.debug(f"Cache SET: {cache_key[:8]}... (ttl={ttl}s)")

    def invalidate(self, key: Any) -> bool:
        """
        Invalida item do cache

        Args:
            key: Chave a invalidar

        Returns:
            True se item foi removido
        """
        cache_key = self._generate_key(key)

        if cache_key in self.cache:
            del self.cache[cache_key]
            logger.debug(f"Cache INVALIDATE: {cache_key[:8]}...")
            return True

        return False

    def clear(self) -> None:
        """Limpa todo o cache"""
        count = len(self.cache)
        self.cache.clear()
        logger.info(f"Cache cleared ({count} items)")

    def clear_expired(self) -> int:
        """
        Remove itens expirados

        Returns:
            Número de itens removidos
        """
        now = datetime.now()
        expired_keys = [
            key for key, item in self.cache.items()
            if now > item['expires_at']
        ]

        for key in expired_keys:
            del self.cache[key]

        if expired_keys:
            logger.info(f"Removed {len(expired_keys)} expired cache items")

        return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(hit_rate, 2),
            "total_requests": total_requests
        }

    def reset_stats(self) -> None:
        """Reseta estatísticas"""
        self.hits = 0
        self.misses = 0


# Instância global do cache
_global_cache = None


def get_cache() -> CacheManager:
    """Obtém instância global do cache"""
    global _global_cache
    if _global_cache is None:
        _global_cache = CacheManager()
    return _global_cache
