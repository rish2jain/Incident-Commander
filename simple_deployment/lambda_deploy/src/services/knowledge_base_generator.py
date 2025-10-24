"""
Knowledge Base Article Generation Service

Automatic knowledge base article creation from successful resolutions
and interactive troubleshooting guide generation.

Task 7.2: Implement knowledge base article generation
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from uuid import uuid4
from collections import defaultdict
import re

from src.models.incident import Incident, IncidentSeverity, ServiceTier
from src.services.aws import AWSServiceFactory, BedrockClient
from src.services.rag_memory import get_rag_memory, IncidentPattern, SimilarityResult
from src.services.documentation_generator import DocumentationGenerator, GeneratedDocument
from src.amazon_q_integration import AmazonQIncidentAnalyzer
from src.utils.logging import get_logger
from src.utils.config import config


logger = get_logger("knowledge_base_generator")


@dataclass
class KnowledgeArticle:
    """Represents a knowledge base article."""
    article_id: str
    title: str
    summary: str
    content: str
    category: str
    tags: List[str]
    difficulty_level: str
    estimated_read_time: int
    confidence_score: float
    source_incidents: List[str]
    related_articles: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    version: int = 1
    view_count: int = 0
    helpful_votes: int = 0
    total_votes: int = 0


@dataclass
class TroubleshootingStep:
    """Represents a step in interactive troubleshooting."""
    step_id: str
    title: str
    description: str
    step_type: str  # "check", "action", "decision", "resolution"
    instructions: List[str]
    expected_results: List[str]
    next_steps: Dict[str, str]  # condition -> next_step_id
    estimated_time: int
    difficulty: str
    success_indicators: List[str]
    failure_indicators: List[str]


@dataclass
class InteractiveTroubleshootingGuide:
    """Interactive troubleshooting guide with decision tree."""
    guide_id: str
    title: str
    description: str
    category: str
    entry_point: str  # First step ID
    steps: Dict[str, TroubleshootingStep]
    success_rate: float
    average_completion_time: int
    created_from_incidents: List[str]
    created_at: datetime = field(default_factory=datetime.utcnow)
    version: int = 1


@dataclass
class ArticleTemplate:
    """Template for different types of knowledge articles."""
    template_id: str
    name: str
    category: str
    sections: List[str]
    content_structure: Dict[str, str]
    variables: List[str]


class KnowledgeBaseGenerator:
    """Service for generating knowledge base articles and troubleshooting guides."""
    
    def __init__(self, service_factory: AWSServiceFactory):
        """Initialize knowledge base generator."""
        self._service_factory = service_factory
        self._bedrock_client = None
        self._q_analyzer = AmazonQIncidentAnalyzer()
        self._rag_memory = None
        self._doc_generator = None
        
        # Knowledge base storage
        self._articles: Dict[str, KnowledgeArticle] = {}
        self._troubleshooting_guides: Dict[str, InteractiveTroubleshootingGuide] = {}
        self._article_templates: Dict[str, ArticleTemplate] = {}
        
        # Analytics and optimization
        self._generation_metrics = {
            "articles_generated": 0,
            "guides_generated": 0,
            "total_views": 0,
            "average_helpfulness": 0.0,
            "generation_time_avg": 0.0
        }
        
        # Content categorization
        self._category_patterns = {
            "database": ["database", "sql", "connection", "query", "deadlock"],
            "network": ["network", "connectivity", "latency", "timeout", "dns"],
            "api": ["api", "endpoint", "rate limit", "authentication", "response"],
            "infrastructure": ["server", "cpu", "memory", "disk", "scaling"],
            "security": ["security", "authentication", "authorization", "ssl", "certificate"],
            "monitoring": ["alert", "metric", "dashboard", "monitoring", "observability"]
        }
        
        self._initialize_article_templates()
    
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
    
    async def _get_doc_generator(self) -> DocumentationGenerator:
        """Get documentation generator instance."""
        if not self._doc_generator:
            from src.services.documentation_generator import get_documentation_generator
            self._doc_generator = get_documentation_generator(self._service_factory)
        return self._doc_generator
    
    def _initialize_article_templates(self) -> None:
        """Initialize knowledge article templates."""
        
        # Problem-solution template
        problem_solution_template = ArticleTemplate(
            template_id="problem_solution",
            name="Problem-Solution Article",
            category="troubleshooting",
            sections=["problem", "symptoms", "diagnosis", "solution", "prevention"],
            content_structure={
                "problem": "Clear description of the problem",
                "symptoms": "Observable symptoms and indicators",
                "diagnosis": "How to diagnose and confirm the issue",
                "solution": "Step-by-step resolution procedure",
                "prevention": "Measures to prevent recurrence"
            },
            variables=["title", "problem_description", "symptoms_list", "diagnosis_steps", 
                      "solution_steps", "prevention_measures", "related_incidents"]
        )
        
        # How-to guide template
        howto_template = ArticleTemplate(
            template_id="howto_guide",
            name="How-To Guide",
            category="procedures",
            sections=["overview", "prerequisites", "steps", "verification", "troubleshooting"],
            content_structure={
                "overview": "What this guide covers",
                "prerequisites": "Required access and tools",
                "steps": "Detailed step-by-step instructions",
                "verification": "How to verify success",
                "troubleshooting": "Common issues and solutions"
            },
            variables=["title", "overview", "prerequisites", "step_list", "verification_steps", 
                      "common_issues", "estimated_time"]
        )
        
        # Best practices template
        best_practices_template = ArticleTemplate(
            template_id="best_practices",
            name="Best Practices Guide",
            category="guidance",
            sections=["introduction", "principles", "recommendations", "examples", "pitfalls"],
            content_structure={
                "introduction": "Context and importance",
                "principles": "Core principles to follow",
                "recommendations": "Specific recommendations",
                "examples": "Real-world examples",
                "pitfalls": "Common mistakes to avoid"
            },
            variables=["title", "context", "principles_list", "recommendations_list", 
                      "examples", "pitfalls_list", "references"]
        )
        
        self._article_templates = {
            problem_solution_template.template_id: problem_solution_template,
            howto_template.template_id: howto_template,
            best_practices_template.template_id: best_practices_template
        }
    
    async def generate_article_from_successful_resolutions(self, 
                                                         incidents: List[Incident],
                                                         resolution_data: List[Dict[str, Any]]) -> KnowledgeArticle:
        """Generate knowledge base article from successful incident resolutions."""
        
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Generating KB article from {len(incidents)} successful resolutions")
            
            # Analyze incidents for common patterns
            article_data = await self._analyze_incidents_for_article(incidents, resolution_data)
            
            # Generate enhanced content using Amazon Q
            enhanced_content = await self._generate_enhanced_article_content(article_data)
            
            # Create knowledge article
            article = KnowledgeArticle(
                article_id=str(uuid4()),
                title=article_data["title"],
                summary=article_data["summary"],
                content=enhanced_content["content"],
                category=article_data["category"],
                tags=article_data["tags"],
                difficulty_level=article_data["difficulty_level"],
                estimated_read_time=self._calculate_read_time(enhanced_content["content"]),
                confidence_score=enhanced_content["confidence_score"],
                source_incidents=[incident.id for incident in incidents]
            )
            
            # Store article
            self._articles[article.article_id] = article
            
            # Update metrics
            self._generation_metrics["articles_generated"] += 1
            generation_time = (datetime.utcnow() - start_time).total_seconds()
            self._update_average_generation_time(generation_time)
            
            logger.info(f"Generated KB article {article.article_id} in {generation_time:.2f}s")
            
            return article
            
        except Exception as e:
            logger.error(f"Failed to generate KB article from resolutions: {e}")
            raise
    
    async def _analyze_incidents_for_article(self, incidents: List[Incident],
                                           resolution_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze incidents to extract article data."""
        
        # Extract common themes
        common_symptoms = self._extract_common_symptoms(incidents)
        common_categories = self._categorize_incidents(incidents)
        primary_category = max(common_categories.items(), key=lambda x: x[1])[0]
        
        # Determine difficulty level
        severity_counts = defaultdict(int)
        for incident in incidents:
            severity_counts[incident.severity] += 1
        
        if severity_counts[IncidentSeverity.CRITICAL] > len(incidents) * 0.3:
            difficulty_level = "Advanced"
        elif severity_counts[IncidentSeverity.HIGH] > len(incidents) * 0.5:
            difficulty_level = "Intermediate"
        else:
            difficulty_level = "Beginner"
        
        # Generate title and summary
        title = self._generate_article_title(primary_category, common_symptoms)
        summary = self._generate_article_summary(incidents, primary_category)
        
        # Extract tags
        tags = self._extract_article_tags(incidents, primary_category)
        
        return {
            "title": title,
            "summary": summary,
            "category": primary_category,
            "tags": tags,
            "difficulty_level": difficulty_level,
            "common_symptoms": common_symptoms,
            "incident_count": len(incidents),
            "resolution_data": resolution_data
        }
    
    def _extract_common_symptoms(self, incidents: List[Incident]) -> List[str]:
        """Extract common symptoms from incidents."""
        
        symptom_counts = defaultdict(int)
        
        for incident in incidents:
            # Extract keywords from title and description
            text = f"{incident.title} {incident.description}".lower()
            words = re.findall(r'\b\w+\b', text)
            
            # Filter for meaningful symptoms
            for word in words:
                if len(word) > 3 and word not in ['incident', 'issue', 'problem', 'error']:
                    symptom_counts[word] += 1
        
        # Return most common symptoms
        sorted_symptoms = sorted(symptom_counts.items(), key=lambda x: x[1], reverse=True)
        return [symptom for symptom, count in sorted_symptoms[:10] if count > 1]
    
    def _categorize_incidents(self, incidents: List[Incident]) -> Dict[str, int]:
        """Categorize incidents based on content analysis."""
        
        category_scores = defaultdict(int)
        
        for incident in incidents:
            text = f"{incident.title} {incident.description}".lower()
            
            for category, patterns in self._category_patterns.items():
                for pattern in patterns:
                    if pattern in text:
                        category_scores[category] += 1
        
        return dict(category_scores)
    
    def _generate_article_title(self, category: str, symptoms: List[str]) -> str:
        """Generate article title based on category and symptoms."""
        
        if symptoms:
            primary_symptom = symptoms[0].replace('_', ' ').title()
            return f"Troubleshooting {category.title()} Issues: {primary_symptom}"
        else:
            return f"Common {category.title()} Troubleshooting Guide"
    
    def _generate_article_summary(self, incidents: List[Incident], category: str) -> str:
        """Generate article summary."""
        
        return f"Comprehensive troubleshooting guide for {category} issues based on analysis of {len(incidents)} successfully resolved incidents. Includes common symptoms, diagnosis steps, and proven resolution procedures."
    
    def _extract_article_tags(self, incidents: List[Incident], category: str) -> List[str]:
        """Extract relevant tags for the article."""
        
        tags = [category]
        
        # Add severity-based tags
        severities = [incident.severity for incident in incidents]
        if IncidentSeverity.CRITICAL in severities:
            tags.append("critical")
        if IncidentSeverity.HIGH in severities:
            tags.append("high-priority")
        
        # Add service tier tags
        service_tiers = [incident.business_impact.service_tier for incident in incidents]
        if ServiceTier.TIER_1 in service_tiers:
            tags.append("customer-facing")
        
        # Add common keywords
        all_text = " ".join([f"{inc.title} {inc.description}" for inc in incidents]).lower()
        for category_name, patterns in self._category_patterns.items():
            for pattern in patterns:
                if pattern in all_text and pattern not in tags:
                    tags.append(pattern)
                    if len(tags) >= 8:  # Limit tag count
                        break
        
        return tags[:8]
    
    async def _generate_enhanced_article_content(self, article_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate enhanced article content using Amazon Q."""
        
        content_prompt = f"""Create a comprehensive knowledge base article for troubleshooting {article_data['category']} issues.

**Article Details:**
- Title: {article_data['title']}
- Category: {article_data['category']}
- Difficulty: {article_data['difficulty_level']}
- Based on: {article_data['incident_count']} resolved incidents

**Common Symptoms:**
{chr(10).join(f'- {symptom}' for symptom in article_data['common_symptoms'][:5])}

**Resolution Data:**
{chr(10).join(f'- {res.get("summary", "Resolution applied")}' for res in article_data['resolution_data'][:3])}

Please create a structured article with:
1. **Problem Overview**: Clear description of the issue category
2. **Common Symptoms**: Observable indicators users will see
3. **Diagnosis Steps**: How to identify and confirm the specific problem
4. **Resolution Procedures**: Step-by-step solutions with success rates
5. **Prevention Measures**: How to avoid similar issues
6. **Advanced Troubleshooting**: For complex cases
7. **Related Resources**: Links to additional documentation

Format as markdown with clear sections and actionable steps.
"""
        
        try:
            bedrock_client = await self._get_bedrock_client()
            enhanced_content = await bedrock_client.invoke_with_fallback(
                content_prompt, 
                max_tokens=2000,
                temperature=0.3
            )
            
            # Calculate confidence score based on incident data
            confidence_score = self._calculate_content_confidence(article_data)
            
            return {
                "content": enhanced_content,
                "confidence_score": confidence_score
            }
            
        except Exception as e:
            logger.warning(f"Failed to generate enhanced content, using fallback: {e}")
            return self._generate_fallback_article_content(article_data)
    
    def _calculate_content_confidence(self, article_data: Dict[str, Any]) -> float:
        """Calculate confidence score for generated content."""
        
        base_confidence = 0.7
        
        # Increase confidence with more incidents
        incident_bonus = min(0.2, article_data['incident_count'] * 0.02)
        
        # Increase confidence with more common symptoms
        symptom_bonus = min(0.1, len(article_data['common_symptoms']) * 0.01)
        
        return min(0.95, base_confidence + incident_bonus + symptom_bonus)
    
    def _generate_fallback_article_content(self, article_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate fallback content when enhanced generation fails."""
        
        content = f"""# {article_data['title']}

## Overview
This guide covers troubleshooting for {article_data['category']} issues based on {article_data['incident_count']} successfully resolved incidents.

## Common Symptoms
{chr(10).join(f'- {symptom.replace("_", " ").title()}' for symptom in article_data['common_symptoms'][:5])}

## Diagnosis Steps
1. Check system health and metrics
2. Review recent changes and deployments
3. Analyze error logs and patterns
4. Verify external dependencies

## Resolution Procedures
{chr(10).join(f'{i+1}. {res.get("summary", "Apply standard resolution procedure")}' for i, res in enumerate(article_data['resolution_data'][:5]))}

## Prevention Measures
- Implement proactive monitoring
- Establish change management processes
- Regular system health checks
- Documentation and training updates

## Additional Resources
- System monitoring dashboards
- Incident response procedures
- Team escalation contacts
"""
        
        return {
            "content": content,
            "confidence_score": 0.75
        }
    
    async def create_interactive_troubleshooting_guide(self, 
                                                     incident_patterns: List[IncidentPattern],
                                                     guide_title: str = None) -> InteractiveTroubleshootingGuide:
        """Create interactive troubleshooting guide with decision tree."""
        
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Creating interactive guide from {len(incident_patterns)} patterns")
            
            # Analyze patterns to build decision tree
            guide_structure = await self._build_troubleshooting_decision_tree(incident_patterns)
            
            # Generate guide steps
            steps = await self._generate_troubleshooting_steps(guide_structure, incident_patterns)
            
            # Create guide
            guide = InteractiveTroubleshootingGuide(
                guide_id=str(uuid4()),
                title=guide_title or f"Interactive Troubleshooting: {incident_patterns[0].incident_type.replace('_', ' ').title()}",
                description=f"Step-by-step interactive troubleshooting guide based on {len(incident_patterns)} successful resolutions",
                category=self._determine_guide_category(incident_patterns),
                entry_point=guide_structure["entry_point"],
                steps=steps,
                success_rate=sum(p.success_rate for p in incident_patterns) / len(incident_patterns),
                average_completion_time=self._estimate_completion_time(steps),
                created_from_incidents=[p.pattern_id for p in incident_patterns]
            )
            
            # Store guide
            self._troubleshooting_guides[guide.guide_id] = guide
            
            # Update metrics
            self._generation_metrics["guides_generated"] += 1
            generation_time = (datetime.utcnow() - start_time).total_seconds()
            self._update_average_generation_time(generation_time)
            
            logger.info(f"Created interactive guide {guide.guide_id} in {generation_time:.2f}s")
            
            return guide
            
        except Exception as e:
            logger.error(f"Failed to create interactive troubleshooting guide: {e}")
            raise
    
    async def _build_troubleshooting_decision_tree(self, patterns: List[IncidentPattern]) -> Dict[str, Any]:
        """Build decision tree structure from incident patterns."""
        
        # Analyze common symptoms and create decision points
        all_symptoms = []
        for pattern in patterns:
            all_symptoms.extend(pattern.symptoms)
        
        # Group symptoms by frequency
        symptom_counts = defaultdict(int)
        for symptom in all_symptoms:
            symptom_counts[symptom] += 1
        
        # Create decision tree structure
        common_symptoms = [s for s, c in symptom_counts.items() if c > 1]
        
        return {
            "entry_point": "initial_check",
            "decision_points": common_symptoms[:5],
            "resolution_paths": len(patterns),
            "complexity_level": "medium" if len(patterns) > 3 else "simple"
        }
    
    async def _generate_troubleshooting_steps(self, guide_structure: Dict[str, Any],
                                            patterns: List[IncidentPattern]) -> Dict[str, TroubleshootingStep]:
        """Generate troubleshooting steps for the guide."""
        
        steps = {}
        
        # Initial check step
        initial_step = TroubleshootingStep(
            step_id="initial_check",
            title="Initial System Check",
            description="Perform initial system health verification",
            step_type="check",
            instructions=[
                "Check system monitoring dashboards",
                "Verify service health status",
                "Review recent alerts and notifications"
            ],
            expected_results=[
                "System status indicators visible",
                "Recent activity logged",
                "Alert history accessible"
            ],
            next_steps={
                "healthy": "symptom_analysis",
                "degraded": "immediate_action",
                "critical": "escalation"
            },
            estimated_time=2,
            difficulty="beginner",
            success_indicators=["Dashboards accessible", "Metrics available"],
            failure_indicators=["Dashboard errors", "No recent data"]
        )
        steps[initial_step.step_id] = initial_step
        
        # Symptom analysis step
        symptom_step = TroubleshootingStep(
            step_id="symptom_analysis",
            title="Symptom Analysis",
            description="Analyze specific symptoms to determine root cause",
            step_type="decision",
            instructions=[
                "Review error logs for patterns",
                "Check performance metrics",
                "Identify affected components"
            ],
            expected_results=[
                "Error patterns identified",
                "Performance bottlenecks located",
                "Scope of impact determined"
            ],
            next_steps={
                "database_issues": "database_troubleshooting",
                "network_issues": "network_troubleshooting",
                "api_issues": "api_troubleshooting",
                "unknown": "general_troubleshooting"
            },
            estimated_time=5,
            difficulty="intermediate",
            success_indicators=["Clear error patterns", "Metrics show anomalies"],
            failure_indicators=["No clear patterns", "Metrics unavailable"]
        )
        steps[symptom_step.step_id] = symptom_step
        
        # Generate specific troubleshooting steps based on patterns
        for i, pattern in enumerate(patterns[:3]):  # Limit to top 3 patterns
            step_id = f"resolution_{i+1}"
            resolution_step = TroubleshootingStep(
                step_id=step_id,
                title=f"Resolution Path {i+1}",
                description=f"Apply resolution for {pattern.incident_type}",
                step_type="action",
                instructions=pattern.resolution_actions[:5],
                expected_results=[
                    "Issue symptoms reduced",
                    "System metrics improving",
                    "Error rates decreasing"
                ],
                next_steps={
                    "success": "verification",
                    "partial": "additional_actions",
                    "failure": "escalation"
                },
                estimated_time=10,
                difficulty="intermediate",
                success_indicators=["Metrics normalized", "Errors resolved"],
                failure_indicators=["No improvement", "New errors"]
            )
            steps[step_id] = resolution_step
        
        # Verification step
        verification_step = TroubleshootingStep(
            step_id="verification",
            title="Solution Verification",
            description="Verify that the issue has been resolved",
            step_type="check",
            instructions=[
                "Monitor system for 10 minutes",
                "Verify all metrics are normal",
                "Test critical user workflows",
                "Confirm no new errors"
            ],
            expected_results=[
                "Stable system metrics",
                "No error recurrence",
                "User workflows functional"
            ],
            next_steps={
                "verified": "completion",
                "unstable": "additional_monitoring",
                "failed": "rollback"
            },
            estimated_time=10,
            difficulty="beginner",
            success_indicators=["Stable for 10+ minutes", "All tests pass"],
            failure_indicators=["Metrics unstable", "Errors returning"]
        )
        steps[verification_step.step_id] = verification_step
        
        return steps
    
    def _determine_guide_category(self, patterns: List[IncidentPattern]) -> str:
        """Determine category for troubleshooting guide."""
        
        # Analyze pattern types
        type_counts = defaultdict(int)
        for pattern in patterns:
            incident_type = pattern.incident_type.split('_')[1] if '_' in pattern.incident_type else pattern.incident_type
            type_counts[incident_type] += 1
        
        if type_counts:
            return max(type_counts.items(), key=lambda x: x[1])[0]
        else:
            return "general"
    
    def _estimate_completion_time(self, steps: Dict[str, TroubleshootingStep]) -> int:
        """Estimate average completion time for troubleshooting guide."""
        
        total_time = sum(step.estimated_time for step in steps.values())
        # Assume users follow 60% of steps on average
        return int(total_time * 0.6)
    
    def _calculate_read_time(self, content: str) -> int:
        """Calculate estimated reading time in minutes."""
        
        word_count = len(content.split())
        # Average reading speed: 200 words per minute
        return max(1, word_count // 200)
    
    def _update_average_generation_time(self, generation_time: float) -> None:
        """Update average generation time statistics."""
        
        current_avg = self._generation_metrics["generation_time_avg"]
        total_generated = self._generation_metrics["articles_generated"] + self._generation_metrics["guides_generated"]
        
        if total_generated > 1:
            new_avg = ((current_avg * (total_generated - 1)) + generation_time) / total_generated
            self._generation_metrics["generation_time_avg"] = new_avg
        else:
            self._generation_metrics["generation_time_avg"] = generation_time
    
    async def get_article_by_id(self, article_id: str) -> Optional[KnowledgeArticle]:
        """Get knowledge article by ID."""
        return self._articles.get(article_id)
    
    async def get_guide_by_id(self, guide_id: str) -> Optional[InteractiveTroubleshootingGuide]:
        """Get troubleshooting guide by ID."""
        return self._troubleshooting_guides.get(guide_id)
    
    async def search_articles(self, query: str, category: str = None, limit: int = 10) -> List[KnowledgeArticle]:
        """Search knowledge articles."""
        
        matching_articles = []
        query_lower = query.lower()
        
        for article in self._articles.values():
            # Category filter
            if category and article.category != category:
                continue
            
            # Text matching
            if (query_lower in article.title.lower() or 
                query_lower in article.summary.lower() or
                query_lower in article.content.lower() or
                any(query_lower in tag.lower() for tag in article.tags)):
                matching_articles.append(article)
        
        # Sort by relevance (view count and helpfulness)
        matching_articles.sort(key=lambda x: (x.view_count, x.helpful_votes), reverse=True)
        return matching_articles[:limit]
    
    async def get_related_articles(self, article_id: str, limit: int = 5) -> List[KnowledgeArticle]:
        """Get articles related to the specified article."""
        
        article = self._articles.get(article_id)
        if not article:
            return []
        
        related_articles = []
        
        for other_article in self._articles.values():
            if other_article.article_id == article_id:
                continue
            
            # Calculate similarity based on tags and category
            similarity_score = self._calculate_article_similarity(article, other_article)
            
            if similarity_score > 0.3:  # Minimum similarity threshold
                related_articles.append((other_article, similarity_score))
        
        # Sort by similarity and return top results
        related_articles.sort(key=lambda x: x[1], reverse=True)
        return [article for article, score in related_articles[:limit]]
    
    def _calculate_article_similarity(self, article1: KnowledgeArticle, 
                                    article2: KnowledgeArticle) -> float:
        """Calculate similarity score between two articles."""
        
        similarity = 0.0
        
        # Category match
        if article1.category == article2.category:
            similarity += 0.4
        
        # Tag overlap
        common_tags = set(article1.tags) & set(article2.tags)
        if article1.tags and article2.tags:
            tag_similarity = len(common_tags) / max(len(article1.tags), len(article2.tags))
            similarity += tag_similarity * 0.6
        
        return similarity
    
    async def update_article_metrics(self, article_id: str, viewed: bool = False, 
                                   helpful: bool = None) -> None:
        """Update article view and helpfulness metrics."""
        
        article = self._articles.get(article_id)
        if not article:
            return
        
        if viewed:
            article.view_count += 1
            self._generation_metrics["total_views"] += 1
        
        if helpful is not None:
            article.total_votes += 1
            if helpful:
                article.helpful_votes += 1
            
            # Update average helpfulness
            total_helpful = sum(a.helpful_votes for a in self._articles.values())
            total_votes = sum(a.total_votes for a in self._articles.values())
            if total_votes > 0:
                self._generation_metrics["average_helpfulness"] = total_helpful / total_votes
    
    def get_knowledge_base_statistics(self) -> Dict[str, Any]:
        """Get comprehensive knowledge base statistics."""
        
        # Category distribution
        category_counts = defaultdict(int)
        for article in self._articles.values():
            category_counts[article.category] += 1
        
        # Difficulty distribution
        difficulty_counts = defaultdict(int)
        for article in self._articles.values():
            difficulty_counts[article.difficulty_level] += 1
        
        return {
            **self._generation_metrics,
            "total_articles": len(self._articles),
            "total_guides": len(self._troubleshooting_guides),
            "category_distribution": dict(category_counts),
            "difficulty_distribution": dict(difficulty_counts),
            "average_confidence": sum(a.confidence_score for a in self._articles.values()) / max(1, len(self._articles)),
            "most_viewed_article": max(self._articles.values(), key=lambda x: x.view_count, default=None),
            "most_helpful_article": max(self._articles.values(), key=lambda x: x.helpful_votes, default=None)
        }


# Global knowledge base generator instance
_kb_generator: Optional[KnowledgeBaseGenerator] = None


def get_knowledge_base_generator(service_factory: AWSServiceFactory) -> KnowledgeBaseGenerator:
    """Get or create global knowledge base generator instance."""
    global _kb_generator
    if _kb_generator is None:
        _kb_generator = KnowledgeBaseGenerator(service_factory)
    return _kb_generator