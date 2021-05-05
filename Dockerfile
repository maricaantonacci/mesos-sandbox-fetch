FROM python:3.8
LABEL maintainer="marica.antonacci@ba.infn.it"

COPY . /app
WORKDIR /app/

ENV PYTHONPATH=/app

RUN pip install gunicorn && pip install -r /app/requirements.txt

ENV PORT 5001
ENV TIMEOUT 60
ENV WORKERS 2


CMD gunicorn --bind 0.0.0.0:$PORT --workers $WORKERS --timeout $TIMEOUT mesos_sandbox_fetch:app

