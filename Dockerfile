# Dockerfile
FROM python:3.13-slim

WORKDIR /app

# Копіюємо тільки requirements спочатку для швидшої кеш-будови
COPY requirements.txt .

# Встановлюємо залежності (додайте psycopg2-binary чи asyncpg, якщо потрібні)
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо весь ваш код
COPY src/ ./src/

# Виставляємо робочу директорію на src, щоб модулі у langchain_poc були на PYTHONPATH
WORKDIR /app/src

EXPOSE 8000

# Запускаємо Uvicorn, вказуючи модуль langchain_poc.api
CMD ["uvicorn", "langchain_poc.api:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
