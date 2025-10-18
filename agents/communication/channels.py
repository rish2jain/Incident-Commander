"""
Notification Channels

Manages different notification channels with rate limiting and deduplication.
"""

import asyncio
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from enum import Enum

from src.utils.logging import get_logger
from src.utils.constants import SHARED_RETRY_POLICIES
from .templates import RenderedMessage, NotificationChannel

logger = get_logger(__name__)


class DeliveryStatus(Enum):
    """Status of message delivery"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    RATE_LIMITED = "rate_limited"
    DEDUPLICATED = "deduplicated"


@dataclass
class DeliveryResult:
    """Result of message delivery attempt"""
    message_id: str
    status: DeliveryStatus
    channel: NotificationChannel
    recipients: List[str]
    sent_at: datetime
    error_message: Optional[str] = None
    retry_count: int = 0
    next_retry_at: Optional[datetime] = None


@dataclass
class ChannelConfig:
    """Configuration for a notification channel"""
    channel: NotificationChannel
    enabled: bool
    rate_limit_per_second: float
    rate_limit_per_minute: float
    max_retries: int
    retry_delay_seconds: int
    deduplication_window_minutes: int
    priority_bypass: bool = False  # Allow high priority to bypass rate limits


class NotificationChannelManager:
    """Manages notification channels with rate limiting and deduplication"""
    
    def __init__(self):
        self.channel_configs = self._initialize_channel_configs()
        self.rate_limiters = {}
        self.delivery_history = []
        self.deduplication_cache = {}  # message_hash -> last_sent_time
        self.pending_messages = {}
        
        # Initialize rate limiters for each channel
        for channel in NotificationChannel:
            self.rate_limiters[channel] = RateLimiter(
                self.channel_configs[channel].rate_limit_per_second,
                self.channel_configs[channel].rate_limit_per_minute
            )
    
    def _initialize_channel_configs(self) -> Dict[NotificationChannel, ChannelConfig]:
        """Initialize channel configurations with rate limits from shared constants"""
        return {
            NotificationChannel.SLACK: ChannelConfig(
                channel=NotificationChannel.SLACK,
                enabled=True,
                rate_limit_per_second=1.0,  # 1 message per second
                rate_limit_per_minute=30.0,  # 30 messages per minute
                max_retries=3,
                retry_delay_seconds=5,
                deduplication_window_minutes=5,
                priority_bypass=True
            ),
            NotificationChannel.EMAIL: ChannelConfig(
                channel=NotificationChannel.EMAIL,
                enabled=True,
                rate_limit_per_second=10.0,  # 10 emails per second
                rate_limit_per_minute=100.0,  # 100 emails per minute
                max_retries=3,
                retry_delay_seconds=10,
                deduplication_window_minutes=10
            ),
            NotificationChannel.PAGERDUTY: ChannelConfig(
                channel=NotificationChannel.PAGERDUTY,
                enabled=True,
                rate_limit_per_second=0.5,  # 1 message per 2 seconds
                rate_limit_per_minute=2.0,  # 2 messages per minute
                max_retries=5,
                retry_delay_seconds=30,
                deduplication_window_minutes=15,
                priority_bypass=True
            ),
            NotificationChannel.SMS: ChannelConfig(
                channel=NotificationChannel.SMS,
                enabled=True,
                rate_limit_per_second=0.2,  # 1 message per 5 seconds
                rate_limit_per_minute=5.0,  # 5 messages per minute
                max_retries=3,
                retry_delay_seconds=60,
                deduplication_window_minutes=30
            ),
            NotificationChannel.WEBHOOK: ChannelConfig(
                channel=NotificationChannel.WEBHOOK,
                enabled=True,
                rate_limit_per_second=5.0,  # 5 webhooks per second
                rate_limit_per_minute=100.0,  # 100 webhooks per minute
                max_retries=3,
                retry_delay_seconds=5,
                deduplication_window_minutes=2
            )
        }
    
    async def send_message(self, message: RenderedMessage) -> DeliveryResult:
        """
        Send a message through the appropriate channel
        
        Args:
            message: Rendered message to send
            
        Returns:
            Delivery result
        """
        try:
            message_id = self._generate_message_id(message)
            
            logger.info(f"Sending message {message_id} via {message.channel.value}")
            
            # Check if channel is enabled
            config = self.channel_configs[message.channel]
            if not config.enabled:
                return DeliveryResult(
                    message_id=message_id,
                    status=DeliveryStatus.FAILED,
                    channel=message.channel,
                    recipients=message.recipients,
                    sent_at=datetime.utcnow(),
                    error_message=f"Channel {message.channel.value} is disabled"
                )
            
            # Check for deduplication
            if await self._is_duplicate_message(message, config):
                return DeliveryResult(
                    message_id=message_id,
                    status=DeliveryStatus.DEDUPLICATED,
                    channel=message.channel,
                    recipients=message.recipients,
                    sent_at=datetime.utcnow(),
                    error_message="Message deduplicated"
                )
            
            # Check rate limits
            rate_limiter = self.rate_limiters[message.channel]
            can_send = await rate_limiter.can_send(
                priority_bypass=config.priority_bypass and message.priority == "critical"
            )
            
            if not can_send:
                # Schedule for retry
                next_retry = datetime.utcnow() + timedelta(seconds=config.retry_delay_seconds)
                return DeliveryResult(
                    message_id=message_id,
                    status=DeliveryStatus.RATE_LIMITED,
                    channel=message.channel,
                    recipients=message.recipients,
                    sent_at=datetime.utcnow(),
                    error_message="Rate limit exceeded",
                    next_retry_at=next_retry
                )
            
            # Send the message
            result = await self._send_via_channel(message, message_id, config)
            
            # Update deduplication cache
            await self._update_deduplication_cache(message)
            
            # Record delivery
            self.delivery_history.append(result)
            
            # Limit history size
            if len(self.delivery_history) > 1000:
                self.delivery_history = self.delivery_history[-500:]
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return DeliveryResult(
                message_id=self._generate_message_id(message),
                status=DeliveryStatus.FAILED,
                channel=message.channel,
                recipients=message.recipients,
                sent_at=datetime.utcnow(),
                error_message=str(e)
            )
    
    async def _send_via_channel(
        self, 
        message: RenderedMessage, 
        message_id: str, 
        config: ChannelConfig
    ) -> DeliveryResult:
        """Send message via specific channel"""
        try:
            if message.channel == NotificationChannel.SLACK:
                return await self._send_slack_message(message, message_id)
            elif message.channel == NotificationChannel.EMAIL:
                return await self._send_email_message(message, message_id)
            elif message.channel == NotificationChannel.PAGERDUTY:
                return await self._send_pagerduty_message(message, message_id)
            elif message.channel == NotificationChannel.SMS:
                return await self._send_sms_message(message, message_id)
            elif message.channel == NotificationChannel.WEBHOOK:
                return await self._send_webhook_message(message, message_id)
            else:
                return DeliveryResult(
                    message_id=message_id,
                    status=DeliveryStatus.FAILED,
                    channel=message.channel,
                    recipients=message.recipients,
                    sent_at=datetime.utcnow(),
                    error_message=f"Unsupported channel: {message.channel.value}"
                )
                
        except Exception as e:
            logger.error(f"Error sending via {message.channel.value}: {e}")
            return DeliveryResult(
                message_id=message_id,
                status=DeliveryStatus.FAILED,
                channel=message.channel,
                recipients=message.recipients,
                sent_at=datetime.utcnow(),
                error_message=str(e)
            )
    
    async def _send_slack_message(self, message: RenderedMessage, message_id: str) -> DeliveryResult:
        """Send message via Slack"""
        try:
            # Simulate Slack API call
            await asyncio.sleep(0.1)  # Simulate network delay
            
            # In a real implementation, this would use the Slack SDK
            logger.info(f"Sent Slack message {message_id} to {len(message.recipients)} recipients")
            
            return DeliveryResult(
                message_id=message_id,
                status=DeliveryStatus.SENT,
                channel=message.channel,
                recipients=message.recipients,
                sent_at=datetime.utcnow()
            )
            
        except Exception as e:
            return DeliveryResult(
                message_id=message_id,
                status=DeliveryStatus.FAILED,
                channel=message.channel,
                recipients=message.recipients,
                sent_at=datetime.utcnow(),
                error_message=str(e)
            )
    
    async def _send_email_message(self, message: RenderedMessage, message_id: str) -> DeliveryResult:
        """Send message via email"""
        try:
            # Simulate email sending
            await asyncio.sleep(0.2)  # Simulate SMTP delay
            
            # In a real implementation, this would use an email service
            logger.info(f"Sent email {message_id} to {len(message.recipients)} recipients")
            
            return DeliveryResult(
                message_id=message_id,
                status=DeliveryStatus.SENT,
                channel=message.channel,
                recipients=message.recipients,
                sent_at=datetime.utcnow()
            )
            
        except Exception as e:
            return DeliveryResult(
                message_id=message_id,
                status=DeliveryStatus.FAILED,
                channel=message.channel,
                recipients=message.recipients,
                sent_at=datetime.utcnow(),
                error_message=str(e)
            )
    
    async def _send_pagerduty_message(self, message: RenderedMessage, message_id: str) -> DeliveryResult:
        """Send message via PagerDuty"""
        try:
            # Simulate PagerDuty API call
            await asyncio.sleep(0.3)  # Simulate API delay
            
            # In a real implementation, this would use the PagerDuty API
            logger.info(f"Sent PagerDuty alert {message_id} to {len(message.recipients)} recipients")
            
            return DeliveryResult(
                message_id=message_id,
                status=DeliveryStatus.SENT,
                channel=message.channel,
                recipients=message.recipients,
                sent_at=datetime.utcnow()
            )
            
        except Exception as e:
            return DeliveryResult(
                message_id=message_id,
                status=DeliveryStatus.FAILED,
                channel=message.channel,
                recipients=message.recipients,
                sent_at=datetime.utcnow(),
                error_message=str(e)
            )
    
    async def _send_sms_message(self, message: RenderedMessage, message_id: str) -> DeliveryResult:
        """Send message via SMS"""
        try:
            # Simulate SMS sending
            await asyncio.sleep(0.5)  # Simulate SMS gateway delay
            
            # In a real implementation, this would use an SMS service
            logger.info(f"Sent SMS {message_id} to {len(message.recipients)} recipients")
            
            return DeliveryResult(
                message_id=message_id,
                status=DeliveryStatus.SENT,
                channel=message.channel,
                recipients=message.recipients,
                sent_at=datetime.utcnow()
            )
            
        except Exception as e:
            return DeliveryResult(
                message_id=message_id,
                status=DeliveryStatus.FAILED,
                channel=message.channel,
                recipients=message.recipients,
                sent_at=datetime.utcnow(),
                error_message=str(e)
            )
    
    async def _send_webhook_message(self, message: RenderedMessage, message_id: str) -> DeliveryResult:
        """Send message via webhook"""
        try:
            # Simulate webhook call
            await asyncio.sleep(0.1)  # Simulate HTTP request
            
            # In a real implementation, this would make HTTP requests
            logger.info(f"Sent webhook {message_id} to {len(message.recipients)} endpoints")
            
            return DeliveryResult(
                message_id=message_id,
                status=DeliveryStatus.SENT,
                channel=message.channel,
                recipients=message.recipients,
                sent_at=datetime.utcnow()
            )
            
        except Exception as e:
            return DeliveryResult(
                message_id=message_id,
                status=DeliveryStatus.FAILED,
                channel=message.channel,
                recipients=message.recipients,
                sent_at=datetime.utcnow(),
                error_message=str(e)
            )
    
    def _generate_message_id(self, message: RenderedMessage) -> str:
        """Generate unique message ID"""
        content = f"{message.channel.value}_{message.subject}_{datetime.utcnow().isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    async def _is_duplicate_message(self, message: RenderedMessage, config: ChannelConfig) -> bool:
        """Check if message is a duplicate within the deduplication window"""
        try:
            # Create message hash for deduplication
            message_hash = self._create_message_hash(message)
            
            # Check if we've seen this message recently
            if message_hash in self.deduplication_cache:
                last_sent = self.deduplication_cache[message_hash]
                time_since_last = datetime.utcnow() - last_sent
                
                if time_since_last < timedelta(minutes=config.deduplication_window_minutes):
                    logger.info(f"Duplicate message detected, last sent {time_since_last} ago")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking for duplicate message: {e}")
            return False
    
    def _create_message_hash(self, message: RenderedMessage) -> str:
        """Create hash for message deduplication"""
        # Hash based on channel, subject, and recipients
        content = f"{message.channel.value}_{message.subject}_{'_'.join(sorted(message.recipients))}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    async def _update_deduplication_cache(self, message: RenderedMessage):
        """Update deduplication cache with sent message"""
        try:
            message_hash = self._create_message_hash(message)
            self.deduplication_cache[message_hash] = datetime.utcnow()
            
            # Clean up old entries (older than 1 hour)
            cutoff_time = datetime.utcnow() - timedelta(hours=1)
            expired_hashes = [
                h for h, t in self.deduplication_cache.items()
                if t < cutoff_time
            ]
            
            for hash_key in expired_hashes:
                del self.deduplication_cache[hash_key]
                
        except Exception as e:
            logger.error(f"Error updating deduplication cache: {e}")
    
    async def batch_send_messages(self, messages: List[RenderedMessage]) -> List[DeliveryResult]:
        """Send multiple messages with intelligent batching"""
        try:
            results = []
            
            # Group messages by channel for efficient processing
            messages_by_channel = {}
            for message in messages:
                channel = message.channel
                if channel not in messages_by_channel:
                    messages_by_channel[channel] = []
                messages_by_channel[channel].append(message)
            
            # Send messages for each channel
            for channel, channel_messages in messages_by_channel.items():
                config = self.channel_configs[channel]
                
                # Send messages with appropriate delays for rate limiting
                for i, message in enumerate(channel_messages):
                    if i > 0:
                        # Add delay between messages to respect rate limits
                        delay = 1.0 / config.rate_limit_per_second
                        await asyncio.sleep(delay)
                    
                    result = await self.send_message(message)
                    results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error batch sending messages: {e}")
            return []
    
    def get_delivery_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get delivery statistics for the specified time period"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            recent_deliveries = [
                d for d in self.delivery_history
                if d.sent_at >= cutoff_time
            ]
            
            stats = {
                "total_messages": len(recent_deliveries),
                "by_status": {},
                "by_channel": {},
                "success_rate": 0.0,
                "average_retry_count": 0.0
            }
            
            if not recent_deliveries:
                return stats
            
            # Count by status
            for delivery in recent_deliveries:
                status = delivery.status.value
                stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
            
            # Count by channel
            for delivery in recent_deliveries:
                channel = delivery.channel.value
                stats["by_channel"][channel] = stats["by_channel"].get(channel, 0) + 1
            
            # Calculate success rate
            successful = stats["by_status"].get("sent", 0) + stats["by_status"].get("delivered", 0)
            stats["success_rate"] = successful / len(recent_deliveries) if recent_deliveries else 0.0
            
            # Calculate average retry count
            total_retries = sum(d.retry_count for d in recent_deliveries)
            stats["average_retry_count"] = total_retries / len(recent_deliveries) if recent_deliveries else 0.0
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting delivery stats: {e}")
            return {"error": str(e)}
    
    def get_channel_status(self) -> Dict[str, Any]:
        """Get status of all notification channels"""
        try:
            status = {}
            
            for channel, config in self.channel_configs.items():
                rate_limiter = self.rate_limiters[channel]
                
                status[channel.value] = {
                    "enabled": config.enabled,
                    "rate_limit_per_second": config.rate_limit_per_second,
                    "rate_limit_per_minute": config.rate_limit_per_minute,
                    "current_usage": rate_limiter.get_current_usage(),
                    "deduplication_window_minutes": config.deduplication_window_minutes,
                    "max_retries": config.max_retries
                }
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting channel status: {e}")
            return {"error": str(e)}


class RateLimiter:
    """Rate limiter for notification channels"""
    
    def __init__(self, per_second_limit: float, per_minute_limit: float):
        self.per_second_limit = per_second_limit
        self.per_minute_limit = per_minute_limit
        self.second_window = []
        self.minute_window = []
    
    async def can_send(self, priority_bypass: bool = False) -> bool:
        """Check if we can send a message without exceeding rate limits"""
        try:
            current_time = datetime.utcnow()
            
            # Clean up old entries
            self._cleanup_windows(current_time)
            
            # Check per-second limit
            if len(self.second_window) >= self.per_second_limit and not priority_bypass:
                return False
            
            # Check per-minute limit
            if len(self.minute_window) >= self.per_minute_limit and not priority_bypass:
                return False
            
            # Record this send
            self.second_window.append(current_time)
            self.minute_window.append(current_time)
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            return False
    
    def _cleanup_windows(self, current_time: datetime):
        """Remove old entries from rate limiting windows"""
        try:
            # Clean second window (keep last 1 second)
            second_cutoff = current_time - timedelta(seconds=1)
            self.second_window = [t for t in self.second_window if t > second_cutoff]
            
            # Clean minute window (keep last 1 minute)
            minute_cutoff = current_time - timedelta(minutes=1)
            self.minute_window = [t for t in self.minute_window if t > minute_cutoff]
            
        except Exception as e:
            logger.error(f"Error cleaning up rate limit windows: {e}")
    
    def get_current_usage(self) -> Dict[str, Any]:
        """Get current rate limit usage"""
        try:
            current_time = datetime.utcnow()
            self._cleanup_windows(current_time)
            
            return {
                "per_second_usage": len(self.second_window),
                "per_second_limit": self.per_second_limit,
                "per_minute_usage": len(self.minute_window),
                "per_minute_limit": self.per_minute_limit,
                "per_second_available": max(0, self.per_second_limit - len(self.second_window)),
                "per_minute_available": max(0, self.per_minute_limit - len(self.minute_window))
            }
            
        except Exception as e:
            logger.error(f"Error getting current usage: {e}")
            return {"error": str(e)}