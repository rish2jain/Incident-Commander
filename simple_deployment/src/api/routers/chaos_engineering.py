"""
Chaos Engineering API Router

FastAPI routes for chaos test execution, monitoring, and resilience reporting.
Implements comprehensive chaos engineering capabilities for system resilience validation.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field

from src.utils.logging import get_logger
from src.services.chaos_engineering_framework import (
    ChaosEngineeringFramework,
    ChaosExperiment,
    ChaosExperimentType,
    FailureMode,
    ChaosExperimentResult
)
from src.services.agent_swarm_coordinator import AgentSwarmCoordinator
from src.api.dependencies import get_services

logger = get_logger(__name__)

router = APIRouter(
    prefix="/chaos",
    tags=["chaos-engineering"],
    responses={404: {"description": "Not found"}}
)

# Global chaos framework instance
_chaos_framework: Optional[ChaosEngineeringFramework] = None

def get_chaos_framework() -> ChaosEngineeringFramework:
    """Get or create chaos engineering framework instance."""
    global _chaos_framework
    if _chaos_framework is None:
        _chaos_framework = ChaosEngineeringFramework()
    return _chaos_framework


# Request/Response Models

class ChaosExperimentRequest(BaseModel):
    """Request model for creating chaos experiments."""
    name: str = Field(..., description="Unique name for the experiment")
    experiment_type: str = Field(..., description="Type of chaos experiment")
    failure_mode: str = Field(..., description="Failure mode to simulate")
    target_components: List[str] = Field(..., description="Components to target")
    duration_seconds: int = Field(300, ge=60, le=1800, description="Experiment duration (60-1800 seconds)")
    intensity: float = Field(0.5, ge=0.0, le=1.0, description="Failure intensity (0.0-1.0)")
    description: str = Field("", description="Experiment description")
    expected_behavior: str = Field("", description="Expected system behavior")
    success_criteria: Dict[str, float] = Field(default_factory=dict, description="Success criteria thresholds")
    blast_radius: str = Field("single_agent", description="Blast radius: single_agent, agent_type, system_wide")


class ChaosExperimentResponse(BaseModel):
    """Response model for chaos experiment results."""
    experiment_id: str
    name: str
    status: str
    start_time: datetime
    end_time: Optional[datetime]
    duration_seconds: Optional[float]
    success: Optional[bool]
    recovery_metrics: Dict[str, float]
    system_behavior: Dict[str, Any]
    lessons_learned: List[str]
    recommendations: List[str]


class ChaosTestSuiteRequest(BaseModel):
    """Request model for running chaos test suite."""
    experiment_filter: Optional[List[str]] = Field(None, description="Filter experiments by name")
    blast_radius_filter: Optional[str] = Field(None, description="Filter by blast radius")
    max_concurrent: int = Field(1, ge=1, le=3, description="Maximum concurrent experiments")


class ResilienceReportResponse(BaseModel):
    """Response model for resilience reports."""
    timestamp: datetime
    total_experiments: int
    successful_experiments: int
    failed_experiments: int
    resilience_summary: Dict[str, Any]
    lessons_learned: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]


# API Endpoints

@router.get("/experiments", response_model=List[Dict[str, Any]])
async def list_chaos_experiments():
    """List all available chaos experiments."""
    try:
        framework = get_chaos_framework()
        
        experiments = []
        for exp in framework.experiments:
            experiments.append({
                "name": exp.name,
                "type": exp.experiment_type.value,
                "failure_mode": exp.failure_mode.value,
                "target_components": exp.target_components,
                "duration_seconds": exp.duration_seconds,
                "intensity": exp.intensity,
                "description": exp.description,
                "blast_radius": exp.blast_radius,
                "success_criteria": exp.success_criteria
            })
        
        return experiments
        
    except Exception as e:
        logger.error(f"Failed to list chaos experiments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/experiments", response_model=Dict[str, str])
async def create_chaos_experiment(request: ChaosExperimentRequest):
    """Create a new chaos experiment."""
    try:
        framework = get_chaos_framework()
        
        # Validate experiment type and failure mode
        try:
            experiment_type = ChaosExperimentType(request.experiment_type)
            failure_mode = FailureMode(request.failure_mode)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid experiment type or failure mode: {e}")
        
        # Create experiment
        experiment = ChaosExperiment(
            name=request.name,
            experiment_type=experiment_type,
            failure_mode=failure_mode,
            target_components=request.target_components,
            duration_seconds=request.duration_seconds,
            intensity=request.intensity,
            description=request.description,
            expected_behavior=request.expected_behavior,
            success_criteria=request.success_criteria,
            blast_radius=request.blast_radius
        )
        
        # Add to framework
        framework.experiments.append(experiment)
        
        logger.info(f"Created chaos experiment: {request.name}")
        
        return {
            "experiment_id": request.name,
            "status": "created",
            "message": f"Chaos experiment '{request.name}' created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create chaos experiment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/experiments/{experiment_name}/execute", response_model=ChaosExperimentResponse)
async def execute_chaos_experiment(
    experiment_name: str,
    background_tasks: BackgroundTasks,
    services = Depends(get_services)
):
    """Execute a specific chaos experiment."""
    try:
        framework = get_chaos_framework()
        
        # Find experiment
        experiment = None
        for exp in framework.experiments:
            if exp.name == experiment_name:
                experiment = exp
                break
        
        if not experiment:
            raise HTTPException(status_code=404, detail=f"Experiment '{experiment_name}' not found")
        
        # Check if experiment is already running
        if experiment_name in framework.active_injections:
            raise HTTPException(status_code=409, detail=f"Experiment '{experiment_name}' is already running")
        
        # Execute experiment
        coordinator = services.coordinator
        result = await framework.run_chaos_experiment(experiment, coordinator)
        
        logger.info(f"Executed chaos experiment: {experiment_name}")
        
        return ChaosExperimentResponse(
            experiment_id=experiment_name,
            name=result.experiment.name,
            status="completed",
            start_time=result.start_time,
            end_time=result.end_time,
            duration_seconds=(result.end_time - result.start_time).total_seconds(),
            success=result.success,
            recovery_metrics=result.recovery_metrics,
            system_behavior=result.system_behavior,
            lessons_learned=result.lessons_learned,
            recommendations=result.recommendations
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute chaos experiment {experiment_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/experiments/{experiment_name}/status")
async def get_experiment_status(experiment_name: str):
    """Get status of a running chaos experiment."""
    try:
        framework = get_chaos_framework()
        
        # Check if experiment is active
        if experiment_name in framework.active_injections:
            injection = framework.active_injections[experiment_name]
            
            return {
                "experiment_name": experiment_name,
                "status": "running",
                "start_time": injection.start_time.isoformat(),
                "duration_seconds": (datetime.utcnow() - injection.start_time).total_seconds(),
                "affected_components": injection.affected_components,
                "injection_state": injection.injection_state
            }
        
        # Check if experiment exists in results
        for result in framework.experiment_results:
            if result.experiment.name == experiment_name:
                return {
                    "experiment_name": experiment_name,
                    "status": "completed",
                    "start_time": result.start_time.isoformat(),
                    "end_time": result.end_time.isoformat(),
                    "duration_seconds": (result.end_time - result.start_time).total_seconds(),
                    "success": result.success,
                    "recovery_metrics": result.recovery_metrics
                }
        
        raise HTTPException(status_code=404, detail=f"Experiment '{experiment_name}' not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get experiment status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/experiments/{experiment_name}/stop")
async def stop_chaos_experiment(experiment_name: str):
    """Stop a running chaos experiment."""
    try:
        framework = get_chaos_framework()
        
        if experiment_name not in framework.active_injections:
            raise HTTPException(status_code=404, detail=f"No active experiment '{experiment_name}' found")
        
        injection = framework.active_injections[experiment_name]
        
        # Trigger recovery
        await framework._recover_from_failure(injection.experiment, injection)
        
        # Remove from active injections
        del framework.active_injections[experiment_name]
        
        logger.info(f"Stopped chaos experiment: {experiment_name}")
        
        return {
            "experiment_name": experiment_name,
            "status": "stopped",
            "message": f"Chaos experiment '{experiment_name}' stopped and recovered"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stop chaos experiment {experiment_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suite/execute", response_model=Dict[str, Any])
async def execute_chaos_suite(
    request: ChaosTestSuiteRequest,
    background_tasks: BackgroundTasks,
    services = Depends(get_services)
):
    """Execute the complete chaos engineering test suite."""
    try:
        framework = get_chaos_framework()
        coordinator = services.coordinator
        
        # Filter experiments if requested
        experiments_to_run = framework.experiments
        
        if request.experiment_filter:
            experiments_to_run = [
                exp for exp in experiments_to_run 
                if exp.name in request.experiment_filter
            ]
        
        if request.blast_radius_filter:
            experiments_to_run = [
                exp for exp in experiments_to_run 
                if exp.blast_radius == request.blast_radius_filter
            ]
        
        # Execute suite in background
        async def run_suite():
            try:
                results = []
                for experiment in experiments_to_run:
                    if framework.emergency_stop_active:
                        break
                    
                    result = await framework.run_chaos_experiment(experiment, coordinator)
                    results.append(result)
                    
                    # Wait between experiments
                    await asyncio.sleep(60)
                
                return results
            except Exception as e:
                logger.error(f"Chaos suite execution failed: {e}")
                return []
        
        # Start suite execution
        background_tasks.add_task(run_suite)
        
        logger.info(f"Started chaos suite execution with {len(experiments_to_run)} experiments")
        
        return {
            "suite_id": f"suite_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "status": "started",
            "total_experiments": len(experiments_to_run),
            "estimated_duration_minutes": len(experiments_to_run) * 6,  # ~6 minutes per experiment
            "experiments": [exp.name for exp in experiments_to_run]
        }
        
    except Exception as e:
        logger.error(f"Failed to execute chaos suite: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/results", response_model=List[ChaosExperimentResponse])
async def get_experiment_results(
    limit: int = 10,
    experiment_type: Optional[str] = None,
    success_only: bool = False
):
    """Get chaos experiment results with optional filtering."""
    try:
        framework = get_chaos_framework()
        
        results = framework.experiment_results
        
        # Apply filters
        if experiment_type:
            results = [r for r in results if r.experiment.experiment_type.value == experiment_type]
        
        if success_only:
            results = [r for r in results if r.success]
        
        # Sort by start time (most recent first)
        results = sorted(results, key=lambda r: r.start_time, reverse=True)
        
        # Limit results
        results = results[:limit]
        
        # Convert to response model
        response_results = []
        for result in results:
            response_results.append(ChaosExperimentResponse(
                experiment_id=result.experiment.name,
                name=result.experiment.name,
                status="completed",
                start_time=result.start_time,
                end_time=result.end_time,
                duration_seconds=(result.end_time - result.start_time).total_seconds(),
                success=result.success,
                recovery_metrics=result.recovery_metrics,
                system_behavior=result.system_behavior,
                lessons_learned=result.lessons_learned,
                recommendations=result.recommendations
            ))
        
        return response_results
        
    except Exception as e:
        logger.error(f"Failed to get experiment results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/resilience-report", response_model=ResilienceReportResponse)
async def generate_resilience_report():
    """Generate comprehensive resilience report from all experiment results."""
    try:
        framework = get_chaos_framework()
        
        if not framework.experiment_results:
            raise HTTPException(status_code=404, detail="No experiment results available")
        
        report = framework.generate_resilience_report(framework.experiment_results)
        
        return ResilienceReportResponse(
            timestamp=datetime.fromisoformat(report["timestamp"]),
            total_experiments=report["total_experiments"],
            successful_experiments=report["successful_experiments"],
            failed_experiments=report["failed_experiments"],
            resilience_summary=report["resilience_summary"],
            lessons_learned=report["lessons_learned"],
            recommendations=report["recommendations"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate resilience report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/active-experiments")
async def get_active_experiments():
    """Get all currently active chaos experiments."""
    try:
        framework = get_chaos_framework()
        
        active_experiments = []
        for name, injection in framework.active_injections.items():
            active_experiments.append({
                "experiment_name": name,
                "start_time": injection.start_time.isoformat(),
                "duration_seconds": (datetime.utcnow() - injection.start_time).total_seconds(),
                "affected_components": injection.affected_components,
                "experiment_type": injection.experiment.experiment_type.value,
                "failure_mode": injection.experiment.failure_mode.value,
                "intensity": injection.experiment.intensity
            })
        
        return {
            "active_experiments": active_experiments,
            "total_active": len(active_experiments),
            "emergency_stop_active": framework.emergency_stop_active
        }
        
    except Exception as e:
        logger.error(f"Failed to get active experiments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/emergency-stop")
async def trigger_emergency_stop():
    """Trigger emergency stop for all active chaos experiments."""
    try:
        framework = get_chaos_framework()
        
        active_count = len(framework.active_injections)
        
        # Trigger emergency stop
        if active_count > 0:
            # Use a dummy experiment for emergency stop
            dummy_experiment = framework.experiments[0] if framework.experiments else None
            if dummy_experiment:
                await framework._trigger_emergency_stop(dummy_experiment)
        
        logger.warning("Emergency stop triggered for chaos engineering")
        
        return {
            "status": "emergency_stop_activated",
            "stopped_experiments": active_count,
            "message": "All active chaos experiments have been stopped and recovered"
        }
        
    except Exception as e:
        logger.error(f"Failed to trigger emergency stop: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_chaos_metrics():
    """Get chaos engineering metrics and statistics."""
    try:
        framework = get_chaos_framework()
        
        # Calculate metrics from results
        total_experiments = len(framework.experiment_results)
        successful_experiments = sum(1 for r in framework.experiment_results if r.success)
        
        # Calculate average recovery times
        recovery_times = []
        for result in framework.experiment_results:
            if "max_recovery_time" in result.recovery_metrics:
                recovery_times.append(result.recovery_metrics["max_recovery_time"])
        
        avg_recovery_time = sum(recovery_times) / len(recovery_times) if recovery_times else 0
        
        # Calculate experiment type distribution
        type_distribution = {}
        for result in framework.experiment_results:
            exp_type = result.experiment.experiment_type.value
            type_distribution[exp_type] = type_distribution.get(exp_type, 0) + 1
        
        return {
            "total_experiments_run": total_experiments,
            "success_rate": successful_experiments / total_experiments if total_experiments > 0 else 0,
            "average_recovery_time_seconds": avg_recovery_time,
            "active_experiments": len(framework.active_injections),
            "experiment_type_distribution": type_distribution,
            "emergency_stops_triggered": 1 if framework.emergency_stop_active else 0,
            "available_experiment_types": [t.value for t in ChaosExperimentType],
            "available_failure_modes": [f.value for f in FailureMode]
        }
        
    except Exception as e:
        logger.error(f"Failed to get chaos metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def get_chaos_framework_health():
    """Get chaos engineering framework health status."""
    try:
        framework = get_chaos_framework()
        
        return {
            "framework_status": "healthy" if not framework.emergency_stop_active else "emergency_stop",
            "total_experiments_available": len(framework.experiments),
            "active_experiments": len(framework.active_injections),
            "max_concurrent_experiments": framework.max_concurrent_experiments,
            "safety_thresholds": framework.safety_thresholds,
            "experiment_results_count": len(framework.experiment_results),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get chaos framework health: {e}")
        raise HTTPException(status_code=500, detail=str(e))