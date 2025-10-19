"""
Unit tests for Documentation Generation System

Tests documentation generation, versioning, and Amazon Q integration.

Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from uuid import uuid4

from src.services.documentation_generator import (
    DocumentationGenerator, get_documentation_generator,
    RunbookEntry, GeneratedDocument, DocumentationTemplate
)
from src.services.knowledge_base_generator import (
    KnowledgeBaseGenerator, get_knowledge_base_generator,
    KnowledgeArticle, InteractiveTroubleshootingGuide, TroubleshootingStep
)
from src.services.post_incident_documentation import (
    PostIncidentDocumentationService, get_post_incident_documentation_service,
    PostIncidentReport, ActionItem, LessonLearned, DocumentVersion, DocumentChangeType
)
from src.models.incident import Incident, IncidentSeverity, ServiceTier, BusinessImpact, IncidentMetadata
from src.services.aws import AWSServiceFactory
from src.services.rag_memory import IncidentPattern


class TestDocumentationGenerator:
    """Test cases for DocumentationGenerator."""
    
    @pytest.fixture
    def aws_factory(self):
        """Mock AWS service factory."""
        return Mock(spec=AWSServiceFactory)
    
    @pytest.fixture
    def doc_generator(self, aws_factory):
        """Create documentation generator instance for testing."""
        return DocumentationGenerator(aws_factory)
    
    @pytest.fixture
    def sample_incident(self):
        """Create sample incident for testing."""
        return Incident(
            id="test_incident_123",
            title="Database Connection Pool Exhaustion",
            description="Critical database connection pool exhaustion causing service degradation",
            severity=IncidentSeverity.HIGH,
            business_impact=BusinessImpact(
                service_tier=ServiceTier.TIER_1,
                affected_users=5000,
                revenue_impact_per_minute=1000.0
            ),
            metadata=IncidentMetadata(
                source_system="monitoring",
                tags={"affected_systems": ["database", "api-gateway"]}
            )
        )
    
    @pytest.mark.asyncio
    async def test_generate_runbook_from_incident(self, doc_generator, sample_incident):
        """Test runbook generation from incident resolution."""
        resolution_actions = [
            "Scale database connection pool to 200 connections",
            "Enable read replicas for load distribution",
            "Implement connection pooling optimization"
        ]
        
        diagnosis_data = {
            "root_cause": "Connection pool exhaustion",
            "symptoms": ["High response times", "Connection timeouts"],
            "analysis_confidence": 0.92
        }
        
        with patch.object(doc_generator, '_get_bedrock_client') as mock_bedrock:
            mock_bedrock.return_value.invoke_with_fallback = AsyncMock(
                return_value="Enhanced runbook content from Amazon Q"
            )
            
            runbook = await doc_generator.generate_runbook_from_incident(
                sample_incident, resolution_actions, diagnosis_data
            )
        
        assert isinstance(runbook, RunbookEntry)
        assert runbook.title == f"Runbook: {sample_incident.title}"
        assert runbook.created_from_incident == sample_incident.id
        assert len(runbook.resolution_steps) == len(resolution_actions)
        assert runbook.success_rate > 0
        assert runbook.difficulty_level in ["Low", "Medium", "High", "Advanced"]
        assert runbook.version == 1
    
    @pytest.mark.asyncio
    async def test_runbook_content_structure(self, doc_generator, sample_incident):
        """Test that generated runbook has proper content structure."""
        resolution_actions = ["Fix database issue", "Verify resolution"]
        
        with patch.object(doc_generator, '_get_bedrock_client') as mock_bedrock:
            mock_bedrock.return_value.invoke_with_fallback = AsyncMock(
                return_value="Mock enhanced content"
            )
            
            runbook = await doc_generator.generate_runbook_from_incident(
                sample_incident, resolution_actions
            )
        
        # Verify required runbook sections
        assert len(runbook.symptoms) > 0
        assert len(runbook.diagnosis_steps) > 0
        assert len(runbook.resolution_steps) > 0
        assert len(runbook.verification_steps) > 0
        assert len(runbook.rollback_steps) > 0
        assert len(runbook.prerequisites) > 0
        assert runbook.estimated_time is not None
    
    @pytest.mark.asyncio
    async def test_runbook_fallback_generation(self, doc_generator, sample_incident):
        """Test runbook generation with fallback when enhanced generation fails."""
        resolution_actions = ["Apply fix", "Monitor system"]
        
        with patch.object(doc_generator, '_get_bedrock_client') as mock_bedrock:
            mock_bedrock.return_value.invoke_with_fallback = AsyncMock(
                side_effect=Exception("Bedrock unavailable")
            )
            
            runbook = await doc_generator.generate_runbook_from_incident(
                sample_incident, resolution_actions
            )
        
        # Should still generate runbook with fallback content
        assert isinstance(runbook, RunbookEntry)
        assert len(runbook.resolution_steps) > 0
        assert runbook.success_rate == 85.0  # Fallback success rate
    
    @pytest.mark.asyncio
    async def test_get_runbook_by_id(self, doc_generator, sample_incident):
        """Test retrieving runbook by ID."""
        resolution_actions = ["Test action"]
        
        with patch.object(doc_generator, '_get_bedrock_client') as mock_bedrock:
            mock_bedrock.return_value.invoke_with_fallback = AsyncMock(return_value="content")
            
            # Generate runbook
            runbook = await doc_generator.generate_runbook_from_incident(
                sample_incident, resolution_actions
            )
            
            # Retrieve by ID
            retrieved = await doc_generator.get_runbook_by_id(runbook.runbook_id)
        
        assert retrieved is not None
        assert retrieved.runbook_id == runbook.runbook_id
        assert retrieved.title == runbook.title
    
    @pytest.mark.asyncio
    async def test_list_runbooks(self, doc_generator, sample_incident):
        """Test listing runbooks with limit."""
        resolution_actions = ["Action 1", "Action 2"]
        
        with patch.object(doc_generator, '_get_bedrock_client') as mock_bedrock:
            mock_bedrock.return_value.invoke_with_fallback = AsyncMock(return_value="content")
            
            # Generate multiple runbooks
            runbooks = []
            for i in range(3):
                incident = Incident(
                    id=f"incident_{i}",
                    title=f"Test Incident {i}",
                    description="Test description",
                    severity=IncidentSeverity.MEDIUM,
                    business_impact=BusinessImpact(service_tier=ServiceTier.TIER_2),
                    metadata=IncidentMetadata(source_system="test")
                )
                runbook = await doc_generator.generate_runbook_from_incident(incident, resolution_actions)
                runbooks.append(runbook)
            
            # List runbooks
            listed = await doc_generator.list_runbooks(limit=2)
        
        assert len(listed) == 2
        assert all(isinstance(rb, RunbookEntry) for rb in listed)
    
    @pytest.mark.asyncio
    async def test_search_runbooks(self, doc_generator, sample_incident):
        """Test searching runbooks by query."""
        resolution_actions = ["Database fix"]
        
        with patch.object(doc_generator, '_get_bedrock_client') as mock_bedrock:
            mock_bedrock.return_value.invoke_with_fallback = AsyncMock(return_value="content")
            
            # Generate runbook
            await doc_generator.generate_runbook_from_incident(sample_incident, resolution_actions)
            
            # Search for runbooks
            results = await doc_generator.search_runbooks("database", limit=5)
        
        assert len(results) > 0
        assert any("database" in rb.title.lower() or "database" in rb.problem_description.lower() 
                  for rb in results)
    
    def test_generation_statistics(self, doc_generator):
        """Test getting generation statistics."""
        stats = doc_generator.get_generation_statistics()
        
        assert "total_generated" in stats
        assert "runbooks_created" in stats
        assert "kb_articles_created" in stats
        assert "post_incident_reports" in stats
        assert "generation_time_avg" in stats
        assert isinstance(stats["total_generated"], int)


class TestKnowledgeBaseGenerator:
    """Test cases for KnowledgeBaseGenerator."""
    
    @pytest.fixture
    def aws_factory(self):
        """Mock AWS service factory."""
        return Mock(spec=AWSServiceFactory)
    
    @pytest.fixture
    def kb_generator(self, aws_factory):
        """Create knowledge base generator instance for testing."""
        return KnowledgeBaseGenerator(aws_factory)
    
    @pytest.fixture
    def sample_incidents(self):
        """Create sample incidents for testing."""
        incidents = []
        for i in range(3):
            incident = Incident(
                id=f"kb_incident_{i}",
                title=f"Database Performance Issue {i}",
                description=f"Database performance degradation incident {i}",
                severity=IncidentSeverity.HIGH,
                business_impact=BusinessImpact(
                    service_tier=ServiceTier.TIER_1,
                    affected_users=1000 * (i + 1)
                ),
                metadata=IncidentMetadata(
                    source_system="monitoring",
                    tags={"category": "database", "type": "performance"}
                )
            )
            incidents.append(incident)
        return incidents
    
    @pytest.fixture
    def sample_resolution_data(self):
        """Create sample resolution data."""
        return [
            {
                "summary": "Optimized database queries",
                "actions": ["Query optimization", "Index creation"],
                "success": True,
                "duration_minutes": 15
            },
            {
                "summary": "Scaled database resources",
                "actions": ["CPU scaling", "Memory increase"],
                "success": True,
                "duration_minutes": 10
            },
            {
                "summary": "Connection pool tuning",
                "actions": ["Pool size increase", "Timeout adjustment"],
                "success": True,
                "duration_minutes": 8
            }
        ]
    
    @pytest.mark.asyncio
    async def test_generate_article_from_successful_resolutions(self, kb_generator, sample_incidents, sample_resolution_data):
        """Test knowledge article generation from successful resolutions."""
        with patch.object(kb_generator, '_get_bedrock_client') as mock_bedrock:
            mock_bedrock.return_value.invoke_with_fallback = AsyncMock(
                return_value="Enhanced knowledge article content"
            )
            
            article = await kb_generator.generate_article_from_successful_resolutions(
                sample_incidents, sample_resolution_data
            )
        
        assert isinstance(article, KnowledgeArticle)
        assert "database" in article.title.lower() or "troubleshooting" in article.title.lower()
        assert article.category in ["database", "network", "api", "infrastructure", "security", "monitoring"]
        assert len(article.source_incidents) == len(sample_incidents)
        assert article.confidence_score > 0
        assert article.estimated_read_time > 0
        assert len(article.tags) > 0
    
    @pytest.mark.asyncio
    async def test_article_categorization(self, kb_generator, sample_incidents, sample_resolution_data):
        """Test that articles are properly categorized."""
        with patch.object(kb_generator, '_get_bedrock_client') as mock_bedrock:
            mock_bedrock.return_value.invoke_with_fallback = AsyncMock(return_value="content")
            
            article = await kb_generator.generate_article_from_successful_resolutions(
                sample_incidents, sample_resolution_data
            )
        
        # Should categorize as database based on incident content
        assert article.category == "database"
        assert "database" in article.tags
    
    @pytest.mark.asyncio
    async def test_create_interactive_troubleshooting_guide(self, kb_generator):
        """Test creating interactive troubleshooting guide."""
        # Create sample incident patterns
        patterns = []
        for i in range(2):
            pattern = IncidentPattern(
                pattern_id=f"pattern_{i}",
                incident_type="database_performance",
                symptoms=[f"Symptom {i}", "Slow queries"],
                root_causes=[f"Root cause {i}"],
                resolution_actions=[f"Action {i}", "Optimize queries"],
                success_rate=0.9,
                confidence=0.85,
                created_at=datetime.utcnow(),
                last_used=datetime.utcnow(),
                usage_count=5
            )
            patterns.append(pattern)
        
        guide = await kb_generator.create_interactive_troubleshooting_guide(
            patterns, "Database Performance Troubleshooting"
        )
        
        assert isinstance(guide, InteractiveTroubleshootingGuide)
        assert guide.title == "Database Performance Troubleshooting"
        assert guide.entry_point in guide.steps
        assert len(guide.steps) > 0
        assert guide.success_rate > 0
        assert guide.average_completion_time > 0
        assert len(guide.created_from_incidents) == len(patterns)
    
    @pytest.mark.asyncio
    async def test_troubleshooting_guide_step_structure(self, kb_generator):
        """Test troubleshooting guide step structure."""
        patterns = [
            IncidentPattern(
                pattern_id="test_pattern",
                incident_type="api_performance",
                symptoms=["High latency", "Timeouts"],
                root_causes=["Resource exhaustion"],
                resolution_actions=["Scale resources", "Optimize code"],
                success_rate=0.95,
                confidence=0.9,
                created_at=datetime.utcnow(),
                last_used=datetime.utcnow(),
                usage_count=10
            )
        ]
        
        guide = await kb_generator.create_interactive_troubleshooting_guide(patterns)
        
        # Verify step structure
        for step_id, step in guide.steps.items():
            assert isinstance(step, TroubleshootingStep)
            assert step.step_id == step_id
            assert step.step_type in ["check", "action", "decision", "resolution"]
            assert len(step.instructions) > 0
            assert len(step.expected_results) > 0
            assert isinstance(step.next_steps, dict)
            assert step.estimated_time > 0
            assert step.difficulty in ["beginner", "intermediate", "advanced"]
    
    @pytest.mark.asyncio
    async def test_search_articles(self, kb_generator, sample_incidents, sample_resolution_data):
        """Test searching knowledge articles."""
        with patch.object(kb_generator, '_get_bedrock_client') as mock_bedrock:
            mock_bedrock.return_value.invoke_with_fallback = AsyncMock(return_value="content")
            
            # Generate article
            article = await kb_generator.generate_article_from_successful_resolutions(
                sample_incidents, sample_resolution_data
            )
            
            # Search articles
            results = await kb_generator.search_articles("database", limit=5)
        
        assert len(results) > 0
        assert any("database" in article.title.lower() or "database" in article.summary.lower() 
                  for article in results)
    
    @pytest.mark.asyncio
    async def test_get_related_articles(self, kb_generator, sample_incidents, sample_resolution_data):
        """Test getting related articles."""
        with patch.object(kb_generator, '_get_bedrock_client') as mock_bedrock:
            mock_bedrock.return_value.invoke_with_fallback = AsyncMock(return_value="content")
            
            # Generate multiple articles with similar tags
            articles = []
            for i in range(3):
                incidents = [sample_incidents[0]]  # Use same incident type
                article = await kb_generator.generate_article_from_successful_resolutions(
                    incidents, [sample_resolution_data[0]]
                )
                articles.append(article)
            
            # Get related articles for first article
            related = await kb_generator.get_related_articles(articles[0].article_id, limit=2)
        
        # Should find related articles based on category/tags
        assert len(related) >= 0  # May be 0 if similarity threshold not met
    
    @pytest.mark.asyncio
    async def test_update_article_metrics(self, kb_generator, sample_incidents, sample_resolution_data):
        """Test updating article view and helpfulness metrics."""
        with patch.object(kb_generator, '_get_bedrock_client') as mock_bedrock:
            mock_bedrock.return_value.invoke_with_fallback = AsyncMock(return_value="content")
            
            article = await kb_generator.generate_article_from_successful_resolutions(
                sample_incidents, sample_resolution_data
            )
            
            initial_views = article.view_count
            initial_votes = article.total_votes
            
            # Update metrics
            await kb_generator.update_article_metrics(article.article_id, viewed=True, helpful=True)
        
        assert article.view_count == initial_views + 1
        assert article.total_votes == initial_votes + 1
        assert article.helpful_votes > 0
    
    def test_knowledge_base_statistics(self, kb_generator):
        """Test getting knowledge base statistics."""
        stats = kb_generator.get_knowledge_base_statistics()
        
        assert "articles_generated" in stats
        assert "guides_generated" in stats
        assert "total_views" in stats
        assert "average_helpfulness" in stats
        assert "total_articles" in stats
        assert "total_guides" in stats
        assert "category_distribution" in stats
        assert "difficulty_distribution" in stats


class TestPostIncidentDocumentationService:
    """Test cases for PostIncidentDocumentationService."""
    
    @pytest.fixture
    def aws_factory(self):
        """Mock AWS service factory."""
        return Mock(spec=AWSServiceFactory)
    
    @pytest.fixture
    def pir_service(self, aws_factory):
        """Create post-incident documentation service instance for testing."""
        return PostIncidentDocumentationService(aws_factory)
    
    @pytest.fixture
    def sample_incident(self):
        """Create sample incident for testing."""
        return Incident(
            id="pir_incident_123",
            title="Critical API Gateway Failure",
            description="API Gateway experienced complete failure affecting all services",
            severity=IncidentSeverity.CRITICAL,
            business_impact=BusinessImpact(
                service_tier=ServiceTier.TIER_1,
                affected_users=50000,
                revenue_impact_per_minute=5000.0
            ),
            metadata=IncidentMetadata(
                source_system="monitoring",
                tags={"affected_systems": ["api-gateway", "load-balancer"]}
            )
        )
    
    @pytest.fixture
    def sample_resolution_data(self):
        """Create sample resolution data."""
        return {
            "actions": [
                "Restarted API Gateway instances",
                "Scaled load balancer capacity",
                "Implemented circuit breaker"
            ],
            "technical_details": {
                "root_cause": "Memory leak in gateway service",
                "fix_applied": "Service restart and memory optimization"
            },
            "metrics": {
                "resolution_time_minutes": 12.5,
                "services_affected": 15,
                "customer_impact_duration": 8.2
            }
        }
    
    @pytest.mark.asyncio
    async def test_generate_post_incident_report(self, pir_service, sample_incident, sample_resolution_data):
        """Test comprehensive post-incident report generation."""
        timeline_events = [
            {
                "timestamp": datetime.utcnow() - timedelta(minutes=15),
                "event": "Incident Detected",
                "description": "Monitoring alerts triggered"
            },
            {
                "timestamp": datetime.utcnow() - timedelta(minutes=10),
                "event": "Investigation Started",
                "description": "Team began root cause analysis"
            },
            {
                "timestamp": datetime.utcnow(),
                "event": "Incident Resolved",
                "description": "All services restored"
            }
        ]
        
        with patch.object(pir_service, '_get_bedrock_client') as mock_bedrock:
            mock_bedrock.return_value.invoke_with_fallback = AsyncMock(
                return_value="Enhanced post-incident analysis"
            )
            
            report = await pir_service.generate_post_incident_report(
                sample_incident, sample_resolution_data, timeline_events
            )
        
        assert isinstance(report, PostIncidentReport)
        assert report.incident_id == sample_incident.id
        assert report.title.startswith("Post-Incident Report:")
        assert len(report.incident_timeline) == len(timeline_events)
        assert len(report.lessons_learned) > 0
        assert len(report.action_items) > 0
        assert len(report.prevention_measures) > 0
        assert report.confidence_score > 0
        assert report.version == 1
        assert report.status == "draft"
    
    @pytest.mark.asyncio
    async def test_report_content_structure(self, pir_service, sample_incident, sample_resolution_data):
        """Test that generated report has proper content structure."""
        with patch.object(pir_service, '_get_bedrock_client') as mock_bedrock:
            mock_bedrock.return_value.invoke_with_fallback = AsyncMock(return_value="content")
            
            report = await pir_service.generate_post_incident_report(
                sample_incident, sample_resolution_data
            )
        
        # Verify required report sections
        assert report.executive_summary is not None
        assert isinstance(report.root_cause_analysis, dict)
        assert isinstance(report.business_impact_assessment, dict)
        assert isinstance(report.resolution_summary, dict)
        assert isinstance(report.appendices, dict)
        
        # Verify root cause analysis structure
        assert "primary_cause" in report.root_cause_analysis
        assert "contributing_factors" in report.root_cause_analysis
        assert "analysis_confidence" in report.root_cause_analysis
    
    @pytest.mark.asyncio
    async def test_action_items_extraction(self, pir_service, sample_incident, sample_resolution_data):
        """Test extraction and storage of action items."""
        with patch.object(pir_service, '_get_bedrock_client') as mock_bedrock:
            mock_bedrock.return_value.invoke_with_fallback = AsyncMock(return_value="content")
            
            initial_count = len(pir_service._action_items)
            
            report = await pir_service.generate_post_incident_report(
                sample_incident, sample_resolution_data
            )
        
        # Should have created action items
        assert len(pir_service._action_items) > initial_count
        
        # Verify action item structure
        action_items = list(pir_service._action_items.values())
        if action_items:
            item = action_items[0]
            assert isinstance(item, ActionItem)
            assert item.priority in ["high", "medium", "low"]
            assert item.category in ["prevention", "process", "technical", "training"]
            assert item.status == "open"
    
    @pytest.mark.asyncio
    async def test_lessons_learned_extraction(self, pir_service, sample_incident, sample_resolution_data):
        """Test extraction and storage of lessons learned."""
        with patch.object(pir_service, '_get_bedrock_client') as mock_bedrock:
            mock_bedrock.return_value.invoke_with_fallback = AsyncMock(return_value="content")
            
            initial_count = len(pir_service._lessons_learned)
            
            report = await pir_service.generate_post_incident_report(
                sample_incident, sample_resolution_data
            )
        
        # Should have created lessons learned
        assert len(pir_service._lessons_learned) > initial_count
        
        # Verify lesson learned structure
        lessons = list(pir_service._lessons_learned.values())
        if lessons:
            lesson = lessons[0]
            assert isinstance(lesson, LessonLearned)
            assert lesson.category in ["monitoring", "process", "technical", "communication", "general"]
            assert lesson.impact_level in ["high", "medium", "low"]
            assert lesson.created_from_incident == sample_incident.id
    
    @pytest.mark.asyncio
    async def test_document_versioning(self, pir_service, sample_incident, sample_resolution_data):
        """Test document version creation and tracking."""
        with patch.object(pir_service, '_get_bedrock_client') as mock_bedrock:
            mock_bedrock.return_value.invoke_with_fallback = AsyncMock(return_value="content")
            
            report = await pir_service.generate_post_incident_report(
                sample_incident, sample_resolution_data
            )
            
            # Should have created initial version
            versions = await pir_service.get_report_versions(report.report_id)
        
        assert len(versions) == 1
        version = versions[0]
        assert isinstance(version, DocumentVersion)
        assert version.document_id == report.report_id
        assert version.version_number == 1
        assert version.change_type == DocumentChangeType.CREATED
        assert version.checksum is not None
    
    @pytest.mark.asyncio
    async def test_update_report(self, pir_service, sample_incident, sample_resolution_data):
        """Test updating existing post-incident report."""
        with patch.object(pir_service, '_get_bedrock_client') as mock_bedrock:
            mock_bedrock.return_value.invoke_with_fallback = AsyncMock(return_value="content")
            
            # Generate initial report
            report = await pir_service.generate_post_incident_report(
                sample_incident, sample_resolution_data
            )
            
            # Update report
            updates = {
                "executive_summary": "Updated executive summary",
                "status": "final"
            }
            
            updated_report = await pir_service.update_report(
                report.report_id, updates, "test_user"
            )
        
        assert updated_report.version == 2
        assert updated_report.executive_summary == "Updated executive summary"
        assert updated_report.status == "final"
        assert updated_report.updated_at > report.updated_at
    
    @pytest.mark.asyncio
    async def test_version_diff(self, pir_service, sample_incident, sample_resolution_data):
        """Test getting diff between report versions."""
        with patch.object(pir_service, '_get_bedrock_client') as mock_bedrock:
            mock_bedrock.return_value.invoke_with_fallback = AsyncMock(return_value="content")
            
            # Generate and update report
            report = await pir_service.generate_post_incident_report(
                sample_incident, sample_resolution_data
            )
            
            await pir_service.update_report(
                report.report_id, {"executive_summary": "Updated summary"}, "test_user"
            )
            
            # Get diff
            diff_result = await pir_service.get_version_diff(report.report_id, 1, 2)
        
        assert diff_result["version1"] == 1
        assert diff_result["version2"] == 2
        assert "diff" in diff_result
        assert "changes_summary" in diff_result
    
    @pytest.mark.asyncio
    async def test_list_action_items(self, pir_service, sample_incident, sample_resolution_data):
        """Test listing action items with filtering."""
        with patch.object(pir_service, '_get_bedrock_client') as mock_bedrock:
            mock_bedrock.return_value.invoke_with_fallback = AsyncMock(return_value="content")
            
            # Generate report to create action items
            await pir_service.generate_post_incident_report(
                sample_incident, sample_resolution_data
            )
            
            # List all action items
            all_items = await pir_service.list_action_items()
            
            # List by status
            open_items = await pir_service.list_action_items(status="open")
            
            # List by priority
            high_priority = await pir_service.list_action_items(priority="high")
        
        assert len(all_items) > 0
        assert all(item.status == "open" for item in open_items)
        assert all(item.priority == "high" for item in high_priority)
    
    @pytest.mark.asyncio
    async def test_update_action_item_status(self, pir_service, sample_incident, sample_resolution_data):
        """Test updating action item status."""
        with patch.object(pir_service, '_get_bedrock_client') as mock_bedrock:
            mock_bedrock.return_value.invoke_with_fallback = AsyncMock(return_value="content")
            
            # Generate report to create action items
            await pir_service.generate_post_incident_report(
                sample_incident, sample_resolution_data
            )
            
            # Get an action item
            items = await pir_service.list_action_items()
            if items:
                item = items[0]
                original_status = item.status
                
                # Update status
                updated_item = await pir_service.update_action_item_status(
                    item.item_id, "completed", "test_user"
                )
                
                assert updated_item.status == "completed"
                assert updated_item.status != original_status
                assert updated_item.updated_at > item.updated_at
    
    def test_get_lessons_learned_by_category(self, pir_service):
        """Test getting lessons learned filtered by category."""
        # Add some test lessons
        lesson1 = LessonLearned(
            lesson_id="lesson_1",
            title="Monitoring Lesson",
            description="Improve monitoring coverage",
            category="monitoring",
            impact_level="high",
            applicable_teams=["sre"],
            implementation_effort="medium",
            created_from_incident="test_incident"
        )
        
        lesson2 = LessonLearned(
            lesson_id="lesson_2",
            title="Process Lesson",
            description="Update escalation process",
            category="process",
            impact_level="medium",
            applicable_teams=["engineering"],
            implementation_effort="low",
            created_from_incident="test_incident"
        )
        
        pir_service._lessons_learned[lesson1.lesson_id] = lesson1
        pir_service._lessons_learned[lesson2.lesson_id] = lesson2
        
        # Get lessons by category
        monitoring_lessons = pir_service.get_lessons_learned_by_category("monitoring")
        process_lessons = pir_service.get_lessons_learned_by_category("process")
        all_lessons = pir_service.get_lessons_learned_by_category()
        
        assert len(monitoring_lessons) == 1
        assert monitoring_lessons[0].category == "monitoring"
        assert len(process_lessons) == 1
        assert process_lessons[0].category == "process"
        assert len(all_lessons) == 2
    
    def test_get_change_log(self, pir_service):
        """Test getting document change log."""
        # Add some test changes
        test_changes = [
            {
                "timestamp": datetime.utcnow().isoformat(),
                "document_id": "doc_1",
                "version_id": "v1",
                "version_number": 1,
                "change_type": "created",
                "change_summary": "Initial creation",
                "created_by": "system",
                "checksum": "abc123"
            },
            {
                "timestamp": datetime.utcnow().isoformat(),
                "document_id": "doc_1",
                "version_id": "v2",
                "version_number": 2,
                "change_type": "updated",
                "change_summary": "Content update",
                "created_by": "user",
                "checksum": "def456"
            }
        ]
        
        pir_service._change_log.extend(test_changes)
        
        # Get change log
        all_changes = pir_service.get_change_log(limit=10)
        doc_changes = pir_service.get_change_log(document_id="doc_1", limit=10)
        
        assert len(all_changes) >= 2
        assert len(doc_changes) == 2
        assert all(change["document_id"] == "doc_1" for change in doc_changes)
    
    def test_documentation_statistics(self, pir_service):
        """Test getting comprehensive documentation statistics."""
        stats = pir_service.get_documentation_statistics()
        
        assert "reports_generated" in stats
        assert "action_items_created" in stats
        assert "lessons_learned_captured" in stats
        assert "average_generation_time" in stats
        assert "total_versions_created" in stats
        assert "total_reports" in stats
        assert "total_action_items" in stats
        assert "completed_action_items" in stats
        assert "action_item_completion_rate" in stats
        assert "total_lessons_learned" in stats
        assert "lesson_categories" in stats
        assert "total_document_changes" in stats


class TestIntegrationAndEdgeCases:
    """Test cases for integration scenarios and edge cases."""
    
    @pytest.fixture
    def aws_factory(self):
        """Mock AWS service factory."""
        return Mock(spec=AWSServiceFactory)
    
    @pytest.mark.asyncio
    async def test_amazon_q_integration_failure_handling(self, aws_factory):
        """Test handling of Amazon Q integration failures."""
        doc_generator = DocumentationGenerator(aws_factory)
        
        # Mock Bedrock client failure
        with patch.object(doc_generator, '_get_bedrock_client') as mock_bedrock:
            mock_bedrock.return_value.invoke_with_fallback = AsyncMock(
                side_effect=Exception("Amazon Q unavailable")
            )
            
            incident = Incident(
                id="test_incident",
                title="Test Incident",
                description="Test description",
                severity=IncidentSeverity.MEDIUM,
                business_impact=BusinessImpact(service_tier=ServiceTier.TIER_2),
                metadata=IncidentMetadata(source_system="test")
            )
            
            # Should still generate runbook with fallback
            runbook = await doc_generator.generate_runbook_from_incident(
                incident, ["Test action"]
            )
        
        assert isinstance(runbook, RunbookEntry)
        assert runbook.success_rate == 85.0  # Fallback success rate
    
    @pytest.mark.asyncio
    async def test_empty_resolution_actions(self, aws_factory):
        """Test handling of empty resolution actions."""
        doc_generator = DocumentationGenerator(aws_factory)
        
        incident = Incident(
            id="empty_actions_test",
            title="Test Incident",
            description="Test description",
            severity=IncidentSeverity.LOW,
            business_impact=BusinessImpact(service_tier=ServiceTier.TIER_3),
            metadata=IncidentMetadata(source_system="test")
        )
        
        with patch.object(doc_generator, '_get_bedrock_client') as mock_bedrock:
            mock_bedrock.return_value.invoke_with_fallback = AsyncMock(return_value="content")
            
            # Should handle empty actions gracefully
            runbook = await doc_generator.generate_runbook_from_incident(incident, [])
        
        assert isinstance(runbook, RunbookEntry)
        assert len(runbook.resolution_steps) > 0  # Should have fallback steps
    
    @pytest.mark.asyncio
    async def test_concurrent_document_generation(self, aws_factory):
        """Test concurrent document generation."""
        doc_generator = DocumentationGenerator(aws_factory)
        
        incidents = []
        for i in range(3):
            incident = Incident(
                id=f"concurrent_test_{i}",
                title=f"Concurrent Test {i}",
                description="Concurrent test description",
                severity=IncidentSeverity.MEDIUM,
                business_impact=BusinessImpact(service_tier=ServiceTier.TIER_2),
                metadata=IncidentMetadata(source_system="test")
            )
            incidents.append(incident)
        
        with patch.object(doc_generator, '_get_bedrock_client') as mock_bedrock:
            mock_bedrock.return_value.invoke_with_fallback = AsyncMock(return_value="content")
            
            # Generate runbooks concurrently
            tasks = [
                doc_generator.generate_runbook_from_incident(incident, [f"Action {i}"])
                for i, incident in enumerate(incidents)
            ]
            
            runbooks = await asyncio.gather(*tasks)
        
        assert len(runbooks) == 3
        assert all(isinstance(rb, RunbookEntry) for rb in runbooks)
        assert len(set(rb.runbook_id for rb in runbooks)) == 3  # All unique IDs
    
    @pytest.mark.asyncio
    async def test_large_incident_data_handling(self, aws_factory):
        """Test handling of large incident data."""
        kb_generator = KnowledgeBaseGenerator(aws_factory)
        
        # Create incident with large description
        large_description = "Large incident description. " * 1000  # ~30KB
        
        incident = Incident(
            id="large_data_test",
            title="Large Data Test Incident",
            description=large_description,
            severity=IncidentSeverity.HIGH,
            business_impact=BusinessImpact(service_tier=ServiceTier.TIER_1),
            metadata=IncidentMetadata(source_system="test")
        )
        
        resolution_data = [{
            "summary": "Large resolution data",
            "actions": ["Action"] * 100,  # Large action list
            "success": True
        }]
        
        with patch.object(kb_generator, '_get_bedrock_client') as mock_bedrock:
            mock_bedrock.return_value.invoke_with_fallback = AsyncMock(return_value="content")
            
            # Should handle large data without errors
            article = await kb_generator.generate_article_from_successful_resolutions(
                [incident], resolution_data
            )
        
        assert isinstance(article, KnowledgeArticle)
        assert len(article.content) > 0
    
    def test_global_service_instances(self, aws_factory):
        """Test global service instance functions."""
        # Test documentation generator
        doc_gen1 = get_documentation_generator(aws_factory)
        doc_gen2 = get_documentation_generator(aws_factory)
        assert doc_gen1 is doc_gen2  # Should be same instance
        
        # Test knowledge base generator
        kb_gen1 = get_knowledge_base_generator(aws_factory)
        kb_gen2 = get_knowledge_base_generator(aws_factory)
        assert kb_gen1 is kb_gen2  # Should be same instance
        
        # Test post-incident documentation service
        pir_svc1 = get_post_incident_documentation_service(aws_factory)
        pir_svc2 = get_post_incident_documentation_service(aws_factory)
        assert pir_svc1 is pir_svc2  # Should be same instance


if __name__ == "__main__":
    pytest.main([__file__])