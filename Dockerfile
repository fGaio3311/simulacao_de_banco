# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Cria diretório de trabalho
WORKDIR /app

# Copia só o requirements primeiro (para cache)
COPY requirements.txt .

# Instala dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código da API
COPY . .

# Expõe a porta do Uvicorn
EXPOSE 8000

# Roda a API
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
