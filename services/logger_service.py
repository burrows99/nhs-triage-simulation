from __future__ import annotations
import logging
from pathlib import Path
from typing import Optional

class LoggerService:
    _initialized: bool = False
    _output_dir: Optional[Path] = None

    @classmethod
    def initialize(cls, output_dir: Path, *, level: int = logging.DEBUG, console_level: int = logging.INFO,
                   filename: str = "simulation.log") -> None:
        # Always (re)initialize so each run gets a fresh file
        cls._initialized = False
        if cls._initialized:
            return
        output_dir.mkdir(parents=True, exist_ok=True)
        log_file = output_dir / filename
        logger = logging.getLogger()
        logger.setLevel(level)
        logger.handlers.clear()
        fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
        file_handler = logging.FileHandler(log_file, mode="w", encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(fmt)
        console = logging.StreamHandler()
        console.setLevel(console_level)
        console.setFormatter(fmt)
        logger.addHandler(file_handler)
        logger.addHandler(console)
        cls._output_dir = output_dir
        cls._initialized = True
        # Log once that logging is initialized
        logger.debug("LoggerService initialized. Output directory: %s", str(output_dir))

    @classmethod
    def get_logger(cls, name: Optional[str] = None) -> logging.Logger:
        # Require explicit initialization; do not auto-initialize silently
        if not cls._initialized:
            raise RuntimeError(
                "LoggerService not initialized. Call LoggerService.initialize(output_dir) before requesting loggers."
            )
        return logging.getLogger(name)