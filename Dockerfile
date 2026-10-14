FROM python:3.12-slim

LABEL maintainer="MoYun Admin"
LABEL description="墨韵 · 文章创作工作台"

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /var/lib/flask-app /var/log/flask-app && \
    chown -R www-data:www-data /var/lib/flask-app /var/log/flask-app

USER www-data

EXPOSE 8000

CMD ["gunicorn", "--workers", "2", "--threads", "4", "--timeout", "300", "--bind", "0.0.0.0:8000", "app:app"]
