"""
Log Corruption Handling and Sanitization (Task 5.3)

Advanced log corruption detection, sanitization pipeline, and
security validation for diagnosis agent log processing.
"""

import asyncio
import json
import re
import base64
import hashlib
import zlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import chardet
import magic
from collections import defaultdict, deque

from src.utils.logging import get_logger

logger = get_logger(__name__)


class CorruptionType(Enum):
    """Types of log corruption detected."""
    BINARY_DATA = "binary_data"
    MALFORMED_JSON = "malformed_json"
    ENCODING_ERROR = "encoding_error"
    INJECTION_ATTEMPT = "injection_attempt"
    TRUNCATED_LOG = "truncated_log"
    COMPRESSED_DATA = "compressed_data"
    OVERSIZED_ENTRY = "oversized_entry"
    SUSPICIOUS_PATTERN = "suspicious_pattern"
    CONTROL_CHARACTERS = "control_characters"
    NULL_BYTES = "null_bytes"


class SanitizationAction(Enum):
    """Actions taken during sanitization."""
    REMOVED = "removed"
    SANITIZED = "sanitized"
    QUARANTINED = "quarantined"
    TRUNCATED = "truncated"
    DECODED = "decoded"
    DECOMPRESSED = "decompressed"
    ESCAPED = "escaped"


@dataclass
class CorruptionDetection:
    """Details of detected corruption."""
    corruption_type: CorruptionType
    severity: str  # low, medium, high, critical
    location: str  # line number, byte offset, etc.
    description: str
    sample_data: str  # First 100 chars of problematic data
    confidence: float  # 0.0 to 1.0


@dataclass
class SanitizationResult:
    """Result of log sanitization process."""
    original_size: int
    sanitized_size: int
    corruptions_detected: List[CorruptionDetection]
    actions_taken: List[Tuple[SanitizationAction, str]]  # (action, description)
    sanitized_content: str
    quarantined_content: List[str]
    processing_time_ms: float
    safety_score: float  # 0.0 to 1.0, higher is safer


class LogCorruptionHandler:
    """
    Advanced log corruption detection and sanitization system with
    security validation, injection prevention, and graceful recovery.
    """
    
    def __init__(self):
        self.logger = logger
        
        # Configuration
        self.max_log_size = 100 * 1024 * 1024  # 100MB limit
        self.max_line_length = 64 * 1024  # 64KB per line
        self.max_json_depth = 20
        self.suspicious_pattern_threshold = 0.7
        
        # Corruption detection patterns
        self.injection_patterns = [
            # SQL injection patterns
            r'(?i)(union\s+select|drop\s+table|delete\s+from|insert\s+into)',
            # XSS patterns
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            # Command injection patterns
            r'[;&|`$(){}[\]\\]',
            # Path traversal
            r'\.\.[\\/]',
            # LDAP injection
            r'[()&|!]',
        ]
        
        self.suspicious_patterns = [
            # Encoded payloads
            r'%[0-9a-fA-F]{2}',
            # Base64 encoded data (long strings)
            r'[A-Za-z0-9+/]{50,}={0,2}',
            # Hex encoded data
            r'\\x[0-9a-fA-F]{2}',
            # Unicode escapes
            r'\\u[0-9a-fA-F]{4}',
        ]
        
        # Statistics tracking
        self.corruption_stats = defaultdict(int)
        self.sanitization_history = deque(maxlen=1000)
        
        # Quarantine storage
        self.quarantine_storage = []
        
        # Initialize file type detector
        try:
            self.file_magic = magic.Magic(mime=True)
        except Exception:
            self.file_magic = None
            self.logger.warning("python-magic not available, file type detection limited")
    
    async def sanitize_log_content(self, content: Union[str, bytes], 
                                 source_info: Dict[str, Any] = None) -> SanitizationResult:
        """
        Sanitize log content with comprehensive corruption detection and removal.
        
        Args:
            content: Raw log content (string or bytes)
            source_info: Optional metadata about the log source
            
        Returns:
            SanitizationResult with sanitized content and detection details
        """
        start_time = datetime.utcnow()
        
        if source_info is None:
            source_info = {}
        
        # Convert to string if bytes
        if isinstance(content, bytes):
            content, encoding_detection = self._handle_encoding(content)
        else:
            encoding_detection = None
        
        original_size = len(content)
        corruptions_detected = []
        actions_taken = []
        quarantined_content = []
        
        # Size validation
        if original_size > self.max_log_size:
            self.logger.warning(f"Log content exceeds size limit: {original_size} bytes")
            content = content[:self.max_log_size]
            actions_taken.append((SanitizationAction.TRUNCATED, f"Truncated from {original_size} to {self.max_log_size} bytes"))
            corruptions_detected.append(CorruptionDetection(
                corruption_type=CorruptionType.OVERSIZED_ENTRY,
                severity="medium",
                location="entire_content",
                description=f"Content size {original_size} exceeds limit {self.max_log_size}",
                sample_data="[OVERSIZED_CONTENT]",
                confidence=1.0
            ))
        
        # Add encoding detection if applicable
        if encoding_detection:
            corruptions_detected.append(encoding_detection)
            actions_taken.append((SanitizationAction.DECODED, f"Decoded from {encoding_detection.description}"))
        
        # Binary data detection
        binary_detection = self._detect_binary_data(content)
        if binary_detection:
            corruptions_detected.extend(binary_detection)
            content, binary_actions = self._sanitize_binary_data(content)
            actions_taken.extend(binary_actions)
        
        # Control character detection and removal
        control_detection = self._detect_control_characters(content)
        if control_detection:
            corruptions_detected.extend(control_detection)
            content, control_actions = self._sanitize_control_characters(content)
            actions_taken.extend(control_actions)
        
        # Null byte detection and removal
        null_detection = self._detect_null_bytes(content)
        if null_detection:
            corruptions_detected.extend(null_detection)
            content, null_actions = self._sanitize_null_bytes(content)
            actions_taken.extend(null_actions)
        
        # Line-by-line processing
        lines = content.split('\n')
        sanitized_lines = []
        
        for line_num, line in enumerate(lines):
            line_corruptions, sanitized_line, line_actions, quarantined_line = await self._sanitize_line(
                line, line_num, source_info
            )
            
            corruptions_detected.extend(line_corruptions)
            actions_taken.extend(line_actions)
            
            if quarantined_line:
                quarantined_content.append(f"Line {line_num}: {quarantined_line}")
            
            if sanitized_line is not None:
                sanitized_lines.append(sanitized_line)
        
        # Reconstruct content
        sanitized_content = '\n'.join(sanitized_lines)
        
        # Calculate safety score
        safety_score = self._calculate_safety_score(corruptions_detected, original_size, len(sanitized_content))
        
        # Processing time
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Update statistics
        for corruption in corruptions_detected:
            self.corruption_stats[corruption.corruption_type] += 1
        
        result = SanitizationResult(
            original_size=original_size,
            sanitized_size=len(sanitized_content),
            corruptions_detected=corruptions_detected,
            actions_taken=actions_taken,
            sanitized_content=sanitized_content,
            quarantined_content=quarantined_content,
            processing_time_ms=processing_time,
            safety_score=safety_score
        )
        
        # Store in history
        self.sanitization_history.append({
            'timestamp': datetime.utcnow(),
            'source_info': source_info,
            'result_summary': {
                'original_size': original_size,
                'sanitized_size': len(sanitized_content),
                'corruptions_count': len(corruptions_detected),
                'safety_score': safety_score
            }
        })
        
        return result
    
    def _handle_encoding(self, content: bytes) -> Tuple[str, Optional[CorruptionDetection]]:
        """Handle encoding detection and conversion."""
        try:
            # Try UTF-8 first
            return content.decode('utf-8'), None
        except UnicodeDecodeError:
            pass
        
        # Use chardet for detection
        try:
            detected = chardet.detect(content)
            encoding = detected.get('encoding', 'latin-1')
            confidence = detected.get('confidence', 0.0)
            
            decoded_content = content.decode(encoding, errors='replace')
            
            corruption = CorruptionDetection(
                corruption_type=CorruptionType.ENCODING_ERROR,
                severity="low" if confidence > 0.8 else "medium",
                location="entire_content",
                description=f"Non-UTF-8 encoding detected: {encoding} (confidence: {confidence:.2f})",
                sample_data=decoded_content[:100],
                confidence=confidence
            )
            
            return decoded_content, corruption
            
        except Exception as e:
            # Fallback to latin-1 with replacement
            decoded_content = content.decode('latin-1', errors='replace')
            
            corruption = CorruptionDetection(
                corruption_type=CorruptionType.ENCODING_ERROR,
                severity="high",
                location="entire_content",
                description=f"Encoding detection failed: {str(e)}",
                sample_data=decoded_content[:100],
                confidence=0.5
            )
            
            return decoded_content, corruption
    
    def _detect_binary_data(self, content: str) -> List[CorruptionDetection]:
        """Detect binary data in text content."""
        corruptions = []
        
        # Check for high ratio of non-printable characters
        non_printable_count = sum(1 for c in content if ord(c) < 32 and c not in '\t\n\r')
        non_printable_ratio = non_printable_count / len(content) if content else 0
        
        if non_printable_ratio > 0.1:  # More than 10% non-printable
            corruptions.append(CorruptionDetection(
                corruption_type=CorruptionType.BINARY_DATA,
                severity="high",
                location="entire_content",
                description=f"High ratio of non-printable characters: {non_printable_ratio:.2%}",
                sample_data=repr(content[:100]),
                confidence=min(1.0, non_printable_ratio * 2)
            ))
        
        # Check for file magic signatures if available
        if self.file_magic and len(content) > 100:
            try:
                content_bytes = content.encode('latin-1', errors='ignore')
                mime_type = self.file_magic.from_buffer(content_bytes)
                
                if not mime_type.startswith('text/'):
                    corruptions.append(CorruptionDetection(
                        corruption_type=CorruptionType.BINARY_DATA,
                        severity="critical",
                        location="file_header",
                        description=f"Binary file detected: {mime_type}",
                        sample_data=content[:50],
                        confidence=0.9
                    ))
            except Exception:
                pass
        
        return corruptions
    
    def _sanitize_binary_data(self, content: str) -> Tuple[str, List[Tuple[SanitizationAction, str]]]:
        """Remove or encode binary data."""
        actions = []
        
        # Remove non-printable characters except common whitespace
        sanitized = ''.join(c for c in content if ord(c) >= 32 or c in '\t\n\r')
        
        if len(sanitized) != len(content):
            removed_count = len(content) - len(sanitized)
            actions.append((SanitizationAction.SANITIZED, f"Removed {removed_count} non-printable characters"))
        
        return sanitized, actions
    
    def _detect_control_characters(self, content: str) -> List[CorruptionDetection]:
        """Detect problematic control characters."""
        corruptions = []
        
        # Find control characters (excluding common whitespace)
        control_chars = []
        for i, char in enumerate(content):
            if ord(char) < 32 and char not in '\t\n\r':
                control_chars.append((i, char, ord(char)))
        
        if control_chars:
            sample_chars = control_chars[:5]  # First 5 for sample
            sample_data = ', '.join(f"\\x{ord_val:02x}@{pos}" for pos, char, ord_val in sample_chars)
            
            corruptions.append(CorruptionDetection(
                corruption_type=CorruptionType.CONTROL_CHARACTERS,
                severity="medium",
                location=f"positions: {[pos for pos, _, _ in sample_chars]}",
                description=f"Found {len(control_chars)} control characters",
                sample_data=sample_data,
                confidence=0.8
            ))
        
        return corruptions
    
    def _sanitize_control_characters(self, content: str) -> Tuple[str, List[Tuple[SanitizationAction, str]]]:
        """Remove control characters."""
        actions = []
        
        # Remove control characters except tab, newline, carriage return
        sanitized = ''.join(c for c in content if ord(c) >= 32 or c in '\t\n\r')
        
        if len(sanitized) != len(content):
            removed_count = len(content) - len(sanitized)
            actions.append((SanitizationAction.SANITIZED, f"Removed {removed_count} control characters"))
        
        return sanitized, actions
    
    def _detect_null_bytes(self, content: str) -> List[CorruptionDetection]:
        """Detect null bytes in content."""
        corruptions = []
        
        null_positions = [i for i, char in enumerate(content) if char == '\x00']
        
        if null_positions:
            corruptions.append(CorruptionDetection(
                corruption_type=CorruptionType.NULL_BYTES,
                severity="high",
                location=f"positions: {null_positions[:10]}",  # First 10 positions
                description=f"Found {len(null_positions)} null bytes",
                sample_data=f"Null bytes at positions: {null_positions[:5]}",
                confidence=1.0
            ))
        
        return corruptions
    
    def _sanitize_null_bytes(self, content: str) -> Tuple[str, List[Tuple[SanitizationAction, str]]]:
        """Remove null bytes."""
        actions = []
        
        sanitized = content.replace('\x00', '')
        
        if len(sanitized) != len(content):
            removed_count = len(content) - len(sanitized)
            actions.append((SanitizationAction.SANITIZED, f"Removed {removed_count} null bytes"))
        
        return sanitized, actions
    
    async def _sanitize_line(self, line: str, line_num: int, 
                           source_info: Dict[str, Any]) -> Tuple[List[CorruptionDetection], 
                                                               Optional[str], 
                                                               List[Tuple[SanitizationAction, str]], 
                                                               Optional[str]]:
        """Sanitize a single log line."""
        corruptions = []
        actions = []
        quarantined_line = None
        
        # Skip empty lines
        if not line.strip():
            return corruptions, line, actions, quarantined_line
        
        # Line length check
        if len(line) > self.max_line_length:
            corruptions.append(CorruptionDetection(
                corruption_type=CorruptionType.OVERSIZED_ENTRY,
                severity="medium",
                location=f"line_{line_num}",
                description=f"Line length {len(line)} exceeds limit {self.max_line_length}",
                sample_data=line[:100],
                confidence=1.0
            ))
            
            line = line[:self.max_line_length]
            actions.append((SanitizationAction.TRUNCATED, f"Line {line_num} truncated to {self.max_line_length} chars"))
        
        # Injection attempt detection
        injection_detected = self._detect_injection_attempts(line, line_num)
        if injection_detected:
            corruptions.extend(injection_detected)
            # Quarantine suspicious lines
            quarantined_line = line
            actions.append((SanitizationAction.QUARANTINED, f"Line {line_num} quarantined due to injection patterns"))
            return corruptions, None, actions, quarantined_line
        
        # Suspicious pattern detection
        suspicious_detected = self._detect_suspicious_patterns(line, line_num)
        if suspicious_detected:
            corruptions.extend(suspicious_detected)
            # Sanitize but don't quarantine
            line = self._escape_suspicious_content(line)
            actions.append((SanitizationAction.ESCAPED, f"Line {line_num} escaped suspicious patterns"))
        
        # JSON validation and sanitization
        if line.strip().startswith('{') or line.strip().startswith('['):
            json_corruptions, sanitized_json, json_actions = self._sanitize_json_line(line, line_num)
            corruptions.extend(json_corruptions)
            actions.extend(json_actions)
            if sanitized_json is not None:
                line = sanitized_json
        
        # Compressed data detection
        compressed_detection = self._detect_compressed_data(line, line_num)
        if compressed_detection:
            corruptions.extend(compressed_detection)
            decompressed_line, decompress_actions = self._handle_compressed_data(line)
            if decompressed_line:
                line = decompressed_line
                actions.extend(decompress_actions)
        
        return corruptions, line, actions, quarantined_line
    
    def _detect_injection_attempts(self, line: str, line_num: int) -> List[CorruptionDetection]:
        """Detect potential injection attempts."""
        corruptions = []
        
        for pattern in self.injection_patterns:
            matches = re.finditer(pattern, line, re.IGNORECASE)
            for match in matches:
                corruptions.append(CorruptionDetection(
                    corruption_type=CorruptionType.INJECTION_ATTEMPT,
                    severity="critical",
                    location=f"line_{line_num}:pos_{match.start()}",
                    description=f"Potential injection pattern detected: {pattern}",
                    sample_data=match.group()[:50],
                    confidence=0.9
                ))
        
        return corruptions
    
    def _detect_suspicious_patterns(self, line: str, line_num: int) -> List[CorruptionDetection]:
        """Detect suspicious but not necessarily malicious patterns."""
        corruptions = []
        
        suspicious_score = 0
        detected_patterns = []
        
        for pattern in self.suspicious_patterns:
            matches = list(re.finditer(pattern, line))
            if matches:
                suspicious_score += len(matches) * 0.1
                detected_patterns.append((pattern, len(matches)))
        
        if suspicious_score > self.suspicious_pattern_threshold:
            pattern_desc = ', '.join(f"{pattern}({count})" for pattern, count in detected_patterns[:3])
            corruptions.append(CorruptionDetection(
                corruption_type=CorruptionType.SUSPICIOUS_PATTERN,
                severity="medium",
                location=f"line_{line_num}",
                description=f"Suspicious patterns detected: {pattern_desc}",
                sample_data=line[:100],
                confidence=min(1.0, suspicious_score)
            ))
        
        return corruptions
    
    def _escape_suspicious_content(self, line: str) -> str:
        """Escape suspicious content to make it safe."""
        # HTML escape
        line = line.replace('<', '&lt;').replace('>', '&gt;')
        
        # JavaScript escape
        line = line.replace('javascript:', 'javascript_ESCAPED:')
        
        # SQL escape
        line = re.sub(r'(?i)(union\s+select)', r'\1_ESCAPED', line)
        line = re.sub(r'(?i)(drop\s+table)', r'\1_ESCAPED', line)
        
        return line
    
    def _sanitize_json_line(self, line: str, line_num: int) -> Tuple[List[CorruptionDetection], 
                                                                   Optional[str], 
                                                                   List[Tuple[SanitizationAction, str]]]:
        """Sanitize JSON content in log line."""
        corruptions = []
        actions = []
        
        try:
            # Try to parse JSON
            parsed = json.loads(line)
            
            # Check depth
            depth = self._calculate_json_depth(parsed)
            if depth > self.max_json_depth:
                corruptions.append(CorruptionDetection(
                    corruption_type=CorruptionType.MALFORMED_JSON,
                    severity="medium",
                    location=f"line_{line_num}",
                    description=f"JSON depth {depth} exceeds limit {self.max_json_depth}",
                    sample_data=line[:100],
                    confidence=0.8
                ))
                
                # Flatten the JSON
                flattened = self._flatten_json(parsed, self.max_json_depth)
                sanitized_line = json.dumps(flattened, ensure_ascii=True)
                actions.append((SanitizationAction.SANITIZED, f"Line {line_num} JSON flattened from depth {depth}"))
                return corruptions, sanitized_line, actions
            
            # Re-serialize to ensure clean JSON
            sanitized_line = json.dumps(parsed, ensure_ascii=True)
            if sanitized_line != line:
                actions.append((SanitizationAction.SANITIZED, f"Line {line_num} JSON re-serialized"))
            
            return corruptions, sanitized_line, actions
            
        except json.JSONDecodeError as e:
            corruptions.append(CorruptionDetection(
                corruption_type=CorruptionType.MALFORMED_JSON,
                severity="high",
                location=f"line_{line_num}:pos_{e.pos if hasattr(e, 'pos') else 'unknown'}",
                description=f"JSON parse error: {str(e)}",
                sample_data=line[:100],
                confidence=0.9
            ))
            
            # Try to fix common JSON issues
            fixed_line = self._attempt_json_fix(line)
            if fixed_line != line:
                try:
                    json.loads(fixed_line)  # Validate fix
                    actions.append((SanitizationAction.SANITIZED, f"Line {line_num} JSON auto-fixed"))
                    return corruptions, fixed_line, actions
                except json.JSONDecodeError:
                    pass
            
            # If unfixable, escape and return as string
            escaped_line = json.dumps(line, ensure_ascii=True)
            actions.append((SanitizationAction.ESCAPED, f"Line {line_num} JSON escaped as string"))
            return corruptions, escaped_line, actions
    
    def _calculate_json_depth(self, obj: Any, current_depth: int = 0) -> int:
        """Calculate maximum depth of JSON object."""
        if isinstance(obj, dict):
            if not obj:
                return current_depth
            return max(self._calculate_json_depth(v, current_depth + 1) for v in obj.values())
        elif isinstance(obj, list):
            if not obj:
                return current_depth
            return max(self._calculate_json_depth(item, current_depth + 1) for item in obj)
        else:
            return current_depth
    
    def _flatten_json(self, obj: Any, max_depth: int, current_depth: int = 0) -> Any:
        """Flatten JSON object to maximum depth."""
        if current_depth >= max_depth:
            return str(obj)  # Convert to string if too deep
        
        if isinstance(obj, dict):
            return {k: self._flatten_json(v, max_depth, current_depth + 1) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._flatten_json(item, max_depth, current_depth + 1) for item in obj]
        else:
            return obj
    
    def _attempt_json_fix(self, line: str) -> str:
        """Attempt to fix common JSON formatting issues."""
        # Remove trailing commas
        line = re.sub(r',(\s*[}\]])', r'\1', line)
        
        # Fix single quotes to double quotes
        line = re.sub(r"'([^']*)':", r'"\1":', line)
        
        # Fix unquoted keys
        line = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', line)
        
        return line
    
    def _detect_compressed_data(self, line: str, line_num: int) -> List[CorruptionDetection]:
        """Detect compressed data in log line."""
        corruptions = []
        
        # Check for base64 encoded compressed data
        if len(line) > 100:
            try:
                # Try to decode as base64
                decoded = base64.b64decode(line, validate=True)
                
                # Check if it's compressed
                if self._is_compressed_data(decoded):
                    corruptions.append(CorruptionDetection(
                        corruption_type=CorruptionType.COMPRESSED_DATA,
                        severity="medium",
                        location=f"line_{line_num}",
                        description="Base64 encoded compressed data detected",
                        sample_data=line[:50],
                        confidence=0.8
                    ))
            except Exception:
                pass
        
        return corruptions
    
    def _is_compressed_data(self, data: bytes) -> bool:
        """Check if data appears to be compressed."""
        # Check for common compression headers
        if data.startswith(b'\x1f\x8b'):  # gzip
            return True
        if data.startswith(b'PK'):  # zip
            return True
        if data.startswith(b'\x78\x9c') or data.startswith(b'\x78\x01'):  # zlib
            return True
        
        # Check entropy (compressed data has high entropy)
        if len(data) > 100:
            entropy = self._calculate_entropy(data)
            return entropy > 7.5  # High entropy suggests compression
        
        return False
    
    def _calculate_entropy(self, data: bytes) -> float:
        """Calculate Shannon entropy of data."""
        if not data:
            return 0
        
        # Count byte frequencies
        frequencies = defaultdict(int)
        for byte in data:
            frequencies[byte] += 1
        
        # Calculate entropy
        entropy = 0
        length = len(data)
        for count in frequencies.values():
            probability = count / length
            entropy -= probability * (probability.bit_length() - 1)
        
        return entropy
    
    def _handle_compressed_data(self, line: str) -> Tuple[Optional[str], List[Tuple[SanitizationAction, str]]]:
        """Attempt to decompress data."""
        actions = []
        
        try:
            # Try base64 decode first
            decoded = base64.b64decode(line, validate=True)
            
            # Try different decompression methods
            for method_name, decompress_func in [
                ('gzip', lambda d: zlib.decompress(d, 16 + zlib.MAX_WBITS)),
                ('zlib', zlib.decompress),
                ('deflate', lambda d: zlib.decompress(d, -zlib.MAX_WBITS))
            ]:
                try:
                    decompressed = decompress_func(decoded)
                    decompressed_str = decompressed.decode('utf-8', errors='replace')
                    
                    actions.append((SanitizationAction.DECOMPRESSED, f"Decompressed using {method_name}"))
                    return decompressed_str, actions
                except Exception:
                    continue
            
        except Exception:
            pass
        
        return None, actions
    
    def _calculate_safety_score(self, corruptions: List[CorruptionDetection], 
                              original_size: int, sanitized_size: int) -> float:
        """Calculate safety score based on corruptions detected and removed."""
        if not corruptions:
            return 1.0
        
        # Base score reduction for each corruption type
        severity_weights = {
            'low': 0.05,
            'medium': 0.15,
            'high': 0.3,
            'critical': 0.5
        }
        
        score_reduction = 0
        for corruption in corruptions:
            weight = severity_weights.get(corruption.severity, 0.1)
            confidence_factor = corruption.confidence
            score_reduction += weight * confidence_factor
        
        # Additional reduction for significant size changes
        size_change_ratio = abs(original_size - sanitized_size) / original_size if original_size > 0 else 0
        if size_change_ratio > 0.5:  # More than 50% size change
            score_reduction += 0.2
        
        # Ensure score is between 0 and 1
        safety_score = max(0.0, 1.0 - score_reduction)
        return safety_score
    
    def get_corruption_statistics(self) -> Dict[str, Any]:
        """Get corruption detection statistics."""
        total_corruptions = sum(self.corruption_stats.values())
        
        stats = {
            'total_corruptions_detected': total_corruptions,
            'corruption_types': dict(self.corruption_stats),
            'sanitization_history_count': len(self.sanitization_history),
            'quarantine_items': len(self.quarantine_storage)
        }
        
        if self.sanitization_history:
            recent_results = list(self.sanitization_history)[-100:]  # Last 100
            avg_safety_score = sum(r['result_summary']['safety_score'] for r in recent_results) / len(recent_results)
            avg_size_reduction = sum(
                (r['result_summary']['original_size'] - r['result_summary']['sanitized_size']) / 
                r['result_summary']['original_size'] 
                for r in recent_results if r['result_summary']['original_size'] > 0
            ) / len(recent_results)
            
            stats['recent_performance'] = {
                'avg_safety_score': avg_safety_score,
                'avg_size_reduction_ratio': avg_size_reduction
            }
        
        return stats
    
    async def validate_sanitization_effectiveness(self, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate sanitization effectiveness with test cases."""
        results = {
            'total_tests': len(test_cases),
            'passed': 0,
            'failed': 0,
            'test_results': []
        }
        
        for i, test_case in enumerate(test_cases):
            test_content = test_case.get('content', '')
            expected_corruptions = test_case.get('expected_corruptions', [])
            expected_safety_score = test_case.get('expected_safety_score', 0.5)
            
            # Run sanitization
            result = await self.sanitize_log_content(test_content)
            
            # Check if expected corruptions were detected
            detected_types = {c.corruption_type for c in result.corruptions_detected}
            expected_types = set(expected_corruptions)
            
            # Evaluate test
            corruptions_match = expected_types.issubset(detected_types)
            safety_score_ok = result.safety_score >= expected_safety_score
            
            test_passed = corruptions_match and safety_score_ok
            
            if test_passed:
                results['passed'] += 1
            else:
                results['failed'] += 1
            
            results['test_results'].append({
                'test_id': i,
                'passed': test_passed,
                'expected_corruptions': list(expected_types),
                'detected_corruptions': list(detected_types),
                'expected_safety_score': expected_safety_score,
                'actual_safety_score': result.safety_score,
                'corruptions_match': corruptions_match,
                'safety_score_ok': safety_score_ok
            })
        
        results['success_rate'] = results['passed'] / results['total_tests'] if results['total_tests'] > 0 else 0
        
        return results


# Example usage and testing
async def main():
    """Example usage of log corruption handler."""
    handler = LogCorruptionHandler()
    
    # Test cases
    test_logs = [
        # Normal log
        '{"timestamp": "2024-01-01T12:00:00Z", "level": "INFO", "message": "Normal log entry"}',
        
        # Malformed JSON
        '{"timestamp": "2024-01-01T12:00:00Z", "level": "INFO", "message": "Missing quote}',
        
        # Injection attempt
        '{"user_input": "admin\'; DROP TABLE users; --", "action": "login"}',
        
        # Binary data
        '\x00\x01\x02\x03{"message": "log with binary data"}\x04\x05',
        
        # Oversized line
        '{"message": "' + 'A' * 100000 + '"}',
        
        # Compressed data (base64 encoded)
        base64.b64encode(zlib.compress(b'{"message": "compressed log entry"}')).decode(),
    ]
    
    print("Testing log corruption handler...")
    
    for i, log_content in enumerate(test_logs):
        print(f"\nTest {i + 1}: {log_content[:50]}...")
        
        result = await handler.sanitize_log_content(log_content)
        
        print(f"  Corruptions detected: {len(result.corruptions_detected)}")
        for corruption in result.corruptions_detected:
            print(f"    - {corruption.corruption_type.value}: {corruption.description}")
        
        print(f"  Actions taken: {len(result.actions_taken)}")
        for action, description in result.actions_taken:
            print(f"    - {action.value}: {description}")
        
        print(f"  Safety score: {result.safety_score:.3f}")
        print(f"  Size: {result.original_size} -> {result.sanitized_size}")
    
    # Get statistics
    stats = handler.get_corruption_statistics()
    print(f"\nCorruption Statistics:")
    print(f"  Total corruptions: {stats['total_corruptions_detected']}")
    print(f"  By type: {stats['corruption_types']}")


if __name__ == "__main__":
    asyncio.run(main())