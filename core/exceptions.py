"""
=========================================
Jaguar QuantX Exception Framework
=========================================
"""


class JaguarError(Exception):
    """Base exception for Jaguar QuantX."""
    pass


class ConfigurationError(JaguarError):
    """Configuration related errors."""
    pass


class MarketDataError(JaguarError):
    """Market data loading errors."""
    pass


class IndicatorError(JaguarError):
    """Indicator calculation errors."""
    pass


class StrategyError(JaguarError):
    """Strategy engine errors."""
    pass


class ExecutionError(JaguarError):
    """Execution engine errors."""
    pass


class RiskError(JaguarError):
    """Risk management errors."""
    pass


class AIEngineError(JaguarError):
    """AI engine errors."""
    pass


class ValidationError(JaguarError):
    """Validation errors."""
    pass
