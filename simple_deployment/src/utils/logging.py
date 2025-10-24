"""
Structured logging configuration for the Incident Commander system.
"""

import logging
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, "incident_id"):
            log_entry["incident_id"] = record.incident_id
        if hasattr(record, "agent_name"):
            log_entry["agent_name"] = record.agent_name
        if hasattr(record, "correlation_id"):
            log_entry["correlation_id"] = record.correlation_id
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry)


class IncidentCommanderLogger:
    """Logger factory for the Incident Commander system."""
    
    _loggers: Dict[str, logging.Logger] = {}
    _configured = False
    
    @classmethod
    def configure(cls, level: str = "INFO", log_file: Optional[Path] = None) -> None:
        """Configure logging for the entire system."""
        if cls._configured:
            return
        
        # Set up root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, level.upper()))
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Console handler with structured formatting
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(console_handler)
        
        # File handler if specified
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(StructuredFormatter())
            root_logger.addHandler(file_handler)
        
        cls._configured = True
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """Get or create a logger with the given name."""
        if name not in cls._loggers:
            cls._loggers[name] = logging.getLogger(f"incident_commander.{name}")
        return cls._loggers[name]


def get_logger(name: str) -> logging.Logger:
    """Convenience function to get a logger."""
    return IncidentCommanderLogger.get_logger(name)


class LogContext:
    """Context manager for adding structured logging context."""
    
    def __init__(self, logger: logging.Logger, **context):
        """Initialize log context."""
        self.logger = logger
        self.context = context
        self.old_context = {}
    
    def __enter__(self):
        """Enter context and add fields to logger."""
        for key, value in self.context.items():
            if hasattr(self.logger, key):
                self.old_context[key] = getattr(self.logger, key)
            setattr(self.logger, key, value)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and restore logger state."""
        for key in self.context:
            if key in self.old_context:
                setattr(self.logger, key, self.old_context[key])
            else:
                delattr(self.logger, key)


# Initialize logging configuration
IncidentCommanderLogger.configure()