#!/usr/bin/env python3
"""
Smart Failover Orchestrator - Адаптивный оркестратор пайплайнов с динамической мутацией и TTL авто-сбросом
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
    def __init__(self, domain: str):
        self.domain = domain.strip().lower()
        self.status = "MUTATING"
        self.current_pipeline = []
        self.failures_count = 0
        self.last_drop_reason = "N/A"
        self.mutation_history = []
        self.last_mutation_timestamp = time.time()  # Временной маркер для TTL

    def add_failure_event(self, failed_pipeline: list, error_reason: str, mutated_to_pipeline: list):
        self.mutation_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "failed_pipeline": list(failed_pipeline),
            "error_reason": str(error_reason),
            "mutated_to_pipeline": list(mutated_to_pipeline)
        })

class SmartFailoverOrchestrator:
    def __init__(self, default_pipeline: list = None, inspector=None, strategy_ttl: int = 60):
        self.lock = asyncio.Lock()
        self.domain_cache = {}
        self.default_pipeline = default_pipeline if default_pipeline else ["fake_packet", "sni_modifier", "jitter_fragmentation"]
        self.inspector = inspector
        self.strategy_ttl = strategy_ttl  # Время жизни заклинившей стратегии в секундах

    def _normalize_domain(self, domain: str) -> str:
        if not domain:
            return "unknown_init"
        return str(domain).strip().lower()

    async def get_or_create_strategy(self, domain: str) -> list:
        norm_domain = self._normalize_domain(domain)
        if norm_domain in ("0.0.0.0", "127.0.0.1", "localhost", "unknown_init"):
            return []
            
        async with self.lock:
            if norm_domain not in self.domain_cache:
                strategy = DomainStrategy(norm_domain)
                strategy.current_pipeline = list(self.default_pipeline)
                self.domain_cache[norm_domain] = strategy
                print(f"[ORCHESTRATOR] Инициализирован базовый геном для {norm_domain}: {strategy.current_pipeline}")
                return list(strategy.current_pipeline)
            
            strategy = self.domain_cache[norm_domain]
            
            # 🔥 АНТИ-ЗАЦИКЛИВАНИЕ: Если стратегия мертва (passthrough) и истек TTL — сбрасываем в дефолт
            current_time = time.time()
            if strategy.status == "PASSTHROUGH" and (current_time - strategy.last_mutation_timestamp) > self.strategy_ttl:
                print(f"[ORCHESTRATOR TTL EXPIRED] Стратегия для {norm_domain} устарела. Сброс конвейера до базового уровня.")
                strategy.status = "MUTATING"
                strategy.failures_count = 0
                strategy.current_pipeline = list(self.default_pipeline)
                strategy.last_mutation_timestamp = current_time
            
            return list(strategy.current_pipeline)

    def _calculate_next_mutation(self, current_pipeline: list, failures_count: int) -> list:
        """
        Строгий пошаговый каскад деградации на основе анализа текущих модулей
        """
        pipeline = list(current_pipeline)
        
        # Шаг 1: Если в упавшем пакете был fake_packet — вырезаем только его
        if "fake_packet" in pipeline:
            return [m for m in pipeline if m != "fake_packet"]
            
        # Шаг 2: Если fake_packet уже нет, но sni_modifier остался — убираем его
        if "sni_modifier" in pipeline:
            return [m for m in pipeline if m != "sni_modifier"]
            
        # Шаг 3: Если остался только jitter_fragmentation, но таймауты продолжаются — падение в passthrough []
        return []

    async def report_failure(self, domain: str, reason: str, current_pipeline: list):
        norm_domain = self._normalize_domain(domain)
        if norm_domain in ("0.0.0.0", "127.0.0.1", "localhost", "unknown_init"):
            return

        async with self.lock:
            if norm_domain not in self.domain_cache:
                self.domain_cache[norm_domain] = DomainStrategy(norm_domain)
                self.domain_cache[norm_domain].current_pipeline = list(current_pipeline)
            
            strategy = self.domain_cache[norm_domain]
            current_time = time.time()
            
            # Логический предохранитель: если на вход по ошибке пришел пустой пайплайн, а мы не в passthrough — восстанавливаем контекст
            actual_failed_pipeline = list(current_pipeline) if current_pipeline else list(self.default_pipeline)
            
            # Расчет следующего шага
            next_pipeline = self._calculate_next_mutation(actual_failed_pipeline, strategy.failures_count)
            
            # Фиксация в хронологию
            strategy.add_failure_event(
                failed_pipeline=actual_failed_pipeline,
                error_reason=reason,
                mutated_to_pipeline=list(next_pipeline)
            )
            
            # Обновление дескрипторов состояния ядра
            strategy.failures_count += 1
            strategy.last_drop_reason = str(reason)
            strategy.last_mutation_timestamp = current_time
            strategy.current_pipeline = list(next_pipeline)
            
            # Если дошли до конца цепочки или превысили лимит — фиксируем PASSTHROUGH
            if not next_pipeline or strategy.failures_count >= 4:
                strategy.status = "PASSTHROUGH"
                strategy.current_pipeline = []
                print(f"[ORCHESTRATOR] Домен {norm_domain} переведен в режим Passthrough (Black Hole). Ожидание TTL.")
            else:
                strategy.status = "UNSTABLE"
                print(f"[ORCHESTRATOR] Домен {norm_domain} мутировал до: {strategy.current_pipeline}")

        # Выгрузка дампа на диск
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
                    "history_of_failures": copy.deepcopy(strategy.mutation_history)
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
                strategy = DomainStrategy(norm_domain)
                strategy.current_pipeline = list(self.default_pipeline)
                self.domain_cache[norm_domain] = strategy
                
                pipeline_config = self._get_base_config()
        
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
