# Ozon Characteristics Updater

Автоматическое обновление характеристик товаров на Ozon через API.

## 📌 Возможности

- ✅ Массовое обновление характеристик (до 100 товаров/запрос)
- ✅ Поддержка справочных атрибутов (цвета, бренды, страны)
- ✅ Обработка ошибок 429 с retry
- ✅ Отчёты в Bitrix24
- ✅ Поддержка нескольких ИП

## 🚀 Быстрый старт

```bash
# 1. Клонируем репозиторий
git clone https://github.com/OlegSergushev/ozon-characteristics-updater.git
cd ozon-characteristics-updater

# 2. Устанавливаем зависимости
pip install -r requirements.txt

# 3. Запускаем
python ozon_update_characteristics.py
