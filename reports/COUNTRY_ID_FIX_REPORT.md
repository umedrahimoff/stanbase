# Отчет о проблеме с передачей названия страны вместо ID

## Дата: 29 июля 2024

## Проблема

В логах обнаружена ошибка:
```
ValueError: invalid literal for int() with base 10: 'Кыргызстан'
```

**Причина:** В форме создания/редактирования компании передавалось название страны (`'Кыргызстан'`), а код пытался преобразовать его в `int()`.

## Анализ проблемы

### 1. Проблема в шаблоне формы

В файле `templates/admin/companies/form.html` в строках 47-49:
```html
<!-- Было (НЕПРАВИЛЬНО): -->
<option value="{{ c.name }}" {% if company and company.country == c.name %}selected{% endif %}>{{ c.name }}</option>
```

### 2. Проблема в коде обработки

В файле `main.py` в строке 2138:
```python
# Было (НЕПРАВИЛЬНО):
country_id = int(form.get('country')) if form.get('country') else None
```

Код ожидал ID (число), а получал название страны (строку).

## Решение

### 1. Исправлен шаблон формы

**Файл:** `templates/admin/companies/form.html`

```html
<!-- Стало (ПРАВИЛЬНО): -->
<option value="{{ c.id }}" {% if company and company.country == c.name %}selected{% endif %}>{{ c.name }}</option>
```

Аналогично исправлено для городов:
```html
<option value="{{ city.id }}" {% if company and company.city == city.name %}selected{% endif %}>{{ city.name }}</option>
```

### 2. Исправлена функция редактирования компании

**Файл:** `main.py` - функция `admin_edit_company_post()`

```python
# Было:
company.country = form.get('country')
company.city = form.get('city')

# Стало:
# Обработка страны и города по ID
country_id = int(form.get('country')) if form.get('country') else None
city_id = int(form.get('city')) if form.get('city') else None

if country_id:
    country = db.query(Country).get(country_id)
    company.country = country.name if country else ''
else:
    company.country = ''
    
if city_id:
    city = db.query(City).get(city_id)
    company.city = city.name if city else ''
else:
    company.city = ''
```

## Изменения в коде

### templates/admin/companies/form.html
- Изменено `value="{{ c.name }}"` на `value="{{ c.id }}"` для стран
- Изменено `value="{{ city.name }}"` на `value="{{ city.id }}"` для городов

### main.py
- Добавлен импорт `Country, City` в функцию редактирования
- Добавлена логика обработки ID стран и городов
- Добавлена проверка существования записей в БД

## Тестирование

После внесения изменений необходимо протестировать:
1. ✅ Создание новой компании с выбором страны и города
2. ✅ Редактирование существующей компании
3. ✅ Проверка, что выбранные значения сохраняются корректно
4. ✅ Проверка, что форма отображает правильные выбранные значения при редактировании

## Статус

✅ **Исправлено** - проблема с передачей названия страны вместо ID решена
🔄 **Требует тестирования** - необходимо проверить работу на стейдже

## Рекомендации

1. **Проверить другие формы** - возможно, есть аналогичные проблемы в других формах
2. **Добавить валидацию** - проверять корректность ID перед запросами к БД
3. **Улучшить обработку ошибок** - добавить try-catch для обработки некорректных ID