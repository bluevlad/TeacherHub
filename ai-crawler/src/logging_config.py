"""
TeacherHub Logging Configuration
구조화된 로깅 설정
"""
import logging
import sys


def setup_logging(level: str = "INFO"):
    """로깅 설정 초기화"""
    log_level = getattr(logging, level.upper(), logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # 기존 핸들러 제거 후 추가
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)

    # 외부 라이브러리 로그 레벨 조정
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
