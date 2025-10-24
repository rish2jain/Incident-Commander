"""
Business Impact API Router

FastAPI routes for ROI analysis, reporting, and real-time business impact tracking.

Requirements: 4.1, 4.2, 4.3
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from fastapi import APIRouter, HTTPException, Query, Path, Body, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import json
import io

from src.services.business_impact_calculator import (
    BusinessImpactCalculator, IndustryType, CompanySize, BusinessMetrics,
    IndustrySpecificMetrics, calculate_business_impact_for_incident
)
from src.services.executive_reporting import (
    ExecutiveReportingSystem, ReportType, generate_executive_summary,
    generate_performance_comparison
)
from src.services.business_data_export import (
    BusinessDataExportService, ExportFormat, ExportScope, ExportRequest,
    export_business_data, start_incident_cost_tracking, get_incident_cost_savings
)
from src.utils.logging import get_logger

logger = get_logger("business_impact_api")

router = APIRouter(prefix="/business-impact", tags=["Business Impact"])


# Pydantic models for API requests/responses
class BusinessMetricsRequest(BaseModel):
    """Request model for custom business metrics."""
    annual_revenue: float = Field(..., gt=0, description="Annual revenue in USD")
    employees: int = Field(..., gt=0, description="Number of employees")
    infrastructure_spend: float = Field(..., gt=0, description="Annual infrastructure spend")
    downtime_cost_per_minute: Optional[float] = Field(None, description="Custom downtime cost per minute")
    incident_frequency_monthly: Optional[int] = Field(None, description="Monthly incident frequency")
    current_mttr_minutes: Optional[float] = Field(None, description="Current MTTR in minutes")
    customer_count: Optional[int] = Field(None, description="Total customer count")
    average_transaction_value: Optional[float] = Field(None, description="Average transaction value")


class IndustryMetricsRequest(BaseModel):
    """Request model for industry-specific metrics."""
    # E-commerce
    conversion_rate: Optional[float] = Field(None, ge=0, le=1, description="Conversion rate (0-1)")
    cart_abandonment_rate: Optional[float] = Field(None, ge=0, le=1, description="Cart abandonment rate (0-1)")
    seasonal_multiplier: Optional[float] = Field(None, gt=0, description="Seasonal traffic multiplier")
    
    # Financial services
    transaction_volume_daily: Optional[int] = Field(None, gt=0, description="Daily transaction volume")
    regulatory_penalty_risk: Optional[float] = Field(None, ge=0, le=1, description="Regulatory penalty risk (0-1)")
    customer_trust_impact: Optional[float] = Field(None, ge=0, le=1, description="Customer trust impact (0-1)")
    
    # SaaS
    monthly_recurring_revenue: Optional[float] = Field(None, gt=0, description="Monthly recurring revenue")
    churn_rate_monthly: Optional[float] = Field(None, ge=0, le=1, description="Monthly churn rate (0-1)")
    customer_acquisition_cost: Optional[float] = Field(None, gt=0, description="Customer acquisition cost")
    
    # Healthcare
    patient_safety_risk: Optional[float] = Field(None, ge=0, le=1, description="Patient safety risk (0-1)")
    regulatory_compliance_cost: Optional[float] = Field(None, gt=0, description="Annual regulatory compliance cost")
    operational_efficiency_impact: Optional[float] = Field(None, ge=0, le=1, description="Operational efficiency impact (0-1)")


class ROIAnalysisRequest(BaseModel):
    """Request model for ROI analysis."""
    industry: IndustryType = Field(..., description="Industry type")
    company_size: CompanySize = Field(..., description="Company size category")
    custom_metrics: Optional[BusinessMetricsRequest] = Field(None, description="Custom business metrics")
    industry_metrics: Optional[IndustryMetricsRequest] = Field(None, description="Industry-specific metrics")


class ExportRequest(BaseModel):
    """Request model for data export."""
    format: ExportFormat = Field(..., description="Export format")
    scope: ExportScope = Field(ExportScope.SUMMARY, description="Export scope")
    include_charts: bool = Field(True, description="Include charts in export")
    include_appendices: bool = Field(False, description="Include appendices")
    custom_sections: Optional[List[str]] = Field(None, description="Custom sections to include")


class IncidentCostTrackingRequest(BaseModel):
    """Request model for incident cost tracking."""
    incident_id: str = Field(..., description="Unique incident identifier")
    industry: IndustryType = Field(..., description="Industry type")
    company_size: CompanySize = Field(..., description="Company size category")
    incident_severity: str = Field("medium", description="Incident severity level")
    custom_metrics: Optional[BusinessMetricsRequest] = Field(None, description="Custom business metrics")


# Business Impact Calculator endpoints
@router.post("/roi-analysis")
async def calculate_roi_analysis(request: ROIAnalysisRequest):
    """
    Calculate comprehensive ROI analysis with industry-specific calculations.
    
    Provides detailed business impact analysis including:
    - Industry-specific ROI calculations
    - Cost breakdown and savings analysis
    - Implementation roadmap and success metrics
    - Competitive advantages and risk mitigation
    """
    try:
        calculator = BusinessImpactCalculator()
        
        # Convert custom metrics if provided
        custom_metrics = None
        if request.custom_metrics:
            custom_metrics = BusinessMetrics(
                annual_revenue=request.custom_metrics.annual_revenue,
                employees=request.custom_metrics.employees,
                infrastructure_spend=request.custom_metrics.infrastructure_spend,
                downtime_cost_per_minute=request.custom_metrics.downtime_cost_per_minute or 5600,
                incident_frequency_monthly=request.custom_metrics.incident_frequency_monthly or 25,
                current_mttr_minutes=request.custom_metrics.current_mttr_minutes or 35.0,
                compliance_requirements=["SOC2", "GDPR"],  # Default
                customer_count=request.custom_metrics.customer_count or 1000,
                average_transaction_value=request.custom_metrics.average_transaction_value or 100
            )
        
        # Convert industry metrics if provided
        industry_metrics = None
        if request.industry_metrics:
            industry_metrics = IndustrySpecificMetrics(
                conversion_rate=request.industry_metrics.conversion_rate,
                cart_abandonment_rate=request.industry_metrics.cart_abandonment_rate,
                seasonal_multiplier=request.industry_metrics.seasonal_multiplier,
                transaction_volume_daily=request.industry_metrics.transaction_volume_daily,
                regulatory_penalty_risk=request.industry_metrics.regulatory_penalty_risk,
                customer_trust_impact=request.industry_metrics.customer_trust_impact,
                monthly_recurring_revenue=request.industry_metrics.monthly_recurring_revenue,
                churn_rate_monthly=request.industry_metrics.churn_rate_monthly,
                customer_acquisition_cost=request.industry_metrics.customer_acquisition_cost,
                patient_safety_risk=request.industry_metrics.patient_safety_risk,
                regulatory_compliance_cost=request.industry_metrics.regulatory_compliance_cost,
                operational_efficiency_impact=request.industry_metrics.operational_efficiency_impact
            )
        
        # Calculate comprehensive impact
        business_impact = await calculator.calculate_comprehensive_impact(
            request.industry,
            request.company_size,
            custom_metrics,
            industry_metrics
        )
        
        logger.info(f"ROI analysis calculated for {request.industry.value} {request.company_size.value}")
        
        return {
            "roi_analysis": {
                "investment_grade": business_impact.roi_analysis.investment_grade,
                "payback_period_months": business_impact.roi_analysis.payback_period_months,
                "net_annual_savings": business_impact.roi_analysis.net_annual_savings,
                "year_3_roi_percentage": business_impact.roi_analysis.year_3_roi_percentage,
                "year_5_roi_percentage": business_impact.roi_analysis.year_5_roi_percentage,
                "npv_5_year": business_impact.roi_analysis.npv_5_year,
                "roi_category": business_impact.roi_analysis.roi_category
            },
            "current_state_costs": business_impact.current_state_costs,
            "future_state_benefits": business_impact.future_state_benefits,
            "industry_specific_analysis": business_impact.industry_specific_analysis,
            "competitive_advantages": business_impact.competitive_advantages,
            "risk_mitigation": business_impact.risk_mitigation,
            "executive_summary": business_impact.executive_summary,
            "implementation_roadmap": business_impact.implementation_roadmap,
            "success_metrics": business_impact.success_metrics,
            "timestamp": business_impact.timestamp.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to calculate ROI analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/roi-analysis/{industry}/{company_size}")
async def get_roi_analysis(
    industry: IndustryType = Path(..., description="Industry type"),
    company_size: CompanySize = Path(..., description="Company size category")
):
    """
    Get ROI analysis for specific industry and company size combination.
    
    Quick ROI analysis using default metrics for the specified industry and company size.
    """
    try:
        calculator = BusinessImpactCalculator()
        
        business_impact = await calculator.calculate_comprehensive_impact(
            industry, company_size
        )
        
        return {
            "industry": industry.value,
            "company_size": company_size.value,
            "roi_summary": {
                "investment_grade": business_impact.roi_analysis.investment_grade,
                "payback_months": business_impact.roi_analysis.payback_period_months,
                "annual_savings": business_impact.roi_analysis.net_annual_savings,
                "3_year_roi": business_impact.roi_analysis.year_3_roi_percentage,
                "roi_category": business_impact.roi_analysis.roi_category
            },
            "key_benefits": {
                "mttr_improvement": business_impact.future_state_benefits["mttr_improvement_percentage"],
                "incidents_prevented": business_impact.future_state_benefits["incidents_prevented_annually"],
                "cost_reduction": business_impact.current_state_costs["total_annual_incident_cost"] - 
                               business_impact.future_state_benefits["total_annual_benefits"]
            },
            "competitive_advantages": business_impact.competitive_advantages[:3],  # Top 3
            "timestamp": business_impact.timestamp.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get ROI analysis for {industry.value} {company_size.value}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Executive Reporting endpoints
@router.get("/executive-summary/{industry}/{company_size}")
async def get_executive_summary(
    industry: IndustryType = Path(..., description="Industry type"),
    company_size: CompanySize = Path(..., description="Company size category")
):
    """
    Generate executive summary report for C-level presentation.
    
    Provides high-level business case with key metrics and strategic benefits.
    """
    try:
        summary = await generate_executive_summary(industry, company_size)
        
        logger.info(f"Executive summary generated for {industry.value} {company_size.value}")
        
        return summary
        
    except Exception as e:
        logger.error(f"Failed to generate executive summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance-comparison/{industry}/{company_size}")
async def get_performance_comparison(
    industry: IndustryType = Path(..., description="Industry type"),
    company_size: CompanySize = Path(..., description="Company size category")
):
    """
    Get performance comparison between traditional and autonomous incident response.
    
    Compares traditional manual approaches with autonomous multi-agent system.
    """
    try:
        comparison = await generate_performance_comparison(industry, company_size)
        
        logger.info(f"Performance comparison generated for {industry.value} {company_size.value}")
        
        return comparison
        
    except Exception as e:
        logger.error(f"Failed to generate performance comparison: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/executive-report")
async def generate_executive_report(
    report_type: ReportType = Query(..., description="Type of executive report"),
    industry: IndustryType = Query(..., description="Industry type"),
    company_size: CompanySize = Query(..., description="Company size category")
):
    """
    Generate comprehensive executive report.
    
    Available report types:
    - executive_summary: High-level overview for executives
    - roi_analysis: Detailed financial analysis
    - competitive_comparison: Market positioning analysis
    - performance_dashboard: Operational metrics dashboard
    - board_presentation: Board-level strategic presentation
    """
    try:
        reporting_system = ExecutiveReportingSystem()
        
        report = await reporting_system.generate_executive_report(
            report_type, industry, company_size
        )
        
        logger.info(f"Executive report {report_type.value} generated for {industry.value} {company_size.value}")
        
        return {
            "report_id": report.report_id,
            "report_type": report.report_type.value,
            "industry": report.industry.value,
            "company_size": report.company_size.value,
            "generated_at": report.generated_at.isoformat(),
            "executive_summary": report.executive_summary,
            "key_findings": report.key_findings,
            "recommendations": report.recommendations,
            "financial_impact": report.financial_impact,
            "performance_metrics": report.performance_metrics,
            "competitive_analysis": report.competitive_analysis,
            "implementation_plan": report.implementation_plan,
            "risk_assessment": report.risk_assessment
        }
        
    except Exception as e:
        logger.error(f"Failed to generate executive report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Data Export endpoints
@router.post("/export")
async def export_business_data_endpoint(
    industry: IndustryType = Query(..., description="Industry type"),
    company_size: CompanySize = Query(..., description="Company size category"),
    export_request: ExportRequest = Body(..., description="Export configuration")
):
    """
    Export business impact data in specified format.
    
    Supported formats:
    - JSON: Structured data export
    - CSV: Tabular data for spreadsheet analysis
    - Excel: Multi-sheet workbook with charts
    - PDF: Professional report document
    """
    try:
        export_result = await export_business_data(
            industry, company_size, export_request.format, export_request.scope
        )
        
        if not export_result.success:
            raise HTTPException(status_code=500, detail=export_result.error_message)
        
        # Determine content type based on format
        content_types = {
            ExportFormat.JSON: "application/json",
            ExportFormat.CSV: "text/csv",
            ExportFormat.EXCEL: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ExportFormat.PDF: "application/pdf"
        }
        
        # Determine filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"business_impact_{industry.value}_{company_size.value}_{timestamp}.{export_request.format.value}"
        
        logger.info(f"Business data exported: {export_result.export_id}")
        
        # Return file as streaming response
        return StreamingResponse(
            io.BytesIO(export_result.file_content),
            media_type=content_types[export_request.format],
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Failed to export business data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export-formats")
async def get_export_formats():
    """
    Get available export formats and their capabilities.
    """
    return {
        "formats": [
            {
                "format": "json",
                "description": "Structured JSON data",
                "supports_charts": False,
                "supports_appendices": True,
                "best_for": "API integration and data processing"
            },
            {
                "format": "csv",
                "description": "Comma-separated values",
                "supports_charts": False,
                "supports_appendices": False,
                "best_for": "Spreadsheet analysis and data import"
            },
            {
                "format": "excel",
                "description": "Multi-sheet Excel workbook",
                "supports_charts": True,
                "supports_appendices": True,
                "best_for": "Financial analysis and presentations"
            },
            {
                "format": "pdf",
                "description": "Professional report document",
                "supports_charts": True,
                "supports_appendices": True,
                "best_for": "Executive presentations and documentation"
            }
        ],
        "scopes": [
            {
                "scope": "summary",
                "description": "Key metrics and ROI summary",
                "recommended_for": "Quick overview and dashboards"
            },
            {
                "scope": "detailed",
                "description": "Comprehensive analysis with breakdowns",
                "recommended_for": "Financial planning and analysis"
            },
            {
                "scope": "full_report",
                "description": "Complete report with all sections",
                "recommended_for": "Executive presentations and documentation"
            }
        ]
    }


# Real-time Cost Tracking endpoints
@router.post("/incidents/{incident_id}/start-cost-tracking")
async def start_incident_cost_tracking_endpoint(
    incident_id: str = Path(..., description="Incident identifier"),
    request: IncidentCostTrackingRequest = Body(..., description="Cost tracking configuration")
):
    """
    Start real-time cost savings analysis for an incident.
    
    Tracks cost accumulation in real-time comparing traditional vs autonomous response.
    """
    try:
        tracking_id = await start_incident_cost_tracking(
            incident_id, request.industry, request.company_size
        )
        
        logger.info(f"Cost tracking started for incident {incident_id}")
        
        return {
            "incident_id": incident_id,
            "tracking_id": tracking_id,
            "status": "tracking_started",
            "industry": request.industry.value,
            "company_size": request.company_size.value,
            "started_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to start cost tracking for incident {incident_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/incidents/{incident_id}/cost-savings")
async def get_incident_cost_savings_endpoint(
    incident_id: str = Path(..., description="Incident identifier")
):
    """
    Get current cost savings analysis for an ongoing incident.
    
    Returns real-time cost accumulation and savings compared to traditional approach.
    """
    try:
        cost_analysis = await get_incident_cost_savings(incident_id)
        
        if not cost_analysis:
            raise HTTPException(status_code=404, detail=f"No cost tracking found for incident {incident_id}")
        
        return cost_analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get cost savings for incident {incident_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/incidents/{incident_id}/finalize-cost-analysis")
async def finalize_incident_cost_analysis(
    incident_id: str = Path(..., description="Incident identifier"),
    actual_resolution_time_minutes: float = Body(..., description="Actual resolution time in minutes")
):
    """
    Finalize cost analysis with actual incident resolution time.
    
    Calculates final cost savings based on actual resolution time vs traditional MTTR.
    """
    try:
        export_service = BusinessDataExportService()
        
        final_analysis = await export_service.finalize_real_time_cost_analysis(
            incident_id, actual_resolution_time_minutes
        )
        
        logger.info(f"Cost analysis finalized for incident {incident_id}")
        
        return {
            "incident_id": final_analysis.incident_id,
            "actual_resolution_time_minutes": actual_resolution_time_minutes,
            "final_cost_savings": final_analysis.cost_savings_realized,
            "mttr_improvement_achieved": final_analysis.mttr_improvement_percentage,
            "business_impact_prevented": final_analysis.business_impact_prevented,
            "traditional_cost": final_analysis.traditional_cost_accumulated,
            "autonomous_cost": final_analysis.autonomous_cost_accumulated,
            "finalized_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to finalize cost analysis for incident {incident_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Incident-specific Business Impact endpoints
@router.post("/incidents/calculate-impact")
async def calculate_incident_business_impact(
    incident_data: Dict[str, Any] = Body(..., description="Incident data"),
    industry: IndustryType = Query(..., description="Industry type"),
    company_size: CompanySize = Query(..., description="Company size category")
):
    """
    Calculate business impact for a specific incident.
    
    Analyzes the business impact of a specific incident including cost, duration,
    and savings achieved through autonomous response.
    """
    try:
        impact_analysis = await calculate_business_impact_for_incident(
            incident_data, industry, company_size
        )
        
        logger.info(f"Business impact calculated for incident {incident_data.get('incident_id', 'unknown')}")
        
        return impact_analysis
        
    except Exception as e:
        logger.error(f"Failed to calculate incident business impact: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Industry and Company Size Information endpoints
@router.get("/industries")
async def get_supported_industries():
    """
    Get list of supported industries with their characteristics.
    """
    return {
        "industries": [
            {
                "industry": "ecommerce",
                "name": "E-commerce",
                "description": "Online retail and marketplace platforms",
                "key_metrics": ["conversion_rate", "cart_abandonment_rate", "seasonal_multiplier"],
                "typical_downtime_cost_multiplier": 2.8
            },
            {
                "industry": "financial_services",
                "name": "Financial Services",
                "description": "Banks, payment processors, fintech companies",
                "key_metrics": ["transaction_volume_daily", "regulatory_penalty_risk", "customer_trust_impact"],
                "typical_downtime_cost_multiplier": 4.2
            },
            {
                "industry": "saas",
                "name": "Software as a Service",
                "description": "Cloud-based software platforms",
                "key_metrics": ["monthly_recurring_revenue", "churn_rate_monthly", "customer_acquisition_cost"],
                "typical_downtime_cost_multiplier": 3.1
            },
            {
                "industry": "healthcare",
                "name": "Healthcare",
                "description": "Healthcare providers and medical technology",
                "key_metrics": ["patient_safety_risk", "regulatory_compliance_cost", "operational_efficiency_impact"],
                "typical_downtime_cost_multiplier": 3.5
            }
        ]
    }


@router.get("/company-sizes")
async def get_supported_company_sizes():
    """
    Get list of supported company sizes with their characteristics.
    """
    return {
        "company_sizes": [
            {
                "size": "startup",
                "name": "Startup",
                "description": "Early-stage companies",
                "typical_revenue_range": "$1M - $5M",
                "typical_employees": "10 - 50",
                "implementation_cost": "$150,000"
            },
            {
                "size": "smb",
                "name": "Small to Medium Business",
                "description": "Established small businesses",
                "typical_revenue_range": "$5M - $50M",
                "typical_employees": "50 - 500",
                "implementation_cost": "$300,000"
            },
            {
                "size": "mid_market",
                "name": "Mid-Market",
                "description": "Mid-size enterprises",
                "typical_revenue_range": "$50M - $500M",
                "typical_employees": "500 - 5,000",
                "implementation_cost": "$500,000"
            },
            {
                "size": "enterprise",
                "name": "Enterprise",
                "description": "Large enterprises",
                "typical_revenue_range": "$500M - $5B",
                "typical_employees": "5,000 - 50,000",
                "implementation_cost": "$750,000"
            },
            {
                "size": "fortune_500",
                "name": "Fortune 500",
                "description": "Largest corporations",
                "typical_revenue_range": "$5B+",
                "typical_employees": "50,000+",
                "implementation_cost": "$1,200,000"
            }
        ]
    }


# Health and Status endpoints
@router.get("/health")
async def business_impact_health():
    """
    Health check for business impact services.
    """
    try:
        # Test calculator
        calculator = BusinessImpactCalculator()
        
        # Test reporting system
        reporting_system = ExecutiveReportingSystem()
        
        # Test export service
        export_service = BusinessDataExportService()
        
        return {
            "status": "healthy",
            "services": {
                "business_calculator": "operational",
                "executive_reporting": "operational",
                "data_export": "operational"
            },
            "capabilities": {
                "roi_analysis": True,
                "executive_reporting": True,
                "data_export": True,
                "real_time_cost_tracking": True,
                "industry_specific_analysis": True
            },
            "supported_formats": ["json", "csv", "excel", "pdf"],
            "supported_industries": len(IndustryType),
            "supported_company_sizes": len(CompanySize),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Business impact health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }