FROM ubuntu:24.04

# NOTE:
# python:3.11.4-bookworm とかを使った場合，Selenium を同時に複数動かせないので，
# Ubuntu イメージを使う

RUN --mount=type=cache,target=/var/lib/apt,sharing=locked \
    --mount=type=cache,target=/var/cache/apt,sharing=locked \
    apt-get update && apt-get install --no-install-recommends --assume-yes \
    curl \
    ca-certificates \
    tini \
    build-essential \
    git \
    language-pack-ja \
    tzdata

ENV TZ=Asia/Tokyo \
    LANG=ja_JP.UTF-8 \
    LANGUAGE=ja_JP:ja \
    LC_ALL=ja_JP.UTF-8

RUN locale-gen en_US.UTF-8
RUN locale-gen ja_JP.UTF-8

RUN curl -O https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb

RUN --mount=type=cache,target=/var/lib/apt,sharing=locked \
    --mount=type=cache,target=/var/cache/apt,sharing=locked \
    apt-get update && apt-get install --no-install-recommends --assume-yes \
    ./google-chrome-stable_current_amd64.deb


COPY font /usr/share/fonts/

USER ubuntu

ENV PATH="/home/ubuntu/.local/bin:$PATH"
ENV UV_LINK_MODE=copy \
    UV_NO_SYNC=1

# ubuntu ユーザーで uv をインストール
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

WORKDIR /opt/eink-weather-panel

RUN --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=.python-version,target=.python-version \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=README.md,target=README.md \
    --mount=type=cache,target=/home/ubuntu/.cache/uv,uid=1000,gid=1000 \
    uv sync --no-install-project --no-editable --no-group dev --compile-bytecode

ARG IMAGE_BUILD_DATE
ENV IMAGE_BUILD_DATE=${IMAGE_BUILD_DATE}

COPY --chown=ubuntu:ubuntu . .

RUN mkdir -p data

# プロジェクトをインストール
RUN --mount=type=cache,target=/home/ubuntu/.cache/uv,uid=1000,gid=1000 \
    uv sync --no-group dev --compile-bytecode

ENTRYPOINT ["/usr/bin/tini", "--", "uv", "run", "--no-group", "dev"]

CMD ["src/display_image.py"]
