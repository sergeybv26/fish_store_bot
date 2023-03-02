"""Конфигурация логгера"""

log_config = {
    "version": 1,
    "handlers": {
        "streamHandler": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "log_formatter",
            "level": "INFO"
        },
        "fileHandler": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "log_formatter",
            "filename": "bot.log",
            "maxBytes": 20000,
            "backupCount": 2,
            "encoding": "utf-8"
        }
    },
    "formatters": {
        "log_formatter": {
            "format": "%(asctime)s %(levelname)-8s %(filename)s %(message)s"
        }
    },
    "loggers": {
        "bot-quiz": {
            "handlers": ["streamHandler", "fileHandler"],
            "level": "DEBUG"
        }
    }
}
