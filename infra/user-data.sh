#!/bin/bash
set -euxo pipefail

APP_DIR="__APP_DIR__"
DOCKER_IMAGE="__DOCKER_IMAGE__"
BOOTSTRAP_ONLY="__BOOTSTRAP_ONLY__"

install_docker_if_missing() {
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    return
  fi

  apt-get update -y
  apt-get install -y ca-certificates curl gnupg lsb-release

  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc

  if [ ! -f /etc/apt/sources.list.d/docker.list ]; then
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      tee /etc/apt/sources.list.d/docker.list > /dev/null
  fi

  apt-get update -y
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
}

write_compose_if_missing() {
  mkdir -p "${APP_DIR}"
  if [ ! -f "${APP_DIR}/docker-compose.yml" ]; then
    cat > "${APP_DIR}/docker-compose.yml" <<'EOF'
version: "3.9"

services:
  app:
    image: ${DOCKER_IMAGE}
    container_name: mini_redis_app
    ports:
      - "8000:8000"
    depends_on:
      - redis
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    container_name: mini_redis_store
    ports:
      - "6379:6379"
    restart: unless-stopped
EOF
  fi
}

sync_env_file() {
  cat > "${APP_DIR}/.env" <<EOF
DOCKER_IMAGE=${DOCKER_IMAGE}
EOF
}

bootstrap_server() {
  install_docker_if_missing
  write_compose_if_missing
  sync_env_file
}

deploy_if_enabled() {
  if [ "${BOOTSTRAP_ONLY}" = "true" ] || [ "${DOCKER_IMAGE}" = "auto" ]; then
    return
  fi

  cd "${APP_DIR}"
  docker compose pull
  docker compose up -d

  until curl -fsS http://localhost:8000/v1/health; do
    sleep 2
  done
}

bootstrap_server
deploy_if_enabled
