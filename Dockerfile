FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends graphviz libgeos-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

CMD gunicorn app:app --bind 0.0.0.0:${PORT:-5000}
```
4. Commit: `Adicionar Dockerfile para AhpAnpLib`

### 4. Aguardar redeploy
Railway detecta o Dockerfile e builda automaticamente. O build demora ~2-3 min (precisa instalar graphviz + pip install AhpAnpLib).

### 5. Testar
```
https://web-production-49489.up.railway.app/
