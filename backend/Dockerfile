FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements/production.txt /app/requirements/production.txt
COPY requirements/base.txt /app/requirements/base.txt

RUN pip install --no-cache-dir -r /app/requirements/production.txt

COPY . /app

EXPOSE 8000