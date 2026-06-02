FROM ubuntu:24.04 AS base

RUN apt-get update && apt-get install -y wget

RUN wget https://obs.osmocom.org/projects/osmocom/public_key && \
    install -Dm644 public_key /usr/share/osmocom-keyring/osmocom.asc && \
    echo "deb [signed-by=/usr/share/osmocom-keyring/osmocom.asc] https://downloads.osmocom.org/packages/osmocom:/latest/xUbuntu_24.04/ ./" > /etc/apt/sources.list.d/osmocom.list && \
    apt-get update

RUN apt-get install -y osmo-msc osmo-bsc osmo-hlr osmo-mgw osmo-stp

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=.python-version,target=.python-version \
    uv sync --frozen --no-install-project --no-dev

# Then, add the rest of the project source code and install it
# Installing separately from its dependencies allows optimal layer caching
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --dev


#### Development target
FROM base AS dev

WORKDIR /app

EXPOSE 8000

ENV PATH="/app/.venv/bin:$PATH"

ENTRYPOINT []
CMD ["/app/entrypoint.sh"]


### Testing target
FROM base AS tests

WORKDIR /app

RUN echo "{\"testsuite\":{\"password\": \"testsuite\"}}" > /app/app/data/users.json
RUN echo "{}" > /app/app/data/dks.json

ENTRYPOINT ["/app/entrypoint-tests.sh"]