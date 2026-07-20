"""FastAPI 엔드포인트에서 재사용하는 의존성."""

from collections.abc import Generator

from sqlalchemy.orm import Session

from database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """요청마다 Session을 만들고 처리 후 안전하게 정리합니다."""
    db = SessionLocal()     # 새로운 데이터베이스 세션을 생성
    try:
        yield db
    except Exception:       # 엔드포인트 처리 중 예외가 발생하면 아직 확정되지 않은 DB 작업을 취소
        db.rollback()
        raise
    finally:
        db.close()          # 성공 여부와 관계 없이 마지막에 세션을 닫음
