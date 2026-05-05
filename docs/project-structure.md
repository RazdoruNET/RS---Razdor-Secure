# 📊 СТРУКТУРА ПРОЕКТА

```
RS---Razdor-Secure/
├── README.md                           # Основная документация проекта
├── USER_GUIDE.md                       # Руководство пользователя
├── FINAL_PROJECT_STRUCTURE.md          # Документация структуры проекта
├── rsecure_modules_integration_guide.md # Гайд по интеграции модулей
├── requirements.txt                     # Зависимости Python
├── .gitignore                         # Правила Git
├── assets/                            # Статические ресурсы
│   └── we_razdor_logo.png
├── bin/                               # Исполняемые файлы
│   ├── README.md
│   ├── rsecure
│   └── start_rsecure.sh
├── config/                            # Файлы конфигурации
│   ├── README.md
│   └── templates/
│       └── rsecure_config.template.json
├── docs/                              # Документация
│   ├── README.md
│   ├── rsecure-documentation.md       # Основная документация RSecure
│   ├── attack-methods.md              # Методы атак
│   ├── defense-methods.md             # Методы защиты
│   ├── importance-of-system.md        # Важность системы
│   ├── wifi-antipositioning-defense.md # WiFi антипозиционирование
│   ├── technology-roadmap.md         # Технологическая дорожная карта
│   ├── protection-layers.md           # Слои защиты
│   ├── quick-start.md                 # Быстрый старт
│   ├── project-structure.md          # Структура проекта
│   ├── setup/                         # Инструкции по установке
│   │   ├── BROWSER_SETUP.md
│   │   ├── FULL_SYSTEM_PROXY.md
│   │   ├── INSTALLATION.md
│   │   └── README_DPI_BYPASS.md
│   ├── organization/                  # Документация по организации
│   │   ├── PROJECT_STRUCTURE.md
│   │   ├── ARCHITECTURE_REORGANIZATION.md
│   │   ├── LOGS_STRUCTURE.md
│   │   ├── TEST_RESULTS_STRUCTURE.md
│   │   └── LOG_PATH_UPDATES_SUMMARY.md
│   ├── algorithms/                    # Алгоритмы
│   │   ├── behavioral-analysis.md
│   │   └── spectral-analysis.md
│   ├── analysis/                      # Анализ
│   │   ├── notifications.md
│   │   └── security-analytics.md
│   ├── api/                           # API документация
│   │   ├── python-api.md
│   │   └── rest-api.md
│   ├── architecture/                  # Архитектура
│   │   ├── overview.md
│   │   └── hybrid-neural-protection-system.md
│   ├── classified/                    # Секретные материалы
│   │   └── [40+ секретных файлов...]
│   ├── core-modules/                  # Основные модули
│   ├── defense/                       # Защита
│   ├── detection/                    # Обнаружение
│   ├── diy/                           # DIY руководства
│   ├── guides/                        # Гайды
│   ├── hardware/                      # Оборудование
│   ├── monitoring/                    # Мониторинг
│   ├── neural/                        # Нейросети
│   └── research/                      # Исследования
├── examples/                          # Примеры кода
│   ├── README.md
│   └── neural_encryptor_examples.py
├── models/                            # AI/ML модели (gitignored)
│   └── ai_models/
│       ├── rsecure-analyst.modelfile
│       ├── rsecure-scanner.modelfile
│       ├── rsecure-security.modelfile
│       └── rsecure-wifi-antipositioning.modelfile
├── rsecure/                           # Основной код приложения
│   ├── __init__.py
│   ├── rsecure_main.py
│   ├── config/                        # Конфигурация
│   │   ├── __init__.py
│   │   └── offline_threats.json
│   ├── core/                          # Ядро системы
│   │   ├── __init__.py
│   │   ├── neural_security_core.py
│   │   └── ollama_integration.py
│   ├── modules/                       # Модули
│   │   ├── __init__.py
│   │   ├── analysis/                  # Анализ
│   │   ├── defense/                   # Защита
│   │   └── detection/                 # Обнаружение
│   └── tests/                         # Тесты RSecure
│       ├── __init__.py
│       └── rsecure_test.py
├── scripts/                           # Все утилиты и скрипты запуска
│   ├── README.md
│   ├── startup/                       # Скрипты запуска и настройки
│   │   ├── README.md
│   │   ├── launch_dpi_bypass_proxy.py
│   │   ├── run_dpi_bypass_daemon.py
│   │   ├── setup_http_proxy.py
│   │   ├── setup_system_proxy.py
│   │   ├── start_dpi_bypass.sh
│   │   ├── start_rsecure.sh
│   │   ├── status_dpi_bypass.sh
│   │   └── stop_dpi_bypass.sh
│   ├── proxy_tools/                   # Скрипты прокси
│   │   ├── README.md
│   │   ├── proxy_setup_instructions.md
│   │   ├── enhanced_fin_storm_proxy.py
│   │   ├── fin_storm_proxy.py
│   │   └── [13+ других прокси скриптов...]
│   ├── dashboard_tools/               # Панели управления
│   │   ├── README.md
│   │   ├── advanced_dashboard.py
│   │   ├── optimized_dashboard.py
│   │   └── [5+ других дашбордов...]
│   ├── install_rsecure.py            # Скрипт установки
│   ├── advanced_pipelines.py          # Утилиты продвинутых конвейеров
│   ├── maximal_rsecure.py             # Максимальная конфигурация
│   ├── minimal_rsecure.py             # Минимальная конфигурация
│   ├── ollama_rsecure.py              # Ollama интеграция
│   ├── rsecure_enhanced.py            # Улучшенная версия
│   ├── simple_rsecure_runner.py       # Простой запуск
│   └── uninstall_rsecure.sh           # Скрипт удаления
├── src/                               # Исходный код
│   └── orpheus_satellite/             # Спутник Орфей
│       ├── config/
│       ├── core/
│       ├── neural/
│       ├── main.py
│       └── README.md
├── tests/                             # Все тесты организованы по типам
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_behavioral_analysis.py
│   ├── test_dpi_bypass.py
│   ├── integration/                   # Интеграционные тесты
│   │   ├── README.md
│   │   ├── test_10min_timeout.py
│   │   ├── test_dns_fix.py
│   │   ├── test_ollama_fix.py
│   │   ├── test_real_accessibility.py
│   │   ├── test_retaliation.py
│   │   ├── test_tor_core_integration.py
│   │   ├── test_tor_simple.py
│   │   └── [8+ других интеграционных тестов...]
│   ├── unit/                          # Модульные тесты
│   │   ├── README.md
│   │   ├── test_neural_encryptor.py
│   │   ├── test_rsecure.py
│   │   └── test_wifi_antipositioning.py
│   ├── performance/                   # Тесты производительности
│   │   └── README.md
│   └── [5+ других тестов...]
├── tools/                             # Инструменты разработки
│   └── README.md
├── templates/                         # Файлы шаблонов
│   └── dashboard.html
├── data/                              # Данные (gitignored)
├── logs/                              # Логи системы организованы по категориям (gitignored)
│   ├── application/                  # Логи уровня приложений
│   ├── security/                    # Логи безопасности
│   ├── dpi_bypass/                  # Логи обхода DPI
│   ├── system/                      # Системные логи
│   └── monitoring/                  # Логи мониторинга
├── test_results/                      # Результаты тестов и отчетов (gitignored)
│   ├── dpi_bypass/                  # Результаты тестов обхода DPI
│   └── summaries/                   # Краткие сводки
├── quarantine/                        # Карантин (gitignored)
├── rsecure_env/                       # Виртуальное окружение Python
├── tf_env/                           # Виртуальное окружение TensorFlow
├── mock_libs/                        # Библиотеки-заглушки для совместимости
│   ├── __init__.py
│   └── tensorflow.py
├── SUPER_DPI_COMBINER/               # Супер DPI комбинер
│   └── [50+ файлов...]
├── DPI_ANALYSIS_REPORT.md            # Отчет DPI анализа
├── DPI_TESTING_README.md             # README DPI тестирования
├── advanced_dpi_test.sh              # Скрипт DPI тестирования
├── port_manager.sh                   # Менеджер портов
└── test_dpi_modules.sh               # Тест DPI модулей
```

## 📂 **КЛЮЧЕВЫЕ ДИРЕКТОРИИ**

### `/rsecure/` - Основной код
- `rsecure_main.py` - Главный модуль запуска
- `core/` - Ядровые компоненты системы
- `modules/` - Функциональные модули
- `config/` - Конфигурационные файлы

### `/scripts/` - Скрипты и утилиты
- `startup/` - Скрипты запуска системы
- `proxy_tools/` - Инструменты прокси
- `dashboard_tools/` - Панели управления
- `*_rsecure.py` - Различные конфигурации запуска

### `/docs/` - Документация
- `setup/` - Инструкции по установке
- `organization/` - Организация проекта
- `classified/` - Секретные материалы
- `api/` - API документация

### `/tests/` - Тесты
- `integration/` - Интеграционные тесты
- `unit/` - Модульные тесты
- `performance/` - Тесты производительности

## 🔧 **ОРГАНИЗАЦИЯ ЛОГОВ**

```
logs/
├── application/     # Логи приложений
├── security/       # Логи безопасности
├── dpi_bypass/     # Логи DPI обхода
├── system/         # Системные логи
└── monitoring/     # Логи мониторинга
```

## 📊 **ОРГАНИЗАЦИЯ ТЕСТОВ**

```
tests/
├── integration/     # Интеграционные тесты
├── unit/           # Модульные тесты
├── performance/    # Тесты производительности
└── conftest.py     # Конфигурация pytest
```

## 🗂️ **ПРИНЦИПЫ ОРГАНИЗАЦИИ**

1. **Модульность** - Каждый компонент в своей директории
2. **Масштабируемость** - Легкое добавление новых модулей
3. **Тестируемость** - Тесты организованы по типам
4. **Документация** - Каждый модуль имеет README
5. **Конфигурация** - Централизованная система конфигурации
6. **Логирование** - Структурированные логи по категориям

---

**© 2026 WE RAZDOR. Все права защищены.**
