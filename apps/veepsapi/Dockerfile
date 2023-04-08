FROM --platform=linux/amd64 python:3.10

# python envs
ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

WORKDIR /app

# python dependencies
COPY ./Pipfile ./Pipfile.lock /app/
RUN pip install --upgrade pip pipenv
RUN pipenv lock
RUN pipenv install --deploy --system -d  # development

# Copy backend code to container (prod)
# COPY ./ /app/

# upload scripts
COPY ./scripts/entrypoint.sh ./scripts/start.sh ./scripts/gunicorn.sh /
