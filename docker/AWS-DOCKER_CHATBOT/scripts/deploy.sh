#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="/opt/compose-ai-lab"
COMPOSE_FILE="${PROJECT_DIR}/compose.production.yaml"

cd "$PROJECT_DIR"

if [ ! -f ".env" ]; then
    echo "Compose 변수 파일이 없습니다: ${PROJECT_DIR}/.env" >&2
    exit 1
fi

if [ ! -f "api.env" ]; then
    echo "API 환경 변수 파일이 없습니다: ${PROJECT_DIR}/api.env" >&2
    exit 1
fi

echo "[1/5] Compose 설정 검증"
docker compose --env-file .env -f "$COMPOSE_FILE" config --quiet

echo "[2/5] 이미지 Pull"
docker compose --env-file .env -f "$COMPOSE_FILE" pull

echo "[3/5] 컨테이너 교체"
docker compose \
    --env-file .env \
    -f "$COMPOSE_FILE" \
    up -d \
    --force-recreate \
    --remove-orphans

echo "[4/5] Compose 상태"
docker compose --env-file .env -f "$COMPOSE_FILE" ps

echo "[5/5] 서비스 Health Check"
for attempt in {1..20}; do
    if curl --fail --silent http://127.0.0.1/api/health > /dev/null; then
        echo "배포 성공"
        curl --fail --silent http://127.0.0.1/api/info
        echo
        exit 0
    fi

    echo "서비스 시작 대기 중... ${attempt}/20"
    sleep 3
done

echo "배포 실패: Health Check가 통과하지 못했습니다." >&2
docker compose --env-file .env -f "$COMPOSE_FILE" ps >&2 || true
docker compose --env-file .env -f "$COMPOSE_FILE" logs --tail 100 >&2 || true
exit 1
