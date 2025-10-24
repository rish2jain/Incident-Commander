"""
Documentation Generation Service

Automated documentation generation using Amazon Q integration for
runbook updates and knowledge base article creation.

Task 7.1: Create documentation generator service
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from uuid import uuid4
import hashlib

from src.models.incident import Incident, IncidentStatus
from src.services.aws import AWSServiceFactory, BedrockClient
from src.services.rag_memory import get_rag_memory, IncidentPattern
from src.amazon_q_integration import AmazonQIncidentAnalyzer
from src.utils.logging import get_logger
from src.utils.config import config


logger = get_logger("documentation_generator")


@dataclass
class DocumentationTemplate:
    """Template for different types of documentation."""
    template_id: str
    name: str
    description: str
    template_content: str
    variables: List[str]
    category: str
    created_at: datetime
    version: str


@dataclass
class GeneratedDocument:
    """Represents a generated documentation artifact."""
    document_id: str
    title: str
    content: str
    document_type: str
    source_incident_id: Optional[str]
    template_id: Optional[str]
    metadata: Dict[str, Any]
    created_at: datetime
    version: int
    checksum: str


@dataclass
class RunbookEntry:
    """Represents a runbook entry generated from incident resolution."""
    runbook_id: str
    title: str
    problem_description: str
    symptoms: List[str]
    diagnosis_steps: List[str]
    resolution_steps: List[str]
    verification_steps: List[str]
    rollback_steps: List[str]
    prerequisites: List[str]
    estimated_time: str
    difficulty_level: str
    success_rate: float
    created_from_incident: str
    created_at: datetime
    last_updated: datetime
    version: int


class DocumentationGenerator:
    """Service for automated documentation generation using Amazon Q."""
    
    def __init__(self, service_factory: AWSServiceFactory):
        """Initialize documentation generator."""
        self._service_factory = service_factory
        self._bedrock_client = None
        self._q_analyzer = AmazonQIncidentAnalyzer()
        self._rag_memory = None
        
        # Document storage
        self._generated_documents: Dict[str, GeneratedDocument] = {}
        self._runbooks: Dict[str, RunbookEntry] = {}
        self._templates: Dict[str, DocumentationTemplate] = {}
        
        # Performance tracking
        self._generation_stats = {
            "total_generated": 0,
            "runbooks_created": 0,
            "kb_articles_created": 0,
            "post_incident_reports": 0,
            "generation_time_avg": 0.0
        }
        
        # Initialize default templates
        self._initialize_default_templates()
    
    async def _get_bedrock_client(self) -> BedrockClient:
        """Get or create Bedrock client."""
        if not self._bedrock_client:
            self._bedrock_client = BedrockClient(self._service_factory)
        return self._bedrock_client
    
    async def _get_rag_memory(self):
        """Get RAG memory instance."""
        if not self._rag_memory:
            self._rag_memory = await get_rag_memory(self._service_factory)
        return self._rag_memory
    
    def _initialize_default_templates(self) -> None:
        """Initialize default documentation templates."""
        
        # Runbook template
        runbook_template = DocumentationTemplate(
            template_id="runbook_standard",
            name="Standard Runbook Template",
            description="Template for creating incident resolution runbooks",
            template_content="""# {title}

## Problem Description
{problem_description}

## Symptoms
{symptoms}

## Prerequisites
{prerequisites}

## Diagnosis Steps
{diagnosis_steps}

## Resolution Steps
{resolution_steps}

## Verification Steps
{verification_steps}

## Rollback Steps
{rollback_steps}

## Metadata
- **Estimated Time**: {estimated_time}
- **Difficulty Level**: {difficulty_level}
- **Success Rate**: {success_rate}%
- **Created From Incident**: {source_incident_id}
- **Last Updated**: {last_updated}
- **Version**: {version}

## Related Documentation
{related_docs}
""",
            variables=[
                "title", "problem_description", "symptoms", "prerequisites",
                "diagnosis_steps", "resolution_steps", "verification_steps",
                "rollback_steps", "estimated_time", "difficulty_level",
                "success_rate", "source_incident_id", "last_updated",
                "version", "related_docs"
            ],
            category="runbook",
            created_at=datetime.utcnow(),
            version="1.0"
        )
        
        # Knowledge base article template
        kb_template = DocumentationTemplate(
            template_id="kb_article_standard",
            name="Knowledge Base Article Template",
            description="Template for creating knowledge base articles",
            template_content="""# {title}

## Overview
{overview}

## Problem Statement
{problem_statement}

## Root Cause Analysis
{root_cause_analysis}

## Solution
{solution}

## Prevention Measures
{prevention_measures}

## Related Incidents
{related_incidents}

## Technical Details
{technical_details}

## References
{references}

---
*Generated automatically from incident resolution patterns*
*Last Updated: {last_updated}*
*Confidence Score: {confidence_score}*
""",
            variables=[
                "title", "overview", "problem_statement", "root_cause_analysis",
                "solution", "prevention_measures", "related_incidents",
                "technical_details", "references", "last_updated", "confidence_score"
            ],
            category="knowledge_base",
            created_at=datetime.utcnow(),
            version="1.0"
        )
        
        # Post-incident report template
        pir_template = DocumentationTemplate(
            template_id="post_incident_report",
            name="Post-Incident Report Template",
            description="Template for automated post-incident reports",
            template_content="""# Post-Incident Report: {incident_title}

## Executive Summary
{executive_summary}

## Incident Details
- **Incident ID**: {incident_id}
- **Severity**: {severity}
- **Start Time**: {start_time}
- **Resolution Time**: {resolution_time}
- **Duration**: {duration}
- **Business Impact**: {business_impact}

## Timeline
{timeline}

## Root Cause Analysis
{root_cause_analysis}

## Resolution Actions
{resolution_actions}

## Business Impact Assessment
{business_impact_assessment}

## Lessons Learned
{lessons_learned}

## Action Items
{action_items}

## Prevention Measures
{prevention_measures}

## Appendices
{appendices}

---
*Report generated automatically by Autonomous Incident Commander*
*Generated on: {generated_at}*
""",
            variables=[
                "incident_title", "executive_summary", "incident_id", "severity",
                "start_time", "resolution_time", "duration", "business_impact",
                "timeline", "root_cause_analysis", "resolution_actions",
                "business_impact_assessment", "lessons_learned", "action_items",
                "prevention_measures", "appendices", "generated_at"
            ],
            category="post_incident_report",
            created_at=datetime.utcnow(),
            version="1.0"
        )
        
        self._templates = {
            runbook_template.template_id: runbook_template,
            kb_template.template_id: kb_template,
            pir_template.template_id: pir_template
        }
    
    async def generate_runbook_from_incident(self, incident: Incident,
                                           resolution_actions: List[str],
                                           diagnosis_data: Dict[str, Any] = None) -> RunbookEntry:
        """Generate runbook from successful incident resolution."""
        
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Generating runbook from incident {incident.id}")
            
            # Get Amazon Q analysis for enhanced content
            q_analysis = await self._q_analyzer.analyze_incident_with_q({
                "incident_id": incident.id,
                "type": incident.business_impact.service_tier.value,
                "severity": incident.severity,
                "description": incident.description,
                "title": incident.title,
                "duration": incident.calculate_duration_minutes(),
                "affected_systems": incident.metadata.tags.get("affected_systems", [])
            })
            
            # Build runbook content using Q intelligence
            runbook_content = await self._build_runbook_content(
                incident, resolution_actions, q_analysis, diagnosis_data
            )
            
            # Create runbook entry
            runbook = RunbookEntry(
                runbook_id=str(uuid4()),
                title=f"Runbook: {incident.title}",
                problem_description=runbook_content["problem_description"],
                symptoms=runbook_content["symptoms"],
                diagnosis_steps=runbook_content["diagnosis_steps"],
                resolution_steps=runbook_content["resolution_steps"],
                verification_steps=runbook_content["verification_steps"],
                rollback_steps=runbook_content["rollback_steps"],
                prerequisites=runbook_content["prerequisites"],
                estimated_time=runbook_content["estimated_time"],
                difficulty_level=runbook_content["difficulty_level"],
                success_rate=runbook_content["success_rate"],
                created_from_incident=incident.id,
                created_at=datetime.utcnow(),
                last_updated=datetime.utcnow(),
                version=1
            )
            
            # Store runbook
            self._runbooks[runbook.runbook_id] = runbook
            
            # Update statistics
            self._generation_stats["runbooks_created"] += 1
            self._generation_stats["total_generated"] += 1
            
            generation_time = (datetime.utcnow() - start_time).total_seconds()
            self._update_average_generation_time(generation_time)
            
            logger.info(f"Generated runbook {runbook.runbook_id} in {generation_time:.2f}s")
            
            return runbook
            
        except Exception as e:
            logger.error(f"Failed to generate runbook from incident {incident.id}: {e}")
            raise
    
    async def _build_runbook_content(self, incident: Incident,
                                   resolution_actions: List[str],
                                   q_analysis: Dict[str, Any],
                                   diagnosis_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Build comprehensive runbook content using Amazon Q intelligence."""
        
        # Extract Q analysis data
        q_data = q_analysis.get("q_analysis", {})
        root_cause = q_data.get("root_cause", {})
        resolution_recs = q_data.get("resolution_recommendations", {})
        
        # Generate intelligent content using Amazon Q
        content_prompt = f"""Generate comprehensive runbook content for this incident:

**Incident Details:**
- Title: {incident.title}
- Description: {incident.description}
- Severity: {incident.severity}
- Service Tier: {incident.business_impact.service_tier.value}

**Root Cause Analysis:**
{root_cause.get('primary_cause', 'Unknown')}

**Resolution Actions Taken:**
{chr(10).join(f'- {action}' for action in resolution_actions)}

**Q Analysis Recommendations:**
{chr(10).join(f'- {rec}' for rec in resolution_recs.get('immediate_actions', []))}

Please provide:
1. Clear problem description
2. Observable symptoms
3. Step-by-step diagnosis procedure
4. Detailed resolution steps
5. Verification procedures
6. Rollback plan
7. Prerequisites and requirements
8. Time estimates and difficulty assessment
"""
        
        try:
            bedrock_client = await self._get_bedrock_client()
            enhanced_content = await bedrock_client.invoke_with_fallback(content_prompt)
            
            # Parse and structure the enhanced content
            structured_content = await self._parse_runbook_content(enhanced_content, incident, resolution_actions)
            
        except Exception as e:
            logger.warning(f"Failed to generate enhanced runbook content, using fallback: {e}")
            structured_content = self._generate_fallback_runbook_content(incident, resolution_actions)
        
        return structured_content
    
    async def _parse_runbook_content(self, enhanced_content: str,
                                   incident: Incident,
                                   resolution_actions: List[str]) -> Dict[str, Any]:
        """Parse enhanced content from Amazon Q into structured runbook data."""
        
        # For now, create structured content based on incident data
        # In production, this would use NLP to parse the enhanced_content
        
        return {
            "problem_description": f"{incident.description}\n\nThis incident affects {incident.business_impact.service_tier.value} services with {incident.severity} severity.",
            "symptoms": [
                incident.title,
                f"Service degradation in {incident.business_impact.service_tier.value} tier",
                f"Incident severity: {incident.severity}",
                "User reports of service issues"
            ],
            "diagnosis_steps": [
                "1. Check service health dashboards",
                "2. Review recent deployments and changes",
                "3. Analyze error logs and metrics",
                "4. Verify external dependencies",
                "5. Confirm resource utilization levels"
            ],
            "resolution_steps": [f"{i+1}. {action}" for i, action in enumerate(resolution_actions)],
            "verification_steps": [
                "1. Confirm service metrics return to baseline",
                "2. Verify error rates have decreased",
                "3. Test critical user workflows",
                "4. Monitor for 15 minutes to ensure stability"
            ],
            "rollback_steps": [
                "1. Revert configuration changes if applied",
                "2. Scale back any resource increases",
                "3. Restore previous deployment if rolled forward",
                "4. Re-enable any disabled services"
            ],
            "prerequisites": [
                "Access to monitoring dashboards",
                "Deployment permissions",
                "Service configuration access",
                "Incident response team notification"
            ],
            "estimated_time": f"{max(5, len(resolution_actions) * 2)}-{max(10, len(resolution_actions) * 3)} minutes",
            "difficulty_level": "Medium" if incident.severity in ["high", "critical"] else "Low",
            "success_rate": 95.0  # Based on successful resolution
        }
    
    def _generate_fallback_runbook_content(self, incident: Incident,
                                         resolution_actions: List[str]) -> Dict[str, Any]:
        """Generate fallback runbook content when enhanced generation fails."""
        
        return {
            "problem_description": f"Incident: {incident.title}\n\n{incident.description}",
            "symptoms": [incident.title, "Service performance degradation"],
            "diagnosis_steps": [
                "1. Check system metrics and logs",
                "2. Verify service dependencies",
                "3. Review recent changes"
            ],
            "resolution_steps": [f"{i+1}. {action}" for i, action in enumerate(resolution_actions)],
            "verification_steps": [
                "1. Verify service restoration",
                "2. Monitor for stability"
            ],
            "rollback_steps": [
                "1. Revert changes if issues persist"
            ],
            "prerequisites": ["System access", "Monitoring tools"],
            "estimated_time": "10-15 minutes",
            "difficulty_level": "Medium",
            "success_rate": 85.0
        }
    
    async def generate_knowledge_base_article(self, incident_patterns: List[IncidentPattern],
                                            title: str = None) -> GeneratedDocument:
        """Generate knowledge base article from incident resolution patterns."""
        
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Generating KB article from {len(incident_patterns)} patterns")
            
            # Analyze patterns to extract common themes
            article_content = await self._build_kb_article_content(incident_patterns, title)
            
            # Create document
            document = GeneratedDocument(
                document_id=str(uuid4()),
                title=article_content["title"],
                content=article_content["content"],
                document_type="knowledge_base_article",
                source_incident_id=None,  # Multiple sources
                template_id="kb_article_standard",
                metadata={
                    "pattern_count": len(incident_patterns),
                    "confidence_score": article_content["confidence_score"],
                    "categories": article_content["categories"],
                    "generated_by": "amazon_q_integration"
                },
                created_at=datetime.utcnow(),
                version=1,
                checksum=""
            )
            
            # Generate checksum
            document.checksum = self._generate_document_checksum(document)
            
            # Store document
            self._generated_documents[document.document_id] = document
            
            # Update statistics
            self._generation_stats["kb_articles_created"] += 1
            self._generation_stats["total_generated"] += 1
            
            generation_time = (datetime.utcnow() - start_time).total_seconds()
            self._update_average_generation_time(generation_time)
            
            logger.info(f"Generated KB article {document.document_id} in {generation_time:.2f}s")
            
            return document
            
        except Exception as e:
            logger.error(f"Failed to generate KB article: {e}")
            raise
    
    async def _build_kb_article_content(self, patterns: List[IncidentPattern],
                                      title: str = None) -> Dict[str, Any]:
        """Build knowledge base article content from incident patterns."""
        
        # Analyze patterns for common themes
        common_symptoms = self._extract_common_elements([p.symptoms for p in patterns])
        common_causes = self._extract_common_elements([p.root_causes for p in patterns])
        common_solutions = self._extract_common_elements([p.resolution_actions for p in patterns])
        
        # Generate intelligent article using Amazon Q
        if not title:
            title = f"Troubleshooting Guide: {patterns[0].incident_type.replace('_', ' ').title()}"
        
        article_prompt = f"""Create a comprehensive knowledge base article based on these incident patterns:

**Common Incident Type:** {patterns[0].incident_type}
**Number of Patterns:** {len(patterns)}
**Average Success Rate:** {sum(p.success_rate for p in patterns) / len(patterns):.1%}

**Common Symptoms:**
{chr(10).join(f'- {symptom}' for symptom in common_symptoms[:5])}

**Common Root Causes:**
{chr(10).join(f'- {cause}' for cause in common_causes[:5])}

**Common Solutions:**
{chr(10).join(f'- {solution}' for solution in common_solutions[:5])}

Please create a structured knowledge base article with:
1. Clear overview of the problem
2. Detailed problem statement
3. Root cause analysis
4. Step-by-step solution
5. Prevention measures
6. Technical details
"""
        
        try:
            bedrock_client = await self._get_bedrock_client()
            enhanced_content = await bedrock_client.invoke_with_fallback(article_prompt)
            
            # Structure the content
            structured_content = self._structure_kb_content(enhanced_content, patterns, title)
            
        except Exception as e:
            logger.warning(f"Failed to generate enhanced KB content, using fallback: {e}")
            structured_content = self._generate_fallback_kb_content(patterns, title)
        
        return structured_content
    
    def _extract_common_elements(self, element_lists: List[List[str]]) -> List[str]:
        """Extract common elements from multiple lists."""
        
        # Flatten all lists and count occurrences
        element_counts = {}
        for element_list in element_lists:
            for element in element_list:
                element_counts[element] = element_counts.get(element, 0) + 1
        
        # Sort by frequency and return most common
        sorted_elements = sorted(element_counts.items(), key=lambda x: x[1], reverse=True)
        return [element for element, count in sorted_elements if count > 1]
    
    def _structure_kb_content(self, enhanced_content: str,
                            patterns: List[IncidentPattern],
                            title: str) -> Dict[str, Any]:
        """Structure KB content from enhanced generation."""
        
        # Calculate confidence score based on pattern data
        avg_success_rate = sum(p.success_rate for p in patterns) / len(patterns)
        avg_confidence = sum(p.confidence for p in patterns) / len(patterns)
        confidence_score = (avg_success_rate + avg_confidence) / 2
        
        # Extract categories from patterns
        categories = list(set(p.incident_type for p in patterns))
        
        # For now, create structured content
        # In production, this would parse the enhanced_content
        template = self._templates["kb_article_standard"]
        
        content = template.template_content.format(
            title=title,
            overview=f"This article covers troubleshooting for {patterns[0].incident_type.replace('_', ' ')} incidents based on {len(patterns)} resolved cases.",
            problem_statement=f"Common issues affecting {patterns[0].incident_type.replace('_', ' ')} services.",
            root_cause_analysis="Analysis of common root causes based on historical incident data.",
            solution="Step-by-step resolution procedures with high success rates.",
            prevention_measures="Proactive measures to prevent similar incidents.",
            related_incidents=f"Based on {len(patterns)} similar incidents",
            technical_details="Technical implementation details and configuration requirements.",
            references="Generated from incident resolution patterns",
            last_updated=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            confidence_score=f"{confidence_score:.1%}"
        )
        
        return {
            "title": title,
            "content": content,
            "confidence_score": confidence_score,
            "categories": categories
        }
    
    def _generate_fallback_kb_content(self, patterns: List[IncidentPattern],
                                    title: str) -> Dict[str, Any]:
        """Generate fallback KB content when enhanced generation fails."""
        
        return {
            "title": title,
            "content": f"# {title}\n\nKnowledge base article generated from {len(patterns)} incident patterns.\n\n## Common Solutions\n\n" + 
                      "\n".join(f"- {action}" for pattern in patterns[:3] for action in pattern.resolution_actions[:2]),
            "confidence_score": 0.75,
            "categories": [patterns[0].incident_type]
        }
    
    def _generate_document_checksum(self, document: GeneratedDocument) -> str:
        """Generate checksum for document integrity."""
        
        content_data = {
            "title": document.title,
            "content": document.content,
            "document_type": document.document_type,
            "version": document.version
        }
        
        content_str = json.dumps(content_data, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()
    
    def _update_average_generation_time(self, generation_time: float) -> None:
        """Update average generation time statistics."""
        
        current_avg = self._generation_stats["generation_time_avg"]
        total_generated = self._generation_stats["total_generated"]
        
        # Calculate new average
        new_avg = ((current_avg * (total_generated - 1)) + generation_time) / total_generated
        self._generation_stats["generation_time_avg"] = new_avg
    
    async def get_runbook_by_id(self, runbook_id: str) -> Optional[RunbookEntry]:
        """Get runbook by ID."""
        return self._runbooks.get(runbook_id)
    
    async def get_document_by_id(self, document_id: str) -> Optional[GeneratedDocument]:
        """Get generated document by ID."""
        return self._generated_documents.get(document_id)
    
    async def list_runbooks(self, limit: int = 50) -> List[RunbookEntry]:
        """List all runbooks with optional limit."""
        runbooks = list(self._runbooks.values())
        runbooks.sort(key=lambda x: x.created_at, reverse=True)
        return runbooks[:limit]
    
    async def list_documents(self, document_type: str = None, limit: int = 50) -> List[GeneratedDocument]:
        """List generated documents with optional filtering."""
        documents = list(self._generated_documents.values())
        
        if document_type:
            documents = [doc for doc in documents if doc.document_type == document_type]
        
        documents.sort(key=lambda x: x.created_at, reverse=True)
        return documents[:limit]
    
    async def search_runbooks(self, query: str, limit: int = 10) -> List[RunbookEntry]:
        """Search runbooks by query string."""
        
        matching_runbooks = []
        query_lower = query.lower()
        
        for runbook in self._runbooks.values():
            # Simple text matching - in production would use vector search
            if (query_lower in runbook.title.lower() or 
                query_lower in runbook.problem_description.lower() or
                any(query_lower in symptom.lower() for symptom in runbook.symptoms)):
                matching_runbooks.append(runbook)
        
        # Sort by relevance (for now, just by creation date)
        matching_runbooks.sort(key=lambda x: x.created_at, reverse=True)
        return matching_runbooks[:limit]
    
    def get_generation_statistics(self) -> Dict[str, Any]:
        """Get documentation generation statistics."""
        
        return {
            **self._generation_stats,
            "runbook_count": len(self._runbooks),
            "document_count": len(self._generated_documents),
            "template_count": len(self._templates),
            "last_generation": max(
                [doc.created_at for doc in self._generated_documents.values()] +
                [rb.created_at for rb in self._runbooks.values()],
                default=None
            )
        }
    
    async def cleanup_old_documents(self, retention_days: int = 365) -> int:
        """Clean up old generated documents."""
        
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        # Find old documents
        old_document_ids = [
            doc_id for doc_id, doc in self._generated_documents.items()
            if doc.created_at < cutoff_date
        ]
        
        old_runbook_ids = [
            rb_id for rb_id, rb in self._runbooks.items()
            if rb.created_at < cutoff_date and rb.usage_count < 5  # Keep frequently used runbooks
        ]
        
        # Remove old documents
        for doc_id in old_document_ids:
            del self._generated_documents[doc_id]
        
        for rb_id in old_runbook_ids:
            del self._runbooks[rb_id]
        
        total_cleaned = len(old_document_ids) + len(old_runbook_ids)
        logger.info(f"Cleaned up {total_cleaned} old documentation artifacts")
        
        return total_cleaned


# Global documentation generator instance
_documentation_generator: Optional[DocumentationGenerator] = None


def get_documentation_generator(service_factory: AWSServiceFactory) -> DocumentationGenerator:
    """Get or create global documentation generator instance."""
    global _documentation_generator
    if _documentation_generator is None:
        _documentation_generator = DocumentationGenerator(service_factory)
    return _documentation_generator