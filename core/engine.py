"""
Base engine runner class.
"""
from abc import ABC, abstractmethod

class EngineRunner(ABC):
    """Base class for all engine runners."""
    @property
    def engine_name(self) -> str:
        return self.__class__.__name__

    @abstractmethod
    def run(self, state, bus):
        """Execute engine analysis."""
        pass

# Backward compatibility alias
Engine = EngineRunner
