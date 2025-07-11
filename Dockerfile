# 1) Imagem base Python
FROM python:3.11-slim

# 2) Dependências do sistema para Python e Node
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential \
      curl \
      ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# 3) Instala Node.js (18.x) + npm
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get update && \
    apt-get install -y --no-install-recommends nodejs && \
    rm -rf /var/lib/apt/lists/*

# 4) Define diretório de trabalho
WORKDIR /app

# 5) Copia só o requirements (cache eficaz)
COPY requirements.txt .

# 6) Instala deps Python
RUN pip install --no-cache-dir -r requirements.txt

# 7) Copia todo o resto do código
COPY . .

# 8) Expõe portas
EXPOSE 8000
EXPOSE 3000

# 9) Comando padrão
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
