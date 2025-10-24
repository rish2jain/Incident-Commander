"""
Business Data Export Service

Implements multi-format export capabilities (PDF, Excel, JSON) and real-time
cost savings analysis during incident resolution.

Requirements: 4.3, 4.5
"""

import asyncio
import json
import io
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, BinaryIO
from dataclasses import dataclass, asdict
from enum import Enum
import csv

# Optional imports for export formats
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from src.services.business_impact_calculator import (
    BusinessImpactCalculator, IndustryType, CompanySize, BusinessImpactReport
)
from src.services.executive_reporting import (
    ExecutiveReportingSystem, ReportType, ExecutiveReport
)


class ExportFormat(Enum):
    """Supported export formats."""
    JSON = "json"
    CSV = "csv"
    EXCEL = "excel"
    PDF = "pdf"


class ExportScope(Enum):
    """Export scope options."""
    SUMMARY = "summary"
    DETAILED = "detailed"
    FULL_REPORT = "full_report"
    CUSTOM = "custom"


@dataclass
class ExportRequest:
    """Export request configuration."""
    format: ExportFormat
    scope: ExportScope
    industry: IndustryType
    company_size: CompanySize
    include_charts: bool = True
    include_appendices: bool = False
    custom_sections: Optional[List[str]] = None
    date_range: Optional[Dict[str, datetime]] = None


@dataclass
class ExportResult:
    """Export operation result."""
    success: bool
    export_id: str
    format: ExportFormat
    file_size_bytes: int
    generated_at: datetime
    download_url: Optional[str] = None
    file_content: Optional[bytes] = None
    error_message: Optional[str] = None


@dataclass
class RealTimeCostAnalysis:
    """Real-time cost savings analysis during incident resolution."""
    incident_id: str
    start_time: datetime
    current_time: datetime
    duration_minutes: float
    traditional_cost_accumulated: float
    autonomous_cost_accumulated: float
    cost_savings_realized: float
    projected_final_savings: float
    mttr_improvement_percentage: float
    business_impact_prevented: Dict[str, float]


class BusinessDataExportService:
    """Service for exporting business impact data in multiple formats."""
    
    def __init__(self):
        """Initialize export service."""
        self.business_calculator = BusinessImpactCalculator()
        self.reporting_system = ExecutiveReportingSystem()
        self.export_cache = {}
        self.real_time_analyses = {}
    
    async def export_business_impact_data(
        self,
        export_request: ExportRequest
    ) -> ExportResult:
        """Export business impact data in specified format."""
        
        export_id = f"export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            # Generate business impact report
            business_impact = await self.business_calculator.calculate_comprehensive_impact(
                export_request.industry, export_request.company_size
            )
            
            # Generate executive report if needed
            executive_report = None
            if export_request.scope in [ExportScope.DETAILED, ExportScope.FULL_REPORT]:
                executive_report = await self.reporting_system.generate_executive_report(
                    ReportType.EXECUTIVE_SUMMARY,
                    export_request.industry,
                    export_request.company_size
                )
            
            # Export based on format
            if export_request.format == ExportFormat.JSON:
                return await self._export_json(
                    export_id, business_impact, executive_report, export_request
                )
            elif export_request.format == ExportFormat.CSV:
                return await self._export_csv(
                    export_id, business_impact, executive_report, export_request
                )
            elif export_request.format == ExportFormat.EXCEL:
                return await self._export_excel(
                    export_id, business_impact, executive_report, export_request
                )
            elif export_request.format == ExportFormat.PDF:
                return await self._export_pdf(
                    export_id, business_impact, executive_report, export_request
                )
            else:
                raise ValueError(f"Unsupported export format: {export_request.format}")
                
        except Exception as e:
            return ExportResult(
                success=False,
                export_id=export_id,
                format=export_request.format,
                file_size_bytes=0,
                generated_at=datetime.utcnow(),
                error_message=str(e)
            )
    
    async def _export_json(
        self,
        export_id: str,
        business_impact: BusinessImpactReport,
        executive_report: Optional[ExecutiveReport],
        export_request: ExportRequest
    ) -> ExportResult:
        """Export data as JSON."""
        
        # Prepare data based on scope
        export_data = await self._prepare_export_data(
            business_impact, executive_report, export_request
        )
        
        # Convert to JSON
        json_content = json.dumps(export_data, indent=2, default=str)
        file_content = json_content.encode('utf-8')
        
        return ExportResult(
            success=True,
            export_id=export_id,
            format=ExportFormat.JSON,
            file_size_bytes=len(file_content),
            generated_at=datetime.utcnow(),
            file_content=file_content
        )
    
    async def _export_csv(
        self,
        export_id: str,
        business_impact: BusinessImpactReport,
        executive_report: Optional[ExecutiveReport],
        export_request: ExportRequest
    ) -> ExportResult:
        """Export data as CSV."""
        
        # Create CSV content
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers and data based on scope
        if export_request.scope == ExportScope.SUMMARY:
            await self._write_summary_csv(writer, business_impact)
        else:
            await self._write_detailed_csv(writer, business_impact, executive_report)
        
        csv_content = output.getvalue()
        file_content = csv_content.encode('utf-8')
        
        return ExportResult(
            success=True,
            export_id=export_id,
            format=ExportFormat.CSV,
            file_size_bytes=len(file_content),
            generated_at=datetime.utcnow(),
            file_content=file_content
        )
    
    async def _export_excel(
        self,
        export_id: str,
        business_impact: BusinessImpactReport,
        executive_report: Optional[ExecutiveReport],
        export_request: ExportRequest
    ) -> ExportResult:
        """Export data as Excel."""
        
        if not PANDAS_AVAILABLE:
            raise RuntimeError("Pandas is required for Excel export but not available")
        
        # Create Excel workbook with multiple sheets
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Executive Summary sheet
            summary_data = await self._prepare_summary_dataframe(business_impact)
            summary_data.to_excel(writer, sheet_name='Executive Summary', index=False)
            
            # ROI Analysis sheet
            roi_data = await self._prepare_roi_dataframe(business_impact)
            roi_data.to_excel(writer, sheet_name='ROI Analysis', index=False)
            
            # Cost Breakdown sheet
            cost_data = await self._prepare_cost_breakdown_dataframe(business_impact)
            cost_data.to_excel(writer, sheet_name='Cost Breakdown', index=False)
            
            # Benefits Analysis sheet
            benefits_data = await self._prepare_benefits_dataframe(business_impact)
            benefits_data.to_excel(writer, sheet_name='Benefits Analysis', index=False)
            
            # Industry Analysis sheet if available
            if business_impact.industry_specific_analysis:
                industry_data = await self._prepare_industry_dataframe(business_impact)
                industry_data.to_excel(writer, sheet_name='Industry Analysis', index=False)
        
        file_content = output.getvalue()
        
        return ExportResult(
            success=True,
            export_id=export_id,
            format=ExportFormat.EXCEL,
            file_size_bytes=len(file_content),
            generated_at=datetime.utcnow(),
            file_content=file_content
        )
    
    async def _export_pdf(
        self,
        export_id: str,
        business_impact: BusinessImpactReport,
        executive_report: Optional[ExecutiveReport],
        export_request: ExportRequest
    ) -> ExportResult:
        """Export data as PDF."""
        
        if not REPORTLAB_AVAILABLE:
            raise RuntimeError("ReportLab is required for PDF export but not available")
        
        # Create PDF document
        output = io.BytesIO()
        doc = SimpleDocTemplate(output, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.darkblue
        )
        story.append(Paragraph("Business Impact Analysis Report", title_style))
        story.append(Spacer(1, 20))
        
        # Executive Summary
        story.append(Paragraph("Executive Summary", styles['Heading2']))
        summary_text = f"""
        <b>Industry:</b> {business_impact.industry.value.title()}<br/>
        <b>Company Size:</b> {business_impact.company_size.value.title()}<br/>
        <b>Investment Grade:</b> {business_impact.roi_analysis.investment_grade}<br/>
        <b>Payback Period:</b> {business_impact.roi_analysis.payback_period_months:.1f} months<br/>
        <b>3-Year ROI:</b> {business_impact.roi_analysis.year_3_roi_percentage:.0f}%<br/>
        <b>Annual Savings:</b> ${business_impact.roi_analysis.net_annual_savings:,.0f}
        """
        story.append(Paragraph(summary_text, styles['Normal']))
        story.append(Spacer(1, 20))
        
        # ROI Analysis Table
        story.append(Paragraph("ROI Analysis", styles['Heading2']))
        roi_data = [
            ['Metric', 'Value'],
            ['Implementation Cost', f"${business_impact.roi_analysis.implementation_cost:,.0f}"],
            ['Annual Licensing', f"${business_impact.roi_analysis.annual_licensing_cost:,.0f}"],
            ['Net Annual Savings', f"${business_impact.roi_analysis.net_annual_savings:,.0f}"],
            ['Payback Period', f"{business_impact.roi_analysis.payback_period_months:.1f} months"],
            ['Year 1 ROI', f"{business_impact.roi_analysis.year_1_roi_percentage:.0f}%"],
            ['Year 3 ROI', f"{business_impact.roi_analysis.year_3_roi_percentage:.0f}%"],
            ['Year 5 ROI', f"{business_impact.roi_analysis.year_5_roi_percentage:.0f}%"],
            ['5-Year NPV', f"${business_impact.roi_analysis.npv_5_year:,.0f}"]
        ]
        
        roi_table = Table(roi_data)
        roi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(roi_table)
        story.append(Spacer(1, 20))
        
        # Cost Breakdown
        story.append(Paragraph("Current State Cost Breakdown", styles['Heading2']))
        cost_breakdown = business_impact.current_state_costs['breakdown_percentages']
        cost_text = "<br/>".join([
            f"<b>{key.replace('_', ' ').title()}:</b> {value:.1f}%"
            for key, value in cost_breakdown.items()
        ])
        story.append(Paragraph(cost_text, styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Competitive Advantages
        story.append(Paragraph("Competitive Advantages", styles['Heading2']))
        advantages_text = "<br/>".join([
            f"• {advantage}" for advantage in business_impact.competitive_advantages
        ])
        story.append(Paragraph(advantages_text, styles['Normal']))
        
        # Build PDF
        doc.build(story)
        file_content = output.getvalue()
        
        return ExportResult(
            success=True,
            export_id=export_id,
            format=ExportFormat.PDF,
            file_size_bytes=len(file_content),
            generated_at=datetime.utcnow(),
            file_content=file_content
        )
    
    async def start_real_time_cost_analysis(
        self,
        incident_id: str,
        industry: IndustryType,
        company_size: CompanySize,
        incident_severity: str = "medium"
    ) -> str:
        """Start real-time cost savings analysis for an incident."""
        
        # Generate baseline metrics
        metrics = await self.business_calculator._generate_realistic_metrics(
            industry, company_size
        )
        
        # Create real-time analysis
        analysis = RealTimeCostAnalysis(
            incident_id=incident_id,
            start_time=datetime.utcnow(),
            current_time=datetime.utcnow(),
            duration_minutes=0.0,
            traditional_cost_accumulated=0.0,
            autonomous_cost_accumulated=0.0,
            cost_savings_realized=0.0,
            projected_final_savings=0.0,
            mttr_improvement_percentage=95.2,
            business_impact_prevented={}
        )
        
        # Store analysis
        self.real_time_analyses[incident_id] = {
            "analysis": analysis,
            "metrics": metrics,
            "industry": industry,
            "company_size": company_size,
            "severity": incident_severity
        }
        
        return incident_id
    
    async def update_real_time_cost_analysis(
        self,
        incident_id: str
    ) -> RealTimeCostAnalysis:
        """Update real-time cost analysis for ongoing incident."""
        
        if incident_id not in self.real_time_analyses:
            raise ValueError(f"No real-time analysis found for incident {incident_id}")
        
        analysis_data = self.real_time_analyses[incident_id]
        analysis = analysis_data["analysis"]
        metrics = analysis_data["metrics"]
        
        # Update current time and duration
        current_time = datetime.utcnow()
        duration_minutes = (current_time - analysis.start_time).total_seconds() / 60
        
        # Calculate traditional cost (what would have been spent)
        traditional_cost_per_minute = metrics.downtime_cost_per_minute * 4.2  # Include indirect costs
        traditional_cost_accumulated = duration_minutes * traditional_cost_per_minute
        
        # Calculate autonomous cost (actual cost with system)
        autonomous_cost_per_minute = traditional_cost_per_minute * 0.05  # 95% reduction
        autonomous_cost_accumulated = duration_minutes * autonomous_cost_per_minute
        
        # Calculate savings
        cost_savings_realized = traditional_cost_accumulated - autonomous_cost_accumulated
        
        # Project final savings based on expected MTTR
        expected_traditional_mttr = metrics.current_mttr_minutes
        expected_autonomous_mttr = expected_traditional_mttr * 0.048  # 95.2% reduction
        
        if duration_minutes < expected_autonomous_mttr:
            # Still in progress, project final cost
            projected_traditional_cost = expected_traditional_mttr * traditional_cost_per_minute
            projected_autonomous_cost = expected_autonomous_mttr * autonomous_cost_per_minute
            projected_final_savings = projected_traditional_cost - projected_autonomous_cost
        else:
            # Incident resolved, final savings realized
            projected_final_savings = cost_savings_realized
        
        # Calculate business impact prevented
        business_impact_prevented = {
            "revenue_loss_prevented": cost_savings_realized * 0.3,
            "productivity_loss_prevented": cost_savings_realized * 0.25,
            "customer_churn_prevented": cost_savings_realized * 0.15,
            "compliance_cost_avoided": cost_savings_realized * 0.1,
            "reputation_damage_avoided": cost_savings_realized * 0.2
        }
        
        # Update analysis
        analysis.current_time = current_time
        analysis.duration_minutes = duration_minutes
        analysis.traditional_cost_accumulated = traditional_cost_accumulated
        analysis.autonomous_cost_accumulated = autonomous_cost_accumulated
        analysis.cost_savings_realized = cost_savings_realized
        analysis.projected_final_savings = projected_final_savings
        analysis.business_impact_prevented = business_impact_prevented
        
        return analysis
    
    async def get_real_time_cost_analysis(
        self,
        incident_id: str
    ) -> Optional[RealTimeCostAnalysis]:
        """Get current real-time cost analysis."""
        
        if incident_id not in self.real_time_analyses:
            return None
        
        return await self.update_real_time_cost_analysis(incident_id)
    
    async def finalize_real_time_cost_analysis(
        self,
        incident_id: str,
        actual_resolution_time_minutes: float
    ) -> RealTimeCostAnalysis:
        """Finalize real-time cost analysis with actual resolution time."""
        
        if incident_id not in self.real_time_analyses:
            raise ValueError(f"No real-time analysis found for incident {incident_id}")
        
        analysis_data = self.real_time_analyses[incident_id]
        analysis = analysis_data["analysis"]
        metrics = analysis_data["metrics"]
        
        # Calculate final costs based on actual resolution time
        traditional_cost_per_minute = metrics.downtime_cost_per_minute * 4.2
        autonomous_cost_per_minute = traditional_cost_per_minute * 0.05
        
        # What traditional approach would have cost
        traditional_total_cost = metrics.current_mttr_minutes * traditional_cost_per_minute
        
        # Actual autonomous cost
        autonomous_total_cost = actual_resolution_time_minutes * autonomous_cost_per_minute
        
        # Final savings
        final_savings = traditional_total_cost - autonomous_total_cost
        
        # Update analysis with final values
        analysis.duration_minutes = actual_resolution_time_minutes
        analysis.traditional_cost_accumulated = traditional_total_cost
        analysis.autonomous_cost_accumulated = autonomous_total_cost
        analysis.cost_savings_realized = final_savings
        analysis.projected_final_savings = final_savings
        
        # Calculate actual MTTR improvement
        actual_improvement = ((metrics.current_mttr_minutes - actual_resolution_time_minutes) / 
                            metrics.current_mttr_minutes) * 100
        analysis.mttr_improvement_percentage = actual_improvement
        
        # Clean up the analysis from memory to prevent unbounded growth
        self.cleanup_incident_analysis(incident_id)
        
        return analysis
    
    def cleanup_incident_analysis(self, incident_id: str) -> None:
        """
        Clean up finalized incident analysis from memory to prevent unbounded growth.
        
        Args:
            incident_id: The incident ID to remove from real_time_analyses
        """
        if incident_id in self.real_time_analyses:
            del self.real_time_analyses[incident_id]
    
    async def _prepare_export_data(
        self,
        business_impact: BusinessImpactReport,
        executive_report: Optional[ExecutiveReport],
        export_request: ExportRequest
    ) -> Dict[str, Any]:
        """Prepare data for export based on scope."""
        
        if export_request.scope == ExportScope.SUMMARY:
            return {
                "summary": {
                    "industry": business_impact.industry.value,
                    "company_size": business_impact.company_size.value,
                    "investment_grade": business_impact.roi_analysis.investment_grade,
                    "payback_months": business_impact.roi_analysis.payback_period_months,
                    "annual_savings": business_impact.roi_analysis.net_annual_savings,
                    "roi_3_year": business_impact.roi_analysis.year_3_roi_percentage
                }
            }
        elif export_request.scope == ExportScope.DETAILED:
            return {
                "business_impact": asdict(business_impact),
                "executive_report": asdict(executive_report) if executive_report else None
            }
        elif export_request.scope == ExportScope.FULL_REPORT:
            return {
                "business_impact": asdict(business_impact),
                "executive_report": asdict(executive_report) if executive_report else None,
                "export_metadata": {
                    "generated_at": datetime.utcnow().isoformat(),
                    "export_scope": export_request.scope.value,
                    "format": export_request.format.value
                }
            }
        else:  # CUSTOM
            custom_data = {}
            if export_request.custom_sections:
                for section in export_request.custom_sections:
                    if hasattr(business_impact, section):
                        custom_data[section] = getattr(business_impact, section)
            return custom_data
    
    async def _write_summary_csv(
        self,
        writer: csv.writer,
        business_impact: BusinessImpactReport
    ) -> None:
        """Write summary data to CSV."""
        
        writer.writerow(['Metric', 'Value'])
        writer.writerow(['Industry', business_impact.industry.value])
        writer.writerow(['Company Size', business_impact.company_size.value])
        writer.writerow(['Investment Grade', business_impact.roi_analysis.investment_grade])
        writer.writerow(['Payback Period (months)', f"{business_impact.roi_analysis.payback_period_months:.1f}"])
        writer.writerow(['Annual Savings', f"${business_impact.roi_analysis.net_annual_savings:,.0f}"])
        writer.writerow(['3-Year ROI', f"{business_impact.roi_analysis.year_3_roi_percentage:.0f}%"])
        writer.writerow(['5-Year NPV', f"${business_impact.roi_analysis.npv_5_year:,.0f}"])
    
    async def _write_detailed_csv(
        self,
        writer: csv.writer,
        business_impact: BusinessImpactReport,
        executive_report: Optional[ExecutiveReport]
    ) -> None:
        """Write detailed data to CSV."""
        
        # ROI Analysis section
        writer.writerow(['ROI Analysis'])
        writer.writerow(['Metric', 'Value'])
        writer.writerow(['Implementation Cost', f"${business_impact.roi_analysis.implementation_cost:,.0f}"])
        writer.writerow(['Annual Licensing', f"${business_impact.roi_analysis.annual_licensing_cost:,.0f}"])
        writer.writerow(['Net Annual Savings', f"${business_impact.roi_analysis.net_annual_savings:,.0f}"])
        writer.writerow(['Payback Period', f"{business_impact.roi_analysis.payback_period_months:.1f} months"])
        writer.writerow(['Year 1 ROI', f"{business_impact.roi_analysis.year_1_roi_percentage:.0f}%"])
        writer.writerow(['Year 3 ROI', f"{business_impact.roi_analysis.year_3_roi_percentage:.0f}%"])
        writer.writerow(['Year 5 ROI', f"{business_impact.roi_analysis.year_5_roi_percentage:.0f}%"])
        writer.writerow([])
        
        # Cost Breakdown section
        writer.writerow(['Current State Cost Breakdown'])
        writer.writerow(['Cost Category', 'Percentage'])
        for category, percentage in business_impact.current_state_costs['breakdown_percentages'].items():
            writer.writerow([category.replace('_', ' ').title(), f"{percentage:.1f}%"])
        writer.writerow([])
        
        # Benefits Breakdown section
        writer.writerow(['Future Benefits Breakdown'])
        writer.writerow(['Benefit Category', 'Percentage'])
        for category, percentage in business_impact.future_state_benefits['benefits_breakdown'].items():
            writer.writerow([category.replace('_', ' ').title(), f"{percentage:.1f}%"])
    
    async def _prepare_summary_dataframe(self, business_impact: BusinessImpactReport) -> 'pd.DataFrame':
        """Prepare summary DataFrame for Excel export."""
        
        data = {
            'Metric': [
                'Industry',
                'Company Size',
                'Investment Grade',
                'Payback Period (months)',
                'Annual Savings',
                '3-Year ROI (%)',
                '5-Year NPV'
            ],
            'Value': [
                business_impact.industry.value,
                business_impact.company_size.value,
                business_impact.roi_analysis.investment_grade,
                f"{business_impact.roi_analysis.payback_period_months:.1f}",
                f"${business_impact.roi_analysis.net_annual_savings:,.0f}",
                f"{business_impact.roi_analysis.year_3_roi_percentage:.0f}%",
                f"${business_impact.roi_analysis.npv_5_year:,.0f}"
            ]
        }
        
        return pd.DataFrame(data)
    
    async def _prepare_roi_dataframe(self, business_impact: BusinessImpactReport) -> 'pd.DataFrame':
        """Prepare ROI DataFrame for Excel export."""
        
        data = {
            'Metric': [
                'Implementation Cost',
                'Annual Licensing Cost',
                'Net Annual Savings',
                'Payback Period (months)',
                'Year 1 ROI (%)',
                'Year 3 ROI (%)',
                'Year 5 ROI (%)',
                '5-Year NPV'
            ],
            'Value': [
                business_impact.roi_analysis.implementation_cost,
                business_impact.roi_analysis.annual_licensing_cost,
                business_impact.roi_analysis.net_annual_savings,
                business_impact.roi_analysis.payback_period_months,
                business_impact.roi_analysis.year_1_roi_percentage,
                business_impact.roi_analysis.year_3_roi_percentage,
                business_impact.roi_analysis.year_5_roi_percentage,
                business_impact.roi_analysis.npv_5_year
            ]
        }
        
        return pd.DataFrame(data)
    
    async def _prepare_cost_breakdown_dataframe(self, business_impact: BusinessImpactReport) -> 'pd.DataFrame':
        """Prepare cost breakdown DataFrame for Excel export."""
        
        breakdown = business_impact.current_state_costs['breakdown_percentages']
        
        data = {
            'Cost Category': [category.replace('_', ' ').title() for category in breakdown.keys()],
            'Percentage': list(breakdown.values()),
            'Annual Amount': [
                business_impact.current_state_costs['total_annual_incident_cost'] * (pct / 100)
                for pct in breakdown.values()
            ]
        }
        
        return pd.DataFrame(data)
    
    async def _prepare_benefits_dataframe(self, business_impact: BusinessImpactReport) -> 'pd.DataFrame':
        """Prepare benefits DataFrame for Excel export."""
        
        breakdown = business_impact.future_state_benefits['benefits_breakdown']
        
        data = {
            'Benefit Category': [category.replace('_', ' ').title() for category in breakdown.keys()],
            'Percentage': list(breakdown.values()),
            'Annual Amount': [
                business_impact.future_state_benefits['total_annual_benefits'] * (pct / 100)
                for pct in breakdown.values()
            ]
        }
        
        return pd.DataFrame(data)
    
    async def _prepare_industry_dataframe(self, business_impact: BusinessImpactReport) -> 'pd.DataFrame':
        """Prepare industry-specific DataFrame for Excel export."""
        
        industry_data = business_impact.industry_specific_analysis
        
        # Flatten industry data for DataFrame
        rows = []
        for section, content in industry_data.items():
            if isinstance(content, dict):
                for key, value in content.items():
                    rows.append({
                        'Section': section.replace('_', ' ').title(),
                        'Metric': key.replace('_', ' ').title(),
                        'Value': str(value)
                    })
            else:
                rows.append({
                    'Section': section.replace('_', ' ').title(),
                    'Metric': 'Value',
                    'Value': str(content)
                })
        
        return pd.DataFrame(rows)


# Utility functions for external integration
async def export_business_data(
    industry: IndustryType,
    company_size: CompanySize,
    format: ExportFormat,
    scope: ExportScope = ExportScope.SUMMARY
) -> ExportResult:
    """Export business data utility function."""
    
    export_service = BusinessDataExportService()
    export_request = ExportRequest(
        format=format,
        scope=scope,
        industry=industry,
        company_size=company_size
    )
    
    return await export_service.export_business_impact_data(export_request)


# Global instance for sharing state across utility functions
_global_export_service: Optional[BusinessDataExportService] = None


def _get_export_service() -> BusinessDataExportService:
    """Get or create the global export service instance."""
    global _global_export_service
    if _global_export_service is None:
        _global_export_service = BusinessDataExportService()
    return _global_export_service


async def start_incident_cost_tracking(
    incident_id: str,
    industry: IndustryType,
    company_size: CompanySize
) -> str:
    """Start real-time cost tracking for an incident."""

    export_service = _get_export_service()
    return await export_service.start_real_time_cost_analysis(
        incident_id, industry, company_size
    )


async def get_incident_cost_savings(incident_id: str) -> Optional[Dict[str, Any]]:
    """Get current cost savings for an incident."""

    export_service = _get_export_service()
    analysis = await export_service.get_real_time_cost_analysis(incident_id)
    
    if analysis:
        return {
            "incident_id": analysis.incident_id,
            "duration_minutes": analysis.duration_minutes,
            "cost_savings_realized": analysis.cost_savings_realized,
            "projected_final_savings": analysis.projected_final_savings,
            "mttr_improvement": analysis.mttr_improvement_percentage,
            "business_impact_prevented": analysis.business_impact_prevented
        }
    
    return None