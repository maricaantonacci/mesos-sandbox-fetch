FROM python:3.8
LABEL maintainer="marica.antonacci@ba.infn.it"

COPY . /app
WORKDIR /app/

ENV PYTHONPATH=/app

RUN pip install gunicorn && pip install -r /app/requirements.txt

ENV PORT 5001
ENV ENABLE_HTTPS False
ENV TIMEOUT 60
ENV WORKERS 2

COPY ./docker/start.sh /start.sh

CMD ["/bin/bash","/start.sh"]

