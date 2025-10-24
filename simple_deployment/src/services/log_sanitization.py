"""
Corrupted Log Sanitization Pipeline and Anomaly Filters (Task 5.3)

Advanced log processing pipeline with corruption detection, sanitization,
and anomaly filtering for secure and reliable log analysis.
"""

import re
import json
import base64
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import unicodedata
from collections import defaultdict, deque

from src.utils.logging import get_logger
from src.utils.exceptions import ValidationError


logger = get_logger(__name__)


class LogCorruptionType(Enum):
    """Types of log corruption detected."""
    BINARY_DATA = "binary_data"
    MALFORMED_JSON = "malformed_json"
    ENCODING_ERROR = "encoding_error"
    INJECTION_ATTEMPT = "injection_attempt"
    TRUNCATED_ENTRY = "truncated_entry"
    TIMESTAMP_CORRUPTION = "timestamp_corruption"
    CIRCULAR_REFERENCE = "circular_reference"
    OVERSIZED_ENTRY = "oversized_entry"


class LogAnomalyType(Enum):
    """Types of log anomalies detected."""
    FREQUENCY_SPIKE = "frequency_spike"
    UNUSUAL_PATTERN = "unusual_pattern"
    SUSPICIOUS_CONTENT = "suspicious_content"
    SIZE_ANOMALY = "size_anomaly"
    TIMING_ANOMALY = "timing_anomaly"
    SOURCE_ANOMALY = "source_anomaly"


@dataclass
class LogEntry:
    """Structured log entry after processing."""
    timestamp: datetime
    level: str
    message: str
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    original_size: int = 0
    sanitized: bool = False
    corruption_detected: List[LogCorruptionType] = field(default_factory=list)
    anomalies_detected: List[LogAnomalyType] = field(default_factory=list)


@dataclass
class SanitizationResult:
    """Result of log sanitization process."""
    original_entry: str
    sanitized_entry: Optional[LogEntry]
    corruptions_found: List[LogCorruptionType]
    anomalies_found: List[LogAnomalyType]
    sanitization_applied: List[str]
    rejected: bool = False
    rejection_reason: Optional[str] = None


class LogSanitizationPipeline:
    """
    Advanced log sanitization pipeline with corruption detection,
    sanitization, and anomaly filtering capabilities.
    """
    
    def __init__(self):
        self.logger = logger
        
        # Sanitization configuration
        self.max_log_size = 10 * 1024 * 1024  # 10MB max per log entry
        self.max_message_length = 50000  # 50K characters max
        self.encoding_whitelist = ['utf-8', 'ascii', 'latin-1']
        
        # Injection patterns
        self.injection_patterns = {
            'sql_injection': [
                r'(\bUNION\b.*\bSELECT\b)',
                r'(\bDROP\b.*\bTABLE\b)',
                r'(\bINSERT\b.*\bINTO\b)',
                r'(\bDELETE\b.*\bFROM\b)',
                r'(\'.*OR.*\'.*=.*\')',
                r'(--.*$)',
                r'(/\*.*\*/)'
            ],
            'xss_injection': [
                r'(<script[^>]*>.*?</script>)',
                r'(<iframe[^>]*>.*?</iframe>)',
                r'(javascript:)',
                r'(on\w+\s*=)',
                r'(<img[^>]*onerror[^>]*>)'
            ],
            'command_injection': [
                r'(\$\(.*\))',
                r'(`.*`)',
                r'(;.*rm\s+-rf)',
                r'(&&.*rm\s+-rf)',
                r'(\|\|.*rm\s+-rf)',
                r'(>\s*/dev/null)',
                r'(curl.*\|.*sh)'
            ],
            'path_traversal': [
                r'(\.\.\/)',
                r'(\.\.\\)',
                r'(%2e%2e%2f)',
                r'(%2e%2e%5c)',
                r'(\/etc\/passwd)',
                r'(\/etc\/shadow)',
                r'(C:\\Windows\\System32)'
            ]
        }
        
        # Anomaly detection state
        self.log_frequency_history = deque(maxlen=1000)
        self.pattern_frequency = defaultdict(int)
        self.source_frequency = defaultdict(int)
        self.size_history = deque(maxlen=100)
        
        # Sanitization statistics
        self.sanitization_stats = {
            'total_processed': 0,
            'corruptions_detected': defaultdict(int),
            'anomalies_detected': defaultdict(int),
            'entries_rejected': 0,
            'entries_sanitized': 0
        }
    
    async def process_log_batch(self, log_entries: List[str]) -> List[SanitizationResult]:
        """Process a batch of log entries through the sanitization pipeline."""
        results = []
        
        for entry in log_entries:
            try:
                result = await self.sanitize_log_entry(entry)
                results.append(result)
                
                # Update statistics
                self._update_statistics(result)
                
            except Exception as e:
                self.logger.error(f"Error processing log entry: {e}")
                results.append(SanitizationResult(
                    original_entry=entry[:100] + "..." if len(entry) > 100 else entry,
                    sanitized_entry=None,
                    corruptions_found=[LogCorruptionType.ENCODING_ERROR],
                    anomalies_found=[],
                    sanitization_applied=[],
                    rejected=True,
                    rejection_reason=f"Processing error: {str(e)}"
                ))
        
        return results
    
    async def sanitize_log_entry(self, raw_entry: str) -> SanitizationResult:
        """Sanitize a single log entry."""
        corruptions_found = []
        anomalies_found = []
        sanitization_applied = []
        
        # Step 1: Basic validation and corruption detection
        corruption_check = self._detect_corruption(raw_entry)
        corruptions_found.extend(corruption_check)
        
        # Step 2: Size validation
        if len(raw_entry) > self.max_log_size:
            corruptions_found.append(LogCorruptionType.OVERSIZED_ENTRY)
            return SanitizationResult(
                original_entry=raw_entry[:100] + "...",
                sanitized_entry=None,
                corruptions_found=corruptions_found,
                anomalies_found=anomalies_found,
                sanitization_applied=sanitization_applied,
                rejected=True,
                rejection_reason="Entry exceeds maximum size limit"
            )
        
        # Step 3: Encoding sanitization
        sanitized_text, encoding_applied = self._sanitize_encoding(raw_entry)
        if encoding_applied:
            sanitization_applied.append("encoding_sanitization")
        
        # Step 4: Injection detection and sanitization
        injection_sanitized, injection_applied = self._sanitize_injections(sanitized_text)
        if injection_applied:
            sanitization_applied.extend(injection_applied)
            corruptions_found.append(LogCorruptionType.INJECTION_ATTEMPT)
        
        # Step 5: JSON structure validation and repair
        structured_entry, json_applied = self._sanitize_json_structure(injection_sanitized)
        if json_applied:
            sanitization_applied.append("json_structure_repair")
        
        # Step 6: Parse into structured log entry
        try:
            log_entry = self._parse_log_entry(structured_entry)
            log_entry.original_size = len(raw_entry)
            log_entry.sanitized = len(sanitization_applied) > 0
            log_entry.corruption_detected = corruptions_found
            
        except Exception as e:
            return SanitizationResult(
                original_entry=raw_entry[:100] + "...",
                sanitized_entry=None,
                corruptions_found=corruptions_found,
                anomalies_found=anomalies_found,
                sanitization_applied=sanitization_applied,
                rejected=True,
                rejection_reason=f"Failed to parse log entry: {str(e)}"
            )
        
        # Step 7: Anomaly detection
        anomalies_found = self._detect_anomalies(log_entry)
        log_entry.anomalies_detected = anomalies_found
        
        # Step 8: Final validation
        if self._should_reject_entry(log_entry, corruptions_found, anomalies_found):
            return SanitizationResult(
                original_entry=raw_entry[:100] + "...",
                sanitized_entry=None,
                corruptions_found=corruptions_found,
                anomalies_found=anomalies_found,
                sanitization_applied=sanitization_applied,
                rejected=True,
                rejection_reason="Entry rejected due to security concerns"
            )
        
        return SanitizationResult(
            original_entry=raw_entry,
            sanitized_entry=log_entry,
            corruptions_found=corruptions_found,
            anomalies_found=anomalies_found,
            sanitization_applied=sanitization_applied,
            rejected=False
        )
    
    def _detect_corruption(self, entry: str) -> List[LogCorruptionType]:
        """Detect various types of corruption in log entry."""
        corruptions = []
        
        # Binary data detection
        if self._contains_binary_data(entry):
            corruptions.append(LogCorruptionType.BINARY_DATA)
        
        # Encoding error detection
        try:
            entry.encode('utf-8').decode('utf-8')
        except UnicodeError:
            corruptions.append(LogCorruptionType.ENCODING_ERROR)
        
        # Malformed JSON detection (if entry looks like JSON)
        if entry.strip().startswith('{') and not self._is_valid_json(entry):
            corruptions.append(LogCorruptionType.MALFORMED_JSON)
        
        # Truncated entry detection
        if self._is_truncated_entry(entry):
            corruptions.append(LogCorruptionType.TRUNCATED_ENTRY)
        
        # Timestamp corruption detection
        if not self._has_valid_timestamp(entry):
            corruptions.append(LogCorruptionType.TIMESTAMP_CORRUPTION)
        
        return corruptions
    
    def _contains_binary_data(self, text: str) -> bool:
        """Check if text contains binary data."""
        # Check for null bytes
        if '\x00' in text:
            return True
        
        # Check for high ratio of non-printable characters
        printable_chars = sum(1 for c in text if c.isprintable() or c.isspace())
        if len(text) > 0 and (printable_chars / len(text)) < 0.8:
            return True
        
        # Check for common binary file signatures
        binary_signatures = [b'\x89PNG', b'\xFF\xD8\xFF', b'PK\x03\x04', b'\x50\x4B']
        text_bytes = text.encode('utf-8', errors='ignore')
        for sig in binary_signatures:
            if sig in text_bytes:
                return True
        
        return False
    
    def _is_valid_json(self, text: str) -> bool:
        """Check if text is valid JSON."""
        try:
            json.loads(text)
            return True
        except (json.JSONDecodeError, ValueError):
            return False
    
    def _is_truncated_entry(self, entry: str) -> bool:
        """Detect if log entry appears to be truncated."""
        # Check for incomplete JSON structures
        if entry.count('{') != entry.count('}'):
            return True
        if entry.count('[') != entry.count(']'):
            return True
        if entry.count('"') % 2 != 0:
            return True
        
        # Check for abrupt endings
        if entry.endswith('...') or entry.endswith('…'):
            return True
        
        return False
    
    def _has_valid_timestamp(self, entry: str) -> bool:
        """Check if entry has a valid timestamp."""
        # Common timestamp patterns
        timestamp_patterns = [
            r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}',  # ISO format
            r'\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}',      # US format
            r'\d{10,13}',                                  # Unix timestamp
            r'\w{3} \w{3} \d{2} \d{2}:\d{2}:\d{2}'        # Syslog format
        ]
        
        for pattern in timestamp_patterns:
            if re.search(pattern, entry):
                return True
        
        return False
    
    def _sanitize_encoding(self, text: str) -> Tuple[str, bool]:
        """Sanitize text encoding issues."""
        applied = False
        
        try:
            # Try to decode and re-encode to fix encoding issues
            if isinstance(text, bytes):
                # Try different encodings
                for encoding in self.encoding_whitelist:
                    try:
                        decoded = text.decode(encoding)
                        applied = True
                        return decoded, applied
                    except UnicodeDecodeError:
                        continue
                
                # Fallback: decode with errors='replace'
                text = text.decode('utf-8', errors='replace')
                applied = True
            
            # Normalize unicode characters
            normalized = unicodedata.normalize('NFKC', text)
            if normalized != text:
                applied = True
                text = normalized
            
            # Remove or replace problematic characters
            # Remove null bytes
            if '\x00' in text:
                text = text.replace('\x00', '')
                applied = True
            
            # Replace other control characters (except common ones like \n, \t)
            control_chars = ''.join(chr(i) for i in range(32) if i not in [9, 10, 13])
            for char in control_chars:
                if char in text:
                    text = text.replace(char, '')
                    applied = True
            
        except Exception as e:
            self.logger.warning(f"Encoding sanitization error: {e}")
        
        return text, applied
    
    def _sanitize_injections(self, text: str) -> Tuple[str, List[str]]:
        """Detect and sanitize injection attempts."""
        applied = []
        sanitized_text = text
        
        for injection_type, patterns in self.injection_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, sanitized_text, re.IGNORECASE | re.MULTILINE)
                if matches:
                    # Replace with sanitized version
                    sanitized_text = re.sub(pattern, '[SANITIZED_INJECTION]', sanitized_text, flags=re.IGNORECASE | re.MULTILINE)
                    applied.append(f"{injection_type}_sanitization")
                    self.logger.warning(f"Detected and sanitized {injection_type}: {matches}")
        
        return sanitized_text, applied
    
    def _sanitize_json_structure(self, text: str) -> Tuple[str, bool]:
        """Attempt to repair malformed JSON structures."""
        applied = False
        
        if not text.strip().startswith('{') and not text.strip().startswith('['):
            return text, applied
        
        try:
            # Try to parse as-is first
            json.loads(text)
            return text, applied
        except json.JSONDecodeError:
            pass
        
        # Attempt basic JSON repairs
        repaired = text
        
        # Fix common JSON issues
        # Remove trailing commas
        repaired = re.sub(r',(\s*[}\]])', r'\1', repaired)
        
        # Fix unquoted keys
        repaired = re.sub(r'(\w+):', r'"\1":', repaired)
        
        # Fix single quotes to double quotes
        repaired = repaired.replace("'", '"')
        
        # Try to balance braces
        open_braces = repaired.count('{')
        close_braces = repaired.count('}')
        if open_braces > close_braces:
            repaired += '}' * (open_braces - close_braces)
            applied = True
        elif close_braces > open_braces:
            repaired = '{' * (close_braces - open_braces) + repaired
            applied = True
        
        # Try to balance brackets
        open_brackets = repaired.count('[')
        close_brackets = repaired.count(']')
        if open_brackets > close_brackets:
            repaired += ']' * (open_brackets - close_brackets)
            applied = True
        elif close_brackets > open_brackets:
            repaired = '[' * (close_brackets - open_brackets) + repaired
            applied = True
        
        # Validate repaired JSON
        try:
            json.loads(repaired)
            return repaired, applied
        except json.JSONDecodeError:
            # If repair failed, return original
            return text, False
    
    def _parse_log_entry(self, text: str) -> LogEntry:
        """Parse sanitized text into structured log entry."""
        # Try to parse as JSON first
        if text.strip().startswith('{'):
            try:
                data = json.loads(text)
                return LogEntry(
                    timestamp=self._parse_timestamp(data.get('timestamp', data.get('time', datetime.utcnow().isoformat()))),
                    level=data.get('level', data.get('severity', 'INFO')),
                    message=data.get('message', data.get('msg', str(data))),
                    source=data.get('source', data.get('logger', 'unknown')),
                    metadata={k: v for k, v in data.items() if k not in ['timestamp', 'time', 'level', 'severity', 'message', 'msg', 'source', 'logger']}
                )
            except (json.JSONDecodeError, ValueError):
                pass
        
        # Parse as structured text log
        timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2})', text)
        level_match = re.search(r'\b(DEBUG|INFO|WARN|WARNING|ERROR|FATAL|CRITICAL)\b', text, re.IGNORECASE)
        
        timestamp = self._parse_timestamp(timestamp_match.group(1) if timestamp_match else datetime.utcnow().isoformat())
        level = level_match.group(1).upper() if level_match else 'INFO'
        
        # Extract message (everything after timestamp and level)
        message = text
        if timestamp_match:
            message = text[timestamp_match.end():].strip()
        if level_match and level_match.start() < len(message):
            message = message[level_match.end():].strip()
        
        return LogEntry(
            timestamp=timestamp,
            level=level,
            message=message[:self.max_message_length],  # Truncate if too long
            source='parsed',
            metadata={}
        )
    
    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse timestamp from various formats."""
        timestamp_formats = [
            '%Y-%m-%dT%H:%M:%S.%fZ',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%d %H:%M:%S.%f',
            '%Y-%m-%d %H:%M:%S',
            '%m/%d/%Y %H:%M:%S',
            '%d/%m/%Y %H:%M:%S'
        ]
        
        for fmt in timestamp_formats:
            try:
                return datetime.strptime(timestamp_str, fmt)
            except ValueError:
                continue
        
        # Try unix timestamp
        try:
            timestamp_float = float(timestamp_str)
            if timestamp_float > 1000000000:  # Reasonable unix timestamp
                return datetime.fromtimestamp(timestamp_float)
        except (ValueError, OSError):
            pass
        
        # Fallback to current time
        return datetime.utcnow()
    
    def _detect_anomalies(self, log_entry: LogEntry) -> List[LogAnomalyType]:
        """Detect anomalies in the log entry."""
        anomalies = []
        
        # Frequency spike detection
        current_time = datetime.utcnow()
        self.log_frequency_history.append(current_time)
        
        # Check for frequency spikes (more than 100 logs per minute)
        recent_logs = [t for t in self.log_frequency_history if (current_time - t).total_seconds() < 60]
        if len(recent_logs) > 100:
            anomalies.append(LogAnomalyType.FREQUENCY_SPIKE)
        
        # Size anomaly detection
        self.size_history.append(log_entry.original_size)
        if len(self.size_history) >= 10:
            avg_size = sum(self.size_history) / len(self.size_history)
            if log_entry.original_size > avg_size * 5:  # 5x larger than average
                anomalies.append(LogAnomalyType.SIZE_ANOMALY)
        
        # Suspicious content detection
        suspicious_keywords = [
            'password', 'secret', 'token', 'key', 'credential',
            'exploit', 'vulnerability', 'attack', 'malware',
            'unauthorized', 'breach', 'compromise'
        ]
        
        message_lower = log_entry.message.lower()
        for keyword in suspicious_keywords:
            if keyword in message_lower:
                anomalies.append(LogAnomalyType.SUSPICIOUS_CONTENT)
                break
        
        # Pattern frequency analysis
        message_pattern = self._extract_pattern(log_entry.message)
        self.pattern_frequency[message_pattern] += 1
        
        # Unusual pattern detection (very rare patterns)
        total_patterns = sum(self.pattern_frequency.values())
        if total_patterns > 100 and self.pattern_frequency[message_pattern] == 1:
            anomalies.append(LogAnomalyType.UNUSUAL_PATTERN)
        
        # Source anomaly detection
        self.source_frequency[log_entry.source] += 1
        if self.source_frequency[log_entry.source] == 1 and len(self.source_frequency) > 10:
            anomalies.append(LogAnomalyType.SOURCE_ANOMALY)
        
        # Timing anomaly detection (logs from future or very old)
        time_diff = abs((current_time - log_entry.timestamp).total_seconds())
        if time_diff > 86400:  # More than 24 hours difference
            anomalies.append(LogAnomalyType.TIMING_ANOMALY)
        
        return anomalies
    
    def _extract_pattern(self, message: str) -> str:
        """Extract a pattern from log message for frequency analysis."""
        # Replace numbers with placeholder
        pattern = re.sub(r'\d+', 'NUM', message)
        
        # Replace common variable parts
        pattern = re.sub(r'\b[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\b', 'UUID', pattern)
        pattern = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', 'IP', pattern)
        pattern = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 'EMAIL', pattern)
        
        # Truncate to reasonable length
        return pattern[:100]
    
    def _should_reject_entry(self, log_entry: LogEntry, corruptions: List[LogCorruptionType], 
                           anomalies: List[LogAnomalyType]) -> bool:
        """Determine if log entry should be rejected."""
        # Reject if critical corruptions detected
        critical_corruptions = [
            LogCorruptionType.BINARY_DATA,
            LogCorruptionType.INJECTION_ATTEMPT,
            LogCorruptionType.OVERSIZED_ENTRY
        ]
        
        if any(corruption in corruptions for corruption in critical_corruptions):
            return True
        
        # Reject if multiple severe anomalies
        severe_anomalies = [
            LogAnomalyType.SUSPICIOUS_CONTENT,
            LogAnomalyType.FREQUENCY_SPIKE
        ]
        
        severe_count = sum(1 for anomaly in anomalies if anomaly in severe_anomalies)
        if severe_count >= 2:
            return True
        
        return False
    
    def _update_statistics(self, result: SanitizationResult):
        """Update sanitization statistics."""
        self.sanitization_stats['total_processed'] += 1
        
        for corruption in result.corruptions_found:
            self.sanitization_stats['corruptions_detected'][corruption] += 1
        
        for anomaly in result.anomalies_found:
            self.sanitization_stats['anomalies_detected'][anomaly] += 1
        
        if result.rejected:
            self.sanitization_stats['entries_rejected'] += 1
        elif result.sanitization_applied:
            self.sanitization_stats['entries_sanitized'] += 1
    
    def get_sanitization_report(self) -> Dict[str, Any]:
        """Generate comprehensive sanitization report."""
        total = self.sanitization_stats['total_processed']
        
        return {
            "total_processed": total,
            "entries_sanitized": self.sanitization_stats['entries_sanitized'],
            "entries_rejected": self.sanitization_stats['entries_rejected'],
            "sanitization_rate": self.sanitization_stats['entries_sanitized'] / total if total > 0 else 0,
            "rejection_rate": self.sanitization_stats['entries_rejected'] / total if total > 0 else 0,
            "corruptions_by_type": dict(self.sanitization_stats['corruptions_detected']),
            "anomalies_by_type": dict(self.sanitization_stats['anomalies_detected']),
            "most_common_corruption": max(self.sanitization_stats['corruptions_detected'].items(), 
                                        key=lambda x: x[1], default=(None, 0))[0],
            "most_common_anomaly": max(self.sanitization_stats['anomalies_detected'].items(), 
                                     key=lambda x: x[1], default=(None, 0))[0],
            "pattern_diversity": len(self.pattern_frequency),
            "source_diversity": len(self.source_frequency)
        }