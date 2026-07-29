#!/usr/bin/env bash
set -Eeuo pipefail

if [ "$#" -ne 2 ]; then
    echo "사용법: rollback.sh API_TAG WEB_TAG" >&2
    echo "예: rollback.sh 1.0.0 1.0.0" >&2
    exit 2
fi

PROJECT_DIR="/opt/compose-ai-lab"
API_TAG="$1"
WEB_TAG="$2"

cd "$PROJECT_DIR"

sed -i "s/^API_IMAGE_TAG=.*/API_IMAGE_TAG=${API_TAG}/" .env
sed -i "s/^WEB_IMAGE_TAG=.*/WEB_IMAGE_TAG=${WEB_TAG}/" .env
sed -i "s/^APP_VERSION=.*/APP_VERSION=${API_TAG}/" api.env

echo "롤백 대상"
echo "API_IMAGE_TAG=${API_TAG}"
echo "WEB_IMAGE_TAG=${WEB_TAG}"

exec "${PROJECT_DIR}/scripts/deploy.sh"
