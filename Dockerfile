FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/uploads

EXPOSE 5000

ENV FLASK_APP=app.py
ENV FLASK_DEBUG=0

CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
