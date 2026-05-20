import sys

from loguru import logger

from config import config

logger.remove()
logger.add(
    sys.stderr,
    level=config.LOG_LEVEL.upper(),
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    ),
)
