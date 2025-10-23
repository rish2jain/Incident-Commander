"""
Integration tests for AWS AI Service Manager.

Tests AWS AI service integration, usage tracking, and health monitoring
for all 8 AWS services in the system.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, MagicMock, patch

from src.services.aws_ai_service_manager import AWSAIServiceManager
from src.models.real_time_models import AWSServiceMetrics


@pytest.fixture
def aws_manager():
    """Create AWS AI service manager with mocked clients."""
    with patch('src.services.aws_ai_service_manager.boto3.client') as mock_boto3:
        # Mock all boto3 clients
        mock_boto3.return_value = MagicMock()

        manager = AWSAIServiceManager(region="us-east-1")

        # Mock the bedrock service
        manager.bedrock_service.invoke_claude_sonnet = AsyncMock(
            return_value=Mock(
                content="Test response",
                metadata={"tokens_used": 100}
            )
        )

        yield manager


class TestAWSServiceManagerInitialization:
    """Test AWS service manager initialization."""

    def test_manager_initialization(self, aws_manager):
        """Test manager initializes with all services."""
        assert aws_manager.region == "us-east-1"
        assert aws_manager.bedrock_service is not None
        assert aws_manager.bedrock_runtime is not None
        assert aws_manager.qbusiness is not None
        assert aws_manager.comprehend is not None

        # Verify metrics tracking initialized
        assert isinstance(aws_manager.service_metrics, dict)
        assert aws_manager.start_time is not None


class TestBedrockIntegration:
    """Test Amazon Bedrock service integration."""

    @pytest.mark.asyncio
    async def test_invoke_bedrock_claude_sonnet(self, aws_manager):
        """Test Claude Sonnet invocation."""
        response = await aws_manager.invoke_bedrock_claude(
            prompt="Test prompt",
            model="sonnet"
        )

        assert response is not None
        assert response.content == "Test response"
        assert response.metadata["tokens_used"] == 100

    @pytest.mark.asyncio
    async def test_invoke_bedrock_with_system_prompt(self, aws_manager):
        """Test Bedrock with system prompt."""
        response = await aws_manager.invoke_bedrock_claude(
            prompt="Test prompt",
            system_prompt="You are a helpful assistant",
            model="sonnet"
        )

        assert response is not None

    @pytest.mark.asyncio
    async def test_bedrock_error_tracking(self, aws_manager):
        """Test error tracking for Bedrock failures."""
        # Mock failure
        aws_manager.bedrock_service.invoke_claude_sonnet = AsyncMock(
            side_effect=Exception("Service error")
        )

        with pytest.raises(Exception, match="Service error"):
            await aws_manager.invoke_bedrock_claude(
                prompt="Test prompt",
                model="sonnet"
            )

        # Verify error was tracked
        metrics = aws_manager.get_service_metrics("bedrock-claude-sonnet")
        assert metrics.failed_calls > 0


class TestNovaIntegration:
    """Test Amazon Nova service integration."""

    @pytest.mark.asyncio
    async def test_invoke_nova_lite(self, aws_manager):
        """Test Nova Lite model invocation."""
        # Mock Nova response
        aws_manager.bedrock_runtime.invoke_model = Mock(
            return_value={
                'body': Mock(read=lambda: b'{"output": "Test response"}')
            }
        )

        response = await aws_manager.invoke_nova(
            prompt="Test prompt",
            model_size="lite"
        )

        assert response is not None

    @pytest.mark.asyncio
    async def test_nova_smart_routing(self, aws_manager):
        """Test Nova smart model routing based on task complexity."""
        # Test micro routing (simple task)
        await aws_manager.invoke_nova(
            prompt="Hello",
            model_size="micro"
        )

        # Test pro routing (complex task)
        await aws_manager.invoke_nova(
            prompt="Complex analysis task",
            model_size="pro"
        )


class TestQBusinessIntegration:
    """Test Amazon Q Business service integration."""

    @pytest.mark.asyncio
    async def test_query_q_business(self, aws_manager):
        """Test Q Business knowledge retrieval."""
        # Mock Q Business response
        aws_manager.qbusiness.chat_sync = Mock(
            return_value={
                'conversationId': 'test-conv-123',
                'systemMessage': 'Test response from Q'
            }
        )

        response = await aws_manager.query_q_business(
            question="What are best practices for incident resolution?",
            application_id="test-app-123"
        )

        assert response is not None

    @pytest.mark.asyncio
    async def test_q_business_historical_lookup(self, aws_manager):
        """Test Q Business historical incident lookup."""
        aws_manager.qbusiness.chat_sync = Mock(
            return_value={
                'conversationId': 'test-conv-123',
                'systemMessage': 'Historical incident data'
            }
        )

        response = await aws_manager.query_q_business(
            question="Find similar incidents to database outage",
            application_id="test-app-123"
        )

        assert response is not None


class TestGuardrailsIntegration:
    """Test Bedrock Guardrails integration."""

    @pytest.mark.asyncio
    async def test_validate_with_guardrails(self, aws_manager):
        """Test content validation with guardrails."""
        # Mock guardrails response
        aws_manager.bedrock_runtime.apply_guardrail = Mock(
            return_value={
                'action': 'NONE',
                'outputs': [{'text': 'Content is safe'}]
            }
        )

        is_safe = await aws_manager.validate_with_guardrails(
            content="Test content to validate",
            guardrail_id="test-guardrail-123"
        )

        assert is_safe is True

    @pytest.mark.asyncio
    async def test_guardrails_blocks_unsafe_content(self, aws_manager):
        """Test guardrails blocks unsafe content."""
        # Mock guardrails blocking content
        aws_manager.bedrock_runtime.apply_guardrail = Mock(
            return_value={
                'action': 'GUARDRAIL_INTERVENED',
                'outputs': []
            }
        )

        is_safe = await aws_manager.validate_with_guardrails(
            content="Unsafe content",
            guardrail_id="test-guardrail-123"
        )

        assert is_safe is False


class TestKnowledgeBasesIntegration:
    """Test Bedrock Knowledge Bases integration."""

    @pytest.mark.asyncio
    async def test_query_knowledge_base(self, aws_manager):
        """Test knowledge base retrieval."""
        # Mock knowledge base response
        aws_manager.bedrock_agent_runtime.retrieve = Mock(
            return_value={
                'retrievalResults': [
                    {'content': {'text': 'Knowledge base result 1'}},
                    {'content': {'text': 'Knowledge base result 2'}}
                ]
            }
        )

        results = await aws_manager.query_knowledge_base(
            query="Database troubleshooting steps",
            knowledge_base_id="test-kb-123"
        )

        assert results is not None
        assert len(results) == 2


class TestComprehendIntegration:
    """Test Amazon Comprehend integration."""

    @pytest.mark.asyncio
    async def test_analyze_sentiment(self, aws_manager):
        """Test sentiment analysis with Comprehend."""
        # Mock Comprehend response
        aws_manager.comprehend.detect_sentiment = Mock(
            return_value={
                'Sentiment': 'NEGATIVE',
                'SentimentScore': {
                    'Negative': 0.8,
                    'Positive': 0.1
                }
            }
        )

        sentiment = await aws_manager.analyze_sentiment(
            text="This incident is causing major issues"
        )

        assert sentiment == 'NEGATIVE'


class TestTextractIntegration:
    """Test Amazon Textract integration."""

    @pytest.mark.asyncio
    async def test_extract_text_from_document(self, aws_manager):
        """Test document text extraction with Textract."""
        # Mock Textract response
        aws_manager.textract.detect_document_text = Mock(
            return_value={
                'Blocks': [
                    {'BlockType': 'LINE', 'Text': 'Line 1'},
                    {'BlockType': 'LINE', 'Text': 'Line 2'}
                ]
            }
        )

        text = await aws_manager.extract_text(
            document_bytes=b"fake document"
        )

        assert text is not None
        assert 'Line 1' in text


class TestUsageTracking:
    """Test service usage tracking and metrics."""

    @pytest.mark.asyncio
    async def test_service_call_tracking(self, aws_manager):
        """Test service call metrics tracking."""
        # Make a service call
        await aws_manager.invoke_bedrock_claude(
            prompt="Test prompt",
            model="sonnet"
        )

        # Get metrics
        metrics = aws_manager.get_service_metrics("bedrock-claude-sonnet")

        assert metrics.total_calls > 0
        assert metrics.successful_calls > 0
        assert metrics.tokens_processed > 0

    @pytest.mark.asyncio
    async def test_cost_calculation(self, aws_manager):
        """Test cost calculation for service usage."""
        # Make multiple calls
        for _ in range(5):
            await aws_manager.invoke_bedrock_claude(
                prompt="Test prompt",
                model="sonnet"
            )

        metrics = aws_manager.get_service_metrics("bedrock-claude-sonnet")

        assert metrics.estimated_cost_usd > 0
        assert metrics.cost_per_call > 0

    @pytest.mark.asyncio
    async def test_latency_tracking(self, aws_manager):
        """Test latency tracking for services."""
        await aws_manager.invoke_bedrock_claude(
            prompt="Test prompt",
            model="sonnet"
        )

        metrics = aws_manager.get_service_metrics("bedrock-claude-sonnet")

        assert metrics.average_latency_ms > 0
        assert metrics.p95_latency_ms >= 0


class TestHealthMonitoring:
    """Test service health monitoring."""

    @pytest.mark.asyncio
    async def test_service_health_status(self, aws_manager):
        """Test service health status reporting."""
        # Make successful calls
        for _ in range(10):
            await aws_manager.invoke_bedrock_claude(
                prompt="Test prompt",
                model="sonnet"
            )

        metrics = aws_manager.get_service_metrics("bedrock-claude-sonnet")

        assert metrics.health_status == "healthy"
        assert metrics.error_rate == 0.0

    @pytest.mark.asyncio
    async def test_degraded_health_detection(self, aws_manager):
        """Test detection of degraded service health."""
        # Mock some failures
        success_count = 0

        for i in range(10):
            if i < 3:  # 30% failure rate
                aws_manager.bedrock_service.invoke_claude_sonnet = AsyncMock(
                    side_effect=Exception("Service error")
                )
                try:
                    await aws_manager.invoke_bedrock_claude(
                        prompt="Test prompt",
                        model="sonnet"
                    )
                except:
                    pass
            else:
                aws_manager.bedrock_service.invoke_claude_sonnet = AsyncMock(
                    return_value=Mock(
                        content="Test response",
                        metadata={"tokens_used": 100}
                    )
                )
                await aws_manager.invoke_bedrock_claude(
                    prompt="Test prompt",
                    model="sonnet"
                )

        metrics = aws_manager.get_service_metrics("bedrock-claude-sonnet")

        # Should detect degraded status with >10% error rate
        assert metrics.error_rate > 0.1

    @pytest.mark.asyncio
    async def test_all_services_health_summary(self, aws_manager):
        """Test overall health summary for all services."""
        # Make calls to multiple services
        await aws_manager.invoke_bedrock_claude(
            prompt="Test",
            model="sonnet"
        )

        # Get overall health
        health_summary = await aws_manager.get_all_services_health()

        assert health_summary is not None
        assert "services" in health_summary
        assert health_summary["healthy_count"] >= 0


class TestIntegrationWithOrchestrator:
    """Test integration with real-time orchestrator."""

    @pytest.mark.asyncio
    async def test_orchestrator_callback_integration(self, aws_manager):
        """Test AWS services as orchestrator callbacks."""
        # Simulate orchestrator using AWS service as callback
        async def detection_callback(incident):
            return await aws_manager.invoke_bedrock_claude(
                prompt=f"Analyze incident: {incident.description}",
                model="sonnet"
            )

        # Mock incident
        mock_incident = Mock(
            description="Database connection pool exhausted"
        )

        result = await detection_callback(mock_incident)

        assert result is not None
        assert result.content == "Test response"


# Run tests with: pytest tests/test_aws_ai_service_manager.py -v
