FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y libpq-dev gcc && \
    apt-get clean

COPY requirements/base.txt ./requirements.txt
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install gunicorn psycopg2-binary

COPY . .

EXPOSE 8082

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8082"]
