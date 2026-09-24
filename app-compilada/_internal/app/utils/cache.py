# ============================================================
#  app/utils/cache.py
#  Sistema simple de caché en memoria para bajo consumo de recursos
#  OPTIMIZADO: Reduce consultas a BD repetidas
# ============================================================
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import threading


class CacheEntry:
    """Entrada de caché con TTL (Time To Live)."""
    
    def __init__(self, data: Any, ttl_segundos: int = 300):
        self.data = data
        self.creado_en = datetime.now()
        self.ttl = ttl_segundos
    
    def es_valido(self) -> bool:
        """Verifica si la entrada aún es válida (no expiró)."""
        tiempo_transcurrido = (datetime.now() - self.creado_en).total_seconds()
        return tiempo_transcurrido < self.ttl
    
    def invalidar(self):
        """Marca la entrada como expirada."""
        self.creado_en = datetime.now() - timedelta(seconds=self.ttl + 1)


class SimpleCache:
    """
    Caché simple en memoria con TTL.
    Thread-safe para uso desde múltiples threads.
    """
    
    def __init__(self):
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
    
    def get(self, clave: str) -> Optional[Any]:
        """Obtiene un valor del caché si aún es válido."""
        with self._lock:
            if clave in self._cache:
                entrada = self._cache[clave]
                if entrada.es_valido():
                    return entrada.data
                else:
                    # Limpiar entrada expirada
                    del self._cache[clave]
            return None
    
    def set(self, clave: str, valor: Any, ttl_segundos: int = 300):
        """Guarda un valor en el caché con TTL."""
        with self._lock:
            self._cache[clave] = CacheEntry(valor, ttl_segundos)
    
    def invalidar(self, clave: str):
        """Invalida una entrada del caché."""
        with self._lock:
            if clave in self._cache:
                self._cache[clave].invalidar()
    
    def limpiar_todo(self):
        """Limpia todo el caché."""
        with self._lock:
            self._cache.clear()
    
    def limpiar_expirados(self):
        """Elimina todas las entradas expiradas."""
        with self._lock:
            claves_expiradas = [
                clave for clave, entrada in self._cache.items()
                if not entrada.es_valido()
            ]
            for clave in claves_expiradas:
                del self._cache[clave]
    
    def estadisticas(self) -> Dict[str, int]:
        """Retorna estadísticas del caché."""
        with self._lock:
            total = len(self._cache)
            validas = sum(1 for e in self._cache.values() if e.es_valido())
            expiradas = total - validas
            return {
                "total_entradas": total,
                "validas": validas,
                "expiradas": expiradas,
            }


# Instancia global del caché
_cache_global = SimpleCache()


def obtener_cache() -> SimpleCache:
    """Retorna la instancia global del caché."""
    return _cache_global
