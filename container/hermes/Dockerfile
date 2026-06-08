FROM python:3.13-slim

ARG HERMES_REPO_URL=https://github.com/NousResearch/hermes-agent.git
ARG HERMES_COMMIT=5921d667855880b0aa2083a50f001748aed52f3e
ARG HERMES_EXTRAS=cli,messaging

ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates git \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --filter=blob:none "$HERMES_REPO_URL" /opt/hermes-agent \
    && cd /opt/hermes-agent \
    && git fetch --depth 1 origin "$HERMES_COMMIT" \
    && git checkout --detach "$HERMES_COMMIT" \
    && python -m pip install --upgrade pip \
    && python -m pip install ".[${HERMES_EXTRAS}]"

WORKDIR /workspace
ENTRYPOINT ["hermes"]
