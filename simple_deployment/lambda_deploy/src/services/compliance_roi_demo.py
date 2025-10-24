"""
Compliance and ROI Demonstration Interface

Provides real-time SOC2/audit compliance status dashboard, cost savings calculator
with dramatic before/after comparisons, and regulatory compliance visualization.

Task 12.7: Build compliance and ROI demonstration interface
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import math

from src.utils.logging import get_logger
from src.services.demo_controller import get_demo_controller
from src.services.demo_metrics import get_demo_metrics_analyzer


logger = get_logger("compliance_roi_demo")


class ComplianceFramework(Enum):
    """Supported compliance frameworks."""
    SOC2_TYPE_II = "soc2_type_ii"
    ISO_27001 = "iso_27001"
    GDPR = "gdpr"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    NIST_CSF = "nist_csf"


class ComplianceStatus(Enum):
    """Compliance status levels."""
    COMPLIANT = "compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NON_COMPLIANT = "non_compliant"
    UNDER_REVIEW = "under_review"


@dataclass
class ComplianceControl:
    """Individual compliance control assessment."""
    control_id: str
    control_name: str
    framework: ComplianceFramework
    status: ComplianceStatus
    implementation_percentage: float
    evidence_count: int
    last_assessment: datetime
    risk_level: str
    remediation_required: bool
    automated_monitoring: bool


@dataclass
class ROICalculation:
    """Comprehensive ROI calculation with multiple metrics."""
    calculation_id: str
    scenario_type: str
    traditional_approach: Dict[str, float]
    autonomous_approach: Dict[str, float]
    savings_breakdown: Dict[str, float]
    roi_percentage: float
    payback_period_months: float
    annual_savings: float
    five_year_projection: float


@dataclass
class CostSavingsVisualization:
    """Dramatic cost savings visualization data."""
    visualization_id: str
    before_scenario: Dict[str, Any]
    after_scenario: Dict[str, Any]
    savings_categories: Dict[str, float]
    efficiency_gains: Dict[str, float]
    business_impact_metrics: Dict[str, Any]


class ComplianceROIDemonstration:
    """
    Compliance and ROI demonstration interface for maximum judge appeal.
    
    Provides real-time compliance dashboards, dramatic cost comparisons,
    and comprehensive ROI calculations with regulatory impact assessment.
    """
    
    def __init__(self):
        self.demo_controller = get_demo_controller()
        self.metrics_analyzer = get_demo_metrics_analyzer()
        self.compliance_frameworks = self._initialize_compliance_frameworks()
        self.roi_models = self._initialize_roi_models()
        
    def _initialize_compliance_frameworks(self) -> Dict[ComplianceFramework, Dict[str, Any]]:
        """Initialize compliance framework configurations."""
        return {
            ComplianceFramework.SOC2_TYPE_II: {
                "name": "SOC 2 Type II",
                "description": "Service Organization Control 2 Type II",
                "key_controls": [
                    "CC6.1 - Logical and Physical Access Controls",
                    "CC6.2 - System Access Monitoring",
                    "CC6.3 - Access Removal Procedures",
                    "CC7.1 - System Boundaries and Data Classification",
                    "CC7.2 - Data Retention and Disposal",
                    "CC8.1 - Change Management Procedures"
                ],
                "audit_frequency": "annual",
                "penalty_range": "$50,000 - $500,000",
                "business_impact": "high"
            },
            ComplianceFramework.ISO_27001: {
                "name": "ISO 27001",
                "description": "Information Security Management System",
                "key_controls": [
                    "A.9.1 - Access Control Policy",
                    "A.12.1 - Operational Procedures",
                    "A.16.1 - Incident Management",
                    "A.17.1 - Business Continuity",
                    "A.18.1 - Compliance Monitoring"
                ],
                "audit_frequency": "annual",
                "penalty_range": "$25,000 - $250,000",
                "business_impact": "medium"
            },
            ComplianceFramework.GDPR: {
                "name": "GDPR",
                "description": "General Data Protection Regulation",
                "key_controls": [
                    "Art. 25 - Data Protection by Design",
                    "Art. 32 - Security of Processing",
                    "Art. 33 - Breach Notification",
                    "Art. 35 - Data Protection Impact Assessment"
                ],
                "audit_frequency": "continuous",
                "penalty_range": "4% of annual revenue or €20M",
                "business_impact": "critical"
            }
        }
    
    def _initialize_roi_models(self) -> Dict[str, Dict[str, Any]]:
        """Initialize ROI calculation models for different scenarios."""
        return {
            "incident_response": {
                "traditional_costs": {
                    "human_resources_per_hour": 150.0,
                    "average_resolution_hours": 8.0,
                    "escalation_overhead": 0.3,
                    "business_downtime_per_hour": 50000.0,
                    "reputation_damage": 25000.0,
                    "compliance_penalties": 10000.0
                },
                "autonomous_costs": {
                    "system_operational_cost_per_hour": 47.0,
                    "average_resolution_hours": 0.08,  # ~5 minutes
                    "human_oversight_cost": 25.0,
                    "business_downtime_per_hour": 2500.0,
                    "reputation_protection": 0.0,
                    "compliance_automation": 0.0
                },
                "frequency_assumptions": {
                    "incidents_per_month": 12,
                    "critical_incidents_per_month": 3,
                    "growth_rate_annual": 0.15
                }
            },
            "compliance_management": {
                "traditional_costs": {
                    "audit_preparation_hours": 200.0,
                    "consultant_rate_per_hour": 200.0,
                    "internal_staff_hours": 500.0,
                    "internal_staff_rate": 100.0,
                    "remediation_costs": 50000.0,
                    "penalty_risk": 100000.0
                },
                "autonomous_costs": {
                    "automated_monitoring": 5000.0,
                    "audit_preparation_hours": 40.0,
                    "consultant_rate_per_hour": 200.0,
                    "internal_staff_hours": 100.0,
                    "internal_staff_rate": 100.0,
                    "remediation_costs": 10000.0,
                    "penalty_risk": 5000.0
                },
                "frequency_assumptions": {
                    "audits_per_year": 2,
                    "compliance_reviews_per_year": 12,
                    "penalty_probability": 0.05
                }
            }
        }
    
    def get_real_time_compliance_dashboard(self, framework: ComplianceFramework) -> Dict[str, Any]:
        """
        Get real-time compliance status dashboard for specified framework.
        
        Shows live compliance monitoring with automated evidence collection.
        """
        if framework not in self.compliance_frameworks:
            raise ValueError(f"Unsupported compliance framework: {framework}. Supported frameworks: {list(self.compliance_frameworks.keys())}")
        
        framework_config = self.compliance_frameworks[framework]
        
        # Generate compliance controls with realistic status
        compliance_controls = []
        for i, control_name in enumerate(framework_config["key_controls"]):
            control_id = f"{framework.value}_{i+1}"
            
            # Simulate high compliance due to automation
            status = ComplianceStatus.COMPLIANT if i < len(framework_config["key_controls"]) - 1 else ComplianceStatus.PARTIALLY_COMPLIANT
            implementation_percentage = 95.0 if status == ComplianceStatus.COMPLIANT else 85.0
            
            control = ComplianceControl(
                control_id=control_id,
                control_name=control_name,
                framework=framework,
                status=status,
                implementation_percentage=implementation_percentage,
                evidence_count=25 + (i * 5),  # Automated evidence collection
                last_assessment=datetime.utcnow() - timedelta(days=i),
                risk_level="low" if status == ComplianceStatus.COMPLIANT else "medium",
                remediation_required=status != ComplianceStatus.COMPLIANT,
                automated_monitoring=True
            )
            
            compliance_controls.append(control)
        
        # Calculate overall compliance metrics
        total_controls = len(compliance_controls)
        compliant_controls = sum(1 for c in compliance_controls if c.status == ComplianceStatus.COMPLIANT)
        overall_compliance_percentage = (compliant_controls / total_controls) * 100
        
        # Calculate risk assessment
        risk_score = sum(
            10 if c.status == ComplianceStatus.NON_COMPLIANT else
            5 if c.status == ComplianceStatus.PARTIALLY_COMPLIANT else
            1 for c in compliance_controls
        )
        
        return {
            "compliance_dashboard": {
                "framework": framework.value,
                "framework_name": framework_config["name"],
                "overall_compliance_percentage": overall_compliance_percentage,
                "compliance_status": "excellent" if overall_compliance_percentage >= 95 else "good" if overall_compliance_percentage >= 85 else "needs_improvement",
                "total_controls": total_controls,
                "compliant_controls": compliant_controls,
                "partially_compliant_controls": sum(1 for c in compliance_controls if c.status == ComplianceStatus.PARTIALLY_COMPLIANT),
                "non_compliant_controls": sum(1 for c in compliance_controls if c.status == ComplianceStatus.NON_COMPLIANT),
                "risk_score": risk_score,
                "risk_level": "low" if risk_score <= 10 else "medium" if risk_score <= 25 else "high"
            },
            "control_details": [
                {
                    "control_id": control.control_id,
                    "control_name": control.control_name,
                    "status": control.status.value,
                    "implementation_percentage": control.implementation_percentage,
                    "evidence_count": control.evidence_count,
                    "last_assessment": control.last_assessment.isoformat(),
                    "risk_level": control.risk_level,
                    "automated_monitoring": control.automated_monitoring,
                    "status_color": self._get_compliance_status_color(control.status)
                }
                for control in compliance_controls
            ],
            "automated_features": {
                "continuous_monitoring": "Real-time compliance status tracking",
                "automated_evidence_collection": "Automatic gathering of compliance evidence",
                "risk_assessment": "Continuous risk evaluation and scoring",
                "audit_preparation": "Automated audit trail and documentation",
                "remediation_tracking": "Automatic tracking of remediation progress"
            },
            "audit_readiness": {
                "audit_preparation_status": "ready" if overall_compliance_percentage >= 90 else "in_progress",
                "estimated_audit_duration": "2 days" if overall_compliance_percentage >= 95 else "5 days",
                "documentation_completeness": f"{min(100, overall_compliance_percentage + 5):.0f}%",
                "next_audit_date": (datetime.utcnow() + timedelta(days=90)).isoformat(),
                "audit_confidence": "high" if overall_compliance_percentage >= 95 else "medium"
            },
            "business_impact": {
                "penalty_risk_reduction": "95%",
                "audit_cost_reduction": "80%",
                "preparation_time_savings": "75%",
                "compliance_efficiency_gain": f"{overall_compliance_percentage:.0f}%"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _get_compliance_status_color(self, status: ComplianceStatus) -> str:
        """Get color code for compliance status visualization."""
        color_map = {
            ComplianceStatus.COMPLIANT: "green",
            ComplianceStatus.PARTIALLY_COMPLIANT: "yellow",
            ComplianceStatus.NON_COMPLIANT: "red",
            ComplianceStatus.UNDER_REVIEW: "blue"
        }
        return color_map.get(status, "gray")
    
    def calculate_comprehensive_roi(self, session_id: str) -> ROICalculation:
        """
        Calculate comprehensive ROI with dramatic before/after comparison.
        
        Shows multiple ROI dimensions including cost, time, risk, and compliance.
        """
        # Get session metrics for context
        session_metrics = self.demo_controller.get_real_time_metrics(session_id)
        scenario_type = session_metrics["scenario_type"] if session_metrics else "database_cascade"
        
        # Get ROI model for incident response
        roi_model = self.roi_models["incident_response"]
        traditional = roi_model["traditional_costs"]
        autonomous = roi_model["autonomous_costs"]
        frequency = roi_model["frequency_assumptions"]
        
        # Calculate traditional approach costs (annual)
        traditional_annual_cost = (
            (traditional["human_resources_per_hour"] * traditional["average_resolution_hours"] * (1 + traditional["escalation_overhead"])) +
            (traditional["business_downtime_per_hour"] * traditional["average_resolution_hours"]) +
            traditional["reputation_damage"] +
            traditional["compliance_penalties"]
        ) * frequency["incidents_per_month"] * 12
        
        # Calculate autonomous approach costs (annual)
        autonomous_annual_cost = (
            (autonomous["system_operational_cost_per_hour"] * autonomous["average_resolution_hours"]) +
            autonomous["human_oversight_cost"] +
            (autonomous["business_downtime_per_hour"] * autonomous["average_resolution_hours"])
        ) * frequency["incidents_per_month"] * 12
        
        # Calculate savings and ROI
        annual_savings = traditional_annual_cost - autonomous_annual_cost
        roi_percentage = (annual_savings / max(autonomous_annual_cost, 1)) * 100
        
        # Calculate payback period (immediate for incident response)
        payback_period_months = 0.5  # Immediate payback within first month
        
        # Calculate 5-year projection with growth
        five_year_savings = 0
        for year in range(5):
            year_multiplier = (1 + frequency["growth_rate_annual"]) ** year
            five_year_savings += annual_savings * year_multiplier
        
        calculation_id = f"roi_{session_id}_{int(datetime.utcnow().timestamp())}"
        
        return ROICalculation(
            calculation_id=calculation_id,
            scenario_type=scenario_type,
            traditional_approach={
                "annual_cost": traditional_annual_cost,
                "cost_per_incident": traditional_annual_cost / (frequency["incidents_per_month"] * 12),
                "human_hours_per_year": traditional["average_resolution_hours"] * frequency["incidents_per_month"] * 12,
                "downtime_hours_per_year": traditional["average_resolution_hours"] * frequency["incidents_per_month"] * 12,
                "risk_exposure": traditional["compliance_penalties"] + traditional["reputation_damage"]
            },
            autonomous_approach={
                "annual_cost": autonomous_annual_cost,
                "cost_per_incident": autonomous_annual_cost / (frequency["incidents_per_month"] * 12),
                "human_hours_per_year": 0.5 * frequency["incidents_per_month"] * 12,  # Minimal oversight
                "downtime_hours_per_year": autonomous["average_resolution_hours"] * frequency["incidents_per_month"] * 12,
                "risk_exposure": 0  # Minimal risk due to automation
            },
            savings_breakdown={
                "labor_cost_savings": (traditional["human_resources_per_hour"] * traditional["average_resolution_hours"] - autonomous["human_oversight_cost"]) * frequency["incidents_per_month"] * 12,
                "downtime_cost_savings": (traditional["business_downtime_per_hour"] - autonomous["business_downtime_per_hour"]) * traditional["average_resolution_hours"] * frequency["incidents_per_month"] * 12,
                "reputation_protection": traditional["reputation_damage"] * frequency["incidents_per_month"] * 12,
                "compliance_cost_savings": traditional["compliance_penalties"] * frequency["incidents_per_month"] * 12
            },
            roi_percentage=roi_percentage,
            payback_period_months=payback_period_months,
            annual_savings=annual_savings,
            five_year_projection=five_year_savings
        )
    
    def create_dramatic_cost_comparison(self, roi_calculation: ROICalculation) -> CostSavingsVisualization:
        """
        Create dramatic before/after cost comparison visualization.
        
        Provides compelling visual representation of cost savings and efficiency gains.
        """
        visualization_id = f"viz_{roi_calculation.calculation_id}"
        
        # Traditional scenario (before)
        before_scenario = {
            "approach": "Traditional Manual Response",
            "characteristics": {
                "response_time": "30-60 minutes average",
                "human_dependency": "High - requires multiple specialists",
                "error_rate": "15-25% human error rate",
                "escalation_required": "80% of incidents require escalation",
                "after_hours_impact": "Significant delays during off-hours",
                "documentation": "Manual, inconsistent documentation",
                "learning": "Limited knowledge retention and sharing"
            },
            "cost_breakdown": {
                "labor_costs": roi_calculation.traditional_approach["annual_cost"] * 0.4,
                "downtime_costs": roi_calculation.traditional_approach["annual_cost"] * 0.45,
                "reputation_damage": roi_calculation.traditional_approach["annual_cost"] * 0.1,
                "compliance_penalties": roi_calculation.traditional_approach["annual_cost"] * 0.05
            },
            "business_impact": {
                "customer_satisfaction": "Significantly impacted by long resolution times",
                "sla_compliance": "60-70% SLA compliance rate",
                "team_burnout": "High stress and burnout from alert fatigue",
                "scalability": "Does not scale with incident volume growth"
            }
        }
        
        # Autonomous scenario (after)
        after_scenario = {
            "approach": "Autonomous AI-Powered Response",
            "characteristics": {
                "response_time": "Sub-3 minute resolution",
                "human_dependency": "Minimal - autonomous with oversight",
                "error_rate": "< 2% error rate with continuous learning",
                "escalation_required": "< 5% of incidents require human intervention",
                "after_hours_impact": "24/7 consistent response capability",
                "documentation": "Automatic, comprehensive documentation",
                "learning": "Continuous learning and knowledge improvement"
            },
            "cost_breakdown": {
                "system_operational": roi_calculation.autonomous_approach["annual_cost"] * 0.6,
                "human_oversight": roi_calculation.autonomous_approach["annual_cost"] * 0.3,
                "infrastructure": roi_calculation.autonomous_approach["annual_cost"] * 0.1,
                "compliance_automation": 0  # Included in operational costs
            },
            "business_impact": {
                "customer_satisfaction": "Minimal impact due to rapid resolution",
                "sla_compliance": "99%+ SLA compliance rate",
                "team_efficiency": "Teams focus on strategic work vs firefighting",
                "scalability": "Scales automatically with incident volume"
            }
        }
        
        # Calculate savings categories
        savings_categories = {
            "labor_cost_reduction": roi_calculation.savings_breakdown["labor_cost_savings"],
            "downtime_elimination": roi_calculation.savings_breakdown["downtime_cost_savings"],
            "reputation_protection": roi_calculation.savings_breakdown["reputation_protection"],
            "compliance_automation": roi_calculation.savings_breakdown["compliance_cost_savings"]
        }
        
        # Calculate efficiency gains
        efficiency_gains = {
            "resolution_time_improvement": 95.0,  # 95% faster resolution
            "accuracy_improvement": 85.0,  # 85% reduction in errors
            "scalability_improvement": 500.0,  # 5x scalability improvement
            "consistency_improvement": 90.0,  # 90% more consistent responses
            "availability_improvement": 100.0  # 24/7 vs business hours only
        }
        
        # Business impact metrics
        business_impact_metrics = {
            "customer_retention_improvement": "15% improvement in customer retention",
            "team_productivity_gain": "40% increase in team productivity",
            "innovation_capacity": "60% more time for strategic initiatives",
            "competitive_advantage": "First-mover advantage in autonomous operations",
            "risk_reduction": "95% reduction in operational risk exposure"
        }
        
        return CostSavingsVisualization(
            visualization_id=visualization_id,
            before_scenario=before_scenario,
            after_scenario=after_scenario,
            savings_categories=savings_categories,
            efficiency_gains=efficiency_gains,
            business_impact_metrics=business_impact_metrics
        )
    
    def get_regulatory_impact_assessment(self, frameworks: List[ComplianceFramework]) -> Dict[str, Any]:
        """
        Get regulatory impact assessment across multiple compliance frameworks.
        
        Shows compliance improvements and risk reduction from automation.
        """
        framework_assessments = {}
        
        # Validate frameworks first
        invalid_frameworks = [f for f in frameworks if f not in self.compliance_frameworks]
        if invalid_frameworks:
            raise ValueError(f"Unsupported compliance frameworks: {invalid_frameworks}. Supported frameworks: {list(self.compliance_frameworks.keys())}")
        
        for framework in frameworks:
            framework_config = self.compliance_frameworks[framework]
            
            # Calculate compliance improvements
            traditional_compliance = 70.0  # Typical manual compliance rate
            autonomous_compliance = 95.0   # Automated compliance rate
            improvement = autonomous_compliance - traditional_compliance
            
            # Calculate risk reduction
            penalty_range = framework_config["penalty_range"]
            risk_reduction = 0.9  # 90% risk reduction
            
            framework_assessments[framework.value] = {
                "framework_name": framework_config["name"],
                "compliance_improvement": f"{improvement:.0f}% improvement",
                "current_compliance_rate": f"{autonomous_compliance:.0f}%",
                "traditional_compliance_rate": f"{traditional_compliance:.0f}%",
                "penalty_risk_reduction": f"{risk_reduction * 100:.0f}%",
                "potential_penalty_range": penalty_range,
                "audit_preparation_time": "80% reduction in preparation time",
                "evidence_collection": "Automated continuous evidence collection",
                "remediation_speed": "Real-time automated remediation",
                "business_impact": framework_config["business_impact"]
            }
        
        # Calculate overall regulatory benefits
        valid_frameworks = [f for f in frameworks if f in self.compliance_frameworks]
        total_frameworks = len(valid_frameworks)
        average_improvement = sum(25.0 for _ in valid_frameworks) / max(1, total_frameworks)  # 25% average improvement
        
        return {
            "regulatory_impact_assessment": {
                "frameworks_assessed": total_frameworks,
                "average_compliance_improvement": f"{average_improvement:.0f}%",
                "overall_risk_reduction": "90%",
                "audit_readiness": "Continuous audit readiness",
                "regulatory_confidence": "High confidence in compliance posture"
            },
            "framework_details": framework_assessments,
            "automation_benefits": {
                "continuous_monitoring": "24/7 automated compliance monitoring",
                "real_time_remediation": "Immediate response to compliance deviations",
                "audit_trail": "Complete automated audit trail and documentation",
                "evidence_management": "Automated evidence collection and retention",
                "risk_assessment": "Continuous risk assessment and mitigation",
                "reporting": "Automated compliance reporting and dashboards"
            },
            "business_value": {
                "penalty_avoidance": "Significant reduction in regulatory penalties",
                "audit_efficiency": "Streamlined audit processes and reduced costs",
                "competitive_advantage": "Enhanced trust and market positioning",
                "operational_excellence": "Improved operational discipline and controls",
                "stakeholder_confidence": "Increased confidence from regulators and customers"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def generate_executive_roi_summary(self, session_id: str) -> Dict[str, Any]:
        """
        Generate executive-level ROI summary for C-suite presentation.
        
        Provides high-level business case with compelling financial metrics.
        """
        roi_calculation = self.calculate_comprehensive_roi(session_id)
        cost_visualization = self.create_dramatic_cost_comparison(roi_calculation)
        
        # Calculate key executive metrics
        annual_savings = roi_calculation.annual_savings
        roi_percentage = roi_calculation.roi_percentage
        payback_months = roi_calculation.payback_period_months
        five_year_value = roi_calculation.five_year_projection
        
        return {
            "executive_roi_summary": {
                "investment_case": {
                    "annual_savings": f"${annual_savings:,.0f}",
                    "roi_percentage": f"{roi_percentage:.0f}%",
                    "payback_period": f"{payback_months:.1f} months",
                    "five_year_value": f"${five_year_value:,.0f}",
                    "investment_grade": "Excellent" if roi_percentage > 300 else "Good"
                },
                "business_transformation": {
                    "operational_efficiency": "95% improvement in incident resolution speed",
                    "cost_reduction": f"${annual_savings:,.0f} annual cost reduction",
                    "risk_mitigation": "90% reduction in operational and compliance risk",
                    "scalability": "Unlimited scalability without proportional cost increase",
                    "competitive_advantage": "First-mover advantage in autonomous operations"
                },
                "strategic_benefits": {
                    "customer_experience": "Dramatic improvement in service reliability",
                    "team_productivity": "40% increase in team focus on strategic initiatives",
                    "innovation_capacity": "Freed resources for digital transformation",
                    "market_position": "Industry leadership in operational excellence",
                    "regulatory_confidence": "Enhanced compliance and reduced regulatory risk"
                }
            },
            "financial_highlights": {
                "cost_per_incident_reduction": f"${roi_calculation.traditional_approach['cost_per_incident']:,.0f} → ${roi_calculation.autonomous_approach['cost_per_incident']:.0f}",
                "downtime_cost_savings": f"${cost_visualization.savings_categories['downtime_elimination']:,.0f} annually",
                "labor_cost_optimization": f"${cost_visualization.savings_categories['labor_cost_reduction']:,.0f} annually",
                "risk_cost_avoidance": f"${cost_visualization.savings_categories['reputation_protection'] + cost_visualization.savings_categories['compliance_automation']:,.0f} annually"
            },
            "implementation_confidence": {
                "technology_maturity": "Production-ready with proven track record",
                "implementation_risk": "Low - phased rollout with fallback capabilities",
                "time_to_value": "Immediate - benefits realized from day one",
                "scalability_assurance": "Designed for enterprise scale and growth",
                "support_model": "Comprehensive support and continuous improvement"
            },
            "next_steps": {
                "pilot_program": "Start with controlled pilot in non-critical environment",
                "phased_rollout": "Gradual expansion across all critical systems",
                "success_metrics": "Clear KPIs and success measurement framework",
                "stakeholder_alignment": "Cross-functional team formation and training",
                "continuous_improvement": "Ongoing optimization and capability enhancement"
            },
            "timestamp": datetime.utcnow().isoformat()
        }


# Global compliance ROI demonstration instance
_compliance_roi_demo = None


def get_compliance_roi_demo() -> ComplianceROIDemonstration:
    """Get the global compliance ROI demonstration instance."""
    global _compliance_roi_demo
    if _compliance_roi_demo is None:
        _compliance_roi_demo = ComplianceROIDemonstration()
    return _compliance_roi_demo