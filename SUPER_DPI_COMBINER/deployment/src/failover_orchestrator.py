#!/usr/bin/env python3
"""
Smart Failover Orchestrator - Адаптивная система мутации пайплайнов
"""

import os
import asyncio
import time
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

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

@dataclass
class DomainStrategy:
    """Стратегия для домена"""
    pipeline_modules: List[str]
    module_configs: Dict[str, Dict[str, Any]]
    success_count: int = 0
    failure_count: int = 0
    last_success: Optional[float] = None
    last_failure: Optional[float] = None
    is_passthrough: bool = False
    passthrough_until: Optional[float] = None

class SmartFailoverOrchestrator:
    """Оркестратор для адаптивной мутации пайплайнов"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Конфигурация из переменных окружения
        self.enabled = os.environ.get('SMART_FAILOVER_ENABLED', 'true').lower() == 'true'
        self.max_mutation_attempts = int(os.environ.get('MAX_MUTATION_ATTEMPTS', '4'))
        self.selective_threshold = int(os.environ.get('SELECTIVE_THRESHOLD', '3000'))
        self.passthrough_duration = 300  # 5 минут в секундах
        
        # Кэш успешных стратегий по доменам
        self.domain_strategies: Dict[str, DomainStrategy] = {}
        self.strategy_lock = asyncio.Lock()
        
        # Активные сессии
        self.active_sessions: Dict[str, SessionContext] = {}
        self.session_lock = asyncio.Lock()
        
        # Базовая конфигурация для мутаций
        self.base_pipeline = os.environ.get('PIPELINE_ORDER', 'fake_packet,jitter_fragmentation').split(',')
        
        self.logger.info(f"SmartFailoverOrchestrator initialized: enabled={self.enabled}, max_attempts={self.max_mutation_attempts}")
    
    async def create_session(self, domain: str) -> SessionContext:
        """
        Создание новой сессии с оптимальной стратегией
        
        Args:
            domain: Целевой домен
            
        Returns:
            Контекст сессии с выбранной стратегией
        """
        if not self.enabled:
            # Если оркестратор отключен, используем базовую конфигурацию
            return SessionContext(
                session_id=f"{domain}_{int(time.time())}",
                domain=domain,
                start_time=time.time(),
                pipeline_config=self._get_base_config()
            )
        
        async with self.strategy_lock:
            # Проверяем, есть ли кэшированная стратегия для домена
            if domain in self.domain_strategies:
                strategy = self.domain_strategies[domain]
                
                # Проверяем, не истекло ли время passthrough
                if strategy.is_passthrough and strategy.passthrough_until and time.time() < strategy.passthrough_until:
                    self.logger.info(f"[ORCHESTRATOR] Domain {domain} still in passthrough mode")
                    return SessionContext(
                        session_id=f"{domain}_{int(time.time())}",
                        domain=domain,
                        start_time=time.time(),
                        pipeline_config=self._create_passthrough_config()
                    )
                
                # Если есть успешная стратегия, используем ее
                if strategy.success_count > 0 and strategy.failure_count == 0:
                    self.logger.info(f"[ORCHESTRATOR] Using cached successful strategy for {domain}")
                    return SessionContext(
                        session_id=f"{domain}_{int(time.time())}",
                        domain=domain,
                        start_time=time.time(),
                        pipeline_config=self._strategy_to_config(strategy)
                    )
            
            # Генерируем новую стратегию
            strategy = await self._generate_strategy_for_domain(domain)
            return SessionContext(
                session_id=f"{domain}_{int(time.time())}",
                domain=domain,
                start_time=time.time(),
                pipeline_config=self._strategy_to_config(strategy)
            )
    
    async def report_success(self, session: SessionContext):
        """
        Отчет об успешной сессии
        
        Args:
            session: Контекст успешной сессии
        """
        if not self.enabled:
            return
        
        session.status = SessionStatus.SUCCESS
        
        async with self.strategy_lock:
            if session.domain not in self.domain_strategies:
                # Создаем новую стратегию на основе успешной сессии
                strategy = self._config_to_strategy(session.domain, session.pipeline_config)
                self.domain_strategies[session.domain] = strategy
            
            strategy = self.domain_strategies[session.domain]
            strategy.success_count += 1
            strategy.last_success = time.time()
            
            # Если домен был в passthrough, возвращаем его в нормальный режим
            if strategy.is_passthrough:
                strategy.is_passthrough = False
                strategy.passthrough_until = None
                self.logger.info(f"[ORCHESTRATOR] Domain {domain} restored from passthrough mode")
            
            self.logger.info(f"[ORCHESTRATOR] Domain {session.domain} marked as STABLE with pipeline {strategy.pipeline_modules}")
    
    async def report_failure(self, domain: str, pipeline_config: Dict[str, Any], error_type: str):
        """
        Отчет о неудачной сессии
        
        Args:
            domain: Домен, на котором произошел сбой
            pipeline_config: Использовавшаяся конфигурация
            error_type: Тип ошибки (timeout, connection_reset, etc.)
        """
        if not self.enabled:
            return
        
        self.logger.info(f"[ORCHESTRATOR] Handshake failed for {domain}. Error: {error_type}. Mutating pipeline strategy...")
        
        async with self.strategy_lock:
            if domain not in self.domain_strategies:
                strategy = self._config_to_strategy(domain, pipeline_config)
                self.domain_strategies[domain] = strategy
            else:
                strategy = self.domain_strategies[domain]
            
            strategy.failure_count += 1
            strategy.last_failure = time.time()
            
            # Генерируем новую стратегию
            new_strategy = await self._mutate_strategy(domain, strategy.failure_count)
            self.domain_strategies[domain] = new_strategy
            
            modules_str = ", ".join(new_strategy.pipeline_modules)
            self.logger.info(f"[ORCHESTRATOR] New strategy generated for {domain}: [{modules_str}]")
    
    async def _generate_strategy_for_domain(self, domain: str) -> DomainStrategy:
        """
        Генерация начальной стратегии для домена
        
        Args:
            domain: Целевой домен
            
        Returns:
            Новая стратегия
        """
        # Для начала используем базовую конфигурацию
        return self._config_to_strategy(domain, self._get_base_config())
    
    async def _mutate_strategy(self, domain: str, failure_count: int) -> DomainStrategy:
        """
        Мутация стратегии на основе количества неудач
        
        Args:
            domain: Целевой домен
            failure_count: Количество неудач
            
        Returns:
            Мутированная стратегия
        """
        if failure_count >= self.max_mutation_attempts:
            # Fallback: переводим в passthrough режим
            self.logger.warning(f"[ORCHESTRATOR] Max mutations reached for {domain}. Switching to passthrough for 5 minutes")
            return DomainStrategy(
                pipeline_modules=[],
                module_configs={},
                is_passthrough=True,
                passthrough_until=time.time() + self.passthrough_duration
            )
        
        # Алгоритм мутации
        if failure_count == 1:
            # Сбой 1: Отключить FakePacketModule
            modules = [m for m in self.base_pipeline if m != 'fake_packet']
            self.logger.info(f"[ORCHESTRATOR] Mutation 1 for {domain}: Removing fake_packet module")
        
        elif failure_count == 2:
            # Сбой 2: Увеличить размеры чанков для ускорения
            modules = [m for m in self.base_pipeline if m != 'fake_packet']
            self.logger.info(f"[ORCHESTRATOR] Mutation 2 for {domain}: Increasing chunk sizes")
        
        elif failure_count == 3:
            # Сбой 3: Включить SniCaseModifierModule + базовый Jitter
            modules = ['sni_modifier', 'jitter_fragmentation']
            self.logger.info(f"[ORCHESTRATOR] Mutation 3 for {domain}: Adding SNI case modifier")
        
        else:
            # Fallback
            modules = []
        
        # Генерируем конфигурацию для мутированных модулей
        module_configs = self._generate_mutation_configs(modules, failure_count)
        
        return DomainStrategy(
            pipeline_modules=modules,
            module_configs=module_configs
        )
    
    def _generate_mutation_configs(self, modules: List[str], failure_count: int) -> Dict[str, Dict[str, Any]]:
        """
        Генерация конфигурации для мутированных модулей
        
        Args:
            modules: Список модулей
            failure_count: Количество неудач
            
        Returns:
            Конфигурация модулей
        """
        configs = {}
        
        for module in modules:
            if module == 'jitter_fragmentation':
                if failure_count == 2:
                    # Увеличиваем размеры чанков
                    configs[module] = {
                        'MIN_CHUNK_SIZE': str(int(os.environ.get('MIN_CHUNK_SIZE', '40')) + 50),
                        'MAX_CHUNK_SIZE': str(int(os.environ.get('MAX_CHUNK_SIZE', '150')) + 50),
                        'MIN_CHUNK_DELAY': os.environ.get('MIN_CHUNK_DELAY', '0.001'),
                        'MAX_CHUNK_DELAY': os.environ.get('MAX_CHUNK_DELAY', '0.003'),
                        'SELECTIVE_THRESHOLD': os.environ.get('SELECTIVE_THRESHOLD', '3000'),
                    }
                else:
                    # Базовая конфигурация
                    configs[module] = {
                        'MIN_CHUNK_SIZE': os.environ.get('MIN_CHUNK_SIZE', '40'),
                        'MAX_CHUNK_SIZE': os.environ.get('MAX_CHUNK_SIZE', '150'),
                        'MIN_CHUNK_DELAY': os.environ.get('MIN_CHUNK_DELAY', '0.001'),
                        'MAX_CHUNK_DELAY': os.environ.get('MAX_CHUNK_DELAY', '0.003'),
                        'SELECTIVE_THRESHOLD': os.environ.get('SELECTIVE_THRESHOLD', '3000'),
                    }
            
            elif module == 'fake_packet':
                configs[module] = {
                    'FAKE_PACKET_BYTES': os.environ.get('FAKE_PACKET_BYTES', '0x160301000500000000'),
                }
            
            elif module == 'sni_modifier':
                configs[module] = {
                    'CASE_MODIFY_PROBABILITY': os.environ.get('CASE_MODIFY_PROBABILITY', '0.7'),
                }
        
        return configs
    
    def _get_base_config(self) -> Dict[str, Any]:
        """Получение базовой конфигурации"""
        return {
            'pipeline_modules': self.base_pipeline,
            'module_configs': self._generate_mutation_configs(self.base_pipeline, 0)
        }
    
    def _create_passthrough_config(self) -> Dict[str, Any]:
        """Создание конфигурации для passthrough режима"""
        return {
            'pipeline_modules': [],
            'module_configs': {}
        }
    
    def _strategy_to_config(self, strategy: DomainStrategy) -> Dict[str, Any]:
        """Преобразование стратегии в конфигурацию"""
        return {
            'pipeline_modules': strategy.pipeline_modules,
            'module_configs': strategy.module_configs
        }
    
    def _config_to_strategy(self, domain: str, config: Dict[str, Any]) -> DomainStrategy:
        """Преобразование конфигурации в стратегию"""
        return DomainStrategy(
            pipeline_modules=config.get('pipeline_modules', []),
            module_configs=config.get('module_configs', {})
        )
    
    async def get_domain_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Получение статистики по доменам
        
        Returns:
            Словарь со статистикой
        """
        async with self.strategy_lock:
            stats = {}
            for domain, strategy in self.domain_strategies.items():
                stats[domain] = {
                    'success_count': strategy.success_count,
                    'failure_count': strategy.failure_count,
                    'last_success': strategy.last_success,
                    'last_failure': strategy.last_failure,
                    'is_passthrough': strategy.is_passthrough,
                    'pipeline_modules': strategy.pipeline_modules
                }
            return stats
