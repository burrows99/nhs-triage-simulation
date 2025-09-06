from __future__ import annotations
from dataclasses import dataclass, field
import logging
from services.logger_service import LoggerService

@dataclass(slots=True)
class BaseEntity:
    """Common base for domain entities providing id validation and a unified logger."""
    id: int
    logger: logging.Logger = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        # Use the subclass's module for logger names to preserve module-level log routing
        module_name = self.__class__.__module__
        self.logger = LoggerService.get_logger(module_name)
        if self.id < 0:
            raise ValueError(f"{self.__class__.__name__}.id must be a non-negative int")
        self.logger.debug("%s created id=%d", self.__class__.__name__, self.id)

@dataclass(slots=True)
class BaseResource(BaseEntity):
    """Marker base for resource units; extend with shared resource behaviors later."""
    def __post_init__(self) -> None:
        BaseEntity.__post_init__(self)