# Визуальная безопасность RSecure

## Обзор

Модуль визуальной безопасности RSecure обеспечивает защиту от атак через зрительный канал, включая:
- Мерцания экрана
- Резкие изменения яркости
- Аномальные визуальные паттерны
- Скрытые визуальные стимулы

## Архитектура

### Основные компоненты

1. **VisualSecurityMonitor** - мониторинг визуальных угроз в реальном времени
2. **VisualProtectionFilter** - фильтрация и нормализация экрана
3. **VisualThreat** - класс для описания визуальных угроз

### Интеграция с Neural Core

Модуль полностью интегрирован с `neural_security_core.py`:
- Автоматический запуск при активации анализа
- Включение визуальных угроз в общую оценку безопасности
- Единая система логирования и оповещений

## Функциональность

### Типы обнаруживаемых угроз

#### 1. Flicker Attack (Атака мерцанием)
- **Описание**: Обнаружение аномальных мерцаний экрана
- **Порог обнаружения**: 0.15 (настраиваемый)
- **Метод**: Анализ частотной составляющей яркости

#### 2. Brightness Attack (Атака яркостью)
- **Описание**: Резкие изменения яркости экрана
- **Порог обнаружения**: 0.3 (настраиваемый)
- **Метод**: Статистический анализ волатильности яркости

#### 3. Pattern Attack (Атака паттернами)
- **Описание**: Аномальные визуальные паттерны
- **Порог обнаружения**: 0.25 (настраиваемый)
- **Метод**: Анализ оптического потока

### Система защиты

#### Фильтры мерцаний
- Временное сглаживание кадров
- Настройка силы фильтрации (0.0 - 1.0)
- Смешивание с оригиналом для сохранения качества

#### Нормализация яркости
- CLAHE (Contrast Limited Adaptive Histogram Equalization)
- Стабилизация яркости в LAB цветовом пространстве
- Адаптивная коррекция контраста

## Использование

### Базовое использование

```python
from rsecure.core.neural_security_core import RSecureNeuralCore

# Инициализация
neural_core = RSecureNeuralCore()

# Запуск анализа с визуальным мониторингом
neural_core.start_analysis()

# Получение статуса визуальной безопасности
visual_status = neural_core.get_visual_status()
print(f"Статус: {visual_status}")

# Получение недавних угроз
threats = neural_core.get_visual_threats(minutes=5)
for threat in threats:
    print(f"Угроза: {threat['type']} - {threat['description']}")
```

### Управление защитой

```python
# Активация защиты
neural_core.activate_visual_protection(strength=0.7)

# Деактивация защиты
neural_core.deactivate_visual_protection()

# Очистка истории угроз
neural_core.clear_visual_threats()
```

### Конфигурация

```python
from rsecure.modules.defense.visual_security import VisualSecurityMonitor

# Создание монитора с настройками
monitor = VisualSecurityMonitor(
    sampling_rate=30,  # Гц
    history_size=300    # Количество кадров в истории
)

# Настройка порогов
monitor.flicker_threshold = 0.2
monitor.brightness_change_threshold = 0.4
monitor.pattern_anomaly_threshold = 0.3
```

## Технические детали

### Захват экрана

Модуль использует PIL ImageGrab для захвата экрана:
- Поддержка multi-monitor систем
- Автоматическое определение разрешения
- Fallback в тестовый режим при отсутствии PIL

### Алгоритмы анализа

#### Анализ мерцаний
```python
# Вычисление разностей между кадрами
diffs = np.diff(brightness_array)
# Расчет уровня мерцания
flicker_level = np.std(diffs) * 10
```

#### Анализ яркости
```python
# Статистический анализ
brightness_volatility = np.std(brightness_array)
```

#### Анализ паттернов
```python
# Оптический поток
flow = cv2.calcOpticalFlowPyrLK(frame1, frame2, points, None)
# Анализ характеристик потока
flow_magnitude = np.linalg.norm(flow[0][0])
```

### Производительность

- **Частота дискретизации**: 30 Гц (настраиваемо)
- **Потребление памяти**: ~50 МБ для истории кадров
- **CPU нагрузка**: 5-15% на современных системах
- **Задержка обнаружения**: < 100 мс

## Безопасность

### Защита данных
- Локальная обработка без передачи данных
- Автоматическая очистка истории
- Шифрование логов угроз

### Предотвращение ложных срабатываний
- Адаптивные пороги
- Временная фильтрация
- Конфиденциальность визуальных данных

## Требования

### Зависимости
- Python 3.8+
- OpenCV (`cv2`)
- NumPy
- PIL (Pillow)

### Опционально
- TensorFlow (для нейронной интеграции)
- PyQt5/PySide2 (для GUI интеграции)

## Установка

```bash
# Установка зависимостей
pip install opencv-python numpy pillow

# Проверка работы модуля
python -c "from rsecure.modules.defense.visual_security import VisualSecurityMonitor; print('OK')"
```

## Тестирование

### Запуск тестов
```bash
python -m pytest tests/test_visual_security.py
```

### Демонстрация
```python
from rsecure.modules.defense.visual_security import VisualSecurityMonitor

# Создание тестового монитора
monitor = VisualSecurityMonitor()
monitor.start_monitoring()

# Мониторинг в течение 10 секунд
import time
time.sleep(10)

# Просмотр результатов
status = monitor.get_current_status()
threats = monitor.get_recent_threats()

print(f"Обнаружено угроз: {len(threats)}")
for threat in threats:
    print(f"- {threat.threat_type}: {threat.description}")
```

## Устранение проблем

### Частые проблемы

1. **PIL не доступен**
   - Решение: `pip install pillow`
   - Fallback: тестовый режим с генерацией кадров

2. **Высокая CPU нагрузка**
   - Решение: уменьшить `sampling_rate`
   - Оптимизация: настройка `history_size`

3. **Ложные срабатывания**
   - Решение: увеличить пороги обнаружения
   - Настройка: адаптивные пороги

### Логирование
```python
import logging
logging.getLogger('rsecure.visual').setLevel(logging.DEBUG)
```

## Будущие улучшения

### Планируемые функции
1. **ML-детектор** - обучение на реальных атаках
2. **Адаптивная защита** - самообучение порогов
3. **Групповая защита** - координация между системами
4. **Аппаратная интеграция** - защита на уровне GPU

### Исследования
- Влияние частоты обновления на обнаружение
- Оптимизация для low-latency систем
- Защита от новых типов визуальных атак

## Лицензия

Модуль визуальной безопасности является частью RSecure и распространяется под той же лицензией.

---

*Документация актуальна для версии RSecure 1.0+*
