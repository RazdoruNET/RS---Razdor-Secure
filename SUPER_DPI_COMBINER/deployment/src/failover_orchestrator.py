#!/usr/bin/env python3
"""
Smart Failover Orchestrator - Адаптивный оркестратор пайплайнов с упреждающим пастру (Pre-emptive Passthrough)
"""

import asyncio
import copy
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

# Import pipeline modules
from pipeline_manager import PipelineManager

class SessionStatus(Enum):
    """Статус сессии"""
    ACTIVE = "active"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"

@dataclass
class SessionContext:
    """Контекст сессии"""
    session_id: str
    domain: str
    start_time: float
    bytes_transferred: int = 0
    status: SessionStatus = SessionStatus.ACTIVE
    pipeline_config: Dict[str, Any] = None
    error_type: Optional[str] = None

class DomainStrategy:
    def __init__(self, domain: str, port: int):
        self.domain = domain.strip().lower()
        self.port = port
        self.status = "CLEAN"
        self.current_pipeline = []
        self.failures_count = 0
        self.last_drop_reason = "N/A"
        self.mutation_history = []
        self.last_mutation_timestamp = time.time()
        # 🔥 НОВЫЙ ДЕСКРИПТОР ДЛЯ СДВИГА ПАРАМЕТРОВ ФРАГМЕНТАЦИИ
        self.chunk_size_modifier = 0

    def add_failure_event(self, failed_pipeline: list, error_reason: str, mutated_to_pipeline: list):
        self.mutation_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "failed_pipeline": list(failed_pipeline),
            "error_reason": str(error_reason),
            "mutated_to_pipeline": list(mutated_to_pipeline)
        })

class SmartFailoverOrchestrator:
    def __init__(self, default_pipeline: list = None, inspector=None, strategy_ttl: int = 120):
        self.lock = asyncio.Lock()
        self.domain_cache = {}
        self.default_pipeline = default_pipeline if default_pipeline else ["fake_packet", "sni_modifier", "jitter_fragmentation"]
        self.inspector = inspector
        self.strategy_ttl = strategy_ttl

    def _make_key(self, domain: str, port: int) -> str:
        return f"{str(domain).strip().lower()}:{int(port)}"

    def _normalize_domain(self, domain: str) -> str:
        if not domain:
            return "unknown_init"
        return str(domain).strip().lower()

    def _filter_pipeline_by_port(self, pipeline: list, port: int) -> list:
        """
        Исключает TLS-модули, если порт не равен 443 (HTTPS)
        """
        if port == 443:
            return list(pipeline)
        
        # Для HTTP (порт 80) и других протоколов оставляем только безопасную фрагментацию
        tls_modules = {"fake_packet", "sni_modifier"}
        filtered = [m for m in pipeline if m not in tls_modules]
        return filtered

    async def get_or_create_strategy(self, domain: str, port: int) -> tuple:
        """
        Возвращает кортеж: (pipeline_list, chunk_size_modifier)
        """
        norm_domain = self._normalize_domain(domain)
        if norm_domain in ("0.0.0.0", "127.0.0.1", "localhost", "unknown_init"):
            return [], 0
            
        cache_key = self._make_key(norm_domain, port)
        
        async with self.lock:
            if cache_key not in self.domain_cache:
                strategy = DomainStrategy(norm_domain, port)
                strategy.current_pipeline = []  # Pre-emptive Passthrough
                self.domain_cache[cache_key] = strategy
                print(f"[ORCHESTRATOR] Домен {norm_domain}:{port} инициализирован в режиме Pre-emptive Passthrough: []")
                return [], 0
            
            strategy = self.domain_cache[cache_key]
            current_time = time.time()
            
            if strategy.status in ("PASSTHROUGH", "UNSTABLE") and (current_time - strategy.last_mutation_timestamp) > self.strategy_ttl:
                strategy.status = "CLEAN"
                strategy.failures_count = 0
                strategy.current_pipeline = []
                strategy.chunk_size_modifier = 0
                strategy.last_mutation_timestamp = current_time
                return [], 0
            
            filtered_pipeline = self._filter_pipeline_by_port(strategy.current_pipeline, port)
            return filtered_pipeline, strategy.chunk_size_modifier

    def _calculate_next_mutation(self, failed_pipeline: list, strategy) -> list:
        """
        failed_pipeline: то, что упало в текущей сессии
        strategy: ссылка на изменяемый объект DomainStrategy домена
        """
        pipeline = list(failed_pipeline)
        
        # 🔥 Шаг 0: Если упал чистый запрос (длина конвейера == 0) — накладываем полный пайплайн
        if not pipeline and strategy.failures_count == 0:
            print(f"[ORCHESTRATOR] Чистый запрос для {strategy.domain} заблокирован. Активация боевого пайплайна.")
            return list(self.default_pipeline)
        
        # Шаг 1: Если упал полный стек (HTTPS) — отсекаем fake_packet
        if "fake_packet" in pipeline:
            return [m for m in pipeline if m != "fake_packet"]
            
        # Шаг 2: Если фейка уже нет, но есть sni_modifier — отсекаем его, оставляя чистый jitter
        elif "sni_modifier" in pipeline:
            return ["jitter_fragmentation"]
            
        # Шаг 3: 🔥 НОВАЯ ЛОГИКА — Если упал чистый jitter_fragmentation (HTTP или HTTPS)
        elif "jitter_fragmentation" in pipeline:
            # Если это первое падение чистого джиттера — увеличиваем размер чанков на +100 байт
            if strategy.chunk_size_modifier == 0:
                strategy.chunk_size_modifier = 100
                print(f"[ORCHESTRATOR CALIBRATION] Jitter сбоит на {strategy.domain}. Увеличиваем MTU на +100B.")
                return ["jitter_fragmentation"]  # Оставляем модуль в пайплайне
                
            # Если это второе падение чистого джиттера — увеличиваем размер чанков еще на +200 байт
            elif strategy.chunk_size_modifier == 100:
                strategy.chunk_size_modifier = 300
                print(f"[ORCHESTRATOR CALIBRATION] Jitter все еще сбоит на {strategy.domain}. Увеличиваем MTU на +300B.")
                return ["jitter_fragmentation"]  # Даем последний шанс модулю
                
            # Все лимиты калибровки джиттера исчерпаны — падаем в пасстру
            else:
                return []
            
        # Защитный fallback
        return []

    async def report_failure(self, domain: str, reason: str, current_pipeline: list, port: int):
        norm_domain = self._normalize_domain(domain)
        if norm_domain in ("0.0.0.0", "127.0.0.1", "localhost", "unknown_init"):
            return

        cache_key = self._make_key(norm_domain, port)

        async with self.lock:
            if cache_key not in self.domain_cache:
                self.domain_cache[cache_key] = DomainStrategy(norm_domain, port)
                self.domain_cache[cache_key].current_pipeline = list(current_pipeline)
            
            strategy = self.domain_cache[cache_key]
            current_time = time.time()
            
            # Вычисляем следующую мутацию, передавая объект strategy для управления chunk_size_modifier
            next_pipeline_raw = self._calculate_next_mutation(current_pipeline, strategy)
            
            # Принудительно фильтруем выданную мутацию по порту (для порта 80 вырежет TLS модули)
            next_pipeline = self._filter_pipeline_by_port(next_pipeline_raw, port)
            
            print(f"[ORCHESTRATOR DEBUG] next_pipeline_raw={next_pipeline_raw}, next_pipeline={next_pipeline}")
            
            # Запись в историю
            strategy.add_failure_event(
                failed_pipeline=list(current_pipeline),
                error_reason=reason,
                mutated_to_pipeline=list(next_pipeline)
            )
            
            strategy.failures_count += 1
            strategy.last_drop_reason = str(reason)
            strategy.last_mutation_timestamp = current_time
            strategy.current_pipeline = list(next_pipeline)
            
            if strategy.failures_count == 1 and next_pipeline:
                strategy.status = "MUTATING"
                print(f"[ORCHESTRATOR] Чистый запрос для {norm_domain} заблокирован. Активация боевого пайплайна: {strategy.current_pipeline}")
            elif not next_pipeline and strategy.failures_count >= 4:
                strategy.status = "PASSTHROUGH"
            else:
                strategy.status = "UNSTABLE"

        if self.inspector:
            await self.inspector.export_matrix_report(orchestrator=self)

    async def get_snapshot(self) -> dict:
        async with self.lock:
            snapshot = {
                "export_timestamp": datetime.utcnow().timestamp(),
                "total_domains": len(self.domain_cache),
                "domains": {}
            }
            for domain, strategy in self.domain_cache.items():
                snapshot["domains"][domain] = {
                    "status": strategy.status,
                    "successful_pipeline": strategy.current_pipeline,
                    "failures_count": strategy.failures_count,
                    "last_drop_reason": strategy.last_drop_reason,
                    "history_of_failures": copy.deepcopy(strategy.mutation_history),
                    "chunk_size_modifier": strategy.chunk_size_modifier  # 🔥 НОВОЕ ПОЛЕ
                }
            return snapshot

    async def create_session(self, domain: str) -> SessionContext:
        """
        Создание новой сессии с оптимальной стратегией
        
        Args:
            domain: Целевой домен
            
        Returns:
            Контекст сессии с выбранной стратегией
        """
        norm_domain = self._normalize_domain(domain)
        
        # Блокировка рекурсивных адресов
        if norm_domain in ("0.0.0.0", "127.0.0.1", "localhost", "unknown_init"):
            return SessionContext(
                session_id=f"{norm_domain}_{int(time.time())}",
                domain=norm_domain,
                start_time=time.time(),
                pipeline_config=self._create_passthrough_config()
            )
        
        # Начинаем анализ соединения через DPI инспектор
        if self.inspector:
            connection_id = self.inspector.start_connection_analysis(norm_domain)
        else:
            connection_id = None
        
        async with self.lock:
            # Проверяем, есть ли кэшированная стратегия для домена
            if norm_domain in self.domain_cache:
                strategy = self.domain_cache[norm_domain]
                
                # Создаем конфигурацию из текущей стратегии
                pipeline_config = self._strategy_to_config(strategy)
            else:
                # Создаем новую стратегию на основе базового пайплайна
                strategy = DomainStrategy(norm_domain, 443)  # Default port for create_session
                strategy.current_pipeline = []  # Pre-emptive Passthrough
                self.domain_cache[norm_domain] = strategy
                
                pipeline_config = self._create_passthrough_config()
        
        # Создаем контекст сессии
        session = SessionContext(
            session_id=f"{norm_domain}_{int(time.time())}",
            domain=norm_domain,
            start_time=time.time(),
            pipeline_config=pipeline_config
        )
        
        return session

    async def report_success(self, session: SessionContext):
        """
        Отчет об успешной сессии
        
        Args:
            session: Контекст успешной сессии
        """
        session.status = SessionStatus.SUCCESS
        
        # Завершаем анализ соединения в DPI инспекторе
        if self.inspector:
            analysis = self.inspector.finalize_connection_analysis(session.session_id)
        else:
            analysis = None
        
        async with self.lock:
            if session.domain not in self.domain_cache:
                # Создаем новую стратегию на основе успешной сессии
                strategy = DomainStrategy(session.domain)
                strategy.current_pipeline = list(session.pipeline_config.get('pipeline_modules', []))
                self.domain_cache[session.domain] = strategy
            
            strategy = self.domain_cache[session.domain]
            strategy.success_count = strategy.success_count + 1 if hasattr(strategy, 'success_count') else 1
            strategy.last_success = time.time()
            
            print(f"[ORCHESTRATOR] Domain {session.domain} marked as STABLE with pipeline {strategy.current_pipeline}")
            
            # Экспортируем матрицу
            if self.inspector:
                await self.inspector.export_matrix_report(self)

    def _strategy_to_config(self, strategy) -> dict:
        """Преобразование стратегии в конфигурацию пайплайна"""
        return {
            'pipeline_modules': strategy.current_pipeline,
            'module_configs': {}
        }

    def _get_base_config(self) -> Dict[str, Any]:
        """Получить базовую конфигурацию пайплайна"""
        return {
            'pipeline_modules': self.default_pipeline,
            'module_configs': {}
        }
    
    def _create_passthrough_config(self) -> Dict[str, Any]:
        """Создание конфигурации для passthrough режима"""
        return {
            'pipeline_modules': [],
            'module_configs': {}
        }
