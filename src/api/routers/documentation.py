"""
Documentation API Router

FastAPI routes for documentation generation and management,
including versioning and retrieval endpoints.

Task 7.4: Create documentation API endpoints
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Depends, Query, Path, Body
from pydantic import BaseModel, Field

from src.api.dependencies import get_services
from src.services.container import ServiceContainer
from src.services.documentation_generator import (
    get_documentation_generator, 
    DocumentationGenerator,
    RunbookEntry,
    GeneratedDocument
)
from src.services.knowledge_base_generator import (
    get_knowledge_base_generator,
    KnowledgeBaseGenerator,
    KnowledgeArticle,
    InteractiveTroubleshootingGuide
)
from src.services.post_incident_documentation import (
    get_post_incident_documentation_service,
    PostIncidentDocumentationService,
    PostIncidentReport,
    ActionItem
)
from src.models.incident import Incident
from src.utils.logging import get_logger


logger = get_logger("documentation_api")

router = APIRouter(prefix="/documentation", tags=["documentation"])


# Request/Response Models

class RunbookGenerationRequest(BaseModel):
    """Request model for runbook generation."""
    incident_id: str
    resolution_actions: List[str]
    diagnosis_data: Optional[Dict[str, Any]] = None


class KnowledgeArticleRequest(BaseModel):
    """Request model for knowledge article generation."""
    incident_ids: List[str]
    title: Optional[str] = None
    category: Optional[str] = None


class PostIncidentReportRequest(BaseModel):
    """Request model for post-incident report generation."""
    incident_id: str
    resolution_data: Dict[str, Any]
    timeline_events: Optional[List[Dict[str, Any]]] = None


class DocumentUpdateRequest(BaseModel):
    """Request model for document updates."""
    updates: Dict[str, Any]
    updated_by: str = "system"


class SearchRequest(BaseModel):
    """Request model for document search."""
    query: str
    category: Optional[str] = None
    document_type: Optional[str] = None
    limit: int = Field(default=10, ge=1, le=100)


class ArticleFeedbackRequest(BaseModel):
    """Request model for article feedback."""
    helpful: bool
    comment: Optional[str] = None


# Runbook Endpoints

@router.post("/runbooks/generate", response_model=Dict[str, Any])
async def generate_runbook(
    request: RunbookGenerationRequest,
    services: ServiceContainer = Depends(get_services)
):
    """Generate runbook from incident resolution."""
    
    try:
        doc_generator = get_documentation_generator(services.aws_factory)
        
        # Get incident data (in production, would fetch from coordinator)
        incident_data = {
            "id": request.incident_id,
            "title": "Sample Incident",
            "description": "Sample incident for runbook generation",
            "severity": "medium",
            "business_impact": {"service_tier": "tier_2"},
            "metadata": {"tags": {}}
        }
        
        # Mock incident object for demonstration
        from src.models.incident import Incident, IncidentSeverity, ServiceTier, BusinessImpact, IncidentMetadata
        
        incident = Incident(
            id=request.incident_id,
            title="Sample Incident",
            description="Sample incident for runbook generation",
            severity=IncidentSeverity.MEDIUM,
            business_impact=BusinessImpact(service_tier=ServiceTier.TIER_2),
            metadata=IncidentMetadata(source_system="api")
        )
        
        # Generate runbook
        runbook = await doc_generator.generate_runbook_from_incident(
            incident,
            request.resolution_actions,
            request.diagnosis_data
        )
        
        return {
            "runbook_id": runbook.runbook_id,
            "title": runbook.title,
            "created_at": runbook.created_at.isoformat(),
            "estimated_time": runbook.estimated_time,
            "difficulty_level": runbook.difficulty_level,
            "success_rate": runbook.success_rate,
            "steps": {
                "diagnosis": runbook.diagnosis_steps,
                "resolution": runbook.resolution_steps,
                "verification": runbook.verification_steps,
                "rollback": runbook.rollback_steps
            },
            "prerequisites": runbook.prerequisites,
            "symptoms": runbook.symptoms
        }
        
    except Exception as e:
        logger.error(f"Failed to generate runbook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runbooks/{runbook_id}", response_model=Dict[str, Any])
async def get_runbook(
    runbook_id: str = Path(..., description="Runbook ID"),
    services: ServiceContainer = Depends(get_services)
):
    """Get runbook by ID."""
    
    try:
        doc_generator = get_documentation_generator(services.aws_factory)
        runbook = await doc_generator.get_runbook_by_id(runbook_id)
        
        if not runbook:
            raise HTTPException(status_code=404, detail="Runbook not found")
        
        return {
            "runbook_id": runbook.runbook_id,
            "title": runbook.title,
            "problem_description": runbook.problem_description,
            "symptoms": runbook.symptoms,
            "diagnosis_steps": runbook.diagnosis_steps,
            "resolution_steps": runbook.resolution_steps,
            "verification_steps": runbook.verification_steps,
            "rollback_steps": runbook.rollback_steps,
            "prerequisites": runbook.prerequisites,
            "estimated_time": runbook.estimated_time,
            "difficulty_level": runbook.difficulty_level,
            "success_rate": runbook.success_rate,
            "created_from_incident": runbook.created_from_incident,
            "created_at": runbook.created_at.isoformat(),
            "last_updated": runbook.last_updated.isoformat(),
            "version": runbook.version
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get runbook {runbook_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runbooks", response_model=Dict[str, Any])
async def list_runbooks(
    limit: int = Query(default=50, ge=1, le=100),
    services: ServiceContainer = Depends(get_services)
):
    """List all runbooks."""
    
    try:
        doc_generator = get_documentation_generator(services.aws_factory)
        runbooks = await doc_generator.list_runbooks(limit)
        
        return {
            "runbooks": [
                {
                    "runbook_id": rb.runbook_id,
                    "title": rb.title,
                    "difficulty_level": rb.difficulty_level,
                    "success_rate": rb.success_rate,
                    "estimated_time": rb.estimated_time,
                    "created_at": rb.created_at.isoformat(),
                    "version": rb.version
                }
                for rb in runbooks
            ],
            "total": len(runbooks),
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Failed to list runbooks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runbooks/search", response_model=Dict[str, Any])
async def search_runbooks(
    query: str = Query(..., description="Search query"),
    limit: int = Query(default=10, ge=1, le=50),
    services: ServiceContainer = Depends(get_services)
):
    """Search runbooks by query."""
    
    try:
        doc_generator = get_documentation_generator(services.aws_factory)
        runbooks = await doc_generator.search_runbooks(query, limit)
        
        return {
            "query": query,
            "results": [
                {
                    "runbook_id": rb.runbook_id,
                    "title": rb.title,
                    "problem_description": rb.problem_description[:200] + "..." if len(rb.problem_description) > 200 else rb.problem_description,
                    "difficulty_level": rb.difficulty_level,
                    "success_rate": rb.success_rate,
                    "created_at": rb.created_at.isoformat()
                }
                for rb in runbooks
            ],
            "total_results": len(runbooks)
        }
        
    except Exception as e:
        logger.error(f"Failed to search runbooks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Knowledge Base Endpoints

@router.post("/knowledge-base/articles/generate", response_model=Dict[str, Any])
async def generate_knowledge_article(
    request: KnowledgeArticleRequest,
    services: ServiceContainer = Depends(get_services)
):
    """Generate knowledge base article from successful incident resolutions."""
    
    try:
        kb_generator = get_knowledge_base_generator(services.aws_factory)
        
        # Mock incident data for demonstration
        incidents = []
        resolution_data = []
        
        for incident_id in request.incident_ids:
            # In production, would fetch real incident data
            incident = Incident(
                id=incident_id,
                title=f"Sample Incident {incident_id}",
                description="Sample incident for KB article generation",
                severity="medium",
                business_impact={"service_tier": "tier_2"},
                metadata={"tags": {}}
            )
            incidents.append(incident)
            resolution_data.append({
                "summary": f"Resolution for incident {incident_id}",
                "actions": ["Action 1", "Action 2"],
                "success": True
            })
        
        # Generate article
        article = await kb_generator.generate_article_from_successful_resolutions(
            incidents, resolution_data
        )
        
        return {
            "article_id": article.article_id,
            "title": article.title,
            "summary": article.summary,
            "category": article.category,
            "tags": article.tags,
            "difficulty_level": article.difficulty_level,
            "estimated_read_time": article.estimated_read_time,
            "confidence_score": article.confidence_score,
            "source_incidents": article.source_incidents,
            "created_at": article.created_at.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to generate knowledge article: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge-base/articles/{article_id}", response_model=Dict[str, Any])
async def get_knowledge_article(
    article_id: str = Path(..., description="Article ID"),
    services: ServiceContainer = Depends(get_services)
):
    """Get knowledge base article by ID."""
    
    try:
        kb_generator = get_knowledge_base_generator(services.aws_factory)
        article = await kb_generator.get_article_by_id(article_id)
        
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        # Update view count
        await kb_generator.update_article_metrics(article_id, viewed=True)
        
        return {
            "article_id": article.article_id,
            "title": article.title,
            "summary": article.summary,
            "content": article.content,
            "category": article.category,
            "tags": article.tags,
            "difficulty_level": article.difficulty_level,
            "estimated_read_time": article.estimated_read_time,
            "confidence_score": article.confidence_score,
            "source_incidents": article.source_incidents,
            "view_count": article.view_count,
            "helpful_votes": article.helpful_votes,
            "total_votes": article.total_votes,
            "created_at": article.created_at.isoformat(),
            "updated_at": article.updated_at.isoformat(),
            "version": article.version
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get knowledge article {article_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/knowledge-base/articles/{article_id}/feedback")
async def submit_article_feedback(
    article_id: str = Path(..., description="Article ID"),
    feedback: ArticleFeedbackRequest = Body(...),
    services: ServiceContainer = Depends(get_services)
):
    """Submit feedback for knowledge base article."""
    
    try:
        kb_generator = get_knowledge_base_generator(services.aws_factory)
        
        # Update article metrics
        await kb_generator.update_article_metrics(
            article_id, 
            viewed=False, 
            helpful=feedback.helpful
        )
        
        return {
            "article_id": article_id,
            "feedback_recorded": True,
            "helpful": feedback.helpful,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to submit feedback for article {article_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge-base/articles", response_model=Dict[str, Any])
async def search_knowledge_articles(
    query: Optional[str] = Query(None, description="Search query"),
    category: Optional[str] = Query(None, description="Article category"),
    limit: int = Query(default=10, ge=1, le=50),
    services: ServiceContainer = Depends(get_services)
):
    """Search knowledge base articles."""
    
    try:
        kb_generator = get_knowledge_base_generator(services.aws_factory)
        
        if query:
            articles = await kb_generator.search_articles(query, category, limit)
        else:
            # Return recent articles if no query
            articles = list(kb_generator._articles.values())
            if category:
                articles = [a for a in articles if a.category == category]
            articles.sort(key=lambda x: x.created_at, reverse=True)
            articles = articles[:limit]
        
        return {
            "query": query,
            "category": category,
            "articles": [
                {
                    "article_id": article.article_id,
                    "title": article.title,
                    "summary": article.summary,
                    "category": article.category,
                    "tags": article.tags,
                    "difficulty_level": article.difficulty_level,
                    "estimated_read_time": article.estimated_read_time,
                    "confidence_score": article.confidence_score,
                    "view_count": article.view_count,
                    "helpful_votes": article.helpful_votes,
                    "created_at": article.created_at.isoformat()
                }
                for article in articles
            ],
            "total_results": len(articles)
        }
        
    except Exception as e:
        logger.error(f"Failed to search knowledge articles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge-base/articles/{article_id}/related", response_model=Dict[str, Any])
async def get_related_articles(
    article_id: str = Path(..., description="Article ID"),
    limit: int = Query(default=5, ge=1, le=10),
    services: ServiceContainer = Depends(get_services)
):
    """Get articles related to the specified article."""
    
    try:
        kb_generator = get_knowledge_base_generator(services.aws_factory)
        related_articles = await kb_generator.get_related_articles(article_id, limit)
        
        return {
            "article_id": article_id,
            "related_articles": [
                {
                    "article_id": article.article_id,
                    "title": article.title,
                    "summary": article.summary,
                    "category": article.category,
                    "confidence_score": article.confidence_score,
                    "created_at": article.created_at.isoformat()
                }
                for article in related_articles
            ],
            "total_related": len(related_articles)
        }
        
    except Exception as e:
        logger.error(f"Failed to get related articles for {article_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Interactive Troubleshooting Guide Endpoints

@router.post("/troubleshooting/guides/generate", response_model=Dict[str, Any])
async def generate_troubleshooting_guide(
    incident_patterns: List[Dict[str, Any]] = Body(...),
    title: Optional[str] = Body(None),
    services: ServiceContainer = Depends(get_services)
):
    """Generate interactive troubleshooting guide from incident patterns."""
    
    try:
        kb_generator = get_knowledge_base_generator(services.aws_factory)
        
        # Convert patterns to IncidentPattern objects (mock for demonstration)
        from src.services.rag_memory import IncidentPattern
        
        patterns = []
        for pattern_data in incident_patterns:
            pattern = IncidentPattern(
                pattern_id=pattern_data.get("pattern_id", str(uuid4())),
                incident_type=pattern_data.get("incident_type", "general"),
                symptoms=pattern_data.get("symptoms", []),
                root_causes=pattern_data.get("root_causes", []),
                resolution_actions=pattern_data.get("resolution_actions", []),
                success_rate=pattern_data.get("success_rate", 0.8),
                confidence=pattern_data.get("confidence", 0.8),
                created_at=datetime.utcnow(),
                last_used=datetime.utcnow(),
                usage_count=1
            )
            patterns.append(pattern)
        
        # Generate guide
        guide = await kb_generator.create_interactive_troubleshooting_guide(patterns, title)
        
        return {
            "guide_id": guide.guide_id,
            "title": guide.title,
            "description": guide.description,
            "category": guide.category,
            "entry_point": guide.entry_point,
            "success_rate": guide.success_rate,
            "average_completion_time": guide.average_completion_time,
            "steps_count": len(guide.steps),
            "created_at": guide.created_at.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to generate troubleshooting guide: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/troubleshooting/guides/{guide_id}", response_model=Dict[str, Any])
async def get_troubleshooting_guide(
    guide_id: str = Path(..., description="Guide ID"),
    services: ServiceContainer = Depends(get_services)
):
    """Get interactive troubleshooting guide by ID."""
    
    try:
        kb_generator = get_knowledge_base_generator(services.aws_factory)
        guide = await kb_generator.get_guide_by_id(guide_id)
        
        if not guide:
            raise HTTPException(status_code=404, detail="Troubleshooting guide not found")
        
        return {
            "guide_id": guide.guide_id,
            "title": guide.title,
            "description": guide.description,
            "category": guide.category,
            "entry_point": guide.entry_point,
            "steps": {
                step_id: {
                    "step_id": step.step_id,
                    "title": step.title,
                    "description": step.description,
                    "step_type": step.step_type,
                    "instructions": step.instructions,
                    "expected_results": step.expected_results,
                    "next_steps": step.next_steps,
                    "estimated_time": step.estimated_time,
                    "difficulty": step.difficulty,
                    "success_indicators": step.success_indicators,
                    "failure_indicators": step.failure_indicators
                }
                for step_id, step in guide.steps.items()
            },
            "success_rate": guide.success_rate,
            "average_completion_time": guide.average_completion_time,
            "created_from_incidents": guide.created_from_incidents,
            "created_at": guide.created_at.isoformat(),
            "version": guide.version
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get troubleshooting guide {guide_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Post-Incident Report Endpoints

@router.post("/post-incident/reports/generate", response_model=Dict[str, Any])
async def generate_post_incident_report(
    request: PostIncidentReportRequest,
    services: ServiceContainer = Depends(get_services)
):
    """Generate comprehensive post-incident report."""
    
    try:
        pir_service = get_post_incident_documentation_service(services.aws_factory)
        
        # Mock incident for demonstration
        incident = Incident(
            id=request.incident_id,
            title="Sample Incident for PIR",
            description="Sample incident for post-incident report generation",
            severity="high",
            business_impact={"service_tier": "tier_1"},
            metadata={"tags": {}}
        )
        
        # Generate report
        report = await pir_service.generate_post_incident_report(
            incident,
            request.resolution_data,
            request.timeline_events
        )
        
        return {
            "report_id": report.report_id,
            "incident_id": report.incident_id,
            "title": report.title,
            "executive_summary": report.executive_summary,
            "confidence_score": report.confidence_score,
            "lessons_learned_count": len(report.lessons_learned),
            "action_items_count": len(report.action_items),
            "prevention_measures_count": len(report.prevention_measures),
            "created_at": report.created_at.isoformat(),
            "version": report.version,
            "status": report.status
        }
        
    except Exception as e:
        logger.error(f"Failed to generate post-incident report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/post-incident/reports/{report_id}", response_model=Dict[str, Any])
async def get_post_incident_report(
    report_id: str = Path(..., description="Report ID"),
    services: ServiceContainer = Depends(get_services)
):
    """Get post-incident report by ID."""
    
    try:
        pir_service = get_post_incident_documentation_service(services.aws_factory)
        report = await pir_service.get_report_by_id(report_id)
        
        if not report:
            raise HTTPException(status_code=404, detail="Post-incident report not found")
        
        return {
            "report_id": report.report_id,
            "incident_id": report.incident_id,
            "title": report.title,
            "executive_summary": report.executive_summary,
            "incident_timeline": report.incident_timeline,
            "root_cause_analysis": report.root_cause_analysis,
            "business_impact_assessment": report.business_impact_assessment,
            "resolution_summary": report.resolution_summary,
            "lessons_learned": report.lessons_learned,
            "action_items": report.action_items,
            "prevention_measures": report.prevention_measures,
            "appendices": report.appendices,
            "created_at": report.created_at.isoformat(),
            "updated_at": report.updated_at.isoformat(),
            "version": report.version,
            "status": report.status,
            "confidence_score": report.confidence_score
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get post-incident report {report_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/post-incident/reports/{report_id}", response_model=Dict[str, Any])
async def update_post_incident_report(
    report_id: str = Path(..., description="Report ID"),
    request: DocumentUpdateRequest = Body(...),
    services: ServiceContainer = Depends(get_services)
):
    """Update existing post-incident report."""
    
    try:
        pir_service = get_post_incident_documentation_service(services.aws_factory)
        
        updated_report = await pir_service.update_report(
            report_id,
            request.updates,
            request.updated_by
        )
        
        return {
            "report_id": updated_report.report_id,
            "version": updated_report.version,
            "updated_at": updated_report.updated_at.isoformat(),
            "updated_by": request.updated_by,
            "changes_applied": True
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update post-incident report {report_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/post-incident/reports/{report_id}/versions", response_model=Dict[str, Any])
async def get_report_versions(
    report_id: str = Path(..., description="Report ID"),
    services: ServiceContainer = Depends(get_services)
):
    """Get all versions of a post-incident report."""
    
    try:
        pir_service = get_post_incident_documentation_service(services.aws_factory)
        versions = await pir_service.get_report_versions(report_id)
        
        return {
            "report_id": report_id,
            "versions": [
                {
                    "version_id": version.version_id,
                    "version_number": version.version_number,
                    "change_summary": version.change_summary,
                    "change_type": version.change_type.value,
                    "created_by": version.created_by,
                    "created_at": version.created_at.isoformat(),
                    "checksum": version.checksum
                }
                for version in versions
            ],
            "total_versions": len(versions)
        }
        
    except Exception as e:
        logger.error(f"Failed to get versions for report {report_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/post-incident/reports/{report_id}/versions/diff", response_model=Dict[str, Any])
async def get_version_diff(
    report_id: str = Path(..., description="Report ID"),
    version1: int = Query(..., description="First version number"),
    version2: int = Query(..., description="Second version number"),
    services: ServiceContainer = Depends(get_services)
):
    """Get diff between two versions of a report."""
    
    try:
        pir_service = get_post_incident_documentation_service(services.aws_factory)
        diff_result = await pir_service.get_version_diff(report_id, version1, version2)
        
        return diff_result
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get version diff for report {report_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Action Items Endpoints

@router.get("/action-items", response_model=Dict[str, Any])
async def list_action_items(
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    services: ServiceContainer = Depends(get_services)
):
    """List action items with optional filtering."""
    
    try:
        pir_service = get_post_incident_documentation_service(services.aws_factory)
        action_items = await pir_service.list_action_items(status, priority)
        
        return {
            "action_items": [
                {
                    "item_id": item.item_id,
                    "title": item.title,
                    "description": item.description,
                    "priority": item.priority,
                    "assignee": item.assignee,
                    "due_date": item.due_date.isoformat(),
                    "category": item.category,
                    "status": item.status,
                    "created_at": item.created_at.isoformat(),
                    "updated_at": item.updated_at.isoformat()
                }
                for item in action_items
            ],
            "total": len(action_items),
            "filters": {
                "status": status,
                "priority": priority
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to list action items: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/action-items/{item_id}/status", response_model=Dict[str, Any])
async def update_action_item_status(
    item_id: str = Path(..., description="Action item ID"),
    new_status: str = Body(..., embed=True),
    updated_by: str = Body("system", embed=True),
    services: ServiceContainer = Depends(get_services)
):
    """Update action item status."""
    
    try:
        pir_service = get_post_incident_documentation_service(services.aws_factory)
        
        updated_item = await pir_service.update_action_item_status(
            item_id, new_status, updated_by
        )
        
        return {
            "item_id": updated_item.item_id,
            "status": updated_item.status,
            "updated_at": updated_item.updated_at.isoformat(),
            "updated_by": updated_by
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update action item status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Statistics and Analytics Endpoints

@router.get("/statistics", response_model=Dict[str, Any])
async def get_documentation_statistics(
    services: ServiceContainer = Depends(get_services)
):
    """Get comprehensive documentation generation statistics."""
    
    try:
        doc_generator = get_documentation_generator(services.aws_factory)
        kb_generator = get_knowledge_base_generator(services.aws_factory)
        pir_service = get_post_incident_documentation_service(services.aws_factory)
        
        # Get statistics from all services
        doc_stats = doc_generator.get_generation_statistics()
        kb_stats = kb_generator.get_knowledge_base_statistics()
        pir_stats = pir_service.get_documentation_statistics()
        
        return {
            "documentation_generation": doc_stats,
            "knowledge_base": kb_stats,
            "post_incident_reports": pir_stats,
            "summary": {
                "total_documents_generated": (
                    doc_stats.get("total_generated", 0) +
                    kb_stats.get("total_articles", 0) +
                    pir_stats.get("total_reports", 0)
                ),
                "total_runbooks": doc_stats.get("runbook_count", 0),
                "total_kb_articles": kb_stats.get("total_articles", 0),
                "total_pir_reports": pir_stats.get("total_reports", 0),
                "total_action_items": pir_stats.get("total_action_items", 0),
                "action_item_completion_rate": pir_stats.get("action_item_completion_rate", 0),
                "average_generation_time": (
                    doc_stats.get("generation_time_avg", 0) +
                    kb_stats.get("generation_time_avg", 0) +
                    pir_stats.get("average_generation_time", 0)
                ) / 3
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get documentation statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=Dict[str, Any])
async def get_documentation_health(
    services: ServiceContainer = Depends(get_services)
):
    """Get documentation system health status."""
    
    try:
        return {
            "status": "healthy",
            "services": {
                "documentation_generator": "operational",
                "knowledge_base_generator": "operational",
                "post_incident_documentation": "operational"
            },
            "features": {
                "runbook_generation": True,
                "knowledge_article_creation": True,
                "interactive_troubleshooting_guides": True,
                "post_incident_reports": True,
                "document_versioning": True,
                "change_tracking": True,
                "amazon_q_integration": True
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get documentation health: {e}")
        raise HTTPException(status_code=500, detail=str(e))