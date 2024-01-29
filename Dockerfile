FROM python:3.8.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libc-dev \
    && rm -rf /var/lib/apt/lists/*

COPY . /app

RUN pip install -r requirements.txt

