FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ENV USER=ava \
    GROUP=ava \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_FROZEN=1

RUN groupadd -r $GROUP \
    && useradd -m -s /bin/bash -g $GROUP $USER

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --no-install-project --no-dev


ENV APP_DIR=/home/$USER/app
USER $USER
WORKDIR $APP_DIR

COPY --chown=$USER:$USER . $APP_DIR

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --package builder

CMD [ "uv", "run", "builder" ]