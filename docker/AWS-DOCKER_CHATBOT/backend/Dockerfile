# python 3.12의 경량 이미지 사용
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1 \
  PIP_NO_CACHE_DIR=1

# 컨테이너 내부 작업 디렉터리
WORKDIR /app

# 로컬 requirements.txt 파일을 컨테이너의 /app/requirements.txt로 복사
COPY requirements.txt ./

# 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt

RUN useradd --create-home --shell /usr/sbin/nologin appuser

# 복사되는 파일의 소유자와 그룹은 appuser로 설정
COPY --chown=appuser:appuser app ./app

# 이후 명령과 컨테이너 프로세스를 root가 아닌 appuser로 실행
USER appuser

# 포트가 8000번 포트를 사용한다는 것 문서화
EXPOSE 8000

# 컨테이너 내부에서 FastAPI 서버가 정상인지 주기적으로 검사
HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"

# 컨테이너가 시작될 때 실행하는 기본 명령
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]