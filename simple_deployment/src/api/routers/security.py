"""
Security API endpoints for guardrails, auditing, and compliance.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Any, Optional
from datetime import datetime

from src.services.guardrails import get_bedrock_guardrails, validate_and_sanitize_input
from src.services.security_audit import get_security_audit_framework, ComplianceFramework
from src.services.chaos_engineering import get_chaos_framework
from src.services.finops_controller import get_finops_controller
from src.utils.logging import get_logger


logger = get_logger("security_api")
router = APIRouter(prefix="/security", tags=["security"])


@router.get("/guardrails/status")
async def get_guardrails_status():
    """Get Bedrock Guardrails status and metrics."""
    try:
        guardrails = await get_bedrock_guardrails()
        metrics = guardrails.get_security_metrics()
        return {
            "status": "active",
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get guardrails status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/guardrails/test")
async def test_guardrails():
    """Test guardrail functionality with sample data."""
    try:
        guardrails = await get_bedrock_guardrails()
        test_results = await guardrails.test_guardrail_functionality()
        return {
            "test_results": test_results,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Guardrails test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate")
async def validate_content(content: Dict[str, Any]):
    """Validate and sanitize content using guardrails."""
    try:
        sanitized_content = await validate_and_sanitize_input(content)
        return {
            "original": content,
            "sanitized": sanitized_content,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Content validation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/audit/comprehensive")
async def run_comprehensive_audit(frameworks: Optional[List[str]] = None):
    """Run comprehensive security audit."""
    try:
        audit_framework = get_security_audit_framework()
        
        # Convert framework strings to enums
        framework_enums = []
        if frameworks:
            for framework in frameworks:
                try:
                    framework_enums.append(ComplianceFramework(framework.lower()))
                except ValueError:
                    logger.warning(f"Unknown compliance framework: {framework}")
        
        audit_result = await audit_framework.run_comprehensive_audit(framework_enums or None)
        
        return {
            "audit_id": audit_result.audit_id,
            "start_time": audit_result.start_time.isoformat(),
            "end_time": audit_result.end_time.isoformat() if audit_result.end_time else None,
            "overall_score": audit_result.overall_score,
            "risk_level": audit_result.risk_level,
            "vulnerabilities_count": len(audit_result.vulnerabilities),
            "compliance_results": audit_result.compliance_results,
            "recommendations": audit_result.recommendations,
            "vulnerabilities": [
                {
                    "id": v.id,
                    "title": v.title,
                    "severity": v.severity.value,
                    "category": v.category.value,
                    "affected_components": v.affected_components
                }
                for v in audit_result.vulnerabilities
            ]
        }
    except Exception as e:
        logger.error(f"Security audit failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit/metrics")
async def get_audit_metrics():
    """Get security audit metrics and statistics."""
    try:
        audit_framework = get_security_audit_framework()
        metrics = audit_framework.get_security_metrics()
        return {
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get audit metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chaos/experiment/{experiment_name}")
async def run_chaos_experiment(experiment_name: str):
    """Run a chaos engineering experiment."""
    try:
        chaos_framework = get_chaos_framework()
        metrics = await chaos_framework.run_experiment(experiment_name)
        
        return {
            "experiment_id": metrics.experiment_id,
            "start_time": metrics.start_time.isoformat(),
            "end_time": metrics.end_time.isoformat() if metrics.end_time else None,
            "mttr_seconds": metrics.mttr_seconds,
            "system_availability": metrics.system_availability,
            "error_rate": metrics.error_rate
        }
    except Exception as e:
        logger.error(f"Chaos experiment failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chaos/byzantine/{scenario_name}")
async def run_byzantine_simulation(scenario_name: str):
    """Run Byzantine attack simulation."""
    try:
        chaos_framework = get_chaos_framework()
        results = await chaos_framework.run_byzantine_attack_simulation(scenario_name)
        return results
    except Exception as e:
        logger.error(f"Byzantine simulation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chaos/validate-mttr")
async def validate_mttr_claims(target_mttr_seconds: int = 180):
    """Validate MTTR claims through systematic testing."""
    try:
        chaos_framework = get_chaos_framework()
        results = await chaos_framework.validate_mttr_claims(target_mttr_seconds)
        return results
    except Exception as e:
        logger.error(f"MTTR validation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chaos/metrics")
async def get_chaos_metrics():
    """Get chaos engineering metrics."""
    try:
        chaos_framework = get_chaos_framework()
        metrics = chaos_framework.get_chaos_metrics()
        return {
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get chaos metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/finops/status")
async def get_finops_status():
    """Get FinOps controller status and metrics."""
    try:
        finops = get_finops_controller()
        metrics = finops.get_finops_metrics()
        return {
            "status": "active",
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get FinOps status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/finops/model-routing")
async def get_model_routing(task_complexity: str, context: Dict[str, Any] = None):
    """Get adaptive model routing recommendation."""
    try:
        finops = get_finops_controller()
        selected_model = await finops.adaptive_model_routing(task_complexity, context or {})
        return {
            "task_complexity": task_complexity,
            "selected_model": selected_model,
            "context": context,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Model routing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/finops/sampling-config")
async def get_sampling_config(incident_risk_level: str, system_load: float):
    """Get dynamic detection sampling configuration."""
    try:
        finops = get_finops_controller()
        config = await finops.dynamic_detection_sampling(incident_risk_level, system_load)
        return config
    except Exception as e:
        logger.error(f"Sampling configuration failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/finops/cost-report")
async def generate_cost_report():
    """Generate comprehensive cost optimization report."""
    try:
        finops = get_finops_controller()
        report = await finops.generate_cost_optimization_report()
        return report
    except Exception as e:
        logger.error(f"Cost report generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/overview")
async def get_security_overview():
    """Get comprehensive security overview."""
    try:
        # Get metrics from all security services
        guardrails = await get_bedrock_guardrails()
        audit_framework = get_security_audit_framework()
        chaos_framework = get_chaos_framework()
        finops = get_finops_controller()
        
        overview = {
            "timestamp": datetime.utcnow().isoformat(),
            "guardrails": guardrails.get_security_metrics(),
            "audit": audit_framework.get_security_metrics(),
            "chaos_engineering": chaos_framework.get_chaos_metrics(),
            "finops": finops.get_finops_metrics(),
            "overall_status": "healthy"  # Would be calculated based on all metrics
        }
        
        return overview
    except Exception as e:
        logger.error(f"Failed to get security overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))