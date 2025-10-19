"""
Dashboard API endpoints for 3D visualization and real-time updates.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.responses import HTMLResponse
from typing import Dict, Any, List
import json
import uuid

from src.services.websocket_manager import get_websocket_manager, WebSocketManager
from src.services.byzantine_consensus import ByzantineFaultTolerantConsensus
from src.services.agent_swarm_coordinator import AgentSwarmCoordinator
from src.models.incident import Incident
from src.utils.logging import get_logger


logger = get_logger("dashboard_api")
router = APIRouter(prefix="/dashboard", tags=["dashboard"])


async def handle_demo_websocket_message(connection_id: str, message_data: Dict[str, Any]):
    """Handle demo-specific WebSocket messages."""
    from src.services.demo_scenario_manager import ScenarioType, ByzantineFaultType, get_demo_manager
    
    action = message_data.get("action")
    
    try:
        if action == "trigger_demo_incident":
            incident_type = message_data.get("incident_type", "database_failure")
            scenario_enum = ScenarioType(incident_type)
            demo_mgr = await get_demo_manager()
            await demo_mgr.trigger_demo_scenario(scenario_enum)
            
        elif action == "inject_byzantine_fault":
            target_agent = message_data.get("target_agent", "diagnosis")
            fault_type = message_data.get("fault_type", "conflicting_recommendations")
            fault_enum = ByzantineFaultType(fault_type)
            demo_mgr = await get_demo_manager()
            await demo_mgr.inject_byzantine_fault(fault_enum, target_agent)
            
        elif action == "reset_agents":
            demo_mgr = await get_demo_manager()
            await demo_mgr.reset_all_agents()
            
    except Exception as e:
        logger.error(f"Error handling demo WebSocket message from {connection_id}: {e}")


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    ws_manager: WebSocketManager = Depends(get_websocket_manager)
):
    """WebSocket endpoint for real-time dashboard updates."""
    connection_id = str(uuid.uuid4())
    
    if not await ws_manager.connect(websocket, connection_id):
        return
    
    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Handle client message
            await ws_manager.handle_client_message(connection_id, message_data)
            
            # Handle demo-specific messages
            await handle_demo_websocket_message(connection_id, message_data)
            
    except WebSocketDisconnect:
        await ws_manager.disconnect(connection_id)
    except Exception as e:
        logger.error(f"WebSocket error for {connection_id}: {e}")
        await ws_manager.disconnect(connection_id)


@router.get("/")
async def get_dashboard():
    """Serve the 3D dashboard HTML."""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Incident Commander - 3D Dashboard</title>
        <script src="https://unpkg.com/three@0.155.0/build/three.min.js"></script>
        <script src="https://unpkg.com/three@0.155.0/examples/js/controls/OrbitControls.js"></script>
        <style>
            body { margin: 0; padding: 0; overflow: hidden; background: #000; font-family: Arial, sans-serif; }
            #container { position: relative; width: 100vw; height: 100vh; }
            .ui-panel { position: absolute; background: rgba(0,0,0,0.8); color: white; padding: 15px; border-radius: 8px; }
            .status-panel { top: 20px; left: 20px; min-width: 250px; }
            .controls-panel { top: 20px; right: 20px; min-width: 200px; }
            .metrics-panel { bottom: 20px; left: 20px; min-width: 300px; }
            .agent-status { display: flex; align-items: center; margin: 5px 0; }
            .status-indicator { width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }
            .btn { background: #007acc; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; margin: 2px; }
            .btn:hover { background: #005a9e; }
            .btn.danger { background: #dc3545; }
            .btn.danger:hover { background: #c82333; }
        </style>
    </head>
    <body>
        <div id="container">
            <div id="threejs-container"></div>
            
            <div class="ui-panel status-panel">
                <h3>Agent Status</h3>
                <div id="agent-status-list"></div>
            </div>
            
            <div class="ui-panel controls-panel">
                <h3>Controls</h3>
                <button class="btn" onclick="triggerDemo()">Trigger Demo</button>
                <button class="btn" onclick="resetAgents()">Reset Agents</button>
                <button class="btn danger" onclick="injectByzantineFault()">Inject Byzantine Fault</button>
            </div>
            
            <div class="ui-panel metrics-panel">
                <h3>System Metrics</h3>
                <div id="metrics-display"></div>
            </div>
        </div>

        <script>
            // WebSocket connection
            let ws = null;
            let scene, camera, renderer, controls;
            let agentNodes = new Map();
            let agentStates = {};
            
            // Initialize WebSocket
            function initWebSocket() {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/dashboard/ws`;
                
                ws = new WebSocket(wsUrl);
                
                ws.onopen = function() {
                    console.log('Connected to dashboard WebSocket');
                };
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    handleWebSocketMessage(data);
                };
                
                ws.onclose = function() {
                    console.log('WebSocket disconnected, attempting reconnection...');
                    setTimeout(initWebSocket, 3000);
                };
                
                ws.onerror = function(error) {
                    console.error('WebSocket error:', error);
                };
            }
            
            // Handle WebSocket messages
            function handleWebSocketMessage(data) {
                if (data.type === 'message_batch') {
                    data.messages.forEach(msg => processMessage(msg));
                } else {
                    processMessage(data);
                }
            }
            
            function processMessage(message) {
                switch(message.type) {
                    case 'initial_state':
                        updateAgentStates(message.data.agent_states);
                        break;
                    case 'agent_state_update':
                        updateAgentState(message.data.agent_name, message.data.state);
                        break;
                    case 'incident_update':
                        updateIncidentFlow(message.data.incident);
                        break;
                    case 'consensus_update':
                        updateConsensusVisualization(message.data);
                        break;
                }
            }
            
            // Initialize Three.js scene
            function initThreeJS() {
                const container = document.getElementById('threejs-container');
                
                // Scene
                scene = new THREE.Scene();
                scene.background = new THREE.Color(0x0a0a0a);
                
                // Camera
                camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
                camera.position.set(0, 10, 20);
                
                // Renderer
                renderer = new THREE.WebGLRenderer({ antialias: true });
                renderer.setSize(window.innerWidth, window.innerHeight);
                renderer.shadowMap.enabled = true;
                renderer.shadowMap.type = THREE.PCFSoftShadowMap;
                container.appendChild(renderer.domElement);
                
                // Controls
                controls = new THREE.OrbitControls(camera, renderer.domElement);
                controls.enableDamping = true;
                controls.dampingFactor = 0.05;
                
                // Lighting
                const ambientLight = new THREE.AmbientLight(0x404040, 0.4);
                scene.add(ambientLight);
                
                const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
                directionalLight.position.set(10, 10, 5);
                directionalLight.castShadow = true;
                scene.add(directionalLight);
                
                // Grid
                const gridHelper = new THREE.GridHelper(50, 50, 0x444444, 0x222222);
                scene.add(gridHelper);
                
                // Initialize agent nodes
                initAgentNodes();
                
                // Start animation loop
                animate();
            }
            
            function initAgentNodes() {
                const agents = [
                    { name: 'detection', position: [-15, 2, 0], color: 0x00ff00 },
                    { name: 'diagnosis', position: [-7.5, 2, 0], color: 0x0088ff },
                    { name: 'prediction', position: [0, 2, 0], color: 0xff8800 },
                    { name: 'resolution', position: [7.5, 2, 0], color: 0xff0088 },
                    { name: 'communication', position: [15, 2, 0], color: 0x8800ff }
                ];
                
                agents.forEach(agent => {
                    // Agent sphere
                    const geometry = new THREE.SphereGeometry(1.5, 32, 32);
                    const material = new THREE.MeshPhongMaterial({ 
                        color: agent.color,
                        transparent: true,
                        opacity: 0.8
                    });
                    const mesh = new THREE.Mesh(geometry, material);
                    mesh.position.set(...agent.position);
                    mesh.castShadow = true;
                    mesh.receiveShadow = true;
                    
                    // Activity ring
                    const ringGeometry = new THREE.RingGeometry(2, 2.5, 32);
                    const ringMaterial = new THREE.MeshBasicMaterial({
                        color: agent.color,
                        transparent: true,
                        opacity: 0.3,
                        side: THREE.DoubleSide
                    });
                    const ring = new THREE.Mesh(ringGeometry, ringMaterial);
                    ring.position.copy(mesh.position);
                    ring.rotation.x = -Math.PI / 2;
                    
                    scene.add(mesh);
                    scene.add(ring);
                    
                    agentNodes.set(agent.name, {
                        mesh: mesh,
                        ring: ring,
                        originalColor: agent.color,
                        state: 'idle'
                    });
                });
            }
            
            function animate() {
                requestAnimationFrame(animate);
                controls.update();
                updateAnimations();
                renderer.render(scene, camera);
            }
            
            function updateAnimations() {
                const time = Date.now() * 0.001;
                
                agentNodes.forEach((node, name) => {
                    if (node.state === 'processing') {
                        const pulse = Math.sin(time * 4) * 0.2 + 0.8;
                        node.mesh.material.opacity = pulse;
                        node.ring.scale.setScalar(1 + Math.sin(time * 3) * 0.1);
                    } else {
                        node.mesh.material.opacity = 0.8;
                        node.ring.scale.setScalar(1);
                    }
                    
                    // Floating animation
                    const baseY = 2;
                    node.mesh.position.y = baseY + Math.sin(time + name.length) * 0.2;
                });
            }
            
            function updateAgentStates(states) {
                agentStates = states;
                updateStatusPanel();
                
                Object.entries(states).forEach(([agent, state]) => {
                    updateAgentVisual(agent, state);
                });
            }
            
            function updateAgentState(agentName, state) {
                agentStates[agentName] = state;
                updateStatusPanel();
                updateAgentVisual(agentName, state);
            }
            
            function updateAgentVisual(agentName, state) {
                const node = agentNodes.get(agentName);
                if (!node) return;
                
                const stateColors = {
                    idle: node.originalColor,
                    processing: 0xffff00,
                    completed: 0x00ff00,
                    failed: 0xff0000,
                    degraded: 0xff8800
                };
                
                const color = stateColors[state] || node.originalColor;
                node.mesh.material.color.setHex(color);
                node.ring.material.color.setHex(color);
                node.state = state;
            }
            
            function updateStatusPanel() {
                const statusList = document.getElementById('agent-status-list');
                statusList.innerHTML = '';
                
                Object.entries(agentStates).forEach(([agent, state]) => {
                    const div = document.createElement('div');
                    div.className = 'agent-status';
                    
                    const indicator = document.createElement('div');
                    indicator.className = 'status-indicator';
                    indicator.style.backgroundColor = getStateColor(state);
                    
                    const text = document.createElement('span');
                    text.textContent = `${agent}: ${state}`;
                    
                    div.appendChild(indicator);
                    div.appendChild(text);
                    statusList.appendChild(div);
                });
            }
            
            function getStateColor(state) {
                const colors = {
                    idle: '#666',
                    processing: '#ffff00',
                    completed: '#00ff00',
                    failed: '#ff0000',
                    degraded: '#ff8800'
                };
                return colors[state] || '#666';
            }
            
            function updateIncidentFlow(incident) {
                // TODO: Add incident flow visualization
                console.log('Incident update:', incident);
            }
            
            function updateConsensusVisualization(consensusData) {
                // TODO: Add consensus visualization
                console.log('Consensus update:', consensusData);
            }
            
            // Control functions
            function triggerDemo() {
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({ action: 'trigger_demo_incident' }));
                }
            }
            
            function resetAgents() {
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({ action: 'reset_agents' }));
                }
            }
            
            function injectByzantineFault() {
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({ action: 'inject_byzantine_fault' }));
                }
            }
            
            // Handle window resize
            window.addEventListener('resize', function() {
                camera.aspect = window.innerWidth / window.innerHeight;
                camera.updateProjectionMatrix();
                renderer.setSize(window.innerWidth, window.innerHeight);
            });
            
            // Initialize everything
            initThreeJS();
            initWebSocket();
        </script>
    </body>
    </html>
    """)


@router.get("/metrics")
async def get_dashboard_metrics(
    ws_manager: WebSocketManager = Depends(get_websocket_manager)
):
    """Get dashboard performance metrics."""
    return ws_manager.get_metrics()


@router.post("/trigger-demo")
async def trigger_demo_incident(
    scenario_type: str = "database_failure",
    demo_manager = Depends(lambda: asyncio.create_task(get_demo_manager()))
):
    """Trigger a demo incident scenario."""
    from src.services.demo_scenario_manager import ScenarioType, get_demo_manager
    
    try:
        # Convert string to enum
        scenario_enum = ScenarioType(scenario_type)
        demo_mgr = await get_demo_manager()
        
        scenario_id = await demo_mgr.trigger_demo_scenario(scenario_enum)
        
        return {
            "status": "demo_triggered",
            "scenario_id": scenario_id,
            "scenario_type": scenario_type,
            "message": f"Demo scenario '{scenario_type}' has been triggered"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid scenario type: {scenario_type}")
    except Exception as e:
        logger.error(f"Error triggering demo: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger demo scenario")


@router.post("/inject-byzantine-fault")
async def inject_byzantine_fault(
    fault_type: str = "conflicting_recommendations",
    target_agent: str = "diagnosis"
):
    """Inject a Byzantine fault for demonstration."""
    from src.services.demo_scenario_manager import ByzantineFaultType, get_demo_manager
    
    try:
        # Convert string to enum
        fault_enum = ByzantineFaultType(fault_type)
        demo_mgr = await get_demo_manager()
        
        fault_id = await demo_mgr.inject_byzantine_fault(fault_enum, target_agent)
        
        return {
            "status": "fault_injected",
            "fault_id": fault_id,
            "fault_type": fault_type,
            "target_agent": target_agent,
            "message": f"Byzantine fault '{fault_type}' injected into agent '{target_agent}'"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid fault type: {fault_type}")
    except Exception as e:
        logger.error(f"Error injecting Byzantine fault: {e}")
        raise HTTPException(status_code=500, detail="Failed to inject Byzantine fault")


@router.post("/reset-agents")
async def reset_agents():
    """Reset all agents to idle state."""
    from src.services.demo_scenario_manager import get_demo_manager
    
    try:
        demo_mgr = await get_demo_manager()
        await demo_mgr.reset_all_agents()
        
        return {
            "status": "agents_reset",
            "message": "All agents have been reset to idle state"
        }
    except Exception as e:
        logger.error(f"Error resetting agents: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset agents")


@router.get("/demo-metrics")
async def get_demo_metrics():
    """Get demo performance metrics."""
    from src.services.demo_scenario_manager import get_demo_manager
    
    try:
        demo_mgr = await get_demo_manager()
        metrics = demo_mgr.get_demo_metrics()
        
        return metrics
    except Exception as e:
        logger.error(f"Error getting demo metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get demo metrics")