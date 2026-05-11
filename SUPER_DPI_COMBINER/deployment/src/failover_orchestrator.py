#!/usr/bin/env python3
"""
Smart Failover Orchestrator - Адаптивная система мутации пайплайнов
"""

import os
import asyncio
import time
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from dpi_sandbox_inspector import DpiSandboxInspector, ConnectionDropReason

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
    mutation_history: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_failure_event(self, pipeline_before_crash: List[str], error_reason: str, mutated_to: List[str]):
        """Регистрирует подробности неудачной попытки"""
        self.mutation_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "failed_pipeline": pipeline_before_crash,
            "error_reason": error_reason,
            "mutated_to_pipeline": mutated_to
        })

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
        
        # DPI Sandbox Inspector
        self.dpi_inspector = DpiSandboxInspector()
        
        # Базовая конфигурация для мутаций
        self.base_pipeline = os.environ.get('PIPELINE_ORDER', 'fake_packet,jitter_fragmentation').split(',')
        
        self.logger.info(f"SmartFailoverOrchestrator initialized: enabled={self.enabled}, max_attempts={self.max_mutation_attempts}")
        self.logger.info(f"SmartFailoverOrchestrator: DPI Sandbox Inspector enabled={self.dpi_inspector.enabled}")
        
        # Pre-seed стратегии из внешнего URL будет вызван позже
    
    async def create_session(self, domain: str) -> SessionContext:
        """
        Создание новой сессии с оптимальной стратегией
        
        Args:
            domain: Целевой домен
            
        Returns:
            Контекст сессии с выбранной стратегией
        """
        # 🔥 КРИТИЧЕСКИЙ ФИЛЬТР: Если на вход пришел битый IP, принудительно возвращаем passthrough (прямой коннект)
        if domain in ("0.0.0.0", "127.0.0.1", "localhost", "unknown_init"):
            self.logger.warning(f"[ORCHESTRATOR] Blocked recursive/invalid address: {domain}. Returning passthrough.")
            return SessionContext(
                session_id=f"{domain}_{int(time.time())}",
                domain=domain,
                start_time=time.time(),
                pipeline_config=self._create_passthrough_config()
            )
        
        if not self.enabled:
            # Если оркестратор отключен, используем базовую конфигурацию
            return SessionContext(
                session_id=f"{domain}_{int(time.time())}",
                domain=domain,
                start_time=time.time(),
                pipeline_config=self._get_base_config()
            )
        
        # Начинаем анализ соединения через DPI инспектор
        connection_id = self.dpi_inspector.start_connection_analysis(domain)
        
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
        
        # Завершаем анализ соединения в DPI инспекторе
        analysis = self.dpi_inspector.finalize_connection_analysis(session.session_id)
        
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
                self.logger.info(f"[ORCHESTRATOR] Domain {session.domain} restored from passthrough mode")
            
            self.logger.info(f"[ORCHESTRATOR] Domain {session.domain} marked as STABLE with pipeline {strategy.pipeline_modules}")
        
        # Экспортируем матрицу стратегий
        await self.dpi_inspector.export_matrix_report(self)
    
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
            # 🔥 КРИТИЧЕСКИЙ ПАТЧ: Проверяем, есть ли уже домен в кэше
            if domain not in self.domain_strategies:
                # Создаем запись С НУЛЯ только если домен встретился ВПЕРВЫЕ
                strategy = self._config_to_strategy(domain, pipeline_config)
                self.domain_strategies[domain] = strategy
                self.logger.info(f"[ORCHESTRATOR] Инициализирована новая запись для домена: {domain}")
            else:
                strategy = self.domain_strategies[domain]
                self.logger.info(f"[ORCHESTRATOR] Домен {domain} найден в кэше. Аккумулируем историю.")
            
            # Фиксируем текущий упавший пайплайн ПЕРЕД тем, как мутировать его
            current_pipeline = strategy.pipeline_modules.copy()
            
            # Вычисляем следующую мутацию (следующий шаг подбора)
            new_strategy = await self._mutate_strategy_with_dpi_analysis(domain, strategy.failure_count, error_type)
            new_pipeline = new_strategy.pipeline_modules
            
            # Дописываем событие в историю (метод делает .append(), ничего не заменяя!)
            strategy.add_failure_event(current_pipeline, error_type, new_pipeline)
            
            # Обновляем текущие параметры домена для следующей попытки
            strategy.failure_count += 1
            strategy.last_failure = time.time()
            strategy.pipeline_modules = new_pipeline
            
            modules_str = ", ".join(new_pipeline)
            self.logger.info(f"[ORCHESTRATOR] New strategy generated for {domain}: [{modules_str}]")
        
        # Экспортируем матрицу стратегий
        await self.dpi_inspector.export_matrix_report(self)
    
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
    
    async def _mutate_strategy_with_dpi_analysis(self, domain: str, failure_count: int, error_type: str) -> DomainStrategy:
        """
        Мутация стратегии с учетом DPI анализа (теперь использует эволюционный алгоритм)
        
        Args:
            domain: Целевой домен
            failure_count: Количество неудач
            error_type: Тип ошибки
            
        Returns:
            Мутированная стратегия
        """
        # Используем единый эволюционный алгоритм вместо DPI-специфичной логики
        return await self._mutate_strategy(domain, failure_count)
    
    def generate_next_mutation(self, strategy: DomainStrategy, domain: str) -> tuple[list, dict]:
        """
        Эволюционный алгоритм градации мутаций с пошаговым снижением агрессивности
        
        Args:
            strategy: Текущая стратегия домена
            domain: Целевой домен
            
        Returns:
            Кортеж (next_pipeline, force_large_chunks_flag)
        """
        base_pipeline = list(self.base_pipeline)
        fail_count = strategy.failure_count
        force_large_chunks = False
        
        # Шаг 1: Первый сбой — Убираем только FakePacketModule
        if fail_count == 1:
            next_pipeline = [m for m in base_pipeline if m != "fake_packet"]
            if not next_pipeline:
                next_pipeline = base_pipeline
            self.logger.info(f"[ORCHESTRATOR] Mutation 1 for {domain}: Removing fake_packet -> {next_pipeline}")
            return next_pipeline, force_large_chunks

        # Шаг 2: Второй сбой — Убираем SniCaseModifierModule (оставляем только чистый джиттер)
        elif fail_count == 2:
            next_pipeline = [m for m in base_pipeline if m == "jitter_fragmentation"]
            if not next_pipeline:
                next_pipeline = base_pipeline
            self.logger.info(f"[ORCHESTRATOR] Mutation 2 for {domain}: Removing sni_modifier -> {next_pipeline}")
            return next_pipeline, force_large_chunks

        # Шаг 3: Третий сбой — Меняем параметры джиттера (увеличиваем чанки)
        elif fail_count == 3:
            next_pipeline = ["jitter_fragmentation"]
            force_large_chunks = True
            self.logger.info(f"[ORCHESTRATOR] Mutation 3 for {domain}: Force large chunks for jitter -> {next_pipeline}")
            return next_pipeline, force_large_chunks

        # Шаг 4: Четвертый сбой и далее — Все методы исчерпаны, уходим в безопасный Passthrough
        else:
            print(f"[ORCHESTRATOR CRITICAL] Обход DPI невозможен для {domain}. Fallback в прямой доступ.")
            self.logger.warning(f"[ORCHESTRATOR] Mutation {fail_count} for {domain}: Passthrough mode")
            return [], force_large_chunks

    async def _mutate_strategy(self, domain: str, failure_count: int) -> DomainStrategy:
        """
        Мутация стратегии на основе количества неудач (использует эволюционный алгоритм)
        
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
        
        # Получаем текущую стратегию для вызова эволюционного алгоритма
        async with self.strategy_lock:
            if domain in self.domain_strategies:
                strategy = self.domain_strategies[domain]
            else:
                strategy = self._config_to_strategy(domain, self._get_base_config())
                self.domain_strategies[domain] = strategy
        
        # Используем эволюционный алгоритм
        next_pipeline, force_large_chunks = self.generate_next_mutation(strategy, domain)
        
        # Генерируем конфигурацию для мутированных модулей
        if force_large_chunks:
            # Принудительно увеличиваем размеры чанков для ускорения
            module_configs = {
                'jitter_fragmentation': {
                    'MIN_CHUNK_SIZE': str(int(os.environ.get('MIN_CHUNK_SIZE', '40')) + 100),
                    'MAX_CHUNK_SIZE': str(int(os.environ.get('MAX_CHUNK_SIZE', '150')) + 100),
                    'MIN_CHUNK_DELAY': os.environ.get('MIN_CHUNK_DELAY', '0.001'),
                    'MAX_CHUNK_DELAY': os.environ.get('MAX_CHUNK_DELAY', '0.003'),
                    'SELECTIVE_THRESHOLD': os.environ.get('SELECTIVE_THRESHOLD', '3000'),
                }
            }
        else:
            module_configs = self._generate_mutation_configs(next_pipeline, failure_count)
        
        return DomainStrategy(
            pipeline_modules=next_pipeline,
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
            
            elif module == 'tls_chameleon':
                configs[module] = {
                    'SNI_SPLITTING_ENABLED': 'true',
                    'MIN_PACKET_SIZE': os.environ.get('MIN_PACKET_SIZE', '100'),
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
    
    async def _preseed_strategies(self):
        """
        Импорт стратегий из внешнего URL при старте
        """
        preseed_url = os.environ.get('STRATEGY_PRESEED_URL')
        if not preseed_url:
            self.logger.info("[ORCHESTRATOR] No preseed URL configured")
            return
        
        try:
            self.logger.info(f"[ORCHESTRATOR] Importing strategies from: {preseed_url}")
            
            # Создаем HTTP клиент
            import aiohttp
            timeout = aiohttp.ClientTimeout(total=30)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(preseed_url) as response:
                    if response.status != 200:
                        self.logger.error(f"[ORCHESTRATOR] Failed to fetch preseed: HTTP {response.status}")
                        return
                    
                    # Читаем JSON
                    data = await response.json()
                    
                    # Импортируем стратегии
                    imported_count = 0
                    for domain, strategy_data in data.items():
                        if isinstance(strategy_data, dict):
                            # Создаем стратегию
                            modules = strategy_data.get('pipeline_modules', [])
                            configs = strategy_data.get('module_configs', {})
                            
                            strategy = self._config_to_strategy(domain, {
                                'pipeline_modules': modules,
                                'module_configs': configs
                            })
                            
                            # Устанавливаем статус если указан
                            if strategy_data.get('status') == 'STABLE':
                                strategy.success_count = 1
                                strategy.failure_count = 0
                            
                            self.domain_strategies[domain] = strategy
                            imported_count += 1
                    
                    self.logger.info(f"[ORCHESTRATOR] Pre-seeded {imported_count} stable domain strategies from external URL")
                    
                    # Экспортируем матрицу
                    await self.dpi_inspector.export_matrix_report(self)
        
        except ImportError:
            self.logger.warning("[ORCHESTRATOR] aiohttp not available, skipping preseed")
        except Exception as e:
            self.logger.error(f"[ORCHESTRATOR] Preseed import failed: {e}")
    
    def _config_to_strategy(self, domain: str, config: Dict[str, Any]) -> DomainStrategy:
        """Преобразование конфигурации в стратегию"""
        return DomainStrategy(
            pipeline_modules=config.get('pipeline_modules', []),
            module_configs=config.get('module_configs', {})
        )
    
    async def get_snapshot(self) -> dict:
        """
        Получить потокобезопасный слепок состояния кэша доменов для Web GUI
        
        Returns:
            Словарь с текущим состоянием стратегий
        """
        async with self.strategy_lock:
            return {
                "domains": {
                    domain: {
                        "status": self._get_domain_status(strategy),
                        "active_pipeline": strategy.pipeline_modules,
                        "failures": strategy.failure_count,
                        "last_drop_reason": self._get_last_drop_reason(domain),
                        "mutation_history": strategy.mutation_history
                    }
                    for domain, strategy in self.domain_strategies.items()
                }
            }
    
    def _get_domain_status(self, strategy) -> str:
        """Определить статус домена"""
        if strategy.is_passthrough:
            return 'PASSTHROUGH'
        elif strategy.success_count > 0 and strategy.failure_count == 0:
            return 'STABLE'
        elif strategy.failure_count > 0:
            return 'UNSTABLE'
        else:
            return 'MUTATING'
    
    def _get_last_drop_reason(self, domain: str) -> str:
        """Получить последнюю причину сброса от DPI инспектора"""
        for analysis in self.dpi_inspector.completed_connections.values():
            if analysis.domain == domain and analysis.drop_reason.value != 'unknown':
                return analysis.drop_reason.value
        return 'N/A'
    
    async def get_domain_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Получить статистику по доменам
        
        Returns:
            Словарь со статистикой
        """
        async with self.strategy_lock:
            stats = {}
            for domain, strategy in self.domain_strategies.items():
                # Определяем статус домена
                if strategy.is_passthrough:
                    status = 'PASSTHROUGH'
                elif strategy.success_count > 0 and strategy.failure_count == 0:
                    status = 'STABLE'
                elif strategy.failure_count > 0:
                    status = 'UNSTABLE'
                else:
                    status = 'MUTATING'
                
                # Получаем последнюю причину сброса от DPI инспектора
                last_drop_reason = None
                for analysis in self.dpi_inspector.completed_connections.values():
                    if analysis.domain == domain and analysis.drop_reason.value != 'unknown':
                        last_drop_reason = analysis.drop_reason.value
                        break
                
                stats[domain] = {
                    'status': status,
                    'success_count': strategy.success_count,
                    'failure_count': strategy.failure_count,
                    'successful_connections': strategy.success_count,
                    'failed_connections': strategy.failure_count,
                    'last_success': strategy.last_success,
                    'last_failure': strategy.last_failure,
                    'is_passthrough': strategy.is_passthrough,
                    'pipeline_modules': strategy.pipeline_modules,
                    'module_configs': strategy.module_configs,
                    'drop_reason': last_drop_reason
                }
            return stats
