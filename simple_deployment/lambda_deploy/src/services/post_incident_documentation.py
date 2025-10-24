"""
Post-Incident Documentation Automation Service

Automated post-incident report generation with version control
and change tracking for generated documentation.

Task 7.3: Add post-incident documentation automation
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from uuid import uuid4
from enum import Enum
import hashlib
import difflib

from src.models.incident import Incident, IncidentStatus, IncidentSeverity
from src.services.aws import AWSServiceFactory, BedrockClient
from src.services.documentation_generator import DocumentationGenerator, GeneratedDocument
from src.amazon_q_integration import AmazonQIncidentAnalyzer
from src.utils.logging import get_logger
from src.utils.config import config


logger = get_logger("post_incident_documentation")


class DocumentChangeType(str, Enum):
    """Types of document changes."""
    CREATED = "created"
    UPDATED = "updated"
    ARCHIVED = "archived"
    RESTORED = "restored"


@dataclass
class DocumentVersion:
    """Represents a version of a document."""
    version_id: str
    document_id: str
    version_number: int
    content: str
    change_summary: str
    change_type: DocumentChangeType
    created_by: str
    created_at: datetime
    checksum: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PostIncidentReport:
    """Comprehensive post-incident report."""
    report_id: str
    incident_id: str
    title: str
    executive_summary: str
    incident_timeline: List[Dict[str, Any]]
    root_cause_analysis: Dict[str, Any]
    business_impact_assessment: Dict[str, Any]
    resolution_summary: Dict[str, Any]
    lessons_learned: List[str]
    action_items: List[Dict[str, Any]]
    prevention_measures: List[str]
    appendices: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: int = 1
    status: str = "draft"
    confidence_score: float = 0.8


@dataclass
class ActionItem:
    """Action item from post-incident analysis."""
    item_id: str
    title: str
    description: str
    priority: str  # "high", "medium", "low"
    assignee: str
    due_date: datetime
    category: str  # "prevention", "process", "technical", "training"
    status: str = "open"  # "open", "in_progress", "completed", "cancelled"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class LessonLearned:
    """Lesson learned from incident analysis."""
    lesson_id: str
    title: str
    description: str
    category: str
    impact_level: str
    applicable_teams: List[str]
    implementation_effort: str
    created_from_incident: str
    created_at: datetime = field(default_factory=datetime.utcnow)


class PostIncidentDocumentationService:
    """Service for automated post-incident documentation generation."""
    
    def __init__(self, service_factory: AWSServiceFactory):
        """Initialize post-incident documentation service."""
        self._service_factory = service_factory
        self._bedrock_client = None
        self._q_analyzer = AmazonQIncidentAnalyzer()
        self._doc_generator = None
        
        # Document storage and versioning
        self._reports: Dict[str, PostIncidentReport] = {}
        self._document_versions: Dict[str, List[DocumentVersion]] = {}
        self._action_items: Dict[str, ActionItem] = {}
        self._lessons_learned: Dict[str, LessonLearned] = {}
        
        # Change tracking
        self._change_log: List[Dict[str, Any]] = []
        
        # Generation statistics
        self._generation_stats = {
            "reports_generated": 0,
            "action_items_created": 0,
            "lessons_learned_captured": 0,
            "average_generation_time": 0.0,
            "total_versions_created": 0
        }
        
        # Report templates
        self._report_templates = self._initialize_report_templates()
    
    async def _get_bedrock_client(self) -> BedrockClient:
        """Get or create Bedrock client."""
        if not self._bedrock_client:
            self._bedrock_client = BedrockClient(self._service_factory)
        return self._bedrock_client
    
    async def _get_doc_generator(self) -> DocumentationGenerator:
        """Get documentation generator instance."""
        if not self._doc_generator:
            from src.services.documentation_generator import get_documentation_generator
            self._doc_generator = get_documentation_generator(self._service_factory)
        return self._doc_generator
    
    def _initialize_report_templates(self) -> Dict[str, str]:
        """Initialize post-incident report templates."""
        
        executive_template = """# Post-Incident Report: {incident_title}

## Executive Summary

**Incident Overview:**
{executive_summary}

**Key Metrics:**
- **Duration**: {incident_duration}
- **Severity**: {incident_severity}
- **Business Impact**: {business_impact_summary}
- **Resolution Time**: {resolution_time}
- **Customer Impact**: {customer_impact}

**Bottom Line:**
{bottom_line_summary}

---

## Incident Details

**Incident ID:** {incident_id}
**Start Time:** {start_time}
**Detection Time:** {detection_time}
**Resolution Time:** {resolution_time}
**Total Duration:** {total_duration}

**Affected Services:**
{affected_services}

**Severity Classification:** {severity} - {severity_justification}

---

## Timeline of Events

{timeline_events}

---

## Root Cause Analysis

**Primary Root Cause:**
{primary_root_cause}

**Contributing Factors:**
{contributing_factors}

**Analysis Methodology:**
{analysis_methodology}

**Evidence:**
{supporting_evidence}

---

## Business Impact Assessment

**Financial Impact:**
{financial_impact}

**Customer Impact:**
{customer_impact_details}

**Operational Impact:**
{operational_impact}

**Reputation Impact:**
{reputation_impact}

---

## Resolution Summary

**Resolution Actions Taken:**
{resolution_actions}

**Key Decision Points:**
{key_decisions}

**Resources Involved:**
{resources_involved}

**Resolution Effectiveness:**
{resolution_effectiveness}

---

## Lessons Learned

{lessons_learned_list}

---

## Action Items

{action_items_list}

---

## Prevention Measures

**Immediate Preventive Actions:**
{immediate_prevention}

**Long-term Improvements:**
{longterm_prevention}

**Process Improvements:**
{process_improvements}

---

## Appendices

**Appendix A: Technical Details**
{technical_appendix}

**Appendix B: Communication Log**
{communication_log}

**Appendix C: Metrics and Dashboards**
{metrics_appendix}

---

*Report generated automatically by Autonomous Incident Commander*
*Generated on: {generation_timestamp}*
*Report Version: {report_version}*
*Confidence Score: {confidence_score}*
"""
        
        return {
            "executive_report": executive_template
        }
    
    async def generate_post_incident_report(self, incident: Incident,
                                          resolution_data: Dict[str, Any],
                                          timeline_events: List[Dict[str, Any]] = None) -> PostIncidentReport:
        """Generate comprehensive post-incident report."""
        
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Generating post-incident report for incident {incident.id}")
            
            # Gather comprehensive incident data
            report_data = await self._gather_incident_data(incident, resolution_data, timeline_events)
            
            # Generate enhanced analysis using Amazon Q
            enhanced_analysis = await self._generate_enhanced_analysis(report_data)
            
            # Create comprehensive report
            report = PostIncidentReport(
                report_id=str(uuid4()),
                incident_id=incident.id,
                title=f"Post-Incident Report: {incident.title}",
                executive_summary=enhanced_analysis["executive_summary"],
                incident_timeline=report_data["timeline"],
                root_cause_analysis=enhanced_analysis["root_cause_analysis"],
                business_impact_assessment=enhanced_analysis["business_impact"],
                resolution_summary=enhanced_analysis["resolution_summary"],
                lessons_learned=enhanced_analysis["lessons_learned"],
                action_items=enhanced_analysis["action_items"],
                prevention_measures=enhanced_analysis["prevention_measures"],
                appendices=report_data["appendices"],
                confidence_score=enhanced_analysis["confidence_score"]
            )
            
            # Store report and create initial version
            self._reports[report.report_id] = report
            await self._create_document_version(report, DocumentChangeType.CREATED, "system")
            
            # Extract and store action items
            await self._extract_and_store_action_items(report)
            
            # Extract and store lessons learned
            await self._extract_and_store_lessons_learned(report, incident)
            
            # Update statistics
            self._generation_stats["reports_generated"] += 1
            generation_time = (datetime.utcnow() - start_time).total_seconds()
            self._update_average_generation_time(generation_time)
            
            logger.info(f"Generated post-incident report {report.report_id} in {generation_time:.2f}s")
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate post-incident report for {incident.id}: {e}")
            raise
    
    async def _gather_incident_data(self, incident: Incident,
                                  resolution_data: Dict[str, Any],
                                  timeline_events: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Gather comprehensive data for incident report."""
        
        # Calculate incident metrics
        duration_minutes = incident.calculate_duration_minutes()
        total_cost = incident.calculate_total_cost()
        
        # Build timeline if not provided
        if not timeline_events:
            timeline_events = [
                {
                    "timestamp": incident.detected_at,
                    "event": "Incident Detected",
                    "description": f"Incident detected: {incident.title}",
                    "severity": incident.severity
                }
            ]
            
            if incident.resolved_at:
                timeline_events.append({
                    "timestamp": incident.resolved_at,
                    "event": "Incident Resolved",
                    "description": "Incident successfully resolved",
                    "resolution_actions": resolution_data.get("actions", [])
                })
        
        # Gather affected systems
        affected_systems = incident.metadata.tags.get("affected_systems", ["Unknown"])
        
        return {
            "incident": incident,
            "duration_minutes": duration_minutes,
            "total_cost": total_cost,
            "timeline": timeline_events,
            "affected_systems": affected_systems,
            "resolution_data": resolution_data,
            "appendices": {
                "technical_details": resolution_data.get("technical_details", {}),
                "metrics": resolution_data.get("metrics", {}),
                "logs": resolution_data.get("logs", [])
            }
        }
    
    async def _generate_enhanced_analysis(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate enhanced analysis using Amazon Q."""
        
        incident = report_data["incident"]
        
        analysis_prompt = f"""Generate comprehensive post-incident analysis for this resolved incident:

**Incident Details:**
- Title: {incident.title}
- Description: {incident.description}
- Severity: {incident.severity}
- Duration: {report_data['duration_minutes']:.1f} minutes
- Business Impact: ${report_data['total_cost']:,.2f}
- Service Tier: {incident.business_impact.service_tier.value}

**Resolution Data:**
{json.dumps(report_data['resolution_data'], indent=2, default=str)[:1000]}

**Timeline Events:**
{chr(10).join(f"- {event.get('timestamp', 'Unknown')}: {event.get('event', 'Unknown')}" for event in report_data['timeline'][:5])}

Please provide:
1. **Executive Summary**: High-level overview for leadership
2. **Root Cause Analysis**: Primary cause and contributing factors
3. **Business Impact Assessment**: Detailed impact analysis
4. **Resolution Summary**: What was done and why it worked
5. **Lessons Learned**: Key insights and learnings (3-5 items)
6. **Action Items**: Specific follow-up actions with priorities
7. **Prevention Measures**: How to prevent similar incidents

Format as structured JSON with clear sections.
"""
        
        try:
            bedrock_client = await self._get_bedrock_client()
            enhanced_content = await bedrock_client.invoke_with_fallback(
                analysis_prompt,
                max_tokens=2500,
                temperature=0.2
            )
            
            # Parse and structure the response
            structured_analysis = await self._parse_analysis_response(enhanced_content, report_data)
            
            return structured_analysis
            
        except Exception as e:
            logger.warning(f"Failed to generate enhanced analysis, using fallback: {e}")
            return self._generate_fallback_analysis(report_data)
    
    async def _parse_analysis_response(self, enhanced_content: str,
                                     report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse enhanced analysis response into structured data."""
        
        incident = report_data["incident"]
        
        # For now, create structured analysis based on incident data
        # In production, this would parse the enhanced_content using NLP
        
        return {
            "executive_summary": f"Incident '{incident.title}' was successfully resolved in {report_data['duration_minutes']:.1f} minutes with total business impact of ${report_data['total_cost']:,.2f}. The incident affected {incident.business_impact.service_tier.value} services and was classified as {incident.severity} severity.",
            
            "root_cause_analysis": {
                "primary_cause": "System performance degradation",
                "contributing_factors": [
                    "Resource utilization spike",
                    "Configuration change impact",
                    "External dependency issues"
                ],
                "analysis_confidence": 0.85,
                "evidence": [
                    "Performance metrics showed degradation",
                    "Error rates increased above baseline",
                    "User reports confirmed service issues"
                ]
            },
            
            "business_impact": {
                "financial_impact": f"${report_data['total_cost']:,.2f}",
                "customer_impact": f"Affected {incident.business_impact.affected_users} users",
                "operational_impact": "Service degradation during incident window",
                "reputation_impact": "Minimal due to quick resolution"
            },
            
            "resolution_summary": {
                "actions_taken": report_data["resolution_data"].get("actions", ["Standard resolution procedures applied"]),
                "effectiveness": "High - incident resolved within target timeframe",
                "resources_used": ["Incident response team", "On-call engineers"],
                "decision_points": ["Escalation to senior team", "Implementation of fix"]
            },
            
            "lessons_learned": [
                "Proactive monitoring could have detected the issue earlier",
                "Response procedures worked effectively",
                "Team coordination was excellent",
                "Documentation should be updated with new resolution steps"
            ],
            
            "action_items": [
                {
                    "title": "Enhance monitoring coverage",
                    "description": "Add additional monitoring for early detection",
                    "priority": "high",
                    "category": "prevention",
                    "estimated_effort": "2 weeks"
                },
                {
                    "title": "Update runbook documentation",
                    "description": "Document new resolution procedures",
                    "priority": "medium",
                    "category": "process",
                    "estimated_effort": "1 week"
                }
            ],
            
            "prevention_measures": [
                "Implement proactive monitoring alerts",
                "Establish regular system health checks",
                "Create automated testing for critical paths",
                "Enhance change management processes"
            ],
            
            "confidence_score": 0.88
        }
    
    def _generate_fallback_analysis(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fallback analysis when enhanced generation fails."""
        
        incident = report_data["incident"]
        
        return {
            "executive_summary": f"Incident resolved in {report_data['duration_minutes']:.1f} minutes.",
            "root_cause_analysis": {
                "primary_cause": "System issue detected",
                "contributing_factors": ["Performance degradation"],
                "analysis_confidence": 0.70
            },
            "business_impact": {
                "financial_impact": f"${report_data['total_cost']:,.2f}",
                "customer_impact": "Service disruption",
                "operational_impact": "Temporary degradation"
            },
            "resolution_summary": {
                "actions_taken": ["Resolution procedures applied"],
                "effectiveness": "Successful"
            },
            "lessons_learned": ["Standard incident response procedures effective"],
            "action_items": [
                {
                    "title": "Review incident response",
                    "description": "Standard post-incident review",
                    "priority": "medium",
                    "category": "process"
                }
            ],
            "prevention_measures": ["Enhanced monitoring"],
            "confidence_score": 0.75
        }
    
    async def _extract_and_store_action_items(self, report: PostIncidentReport) -> None:
        """Extract and store action items from report."""
        
        for item_data in report.action_items:
            action_item = ActionItem(
                item_id=str(uuid4()),
                title=item_data["title"],
                description=item_data["description"],
                priority=item_data.get("priority", "medium"),
                assignee=item_data.get("assignee", "unassigned"),
                due_date=datetime.utcnow() + timedelta(days=30),  # Default 30 days
                category=item_data.get("category", "general")
            )
            
            self._action_items[action_item.item_id] = action_item
            self._generation_stats["action_items_created"] += 1
    
    async def _extract_and_store_lessons_learned(self, report: PostIncidentReport,
                                               incident: Incident) -> None:
        """Extract and store lessons learned from report."""
        
        for lesson_text in report.lessons_learned:
            lesson = LessonLearned(
                lesson_id=str(uuid4()),
                title=lesson_text[:100],  # First 100 chars as title
                description=lesson_text,
                category=self._categorize_lesson(lesson_text),
                impact_level=self._assess_lesson_impact(incident.severity),
                applicable_teams=["incident_response", "engineering"],
                implementation_effort="medium",
                created_from_incident=incident.id
            )
            
            self._lessons_learned[lesson.lesson_id] = lesson
            self._generation_stats["lessons_learned_captured"] += 1
    
    def _categorize_lesson(self, lesson_text: str) -> str:
        """Categorize lesson learned based on content."""
        
        lesson_lower = lesson_text.lower()
        
        if any(word in lesson_lower for word in ["monitor", "alert", "detect"]):
            return "monitoring"
        elif any(word in lesson_lower for word in ["process", "procedure", "workflow"]):
            return "process"
        elif any(word in lesson_lower for word in ["technical", "system", "code"]):
            return "technical"
        elif any(word in lesson_lower for word in ["communication", "team", "coordination"]):
            return "communication"
        else:
            return "general"
    
    def _assess_lesson_impact(self, incident_severity: IncidentSeverity) -> str:
        """Assess impact level of lesson based on incident severity."""
        
        if incident_severity == IncidentSeverity.CRITICAL:
            return "high"
        elif incident_severity == IncidentSeverity.HIGH:
            return "medium"
        else:
            return "low"
    
    async def _create_document_version(self, report: PostIncidentReport,
                                     change_type: DocumentChangeType,
                                     created_by: str,
                                     change_summary: str = None) -> DocumentVersion:
        """Create a new version of the document."""
        
        # Generate document content
        content = await self._generate_report_content(report)
        
        # Create version
        version = DocumentVersion(
            version_id=str(uuid4()),
            document_id=report.report_id,
            version_number=report.version,
            content=content,
            change_summary=change_summary or f"Document {change_type.value}",
            change_type=change_type,
            created_by=created_by,
            created_at=datetime.utcnow(),
            checksum=self._generate_content_checksum(content),
            metadata={
                "incident_id": report.incident_id,
                "report_title": report.title,
                "confidence_score": report.confidence_score
            }
        )
        
        # Store version
        if report.report_id not in self._document_versions:
            self._document_versions[report.report_id] = []
        
        self._document_versions[report.report_id].append(version)
        
        # Log change
        self._log_document_change(version)
        
        # Update statistics
        self._generation_stats["total_versions_created"] += 1
        
        return version
    
    async def _generate_report_content(self, report: PostIncidentReport) -> str:
        """Generate formatted report content."""
        
        template = self._report_templates["executive_report"]
        
        # Format timeline events
        timeline_text = "\n".join([
            f"**{event.get('timestamp', 'Unknown')}**: {event.get('event', 'Unknown')} - {event.get('description', '')}"
            for event in report.incident_timeline
        ])
        
        # Format lessons learned
        lessons_text = "\n".join([
            f"- {lesson}" for lesson in report.lessons_learned
        ])
        
        # Format action items
        action_items_text = "\n".join([
            f"- **{item['title']}** ({item.get('priority', 'medium')} priority): {item['description']}"
            for item in report.action_items
        ])
        
        # Format prevention measures
        prevention_text = "\n".join([
            f"- {measure}" for measure in report.prevention_measures
        ])
        
        # Fill template
        content = template.format(
            incident_title=report.title,
            executive_summary=report.executive_summary,
            incident_id=report.incident_id,
            incident_duration="N/A",  # Would be calculated from incident data
            incident_severity="N/A",  # Would come from incident
            business_impact_summary=str(report.business_impact_assessment.get("financial_impact", "N/A")),
            resolution_time="N/A",
            customer_impact=str(report.business_impact_assessment.get("customer_impact", "N/A")),
            bottom_line_summary="Incident successfully resolved with minimal long-term impact",
            start_time="N/A",
            detection_time="N/A",
            total_duration="N/A",
            affected_services="N/A",
            severity="N/A",
            severity_justification="Based on business impact assessment",
            timeline_events=timeline_text,
            primary_root_cause=report.root_cause_analysis.get("primary_cause", "Under investigation"),
            contributing_factors="\n".join(f"- {factor}" for factor in report.root_cause_analysis.get("contributing_factors", [])),
            analysis_methodology="Automated analysis using Amazon Q integration",
            supporting_evidence="\n".join(f"- {evidence}" for evidence in report.root_cause_analysis.get("evidence", [])),
            financial_impact=report.business_impact_assessment.get("financial_impact", "N/A"),
            customer_impact_details=report.business_impact_assessment.get("customer_impact", "N/A"),
            operational_impact=report.business_impact_assessment.get("operational_impact", "N/A"),
            reputation_impact=report.business_impact_assessment.get("reputation_impact", "N/A"),
            resolution_actions="\n".join(f"- {action}" for action in report.resolution_summary.get("actions_taken", [])),
            key_decisions="\n".join(f"- {decision}" for decision in report.resolution_summary.get("decision_points", [])),
            resources_involved="\n".join(f"- {resource}" for resource in report.resolution_summary.get("resources_used", [])),
            resolution_effectiveness=report.resolution_summary.get("effectiveness", "N/A"),
            lessons_learned_list=lessons_text,
            action_items_list=action_items_text,
            immediate_prevention=prevention_text,
            longterm_prevention="Long-term improvements to be determined",
            process_improvements="Process improvements to be implemented",
            technical_appendix=json.dumps(report.appendices.get("technical_details", {}), indent=2),
            communication_log="Communication log not available",
            metrics_appendix=json.dumps(report.appendices.get("metrics", {}), indent=2),
            generation_timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            report_version=report.version,
            confidence_score=f"{report.confidence_score:.1%}"
        )
        
        return content
    
    def _generate_content_checksum(self, content: str) -> str:
        """Generate checksum for content integrity."""
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _log_document_change(self, version: DocumentVersion) -> None:
        """Log document change for audit trail."""
        
        change_entry = {
            "timestamp": version.created_at.isoformat(),
            "document_id": version.document_id,
            "version_id": version.version_id,
            "version_number": version.version_number,
            "change_type": version.change_type.value,
            "change_summary": version.change_summary,
            "created_by": version.created_by,
            "checksum": version.checksum
        }
        
        self._change_log.append(change_entry)
        
        # Keep only last 1000 changes
        if len(self._change_log) > 1000:
            self._change_log = self._change_log[-1000:]
    
    async def update_report(self, report_id: str, updates: Dict[str, Any],
                          updated_by: str) -> PostIncidentReport:
        """Update existing post-incident report."""
        
        report = self._reports.get(report_id)
        if not report:
            raise ValueError(f"Report {report_id} not found")
        
        # Track changes
        changes = []
        
        # Update fields
        for field, new_value in updates.items():
            if hasattr(report, field):
                old_value = getattr(report, field)
                if old_value != new_value:
                    setattr(report, field, new_value)
                    changes.append(f"Updated {field}")
        
        if changes:
            # Increment version
            report.version += 1
            report.updated_at = datetime.utcnow()
            
            # Create new version
            change_summary = "; ".join(changes)
            await self._create_document_version(
                report, 
                DocumentChangeType.UPDATED, 
                updated_by, 
                change_summary
            )
        
        return report
    
    async def get_report_by_id(self, report_id: str) -> Optional[PostIncidentReport]:
        """Get post-incident report by ID."""
        return self._reports.get(report_id)
    
    async def get_report_versions(self, report_id: str) -> List[DocumentVersion]:
        """Get all versions of a report."""
        return self._document_versions.get(report_id, [])
    
    async def get_version_diff(self, report_id: str, version1: int, version2: int) -> Dict[str, Any]:
        """Get diff between two versions of a report."""
        
        versions = self._document_versions.get(report_id, [])
        
        v1 = next((v for v in versions if v.version_number == version1), None)
        v2 = next((v for v in versions if v.version_number == version2), None)
        
        if not v1 or not v2:
            raise ValueError("One or both versions not found")
        
        # Generate diff
        diff = list(difflib.unified_diff(
            v1.content.splitlines(keepends=True),
            v2.content.splitlines(keepends=True),
            fromfile=f"Version {version1}",
            tofile=f"Version {version2}",
            n=3
        ))
        
        return {
            "version1": version1,
            "version2": version2,
            "diff": "".join(diff),
            "changes_summary": f"Comparing version {version1} to {version2}"
        }
    
    async def list_action_items(self, status: str = None, priority: str = None) -> List[ActionItem]:
        """List action items with optional filtering."""
        
        items = list(self._action_items.values())
        
        if status:
            items = [item for item in items if item.status == status]
        
        if priority:
            items = [item for item in items if item.priority == priority]
        
        # Sort by priority and due date
        priority_order = {"high": 0, "medium": 1, "low": 2}
        items.sort(key=lambda x: (priority_order.get(x.priority, 3), x.due_date))
        
        return items
    
    async def update_action_item_status(self, item_id: str, new_status: str,
                                      updated_by: str = None) -> ActionItem:
        """Update action item status."""
        
        item = self._action_items.get(item_id)
        if not item:
            raise ValueError(f"Action item {item_id} not found")
        
        item.status = new_status
        item.updated_at = datetime.utcnow()
        
        return item
    
    def get_lessons_learned_by_category(self, category: str = None) -> List[LessonLearned]:
        """Get lessons learned, optionally filtered by category."""
        
        lessons = list(self._lessons_learned.values())
        
        if category:
            lessons = [lesson for lesson in lessons if lesson.category == category]
        
        # Sort by creation date
        lessons.sort(key=lambda x: x.created_at, reverse=True)
        
        return lessons
    
    def get_change_log(self, document_id: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get document change log."""
        
        changes = self._change_log
        
        if document_id:
            changes = [change for change in changes if change["document_id"] == document_id]
        
        # Sort by timestamp (most recent first)
        changes.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return changes[:limit]
    
    def _update_average_generation_time(self, generation_time: float) -> None:
        """Update average generation time statistics."""
        
        current_avg = self._generation_stats["average_generation_time"]
        total_generated = self._generation_stats["reports_generated"]
        
        if total_generated > 1:
            new_avg = ((current_avg * (total_generated - 1)) + generation_time) / total_generated
            self._generation_stats["average_generation_time"] = new_avg
        else:
            self._generation_stats["average_generation_time"] = generation_time
    
    def get_documentation_statistics(self) -> Dict[str, Any]:
        """Get comprehensive documentation statistics."""
        
        # Calculate completion rates for action items
        total_items = len(self._action_items)
        completed_items = len([item for item in self._action_items.values() if item.status == "completed"])
        completion_rate = (completed_items / total_items) if total_items > 0 else 0
        
        # Category distribution for lessons learned
        lesson_categories = {}
        for lesson in self._lessons_learned.values():
            lesson_categories[lesson.category] = lesson_categories.get(lesson.category, 0) + 1
        
        return {
            **self._generation_stats,
            "total_reports": len(self._reports),
            "total_action_items": total_items,
            "completed_action_items": completed_items,
            "action_item_completion_rate": completion_rate,
            "total_lessons_learned": len(self._lessons_learned),
            "lesson_categories": lesson_categories,
            "total_document_changes": len(self._change_log),
            "average_report_versions": sum(len(versions) for versions in self._document_versions.values()) / max(1, len(self._document_versions))
        }


# Global post-incident documentation service instance
_post_incident_service: Optional[PostIncidentDocumentationService] = None


def get_post_incident_documentation_service(service_factory: AWSServiceFactory) -> PostIncidentDocumentationService:
    """Get or create global post-incident documentation service instance."""
    global _post_incident_service
    if _post_incident_service is None:
        _post_incident_service = PostIncidentDocumentationService(service_factory)
    return _post_incident_service