FROM tiangolo/uwsgi-nginx-flask:python3.7

ENV NGINX_MAX_UPLOAD 16m

COPY app/requirements.txt /app/

RUN pip install -r /app/requirements.txt

COPY ./app /app
