from logger_setup import get_logger

logger = get_logger(
    "collector",
    "/opt/pimes/logs/collector/collector.log"
)

logger.info("PIMES logging initialized")
