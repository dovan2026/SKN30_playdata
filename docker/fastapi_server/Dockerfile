# uv 공식 이미지를 베이스로. python 3.12 + uv 미리 설치
FROM astral/uv:python3.12-bookworm-slim

# 이후 명령이 실행될 컨테이너 내부의 작업 디렉터리 지정
# 현재 작업경로를 /app 폴더로 바꿔주고 /app 폴더가 없으면 하나 만들어줌 
WORKDIR /app

# 의존성 정의만 먼저 복사(소스 변경 시 캐시 활용)
# 소스 코드만 변경되었을 때 의존성 설치 레이어의 캐시를 
# 재사용하여 빌드 시간 줄일수 있음
COPY pyproject.toml ./

# 가상환경 생성 _ 의존성 설치(lcok 없으면 이때 만들어짐)
RUN uv sync --no-dev

# Dockerfile 현재 경로 옆에 있는 모든 파일과 폴더들을 
# 가상컴퓨터 현재경로로 복사해 달라.  
COPY . .

# 이 컨테이너가 8000번 포트를 사용한다는 사실을 문서화 
EXPOSE 8000

# uv run으로 venv의 uvicorn 실행
# 컨테이너가 시작될 때 실행할 기본 명령
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port","8000"]