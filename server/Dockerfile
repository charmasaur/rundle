# From https://testdriven.io/blog/dockerizing-flask-with-postgres-gunicorn-and-nginx/

FROM python:3.8.1-slim-buster

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip install --upgrade pip
COPY ./requirements.txt /usr/src/app/requirements.txt
RUN pip install -r requirements.txt

COPY . /usr/src/app/

CMD gunicorn --bind 0.0.0.0:$PORT wsgi
