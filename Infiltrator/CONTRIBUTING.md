# 🤝 Вклад в проект INFILTRATOR

Спасибо за интерес к внесению вклада в INFILTRATOR! Этот документ поможет вам начать работу над проектом.

## 📋 Содержание

- [Как внести вклад](#как-внести-вклад)
- [Начало работы](#начало-работы)
- [Процесс разработки](#процесс-разработки)
- [Стандарты кода](#стандарты-кода)
- [Тестирование](#тестирование)
- [Документация](#документация)
- [Сообщество](#сообщество)

---

## 🎯 Как внести вклад

### 🐛 Сообщить о проблеме
- Используйте [GitHub Issues](https://github.com/razdor/RS---Razdor-Secure/issues)
- Проверьте, что проблема еще не сообщена
- Используйте шаблон для bug reports
- Предоставьте минимальный воспроизводимый пример

### 💡 Предложить функцию
- Откройте [GitHub Discussion](https://github.com/razdor/RS---Razdor-Secure/discussions)
- Опишите проблему, которую решает функция
- Объясните, почему это важно для проекта
- Предложите возможные решения

### 📝 Улучшить документацию
- Исправьте опечатки и грамматические ошибки
- Добавьте недостающие примеры
- Улучшите объяснения
- Переведите на другие языки

### 🔧 Внести код
- Решите существующую проблему
- Добавьте новую функцию
- Улучшите производительность
- Оптимизируйте код

---

## 🚀 Начало работы

### 1. Форк репозитория
```bash
# Форкните репозиторий на GitHub
# Затем клонируйте ваш форк
git clone https://github.com/YOUR_USERNAME/RS---Razdor-Secure.git
cd RS---Razdor-Secure/Infiltrator
```

### 2. Настройка окружения
```bash
# Создайте виртуальное окружение
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Установите зависимости
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Для разработки

# Установите pre-commit хуки
pre-commit install
```

### 3. Создайте ветку
```bash
# Создайте новую ветку для вашей функции
git checkout -b feature/your-feature-name

# Или для исправления ошибки
git checkout -b fix/issue-number-description
```

### 4. Сделайте изменения
- Внесите необходимые изменения
- Следуйте стандартам кода
- Добавьте тесты
- Обновите документацию

### 5. Тестирование
```bash
# Запустите тесты
python -m pytest tests/

# Проверьте стиль кода
flake8 infiltrator_v2.py
black infiltrator_v2.py

# Запустите все проверки
pre-commit run --all-files
```

### 6. Отправьте изменения
```bash
# Добавьте изменения
git add .

# Сделайте коммит
git commit -m "feat: add new feature description"

# Отправьте в ваш форк
git push origin feature/your-feature-name
```

### 7. Создайте Pull Request
- Откройте Pull Request на GitHub
- Используйте понятный заголовок
- Опишите ваши изменения
- Ссылайтесь на связанные issues

---

## 🔄 Процесс разработки

### Ветвление
- **main** - стабильная версия
- **develop** - разработка следующей версии
- **feature/*** - новые функции
- **fix/*** - исправления ошибок
- **docs/*** - документация
- **release/*** - подготовка релиза

### Коммиты
Используйте [Conventional Commits](https://www.conventionalcommits.org/ru/v1.0.0/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

#### Типы коммитов
- **feat**: Новая функция
- **fix**: Исправление ошибки
- **docs**: Документация
- **style**: Форматирование кода
- **refactor**: Рефакторинг
- **test**: Тесты
- **chore**: Обслуживание

#### Примеры
```bash
feat(analyzer): add support for TypeScript files
fix(parser): handle empty JavaScript files correctly
docs(api): update endpoint extraction examples
test(coverage): add tests for obfuscation resistance
```

### Pull Requests
#### Требования
- Все тесты должны проходить
- Код должен соответствовать стандартам
- Документация должна быть обновлена
- Описание должно быть понятным

#### Шаблон PR
```markdown
## Описание
Краткое описание изменений

## Тип изменений
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Тестирование
- [ ] Добавлены новые тесты
- [ ] Все тесты проходят
- [ ] Ручное тестирование проведено

## Проверка
- [ ] Код соответствует стандартам
- [ ] Документация обновлена
- [ ] Нет конфликтов слияния
```

---

## 📝 Стандарты кода

### Python
#### Стиль кода
- Используйте **PEP 8**
- Максимальная длина строки: 88 символов
- Используйте **Black** для форматирования
- Используйте **flake8** для проверки

#### Именование
```python
# Классы - CamelCase
class InfiltratorV2:
    pass

# Функции и переменные - snake_case
def analyze_bundle():
    pass

# Константы - UPPER_CASE
MAX_BUNDLE_SIZE = 50 * 1024 * 1024

# Приватные методы - с подчеркиванием
def _private_method():
    pass
```

#### Документация
```python
def analyze_bundle(self, bundle_path: str) -> Dict[str, Any]:
    """
    Анализ JavaScript бандла
    
    Args:
        bundle_path: Путь к JavaScript файлу для анализа
        
    Returns:
        Dict[str, Any]: Результаты анализа
        
    Raises:
        FileNotFoundError: Файл не найден
        ParseError: Ошибка парсинга JavaScript
        
    Example:
        >>> infiltrator = InfiltratorV2()
        >>> results = infiltrator.analyze_bundle("app.js")
    """
```

### JavaScript
#### Стиль кода
- Используйте **ESLint**
- Максимальная длина строки: 100 символов
- Используйте **Prettier** для форматирования

#### Примеры
```javascript
// Функции - camelCase
function analyzeBundle() {
    // ...
}

// Константы - UPPER_CASE
const MAX_BUNDLE_SIZE = 50 * 1024 * 1024;

// Классы - PascalCase
class InfiltratorV2 {
    // ...
}
```

---

## 🧪 Тестирование

### Структура тестов
```
tests/
├── unit/           # Unit тесты
├── integration/    # Интеграционные тесты
├── fixtures/       # Тестовые данные
└── conftest.py     # Конфигурация pytest
```

### Написание тестов
```python
import pytest
from infiltrator_v2 import InfiltratorV2, InfiltratorConfig

class TestInfiltratorV2:
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.config = InfiltratorConfig(enable_stealth=True)
        self.infiltrator = InfiltratorV2(self.config)
    
    def test_analyze_simple_bundle(self):
        """Тест анализа простого бандла"""
        js_code = """
        const api = axios.get(process.env.API_URL + '/users');
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(js_code)
            f.flush()
            
            result = self.infiltrator.analyze_bundle(f.name)
            
            assert 'endpoints' in result
            assert len(result['endpoints']) > 0
            assert 'API_URL' in result['process_env_vars']
```

### Запуск тестов
```bash
# Все тесты
pytest

# С покрытием
pytest --cov=infiltrator_v2

# Конкретный файл
pytest tests/test_analyzer.py

# С маркером
pytest -m "unit"
```

### Покрытие кода
- Минимальное покрытие: 85%
- Целевое покрытие: 90%
- Новые функции должны иметь 100% покрытие

---

## 📚 Документация

### Типы документации
- **API документация** - автоматическая из docstrings
- **Пользовательская документация** - руководства и примеры
- **Техническая документация** - архитектура и алгоритмы
- **README** - краткое описание проекта

### Написание документации
#### Markdown
```markdown
# Заголовок уровня 1
## Заголовок уровня 2

**Жирный текст** и *курсив*

- Список элементов
- Еще один элемент

```python
# Код блок
def example():
    pass
```

[Ссылка](url)
```

#### Docstrings
```python
def example_function(param1: str, param2: int = 0) -> bool:
    """
    Краткое описание функции
    
    Подробное описание функции, ее назначение и особенности.
    
    Args:
        param1: Описание первого параметра
        param2: Описание второго параметра со значением по умолчанию
        
    Returns:
        Описание возвращаемого значения
        
    Raises:
        ValueError: Описание когда возникает исключение
        
    Note:
        Дополнительная информация об использовании
        
    Example:
        >>> result = example_function("test", 5)
        >>> print(result)
        True
    """
```

### Обновление документации
- Изменения в API требуют обновления документации
- Новые функции должны быть задокументированы
- Примеры должны быть рабочими
- Ссылки должны быть актуальными

---

## 🌍 Сообщество

### Кодекс поведения
Мы стремимся создать дружелюбную и инклюзивную среду для всех участников.

#### Правила
- Будьте уважительны и вежливы
- Используйте инклюзивный язык
- Помогайте другим участникам
- Конструктивная критика
- Следуйте правилам проекта

#### Нарушения
- Харассment или дискриминация
- Неприемлемый контент
- Спам или реклама
- Вредоносный код

### Связь
- **GitHub Issues** - проблемы и вопросы
- **GitHub Discussions** - обсуждения и идеи
- **Email** - security@razdor.net

### Признание вклада
- Все контрибьюторы отмечены в CONTRIBUTORS.md
- Топ контрибьюторы в README
- Особые заслуги в релизах

---

## 🔧 Инструменты разработки

### Обязательные инструменты
```bash
# Установка инструментов разработки
pip install black flake8 pytest pytest-cov pre-commit
```

### Рекомендуемые инструменты
```bash
# Дополнительные инструменты
pip install mypy bandit safety isort
```

### VS Code настройки
```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.testing.pytestEnabled": true
}
```

---

## 📋 Чеклист перед отправкой PR

### Код
- [ ] Код соответствует стандартам PEP 8
- [ ] Все тесты проходят
- [ ] Покрытие кода не менее 85%
- [ ] Нет предупреждений линтера
- [ ] Коммиты следуют conventional commits

### Документация
- [ ] Docstrings добавлены/обновлены
- [ ] README обновлен при необходимости
- [ ] Примеры рабочие
- [ ] CHANGELOG обновлен

### Тестирование
- [ ] Unit тесты написаны
- [ ] Интеграционные тесты пройдены
- [ ] Ручное тестирование проведено
- [ ] Производительность проверена

### Безопасность
- [ ] Нет уязвимостей безопасности
- [ ] Валидация входных данных
- [ ] Обработка ошибок реализована

---

## 🏆 Типы вклада

### 🐛 Bug Reports
- Найденные и задокументированные ошибки
- Минимальные воспроизводимые примеры
- Предложения по исправлению

### 💡 Feature Requests
- Новые идеи и функции
- Улучшения существующего функционала
- Обратная связь от пользователей

### 🔧 Code Contributions
- Исправления ошибок
- Новые функции
- Оптимизации производительности
- Рефакторинг

### 📚 Documentation
- Улучшение существующей документации
- Переводы на другие языки
- Примеры использования
- Учебные материалы

### 🧪 Testing
- Новые тесты
- Улучшение покрытия кода
- Тестовые данные
- Автоматизация тестирования

### 🎨 Design
- UI/UX улучшения
- Логотип и брендинг
- Иконки и графика
- Веб-дизайн

---

## 🚨 Особые случаи

### Критические уязвимости
Если вы нашли критическую уязвимость безопасности:
1. Не создавайте публичный issue
2. Отправьте email на security@razdor.net
3. Опишите проблему детально
4. Дайте нам время для исправления
5. Мы координируем публичное раскрытие

### Breaking Changes
- Обсуждайте в issues перед реализацией
- Предоставьте план миграции
- Обновите все связанные части
- Задокументируйте изменения

### Зависимости
- Проверьте совместимость
- Обновите requirements.txt
- Протестируйте с новыми версиями
- Обновите документацию

---

## 📞 Получение помощи

### Вопросы
- **GitHub Discussions** - общие вопросы
- **Issues** - проблемы и баги
- **Email** - конфиденциальные вопросы

### Ресурсы
- [Документация](docs/README.md)
- [API Справочник](docs/api.md)
- [Примеры](docs/examples.md)
- [FAQ](docs/faq.md)

### Менторство
- Новым контрибьюторам доступен менторинг
- Помощь с первым Pull Request
- Обучение процессу разработки
- Код ревью и советы

---

## 🎉 Благодарности

Спасибо всем, кто вносит вклад в INFILTRATOR!

### Топ контрибьюторы
- **@razdor** - Основатель и ведущий разработчик
- **@security-team** - Аудит безопасности
- **@docs-team** - Документация

### Особая благодарность
- Всем пользователям за фидбэк
- Тестировщикам за поиск ошибок
- Сообществу за поддержку

---

**[📖 Документация](docs/README.md) • [🏠 Главная](README.md) • [🔄 История изменений](CHANGELOG.md)**
