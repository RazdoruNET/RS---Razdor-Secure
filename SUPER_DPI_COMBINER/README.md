# 🚀 Super DPI Combiner

Универсальный адаптивный комбайн для обхода DPI с LLM интеграцией и многопоточной автогенерацией пайплайнов.

## 🎯 Возможности

### 🧠 Интеллектуальные функции:
- **Автогенерация пайплайнов** - динамическое создание техник обхода
- **LLM интеграция** - оптимизация через локальный Ollama
- **Адаптивное переключение** - автоматический выбор лучших техник
- **Многопоточность** - параллельная обработка запросов
- **Эволюция пайплайнов** - улучшение на основе результатов

### 🔧 Техники обхода:
- **SpoofDPI** - TCP сегментация, фейковые пакеты
- **Domain Fronting** - CDN маскировка, SNI спуфинг
- **Protocol Obfuscation** - HTTP фрагментация, TLS обфускация
- **Tor Integration** - мосты, darknet доступ
- **Omega Transport** - прокси цепочки, шифрование
- **Adaptive** - ML детекция, автопереключение

### 📊 Мониторинг:
- Веб-интерфейс на порту 8080
- Статистика производительности
- Журналирование всех операций
- Графики успешности

## 🚀 Быстрый запуск

### Установка зависимостей:
```bash
pip install aiohttp asyncio
```

### Запуск Ollama (если не установлен):
```bash
# macOS
brew install ollama
ollama pull llama2

# Linux
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama2
```

### Запуск комбайна:
```bash
cd SUPER_DPI_COMBINER
python3 main.py
```

### С опциями:
```bash
# Конкретный целевой URL
python3 main.py --target https://www.youtube.com

# Режим работы
python3 main.py --mode adaptive

# Количество потоков
python3 main.py --workers 30

# Без LLM
python3 main.py --no-llm

# Показать статус
python3 main.py --status
```

## 🌐 Управление

### Веб-интерфейс:
- **Статистика:** http://localhost:8080/stats
- **Управление:** http://localhost:8080/control
- **Тестирование:** http://localhost:8080/test

### API команды:
```bash
# Оптимизация под конкретный URL
curl -X POST http://localhost:8080/control \
  -H "Content-Type: application/json" \
  -d '{"command": "optimize", "target_url": "https://www.youtube.com"}'

# Переключение режима
curl -X POST http://localhost:8080/control \
  -H "Content-Type: application/json" \
  -d '{"command": "switch_mode", "mode": "performance"}'

# Перезагрузка пайплайнов
curl -X POST http://localhost:8080/control \
  -H "Content-Type: application/json" \
  -d '{"command": "reload_pipelines"}'
```

## 📁 Структура проекта

```
SUPER_DPI_COMBINER/
├── main.py                     # Главный комбайн
├── config/
│   └── settings.py              # Конфигурация
├── core/
│   ├── base_pipeline.py         # Базовый класс пайплайна
│   ├── pipeline_manager.py       # Менеджер пайплайнов
│   ├── pipeline_generator.py    # Автогенерация пайплайнов
│   ├── multi_thread_engine.py   # Многопоточный движок
│   └── llm_integration.py      # LLM интеграция
├── pipelines/
│   ├── spoof_dpi/             # SpoofDPI техники
│   ├── domain_fronting/         # Domain Fronting
│   ├── protocol_obfuscation/     # Обфускация протоколов
│   ├── tor_integration/         # Tor интеграция
│   ├── omega_transport/         # Omega транспорт
│   └── adaptive/              # Адаптивные техники
├── utils/
│   └── logger.py              # Логирование
└── logs/                      # Логи работы
```

## ⚙️ Конфигурация

### Основные настройки (config/settings.json):
```json
{
  "engine": {
    "max_workers": 20,
    "mode": "adaptive",
    "auto_optimization": true
  },
  "pipelines": {
    "auto_generation": true,
    "max_generations": 5,
    "templates_per_technique": 50
  },
  "llm": {
    "enabled": true,
    "url": "http://localhost:11434",
    "model": "llama2"
  },
  "targets": {
    "default_urls": [
      "https://www.youtube.com",
      "https://m.youtube.com"
    ]
  }
}
```

## 🎯 Режимы работы

### Auto Select:
- Сбалансированный выбор между скоростью и надежностью
- Автоматическое переключение при проблемах

### Performance:
- Приоритет скорости отклика
- Быстрые, но менее надежные техники

### Reliability:
- Приоритет успешности подключения
- Надежные, но медленные техники

### Adaptive:
- LLM-оптимизация в реальном времени
- Динамическая генерация новых техник

## 📊 Метрики

### Производительность пайплайнов:
- **Success Rate:** Успешность (%)
- **Response Time:** Среднее время отклика
- **Performance Score:** Общая оценка (0-1)
- **Active Connections:** Активные соединения

### Статистика движка:
- **Total Requests:** Всего запросов
- **Pipeline Switches:** Переключений пайплайнов
- **Best Pipeline:** Лучший пайплайн
- **Uptime:** Время работы

## 🧪 Тестирование

### Базовое тестирование:
```bash
# Тестирование конкретного URL
curl -X POST http://localhost:8080/test \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com"}'
```

### Нагрузочное тестирование:
```python
import asyncio
import aiohttp

async def load_test():
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(100):
            task = session.post(
                'http://localhost:8080/test',
                json={'url': 'https://www.youtube.com'}
            )
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        success_count = sum(1 for r in responses if r.status == 200)
        print(f"Успешно: {success_count}/100")

asyncio.run(load_test())
```

## 🛠️ Разработка

### Создание нового пайплайна:
```python
# pipelines/custom_technique/custom_pipeline.py
from core.base_pipeline import BasePipeline, BypassTechnique, BypassRequest, BypassResponse

class CustomPipeline(BasePipeline):
    def __init__(self):
        super().__init__("CustomPipeline", BypassTechnique.ADAPTIVE, priority=1)
    
    async def execute(self, request: BypassRequest) -> BypassResponse:
        # Реализация техники обхода
        return BypassResponse(
            success=True,
            status_code=200,
            response_time=0.1,
            technique_used=self.name
        )
    
    def initialize(self, config) -> bool:
        self.config = config
        return True
    
    def cleanup(self) -> bool:
        return True
```

### Интеграция с LLM:
```python
# Добавление новых промптов в llm_integration.py
self.prompts['custom_analysis'] = """
Анализируй ситуацию:
{context}

Предложи решение:
...
"""
```

## 🔍 Диагностика

### Проверка статуса:
```bash
python3 main.py --status
```

### Просмотр логов:
```bash
tail -f logs/combiner.log
```

### Мониторинг производительности:
```bash
# В реальном времени
curl http://localhost:8080/stats | jq .
```

## 🚨 Устранение проблем

### LLM недоступен:
```bash
# Проверяем Ollama
curl http://localhost:11434/api/tags

# Перезапускаем
ollama serve
```

### Пайплайны не загружаются:
```bash
# Проверяем структуру
ls -la pipelines/

# Проверяем логи
cat logs/combiner.log | grep ERROR
```

### Прокси не работает:
```bash
# Проверяем порты
lsof -i :8080

# Перезапускаем
python3 main.py
```

## 🎯 Конечная цель

**Super DPI Combiner** - самый мощный инструмент обхода DPI, который:
- ✅ Объединяет ВСЕ известные техники
- ✅ Автоматически генерирует новые методы
- ✅ Оптимизируется через LLM
- ✅ Работает в многопоточном режиме
- ✅ Адаптируется к любым блокировкам
- ✅ Предсказывает и предотвращает проблемы

**Это финальное решение для обхода любой цензуры!** 🚀🔓

---

**Готов к революции в обходе DPI!** 💪
