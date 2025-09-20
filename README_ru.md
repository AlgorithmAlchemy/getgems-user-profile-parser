# NFT Parser for GetGems.io

  `⭐️ Thanks everyone who has starred the project, it means a lot!`

**Read this in other languages:** [English (README.md)](README.md)

Это проект на Python, который парсит данные пользователей с [GetGems.io](https://getgems.io/) и сохраняет результаты в базу данных SQLite.

## Особенности
- Сбор данных о NFT для пользователей с GetGems.io.
- Сохранение данных в базу данных SQLite.
- Использует Selenium WebDriver с браузером Firefox для автоматизации.
- Парсит имена кошельков из текстового файла и обрабатывает каждый кошелек.

## Требования

- Python 3.10+
- Selenium
- Браузер Firefox
- GeckoDriver
- SQLite3 (предустановлен в Python)

## Установка

1. Клонируйте репозиторий:

```bash
git clone https://github.com/yourusername/nft-getgems-parser.git
cd nft-getgems-parser
```
2. Установите реккомендуемые пакеты
```bash
pip install selenium
