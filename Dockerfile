# syntax=docker/dockerfile:1

ARG PYTHON_VERSION="3.12"
ARG ALPINE_VERSION="3.19"

FROM python:${PYTHON_VERSION}-alpine${ALPINE_VERSION} as build

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="${VIRTUAL_ENV}/bin:$PATH"

WORKDIR /app

# Copy and install requirements only first to cache the dependency layer
RUN pip install uv

COPY pyproject.toml ./
RUN --mount=type=cache,target=/root/.cache/uv \
uv venv $VIRTUAL_ENV && \
uv pip install -r pyproject.toml

COPY src/ ./

CMD ["python", "/app/gha_issue_resolution"]
