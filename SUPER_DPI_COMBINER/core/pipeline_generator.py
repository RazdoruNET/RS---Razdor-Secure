#!/usr/bin/env python3
"""
Многопоточная автогенерация пайплайнов
Динамическое создание и тестирование техник обхода DPI
"""

import asyncio
import threading
import time
import random
import hashlib
import json
from typing import Dict, List, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

from .base_pipeline import BasePipeline, BypassTechnique, BypassRequest, BypassResponse

# Импорт логгера с корректным путем
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class PipelineTemplate:
    """Шаблон для генерации пайплайнов"""
    name: str
    technique: BypassTechnique
    parameters: Dict[str, Any]
    success_rate: float = 0.0
    last_tested: float = 0.0

class PipelineGenerator:
    """Многопоточный генератор пайплайнов"""
    
    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers
        self.templates: List[PipelineTemplate] = []
        self.generated_pipelines: Dict[str, BasePipeline] = {}
        self.test_results: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()
        
        # База техник для генерации
        self.technique_patterns = {
            BypassTechnique.SPOOF_DPI: {
                'tcp_segmentation': [1, 2, 4, 8],
                'fake_ttl': [1, 2, 8, 64],
                'fragment_size': [1, 2, 4, 8, 16],
                'packet_delay': [0.001, 0.01, 0.1, 0.5],
                'duplicate_packets': [1, 2, 3, 5]
            },
            BypassTechnique.DOMAIN_FRONTING: {
                'cdn_domains': ['cloudflare.com', 'fastly.com', 'akamai.com', 'cloudfront.net'],
                'host_overrides': ['www.google.com', 'www.youtube.com', 'www.facebook.com'],
                'sni_spoofing': [True, False],
                'http_methods': ['GET', 'POST', 'HEAD', 'OPTIONS']
            },
            BypassTechnique.PROTOCOL_OBFUSCATION: {
                'http_fragmentation': [True, False],
                'chunk_size': [64, 128, 256, 512, 1024],
                'header_obfuscation': [True, False],
                'random_padding': [True, False],
                'tls_version': ['1.2', '1.3']
            },
            BypassTechnique.TOR_INTEGRATION: {
                'bridge_types': ['obfs4', 'meiko', 'snowflake', 'obfs5'],
                'transport_protocols': ['tcp', 'udp'],
                'pluggable_transports': ['obfs4', 'obfs3', 'fte']
            },
            BypassTechnique.OMEGA_TRANSPORT: {
                'proxy_chains': [1, 2, 3, 5],
                'encryption_methods': ['aes256', 'chacha20', 'blowfish'],
                'compression': ['gzip', 'lz4', 'none'],
                'hopping_interval': [30, 60, 120, 300]
            }
        }
        
        logger.info(f"Инициализация PipelineGenerator с {max_workers} потоками")
    
    def generate_templates(self, count_per_technique: int = 50) -> List[PipelineTemplate]:
        """
        Генерация шаблонов пайплайнов
        
        Args:
            count_per_technique: Количество шаблонов на каждую технику
            
        Returns:
            List[PipelineTemplate]: Список сгенерированных шаблонов
        """
        logger.info(f"Генерация {count_per_technique} шаблонов на технику...")
        
        templates = []
        
        for technique, patterns in self.technique_patterns.items():
            for i in range(count_per_technique):
                # Генерируем случайные параметры
                parameters = {}
                for param_name, values in patterns.items():
                    if isinstance(values, list):
                        parameters[param_name] = random.choice(values)
                    else:
                        parameters[param_name] = values
                
                # Создаем уникальное имя
                param_hash = hashlib.md5(
                    json.dumps(parameters, sort_keys=True).encode()
                ).hexdigest()[:8]
                
                template = PipelineTemplate(
                    name=f"AutoGen_{technique.value}_{param_hash}",
                    technique=technique,
                    parameters=parameters
                )
                
                templates.append(template)
        
        logger.info(f"Сгенерировано {len(templates)} шаблонов")
        return templates
    
    def create_pipeline_from_template(self, template: PipelineTemplate) -> BasePipeline:
        """
        Создание пайплайна из шаблона
        
        Args:
            template: Шаблон пайплайна
            
        Returns:
            BasePipeline: Созданный пайплайн
        """
        try:
            if template.technique == BypassTechnique.SPOOF_DPI:
                return self._create_spoof_dpi_pipeline(template)
            elif template.technique == BypassTechnique.DOMAIN_FRONTING:
                return self._create_domain_fronting_pipeline(template)
            elif template.technique == BypassTechnique.PROTOCOL_OBFUSCATION:
                return self._create_protocol_obfuscation_pipeline(template)
            elif template.technique == BypassTechnique.TOR_INTEGRATION:
                return self._create_tor_integration_pipeline(template)
            elif template.technique == BypassTechnique.OMEGA_TRANSPORT:
                return self._create_omega_transport_pipeline(template)
            else:
                return self._create_generic_pipeline(template)
                
        except Exception as e:
            logger.error(f"Ошибка создания пайплайна из шаблона {template.name}: {e}")
            return None
    
    def _create_spoof_dpi_pipeline(self, template: PipelineTemplate) -> BasePipeline:
        """Создание SpoofDPI пайплайна"""
        
        class AutoGenSpoofDPI(BasePipeline):
            def __init__(self):
                super().__init__(template.name, template.technique, priority=1)
                self.params = template.parameters
                
            async def execute(self, request: BypassRequest) -> BypassResponse:
                # Реализация SpoofDPI с параметрами
                start_time = time.time()
                
                try:
                    # TCP сегментация
                    segment_size = self.params.get('tcp_segmentation', 1)
                    
                    # Фейковые пакеты
                    fake_ttl = self.params.get('fake_ttl', 1)
                    
                    # Размер фрагментов
                    fragment_size = self.params.get('fragment_size', 1)
                    
                    # Имитация обхода
                    await asyncio.sleep(0.01)  # Имитация задержки
                    
                    response_time = time.time() - start_time
                    
                    # Вероятность успеха зависит от параметров
                    success_probability = 0.3 + (segment_size * 0.1) + (fake_ttl * 0.05)
                    success = random.random() < success_probability
                    
                    return BypassResponse(
                        success=success,
                        status_code=200 if success else 403,
                        response_time=response_time,
                        technique_used=self.name
                    )
                    
                except Exception as e:
                    return BypassResponse(
                        success=False,
                        error=str(e),
                        response_time=time.time() - start_time
                    )
            
            def initialize(self, config: Dict[str, Any]) -> bool:
                self.config = config
                return True
            
            def cleanup(self) -> bool:
                return True
        
        return AutoGenSpoofDPI()
    
    def _create_domain_fronting_pipeline(self, template: PipelineTemplate) -> BasePipeline:
        """Создание Domain Fronting пайплайна"""
        
        class AutoGenDomainFronting(BasePipeline):
            def __init__(self):
                super().__init__(template.name, template.technique, priority=2)
                self.params = template.parameters
                
            async def execute(self, request: BypassRequest) -> BypassResponse:
                start_time = time.time()
                
                try:
                    # CDN домен
                    cdn_domain = self.params.get('cdn_domains', 'cloudflare.com')
                    
                    # Override хоста
                    host_override = self.params.get('host_overrides', 'www.google.com')
                    
                    # SNI спуфинг
                    sni_spoof = self.params.get('sni_spoofing', True)
                    
                    # Имитация запроса
                    await asyncio.sleep(0.02)
                    
                    response_time = time.time() - start_time
                    
                    # Вероятность успеха
                    success_probability = 0.4 + (0.1 if sni_spoof else 0)
                    success = random.random() < success_probability
                    
                    return BypassResponse(
                        success=success,
                        status_code=200 if success else 403,
                        response_time=response_time,
                        technique_used=self.name
                    )
                    
                except Exception as e:
                    return BypassResponse(
                        success=False,
                        error=str(e),
                        response_time=time.time() - start_time
                    )
            
            def initialize(self, config: Dict[str, Any]) -> bool:
                self.config = config
                return True
            
            def cleanup(self) -> bool:
                return True
        
        return AutoGenDomainFronting()
    
    def _create_protocol_obfuscation_pipeline(self, template: PipelineTemplate) -> BasePipeline:
        """Создание Protocol Obfuscation пайплайна"""
        
        class AutoGenProtocolObfuscation(BasePipeline):
            def __init__(self):
                super().__init__(template.name, template.technique, priority=3)
                self.params = template.parameters
                
            async def execute(self, request: BypassRequest) -> BypassResponse:
                start_time = time.time()
                
                try:
                    # HTTP фрагментация
                    http_frag = self.params.get('http_fragmentation', True)
                    
                    # Размер чанков
                    chunk_size = self.params.get('chunk_size', 256)
                    
                    # Обфускация заголовков
                    header_obf = self.params.get('header_obfuscation', True)
                    
                    await asyncio.sleep(0.015)
                    
                    response_time = time.time() - start_time
                    
                    success_probability = 0.35 + (0.1 if http_frag else 0)
                    success = random.random() < success_probability
                    
                    return BypassResponse(
                        success=success,
                        status_code=200 if success else 403,
                        response_time=response_time,
                        technique_used=self.name
                    )
                    
                except Exception as e:
                    return BypassResponse(
                        success=False,
                        error=str(e),
                        response_time=time.time() - start_time
                    )
            
            def initialize(self, config: Dict[str, Any]) -> bool:
                self.config = config
                return True
            
            def cleanup(self) -> bool:
                return True
        
        return AutoGenProtocolObfuscation()
    
    def _create_tor_integration_pipeline(self, template: PipelineTemplate) -> BasePipeline:
        """Создание Tor Integration пайплайна"""
        
        class AutoGenTorIntegration(BasePipeline):
            def __init__(self):
                super().__init__(template.name, template.technique, priority=4)
                self.params = template.parameters
                
            async def execute(self, request: BypassRequest) -> BypassResponse:
                start_time = time.time()
                
                try:
                    # Тип моста
                    bridge_type = self.params.get('bridge_types', 'obfs4')
                    
                    # Протокол транспорта
                    transport_proto = self.params.get('transport_protocols', 'tcp')
                    
                    await asyncio.sleep(0.05)  # Tor задержка
                    
                    response_time = time.time() - start_time
                    
                    # Tor обычно медленнее но надежнее
                    success_probability = 0.6
                    success = random.random() < success_probability
                    
                    return BypassResponse(
                        success=success,
                        status_code=200 if success else 503,
                        response_time=response_time,
                        technique_used=self.name
                    )
                    
                except Exception as e:
                    return BypassResponse(
                        success=False,
                        error=str(e),
                        response_time=time.time() - start_time
                    )
            
            def initialize(self, config: Dict[str, Any]) -> bool:
                self.config = config
                return True
            
            def cleanup(self) -> bool:
                return True
        
        return AutoGenTorIntegration()
    
    def _create_omega_transport_pipeline(self, template: PipelineTemplate) -> BasePipeline:
        """Создание Omega Transport пайплайна"""
        
        class AutoGenOmegaTransport(BasePipeline):
            def __init__(self):
                super().__init__(template.name, template.technique, priority=5)
                self.params = template.parameters
                
            async def execute(self, request: BypassRequest) -> BypassResponse:
                start_time = time.time()
                
                try:
                    # Цепочки прокси
                    proxy_chains = self.params.get('proxy_chains', 1)
                    
                    # Метод шифрования
                    encryption = self.params.get('encryption_methods', 'aes256')
                    
                    await asyncio.sleep(0.03 * proxy_chains)  # Задержка от цепочек
                    
                    response_time = time.time() - start_time
                    
                    success_probability = 0.45 + (proxy_chains * 0.05)
                    success = random.random() < success_probability
                    
                    return BypassResponse(
                        success=success,
                        status_code=200 if success else 403,
                        response_time=response_time,
                        technique_used=self.name
                    )
                    
                except Exception as e:
                    return BypassResponse(
                        success=False,
                        error=str(e),
                        response_time=time.time() - start_time
                    )
            
            def initialize(self, config: Dict[str, Any]) -> bool:
                self.config = config
                return True
            
            def cleanup(self) -> bool:
                return True
        
        return AutoGenOmegaTransport()
    
    def _create_generic_pipeline(self, template: PipelineTemplate) -> BasePipeline:
        """Создание универсального пайплайна"""
        
        class AutoGenGeneric(BasePipeline):
            def __init__(self):
                super().__init__(template.name, template.technique, priority=6)
                self.params = template.parameters
                
            async def execute(self, request: BypassRequest) -> BypassResponse:
                start_time = time.time()
                
                try:
                    await asyncio.sleep(0.02)
                    
                    response_time = time.time() - start_time
                    success = random.random() < 0.3  # Базовая вероятность
                    
                    return BypassResponse(
                        success=success,
                        status_code=200 if success else 403,
                        response_time=response_time,
                        technique_used=self.name
                    )
                    
                except Exception as e:
                    return BypassResponse(
                        success=False,
                        error=str(e),
                        response_time=time.time() - start_time
                    )
            
            def initialize(self, config: Dict[str, Any]) -> bool:
                self.config = config
                return True
            
            def cleanup(self) -> bool:
                return True
        
        return AutoGenGeneric()
    
    async def test_pipeline_batch(self, templates: List[PipelineTemplate], test_url: str = "https://www.youtube.com") -> Dict[str, Dict[str, Any]]:
        """
        Многопоточное тестирование пайплайнов
        
        Args:
            templates: Список шаблонов для тестирования
            test_url: URL для тестирования
            
        Returns:
            Dict: Результаты тестирования
        """
        logger.info(f"Многопоточное тестирование {len(templates)} пайплайнов...")
        
        results = {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Создаем задачи для каждого пайплайна
            future_to_template = {}
            
            for template in templates:
                # Создаем пайплайн
                pipeline = self.create_pipeline_from_template(template)
                if pipeline is None:
                    continue
                
                self.generated_pipelines[template.name] = pipeline
                
                # Создаем тестовый запрос
                test_request = BypassRequest(
                    host="www.youtube.com",
                    port=443,
                    method="HEAD",
                    timeout=10.0
                )
                
                # Отправляем на выполнение
                future = executor.submit(
                    asyncio.run, 
                    pipeline.execute(test_request)
                )
                future_to_template[future] = template
            
            # Обрабатываем результаты
            for future in as_completed(future_to_template):
                template = future_to_template[future]
                
                try:
                    response = future.result(timeout=15.0)
                    
                    # Обновляем метрики пайплайна
                    pipeline = self.generated_pipelines[template.name]
                    pipeline.update_metrics(response.success, response.response_time)
                    
                    # Сохраняем результат
                    results[template.name] = {
                        'template': template,
                        'response': response,
                        'performance_score': pipeline.get_performance_score(),
                        'test_time': time.time()
                    }
                    
                    if response.success:
                        logger.info(f"✅ {template.name}: Успех ({response.response_time:.3f}s)")
                    else:
                        logger.warning(f"❌ {template.name}: Провал ({response.error})")
                        
                except Exception as e:
                    logger.error(f"💥 {template.name}: Ошибка {e}")
                    results[template.name] = {
                        'template': template,
                        'response': None,
                        'error': str(e),
                        'performance_score': 0.0
                    }
        
        return results
    
    def get_best_pipelines(self, results: Dict[str, Dict[str, Any]], count: int = 5) -> List[Dict[str, Any]]:
        """
        Получение лучших пайплайнов по результатам тестирования
        
        Args:
            results: Результаты тестирования
            count: Количество лучших пайплайнов
            
        Returns:
            List: Список лучших пайплайнов
        """
        # Фильтруем только успешные
        successful_results = [
            (name, result) for name, result in results.items()
            if result.get('response') and result['response'].success
        ]
        
        # Сортируем по performance score
        successful_results.sort(
            key=lambda x: x[1]['performance_score'],
            reverse=True
        )
        
        return successful_results[:count]
    
    def evolve_pipelines(self, results: Dict[str, Dict[str, Any]], generation: int = 1) -> List[PipelineTemplate]:
        """
        Эволюция пайплайнов на основе лучших результатов
        
        Args:
            results: Результаты тестирования
            generation: Номер поколения
            
        Returns:
            List[PipelineTemplate]: Новые шаблоны пайплайнов
        """
        logger.info(f"Эволюция пайплайнов, поколение {generation}")
        
        # Получаем лучшие пайплайны
        best_pipelines = self.get_best_pipelines(results, count=10)
        
        if not best_pipelines:
            logger.warning("Нет успешных пайплайнов для эволюции")
            return []
        
        new_templates = []
        
        for name, result in best_pipelines:
            template = result['template']
            
            # Мутация параметров
            for param_name, param_value in template.parameters.items():
                if isinstance(param_value, (int, float)):
                    # Добавляем шум
                    mutation = param_value * random.uniform(0.8, 1.2)
                    
                    # Ограничиваем диапазон
                    if param_name in self.technique_patterns.get(template.technique, {}):
                        possible_values = self.technique_patterns[template.technique][param_name]
                        if isinstance(possible_values, list):
                            # Находим ближайшее значение
                            mutation = min(possible_values, key=lambda x: abs(x - mutation))
                    
                    # Создаем новый шаблон
                    new_params = template.parameters.copy()
                    new_params[param_name] = mutation
                    
                    param_hash = hashlib.md5(
                        json.dumps(new_params, sort_keys=True).encode()
                    ).hexdigest()[:8]
                    
                    new_template = PipelineTemplate(
                        name=f"Evolved_G{generation}_{template.technique.value}_{param_hash}",
                        technique=template.technique,
                        parameters=new_params
                    )
                    
                    new_templates.append(new_template)
        
        logger.info(f"Создано {len(new_templates)} эволюционных шаблонов")
        return new_templates
    
    async def auto_optimize(self, target_url: str = "https://www.youtube.com", generations: int = 5) -> List[Dict[str, Any]]:
        """
        Автоматическая оптимизация пайплайнов
        
        Args:
            target_url: Целевой URL
            generations: Количество поколений эволюции
            
        Returns:
            List: Лучшие пайплайны
        """
        logger.info(f"Начало автоматической оптимизации для {target_url}")
        
        best_overall = []
        
        # Начальная генерация
        current_templates = self.generate_templates(count_per_technique=20)
        
        for generation in range(generations):
            logger.info(f"Поколение {generation + 1}/{generations}")
            
            # Тестируем текущие шаблоны
            results = await self.test_pipeline_batch(current_templates, target_url)
            
            # Получаем лучшие
            best_in_generation = self.get_best_pipelines(results, count=3)
            best_overall.extend(best_in_generation)
            
            # Эволюция для следующего поколения
            if generation < generations - 1:
                current_templates = self.evolve_pipelines(results, generation + 1)
            
            # Небольшая пауза
            await asyncio.sleep(1)
        
        # Финальная сортировка всех лучших
        best_overall.sort(key=lambda x: x[1]['performance_score'], reverse=True)
        
        logger.info(f"Оптимизация завершена. Найдено {len(best_overall)} лучших пайплайнов")
        
        return best_overall[:10]  # Возвращаем топ-10
