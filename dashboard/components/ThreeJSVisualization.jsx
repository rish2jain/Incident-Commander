import React, { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls";

const AgentVisualization = () => {
  const mountRef = useRef(null);
  const sceneRef = useRef(null);
  const rendererRef = useRef(null);
  const agentNodesRef = useRef(new Map());
  const [wsConnection, setWsConnection] = useState(null);
  const [agentStates, setAgentStates] = useState({});

  useEffect(() => {
    // Initialize Three.js scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0a0a0a);
    sceneRef.current = scene;

    // Camera setup
    const camera = new THREE.PerspectiveCamera(
      75,
      window.innerWidth / window.innerHeight,
      0.1,
      1000
    );
    camera.position.set(0, 10, 20);

    // Renderer setup
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    rendererRef.current = renderer;

    // Controls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;

    // Lighting
    const ambientLight = new THREE.AmbientLight(0x404040, 0.4);
    scene.add(ambientLight);

    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(10, 10, 5);
    directionalLight.castShadow = true;
    scene.add(directionalLight);

    // Add grid
    const gridHelper = new THREE.GridHelper(50, 50, 0x444444, 0x222222);
    scene.add(gridHelper);

    // Mount renderer
    if (mountRef.current) {
      mountRef.current.appendChild(renderer.domElement);
    }

    // Initialize agent nodes
    initializeAgentNodes(scene);

    // WebSocket connection
    initializeWebSocket();

    // Animation loop
    const animate = () => {
      requestAnimationFrame(animate);
      controls.update();
      updateAgentAnimations();
      renderer.render(scene, camera);
    };
    animate();

    // Cleanup
    return () => {
      if (mountRef.current && renderer.domElement) {
        mountRef.current.removeChild(renderer.domElement);
      }
      renderer.dispose();
      if (wsConnection) {
        wsConnection.close();
      }
    };
  }, []);

  const initializeAgentNodes = (scene) => {
    const agentTypes = [
      { name: "detection", position: [-15, 2, 0], color: 0x00ff00 },
      { name: "diagnosis", position: [-7.5, 2, 0], color: 0x0088ff },
      { name: "prediction", position: [0, 2, 0], color: 0xff8800 },
      { name: "resolution", position: [7.5, 2, 0], color: 0xff0088 },
      { name: "communication", position: [15, 2, 0], color: 0x8800ff },
    ];

    agentTypes.forEach((agent) => {
      // Agent node geometry
      const geometry = new THREE.SphereGeometry(1.5, 32, 32);
      const material = new THREE.MeshPhongMaterial({
        color: agent.color,
        transparent: true,
        opacity: 0.8,
      });

      const mesh = new THREE.Mesh(geometry, material);
      mesh.position.set(...agent.position);
      mesh.castShadow = true;
      mesh.receiveShadow = true;

      // Add pulsing ring for activity
      const ringGeometry = new THREE.RingGeometry(2, 2.5, 32);
      const ringMaterial = new THREE.MeshBasicMaterial({
        color: agent.color,
        transparent: true,
        opacity: 0.3,
        side: THREE.DoubleSide,
      });
      const ring = new THREE.Mesh(ringGeometry, ringMaterial);
      ring.position.copy(mesh.position);
      ring.rotation.x = -Math.PI / 2;

      // Agent label
      const canvas = document.createElement("canvas");
      const context = canvas.getContext("2d");
      canvas.width = 256;
      canvas.height = 64;
      context.fillStyle = "#ffffff";
      context.font = "24px Arial";
      context.textAlign = "center";
      context.fillText(agent.name.toUpperCase(), 128, 40);

      const texture = new THREE.CanvasTexture(canvas);
      const labelMaterial = new THREE.SpriteMaterial({ map: texture });
      const label = new THREE.Sprite(labelMaterial);
      label.position.set(
        agent.position[0],
        agent.position[1] + 3,
        agent.position[2]
      );
      label.scale.set(4, 1, 1);

      scene.add(mesh);
      scene.add(ring);
      scene.add(label);

      agentNodesRef.current.set(agent.name, {
        mesh,
        ring,
        label,
        originalColor: agent.color,
        state: "idle",
      });
    });
  };

  const initializeWebSocket = () => {
    const ws = new WebSocket("ws://localhost:8000/ws/dashboard");

    ws.onopen = () => {
      console.log("WebSocket connected to dashboard");
      setWsConnection(ws);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleAgentUpdate(data);
    };

    ws.onclose = () => {
      console.log("WebSocket disconnected");
      // Attempt reconnection after 3 seconds
      setTimeout(initializeWebSocket, 3000);
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
    };
  };

  const handleAgentUpdate = (data) => {
    if (data.type === "agent_state_update") {
      setAgentStates((prev) => ({
        ...prev,
        [data.agent_name]: data.state,
      }));

      updateAgentVisual(data.agent_name, data.state);
    } else if (data.type === "incident_update") {
      updateIncidentFlow(data.incident);
    }
  };

  const updateAgentVisual = (agentName, state) => {
    const agentNode = agentNodesRef.current.get(agentName);
    if (!agentNode) return;

    const stateColors = {
      idle: agentNode.originalColor,
      processing: 0xffff00,
      completed: 0x00ff00,
      failed: 0xff0000,
      degraded: 0xff8800,
    };

    const targetColor = stateColors[state] || agentNode.originalColor;
    agentNode.mesh.material.color.setHex(targetColor);
    agentNode.ring.material.color.setHex(targetColor);

    // Update ring animation based on state
    if (state === "processing") {
      agentNode.ring.material.opacity = 0.6;
    } else {
      agentNode.ring.material.opacity = 0.3;
    }

    agentNode.state = state;
  };

  const updateAgentAnimations = () => {
    const time = Date.now() * 0.001;

    agentNodesRef.current.forEach((agentNode, agentName) => {
      // Pulsing animation for active agents
      if (agentNode.state === "processing") {
        const pulse = Math.sin(time * 4) * 0.2 + 0.8;
        agentNode.mesh.material.opacity = pulse;
        agentNode.ring.scale.setScalar(1 + Math.sin(time * 3) * 0.1);
      } else {
        agentNode.mesh.material.opacity = 0.8;
        agentNode.ring.scale.setScalar(1);
      }

      // Gentle floating animation
      agentNode.mesh.position.y =
        agentNode.mesh.position.y + Math.sin(time + agentName.length) * 0.01;
    });
  };

  const updateIncidentFlow = (incident) => {
    // TODO: Add incident flow visualization
    // - Create flowing particles between agents
    // - Show incident severity with visual effects
    // - Display incident timeline
  };

  return (
    <div className="relative w-full h-screen">
      <div ref={mountRef} className="w-full h-full" />

      {/* Agent Status Panel */}
      <div className="absolute top-4 left-4 bg-black bg-opacity-70 text-white p-4 rounded-lg">
        <h3 className="text-lg font-bold mb-2">Agent Status</h3>
        {Object.entries(agentStates).map(([agent, state]) => (
          <div key={agent} className="flex items-center mb-1">
            <div
              className={`w-3 h-3 rounded-full mr-2 ${
                state === "processing"
                  ? "bg-yellow-400"
                  : state === "completed"
                  ? "bg-green-400"
                  : state === "failed"
                  ? "bg-red-400"
                  : "bg-gray-400"
              }`}
            />
            <span className="capitalize">
              {agent}: {state}
            </span>
          </div>
        ))}
      </div>

      {/* Controls Panel */}
      <div className="absolute top-4 right-4 bg-black bg-opacity-70 text-white p-4 rounded-lg">
        <h3 className="text-lg font-bold mb-2">Controls</h3>
        <button
          className="bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded mr-2"
          onClick={() =>
            wsConnection?.send(
              JSON.stringify({ action: "trigger_demo_incident" })
            )
          }
        >
          Trigger Demo
        </button>
        <button
          className="bg-red-600 hover:bg-red-700 px-3 py-1 rounded"
          onClick={() =>
            wsConnection?.send(JSON.stringify({ action: "reset_agents" }))
          }
        >
          Reset
        </button>
      </div>
    </div>
  );
};

export default AgentVisualization;
