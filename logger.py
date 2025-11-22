from loguru import logger
import sys

# Remove default handler
logger.remove()

# Configure console logger
logger.add(
    sys.stdout,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)

# Configure file logger for structured JSON output
logger.add(
    "bot.log",
    level="INFO",
    format="{message}", # We will manually structure the log message
    rotation="10 MB", # Rotate log file when it reaches 10 MB
    retention="7 days", # Keep logs for 7 days
    compression="zip", # Compress rotated files
    serialize=True # IMPORTANT: This enables structured (JSON) logging
)

# Export the configured logger
log = logger