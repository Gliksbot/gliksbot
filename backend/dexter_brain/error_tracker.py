"""Error tracking and pattern detection system for Dexter v3."""

import json
import time
import traceback
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, List, Any, Optional
from pathlib import Path


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SystemError:
    """Represents a system error with metadata."""
    id: str
    timestamp: float
    error_type: str
    severity: ErrorSeverity
    message: str
    context: Dict[str, Any]
    source: str  # 'sandbox', 'llm', 'api', 'collaboration', etc.
    stack_trace: Optional[str] = None
    resolved: bool = False
    resolution_attempts: int = 0
    healing_session_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        result['severity'] = self.severity.value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SystemError':
        """Create SystemError from dictionary."""
        data['severity'] = ErrorSeverity(data['severity'])
        return cls(**data)


class ErrorTracker:
    """Central error tracking and pattern detection system."""
    
    def __init__(self, max_errors: int = 1000, persist_path: Optional[str] = None):
        self.errors: List[SystemError] = []
        self.max_errors = max_errors
        self.error_patterns: Dict[str, List[float]] = {}
        self.persist_path = persist_path
        
        # Load persisted errors if path provided
        if persist_path:
            self._load_persisted_errors()
    
    def log_error(
        self, 
        error_type: str, 
        message: str, 
        severity: ErrorSeverity, 
        source: str, 
        context: Optional[Dict[str, Any]] = None, 
        stack_trace: Optional[str] = None,
        auto_capture_traceback: bool = True
    ) -> str:
        """Log a new system error and return error ID."""
        
        error_id = f"err_{int(time.time() * 1000)}_{len(self.errors)}"
        
        # Auto-capture stack trace if requested and not provided
        if auto_capture_traceback and not stack_trace:
            stack_trace = traceback.format_exc() if traceback.format_exc() != 'NoneType: None\n' else None
        
        error = SystemError(
            id=error_id,
            timestamp=time.time(),
            error_type=error_type,
            severity=severity,
            message=message,
            context=context or {},
            source=source,
            stack_trace=stack_trace
        )
        
        self.errors.append(error)
        
        # Maintain size limit
        if len(self.errors) > self.max_errors:
            self.errors = self.errors[-self.max_errors:]
        
        # Detect patterns
        self._detect_patterns(error)
        
        # Persist if configured
        if self.persist_path:
            self._persist_error(error)
        
        return error_id
    
    def get_error(self, error_id: str) -> Optional[SystemError]:
        """Get error by ID."""
        for error in self.errors:
            if error.id == error_id:
                return error
        return None
    
    def mark_resolved(self, error_id: str, healing_session_id: Optional[str] = None) -> bool:
        """Mark an error as resolved."""
        error = self.get_error(error_id)
        if error:
            error.resolved = True
            if healing_session_id:
                error.healing_session_id = healing_session_id
            return True
        return False
    
    def increment_healing_attempts(self, error_id: str) -> bool:
        """Increment the healing attempt count for an error."""
        error = self.get_error(error_id)
        if error:
            error.resolution_attempts += 1
            return True
        return False
    
    def get_recent_errors(self, since_minutes: int = 5) -> List[SystemError]:
        """Get errors from the last N minutes."""
        cutoff = time.time() - (since_minutes * 60)
        return [e for e in self.errors if e.timestamp > cutoff and not e.resolved]
    
    def get_critical_errors(self) -> List[SystemError]:
        """Get all unresolved critical errors."""
        return [e for e in self.errors 
                if e.severity == ErrorSeverity.CRITICAL and not e.resolved]
    
    def get_errors_by_source(self, source: str, unresolved_only: bool = True) -> List[SystemError]:
        """Get errors from a specific source."""
        return [e for e in self.errors 
                if e.source == source and (not unresolved_only or not e.resolved)]
    
    def get_errors_by_type(self, error_type: str, unresolved_only: bool = True) -> List[SystemError]:
        """Get errors of a specific type."""
        return [e for e in self.errors 
                if e.error_type == error_type and (not unresolved_only or not e.resolved)]
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics."""
        recent_errors = self.get_recent_errors(60)  # Last hour
        
        stats = {
            "total_errors": len(self.errors),
            "recent_errors": len(recent_errors),
            "critical_errors": len(self.get_critical_errors()),
            "errors_by_severity": {},
            "errors_by_source": {},
            "errors_by_type": {},
            "resolution_rate": 0.0
        }
        
        # Count by severity
        for severity in ErrorSeverity:
            stats["errors_by_severity"][severity.value] = len([
                e for e in self.errors if e.severity == severity
            ])
        
        # Count by source
        sources = set(e.source for e in self.errors)
        for source in sources:
            stats["errors_by_source"][source] = len(self.get_errors_by_source(source, False))
        
        # Count by type
        types = set(e.error_type for e in self.errors)
        for error_type in types:
            stats["errors_by_type"][error_type] = len(self.get_errors_by_type(error_type, False))
        
        # Calculate resolution rate
        if self.errors:
            resolved_count = len([e for e in self.errors if e.resolved])
            stats["resolution_rate"] = resolved_count / len(self.errors)
        
        return stats
    
    def _detect_patterns(self, new_error: SystemError):
        """Detect recurring error patterns."""
        pattern_key = f"{new_error.error_type}:{new_error.source}"
        
        if pattern_key not in self.error_patterns:
            self.error_patterns[pattern_key] = []
        
        self.error_patterns[pattern_key].append(new_error.timestamp)
        
        # Keep only recent patterns (last hour)
        cutoff = time.time() - 3600
        self.error_patterns[pattern_key] = [
            ts for ts in self.error_patterns[pattern_key] if ts > cutoff
        ]
        
        # Alert if pattern detected (3+ occurrences in 10 minutes)
        recent_cutoff = time.time() - 600
        recent_count = len([
            ts for ts in self.error_patterns[pattern_key] if ts > recent_cutoff
        ])
        
        if recent_count >= 3:
            self.log_error(
                "PATTERN_DETECTED",
                f"Recurring error pattern detected: {pattern_key} ({recent_count} times in 10 minutes)",
                ErrorSeverity.HIGH,
                "error_tracker",
                {
                    "pattern": pattern_key,
                    "count": recent_count,
                    "original_error_id": new_error.id
                },
                auto_capture_traceback=False
            )
    
    def _persist_error(self, error: SystemError):
        """Persist error to disk."""
        if not self.persist_path:
            return
        
        try:
            persist_file = Path(self.persist_path)
            persist_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Append to error log file
            with open(persist_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(error.to_dict()) + '\n')
                
        except Exception as e:
            # Don't log errors while logging errors (avoid recursion)
            print(f"Failed to persist error: {e}")
    
    def _load_persisted_errors(self):
        """Load errors from persisted file."""
        if not self.persist_path:
            return
        
        try:
            persist_file = Path(self.persist_path)
            if not persist_file.exists():
                return
            
            with open(persist_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            error_data = json.loads(line)
                            error = SystemError.from_dict(error_data)
                            self.errors.append(error)
                        except Exception as e:
                            print(f"Failed to load persisted error: {e}")
            
            # Maintain size limit
            if len(self.errors) > self.max_errors:
                self.errors = self.errors[-self.max_errors:]
                
        except Exception as e:
            print(f"Failed to load persisted errors: {e}")
    
    def clear_old_errors(self, days: int = 7):
        """Clear errors older than specified days."""
        cutoff = time.time() - (days * 24 * 3600)
        self.errors = [e for e in self.errors if e.timestamp > cutoff]
    
    def export_errors(self, output_file: str, include_resolved: bool = False):
        """Export errors to JSON file."""
        errors_to_export = self.errors if include_resolved else [e for e in self.errors if not e.resolved]
        
        export_data = {
            "exported_at": time.time(),
            "total_errors": len(errors_to_export),
            "errors": [error.to_dict() for error in errors_to_export]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2)