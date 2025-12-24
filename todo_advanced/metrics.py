"""
Metrics and monitoring utilities.
"""

import time
from typing import Dict, List
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Metric:
    """Represents a performance metric."""
    name: str
    value: float
    unit: str = "ms"
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class OperationMetrics:
    """Tracks metrics for an operation."""
    operation_name: str
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    duration_ms: float = 0.0
    success: bool = True
    error: Optional[str] = None

    def finish(self, success: bool = True, error: Optional[str] = None) -> None:
        """Mark operation as finished."""
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        self.success = success
        self.error = error


class MetricsCollector:
    """Collects and aggregates performance metrics."""

    def __init__(self):
        self.metrics: List[Metric] = []
        self.operations: List[OperationMetrics] = []

    def record_metric(self, name: str, value: float, unit: str = "ms") -> None:
        """Record a single metric."""
        metric = Metric(name, value, unit)
        self.metrics.append(metric)

    def start_operation(self, name: str) -> OperationMetrics:
        """Start tracking an operation."""
        op = OperationMetrics(name)
        self.operations.append(op)
        return op

    def get_average_duration(self, operation_name: str) -> float:
        """Get average duration for an operation."""
        ops = [
            op
            for op in self.operations
            if op.operation_name == operation_name and op.success
        ]
        if not ops:
            return 0.0
        return sum(op.duration_ms for op in ops) / len(ops)

    def get_summary(self) -> Dict:
        """Get summary of collected metrics."""
        return {
            "total_operations": len(self.operations),
            "successful_operations": sum(1 for op in self.operations if op.success),
            "failed_operations": sum(1 for op in self.operations if not op.success),
            "total_metrics": len(self.metrics),
            "operation_types": list(set(op.operation_name for op in self.operations)),
        }

    def clear(self) -> None:
        """Clear all metrics."""
        self.metrics.clear()
        self.operations.clear()


# Global metrics collector
_collector = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector."""
    return _collector
