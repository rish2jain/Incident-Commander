import React, { useEffect, useRef, useState, useCallback } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls";

const EnhancedAgentVisualization = () => {
  const mountRef = useRef(null);
  const sceneRef = useRef(null);
  const rendererRef = useRef(null);
  const agentNodesRef = useRef(new Map());
  const particleSystemsRef = useRef(new Map());
  const connectionLinesRef = useRef(new Map());
  const consensusTreeRef = useRef(null);

  const [wsConnection, setWsConnection] = useState(null);
  const [agentStates, setAgentStates] = useState({});
  const [currentIncident, setCurrentIncident] = useState(null);
  const [consensusData, setConsensusData] = useState(null);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [demoMode, setDemoMode] = useState("idle");

  useEffect(() => {
    initializeScene();
    initializeWebSocket();

    return () => {
      cleanup();
    };
  }, []);

  const initializeScene = () => {
    // Scene setup
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0a0a0a);
    scene.fog = new THREE.Fog(0x0a0a0a, 50, 200);
    sceneRef.current = scene;

    // Camera with better positioning
    const camera = new THREE.PerspectiveCamera(
      75,
      window.innerWidth / window.innerHeight,
      0.1,
      1000
    );
    camera.position.set(0, 15, 25);

    // Enhanced renderer
    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: true,
      powerPreference: "high-performance",
    });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.outputEncoding = THREE.sRGBEncoding;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.2;
    rendererRef.current = renderer;

    // Enhanced controls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.minDistance = 10;
    controls.maxDistance = 100;
    controls.maxPolarAngle = Math.PI / 2;

    // Advanced lighting setup
    const ambientLight = new THREE.AmbientLight(0x404040, 0.3);
    scene.add(ambientLight);

    const directionalLight = new THREE.DirectionalLight(0xffffff, 1.0);
    directionalLight.position.set(20, 20, 10);
    directionalLight.castShadow = true;
    directionalLight.shadow.mapSize.width = 2048;
    directionalLight.shadow.mapSize.height = 2048;
    directionalLight.shadow.camera.near = 0.5;
    directionalLight.shadow.camera.far = 100;
    scene.add(directionalLight);

    // Rim lighting for dramatic effect
    const rimLight = new THREE.DirectionalLight(0x0088ff, 0.5);
    rimLight.position.set(-10, 5, -10);
    scene.add(rimLight);

    // Enhanced grid with glow effect
    const gridHelper = new THREE.GridHelper(100, 100, 0x444444, 0x222222);
    gridHelper.material.opacity = 0.3;
    gridHelper.material.transparent = true;
    scene.add(gridHelper);

    // Add environment elements
    createEnvironmentElements(scene);

    // Initialize agent nodes with enhanced visuals
    initializeEnhancedAgentNodes(scene);

    // Initialize particle systems
    initializeParticleSystems(scene);

    // Initialize consensus visualization
    initializeConsensusVisualization(scene);

    // Mount renderer
    if (mountRef.current) {
      mountRef.current.appendChild(renderer.domElement);
    }

    // Start animation loop
    const animate = () => {
      requestAnimationFrame(animate);
      controls.update();
      updateParticleAnimations();
      updateAgentAnimations();
      updateConsensusVisualization();
      renderer.render(scene, camera);
    };
    animate();
  };

  const createEnvironmentElements = (scene) => {
    // Holographic data streams in background
    const streamGeometry = new THREE.CylinderGeometry(0.1, 0.1, 50, 8);
    const streamMaterial = new THREE.MeshBasicMaterial({
      color: 0x00ffff,
      transparent: true,
      opacity: 0.1,
    });

    for (let i = 0; i < 20; i++) {
      const stream = new THREE.Mesh(streamGeometry, streamMaterial);
      stream.position.set(
        (Math.random() - 0.5) * 80,
        25,
        (Math.random() - 0.5) * 80
      );
      stream.rotation.z = Math.random() * Math.PI;
      scene.add(stream);
    }

    // Central command platform
    const platformGeometry = new THREE.CylinderGeometry(25, 25, 0.5, 32);
    const platformMaterial = new THREE.MeshPhongMaterial({
      color: 0x333333,
      transparent: true,
      opacity: 0.8,
    });
    const platform = new THREE.Mesh(platformGeometry, platformMaterial);
    platform.position.y = -0.25;
    platform.receiveShadow = true;
    scene.add(platform);
  };

  const initializeEnhancedAgentNodes = (scene) => {
    const agentConfigs = [
      {
        name: "detection",
        position: [-20, 3, 0],
        color: 0x00ff00,
        role: "Detection Agent",
        description: "Monitors system metrics and detects anomalies",
      },
      {
        name: "diagnosis",
        position: [-10, 3, 0],
        color: 0x0088ff,
        role: "Diagnosis Agent",
        description: "Analyzes incidents and determines root causes",
      },
      {
        name: "prediction",
        position: [0, 3, 0],
        color: 0xff8800,
        role: "Prediction Agent",
        description: "Forecasts incident impact and progression",
      },
      {
        name: "resolution",
        position: [10, 3, 0],
        color: 0xff0088,
        role: "Resolution Agent",
        description: "Executes remediation actions and fixes",
      },
      {
        name: "communication",
        position: [20, 3, 0],
        color: 0x8800ff,
        role: "Communication Agent",
        description: "Manages notifications and stakeholder updates",
      },
    ];

    agentConfigs.forEach((agent) => {
      // Main agent sphere with enhanced materials
      const geometry = new THREE.SphereGeometry(2, 32, 32);
      const material = new THREE.MeshPhongMaterial({
        color: agent.color,
        transparent: true,
        opacity: 0.9,
        shininess: 100,
        specular: 0x444444,
      });

      const mesh = new THREE.Mesh(geometry, material);
      mesh.position.set(...agent.position);
      mesh.castShadow = true;
      mesh.receiveShadow = true;
      mesh.userData = { agentName: agent.name, config: agent };

      // Holographic ring with animated rotation
      const ringGeometry = new THREE.RingGeometry(3, 3.5, 32);
      const ringMaterial = new THREE.MeshBasicMaterial({
        color: agent.color,
        transparent: true,
        opacity: 0.4,
        side: THREE.DoubleSide,
      });
      const ring = new THREE.Mesh(ringGeometry, ringMaterial);
      ring.position.copy(mesh.position);
      ring.rotation.x = -Math.PI / 2;

      // Status indicator above agent
      const statusGeometry = new THREE.ConeGeometry(0.5, 2, 8);
      const statusMaterial = new THREE.MeshBasicMaterial({
        color: 0x666666,
        transparent: true,
        opacity: 0.8,
      });
      const statusIndicator = new THREE.Mesh(statusGeometry, statusMaterial);
      statusIndicator.position.set(
        agent.position[0],
        agent.position[1] + 4,
        agent.position[2]
      );

      // Enhanced label with better typography
      const canvas = document.createElement("canvas");
      const context = canvas.getContext("2d");
      canvas.width = 512;
      canvas.height = 128;

      // Gradient background
      const gradient = context.createLinearGradient(0, 0, 512, 128);
      gradient.addColorStop(0, "rgba(0,0,0,0.8)");
      gradient.addColorStop(1, "rgba(0,0,0,0.4)");
      context.fillStyle = gradient;
      context.fillRect(0, 0, 512, 128);

      // Text with glow effect
      context.shadowColor = `#${agent.color.toString(16).padStart(6, "0")}`;
      context.shadowBlur = 10;
      context.fillStyle = "#ffffff";
      context.font = "bold 32px Arial";
      context.textAlign = "center";
      context.fillText(agent.role, 256, 50);
      context.font = "18px Arial";
      context.fillText(agent.name.toUpperCase(), 256, 80);

      const texture = new THREE.CanvasTexture(canvas);
      const labelMaterial = new THREE.SpriteMaterial({
        map: texture,
        transparent: true,
        alphaTest: 0.1,
      });
      const label = new THREE.Sprite(labelMaterial);
      label.position.set(
        agent.position[0],
        agent.position[1] + 6,
        agent.position[2]
      );
      label.scale.set(8, 2, 1);

      // Add click interaction
      mesh.callback = () => setSelectedAgent(agent);

      scene.add(mesh);
      scene.add(ring);
      scene.add(statusIndicator);
      scene.add(label);

      agentNodesRef.current.set(agent.name, {
        mesh,
        ring,
        statusIndicator,
        label,
        originalColor: agent.color,
        state: "idle",
        config: agent,
      });
    });
  };

  const initializeParticleSystems = (scene) => {
    // Create particle system for incident flow visualization
    const particleCount = 1000;
    const positions = new Float32Array(particleCount * 3);
    const colors = new Float32Array(particleCount * 3);
    const sizes = new Float32Array(particleCount);

    for (let i = 0; i < particleCount; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 100;
      positions[i * 3 + 1] = Math.random() * 50;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 100;

      colors[i * 3] = Math.random();
      colors[i * 3 + 1] = Math.random();
      colors[i * 3 + 2] = Math.random();

      sizes[i] = Math.random() * 2 + 1;
    }

    const particleGeometry = new THREE.BufferGeometry();
    particleGeometry.setAttribute(
      "position",
      new THREE.BufferAttribute(positions, 3)
    );
    particleGeometry.setAttribute(
      "color",
      new THREE.BufferAttribute(colors, 3)
    );
    particleGeometry.setAttribute("size", new THREE.BufferAttribute(sizes, 1));

    const particleMaterial = new THREE.ShaderMaterial({
      uniforms: {
        time: { value: 0 },
        pixelRatio: { value: Math.min(window.devicePixelRatio, 2) },
      },
      vertexShader: `
        attribute float size;
        varying vec3 vColor;
        uniform float time;
        
        void main() {
          vColor = color;
          vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
          gl_PointSize = size * (300.0 / -mvPosition.z);
          gl_Position = projectionMatrix * mvPosition;
        }
      `,
      fragmentShader: `
        varying vec3 vColor;
        
        void main() {
          float distanceToCenter = distance(gl_PointCoord, vec2(0.5));
          float alpha = 1.0 - smoothstep(0.0, 0.5, distanceToCenter);
          gl_FragColor = vec4(vColor, alpha * 0.8);
        }
      `,
      transparent: true,
      vertexColors: true,
      blending: THREE.AdditiveBlending,
    });

    const particleSystem = new THREE.Points(particleGeometry, particleMaterial);
    particleSystem.visible = false; // Initially hidden
    scene.add(particleSystem);

    particleSystemsRef.current.set("incident_flow", {
      system: particleSystem,
      geometry: particleGeometry,
      material: particleMaterial,
      positions: positions,
    });
  };

  const initializeConsensusVisualization = (scene) => {
    // Create consensus decision tree visualization
    const treeGroup = new THREE.Group();
    treeGroup.position.set(0, 10, -30);
    treeGroup.visible = false;

    // Central decision node
    const centralGeometry = new THREE.OctahedronGeometry(2);
    const centralMaterial = new THREE.MeshPhongMaterial({
      color: 0xffffff,
      transparent: true,
      opacity: 0.8,
      emissive: 0x222222,
    });
    const centralNode = new THREE.Mesh(centralGeometry, centralMaterial);
    treeGroup.add(centralNode);

    // Decision branches
    const branchPositions = [
      [-8, 0, 0],
      [8, 0, 0],
      [0, 0, -8],
      [0, 0, 8],
    ];

    branchPositions.forEach((pos, index) => {
      const branchGeometry = new THREE.SphereGeometry(1, 16, 16);
      const branchMaterial = new THREE.MeshPhongMaterial({
        color: 0x00ff88,
        transparent: true,
        opacity: 0.6,
      });
      const branchNode = new THREE.Mesh(branchGeometry, branchMaterial);
      branchNode.position.set(...pos);

      // Connection line
      const lineGeometry = new THREE.BufferGeometry().setFromPoints([
        new THREE.Vector3(0, 0, 0),
        new THREE.Vector3(...pos),
      ]);
      const lineMaterial = new THREE.LineBasicMaterial({
        color: 0x00ff88,
        transparent: true,
        opacity: 0.5,
      });
      const line = new THREE.Line(lineGeometry, lineMaterial);

      treeGroup.add(branchNode);
      treeGroup.add(line);
    });

    scene.add(treeGroup);
    consensusTreeRef.current = treeGroup;
  };

  const initializeWebSocket = () => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/dashboard/ws`;

    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log("Connected to enhanced dashboard WebSocket");
      setWsConnection(ws);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleWebSocketMessage(data);
    };

    ws.onclose = () => {
      console.log("WebSocket disconnected, attempting reconnection...");
      setTimeout(initializeWebSocket, 3000);
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
    };
  };

  const handleWebSocketMessage = (data) => {
    if (data.type === "message_batch") {
      data.messages.forEach((msg) => processMessage(msg));
    } else {
      processMessage(data);
    }
  };

  const processMessage = (message) => {
    switch (message.type) {
      case "initial_state":
        updateAgentStates(message.data.agent_states);
        break;
      case "agent_state_update":
        updateAgentState(message.data.agent_name, message.data.state);
        break;
      case "incident_update":
        updateIncidentFlow(message.data.incident);
        break;
      case "consensus_update":
        updateConsensusVisualization(message.data);
        break;
      case "byzantine_fault_detected":
        handleByzantineFaultVisualization(message.data);
        break;
    }
  };

  const updateAgentState = (agentName, state) => {
    setAgentStates((prev) => ({ ...prev, [agentName]: state }));

    const agentNode = agentNodesRef.current.get(agentName);
    if (!agentNode) return;

    const stateColors = {
      idle: agentNode.originalColor,
      processing: 0xffff00,
      completed: 0x00ff00,
      failed: 0xff0000,
      degraded: 0xff8800,
      byzantine: 0xff0000,
      isolated: 0x666666,
    };

    const targetColor = stateColors[state] || agentNode.originalColor;

    // Animate color transition
    const currentColor = new THREE.Color(agentNode.mesh.material.color);
    const targetColorObj = new THREE.Color(targetColor);

    const animateColor = () => {
      currentColor.lerp(targetColorObj, 0.1);
      agentNode.mesh.material.color.copy(currentColor);
      agentNode.ring.material.color.copy(currentColor);

      if (currentColor.distanceTo(targetColorObj) > 0.01) {
        requestAnimationFrame(animateColor);
      }
    };
    animateColor();

    // Update status indicator
    agentNode.statusIndicator.material.color.setHex(targetColor);

    // Special effects for different states
    if (state === "processing") {
      agentNode.ring.material.opacity = 0.8;
      createProcessingEffect(agentNode);
    } else if (state === "byzantine") {
      createByzantineEffect(agentNode);
    } else {
      agentNode.ring.material.opacity = 0.4;
    }

    agentNode.state = state;
  };

  const createProcessingEffect = (agentNode) => {
    // Create pulsing energy effect
    const pulseGeometry = new THREE.SphereGeometry(4, 16, 16);
    const pulseMaterial = new THREE.MeshBasicMaterial({
      color: agentNode.originalColor,
      transparent: true,
      opacity: 0.3,
      wireframe: true,
    });
    const pulseEffect = new THREE.Mesh(pulseGeometry, pulseMaterial);
    pulseEffect.position.copy(agentNode.mesh.position);

    sceneRef.current.add(pulseEffect);

    // Animate pulse
    let scale = 1;
    const animatePulse = () => {
      scale += 0.05;
      pulseEffect.scale.setScalar(scale);
      pulseMaterial.opacity = Math.max(0, 0.3 - scale * 0.1);

      if (scale < 3) {
        requestAnimationFrame(animatePulse);
      } else {
        sceneRef.current.remove(pulseEffect);
      }
    };
    animatePulse();
  };

  const createByzantineEffect = (agentNode) => {
    // Create warning effect for Byzantine agents
    const warningGeometry = new THREE.OctahedronGeometry(3);
    const warningMaterial = new THREE.MeshBasicMaterial({
      color: 0xff0000,
      transparent: true,
      opacity: 0.8,
      wireframe: true,
    });
    const warningEffect = new THREE.Mesh(warningGeometry, warningMaterial);
    warningEffect.position.copy(agentNode.mesh.position);
    warningEffect.position.y += 5;

    sceneRef.current.add(warningEffect);

    // Animate warning
    let rotation = 0;
    const animateWarning = () => {
      rotation += 0.1;
      warningEffect.rotation.y = rotation;
      warningEffect.rotation.x = rotation * 0.5;

      if (rotation < Math.PI * 4) {
        requestAnimationFrame(animateWarning);
      } else {
        sceneRef.current.remove(warningEffect);
      }
    };
    animateWarning();
  };

  const updateIncidentFlow = (incident) => {
    setCurrentIncident(incident);

    // Show particle system for incident flow
    const particleSystem = particleSystemsRef.current.get("incident_flow");
    if (particleSystem) {
      particleSystem.system.visible = true;

      // Update particle colors based on incident severity
      const severityColors = {
        low: [0, 1, 0], // Green
        medium: [1, 1, 0], // Yellow
        high: [1, 0.5, 0], // Orange
        critical: [1, 0, 0], // Red
      };

      const color = severityColors[incident.severity] || [1, 1, 1];
      const colors = particleSystem.geometry.attributes.color.array;

      for (let i = 0; i < colors.length; i += 3) {
        colors[i] = color[0];
        colors[i + 1] = color[1];
        colors[i + 2] = color[2];
      }

      particleSystem.geometry.attributes.color.needsUpdate = true;
    }

    // Create incident flow between agents
    createIncidentFlowVisualization(incident);
  };

  const createIncidentFlowVisualization = (incident) => {
    // Create flowing particles between agents based on incident phase
    const agentOrder = [
      "detection",
      "diagnosis",
      "prediction",
      "resolution",
      "communication",
    ];

    agentOrder.forEach((agentName, index) => {
      if (index < agentOrder.length - 1) {
        const currentAgent = agentNodesRef.current.get(agentName);
        const nextAgent = agentNodesRef.current.get(agentOrder[index + 1]);

        if (currentAgent && nextAgent) {
          createFlowingParticles(
            currentAgent.mesh.position,
            nextAgent.mesh.position,
            incident.severity
          );
        }
      }
    });
  };

  const createFlowingParticles = (startPos, endPos, severity) => {
    const particleCount = 20;
    const particles = [];

    for (let i = 0; i < particleCount; i++) {
      const geometry = new THREE.SphereGeometry(0.1, 8, 8);
      const material = new THREE.MeshBasicMaterial({
        color: severity === "critical" ? 0xff0000 : 0x00ffff,
        transparent: true,
        opacity: 0.8,
      });
      const particle = new THREE.Mesh(geometry, material);

      particle.position.copy(startPos);
      sceneRef.current.add(particle);
      particles.push(particle);
    }

    // Animate particles along path
    let progress = 0;
    const animateFlow = () => {
      progress += 0.02;

      particles.forEach((particle, index) => {
        const particleProgress = Math.max(0, progress - index * 0.05);
        if (particleProgress <= 1) {
          particle.position.lerpVectors(startPos, endPos, particleProgress);
          particle.material.opacity = 0.8 * (1 - particleProgress);
        }
      });

      if (progress < 1.5) {
        requestAnimationFrame(animateFlow);
      } else {
        // Cleanup particles
        particles.forEach((particle) => {
          sceneRef.current.remove(particle);
        });
      }
    };
    animateFlow();
  };

  const updateConsensusVisualization = (consensusData) => {
    setConsensusData(consensusData);

    if (consensusTreeRef.current) {
      consensusTreeRef.current.visible = true;

      // Animate consensus tree based on decision data
      const centralNode = consensusTreeRef.current.children[0];

      // Pulse effect for active consensus
      let scale = 1;
      const animateConsensus = () => {
        scale = 1 + Math.sin(Date.now() * 0.005) * 0.2;
        centralNode.scale.setScalar(scale);

        if (consensusData && consensusData.decision) {
          centralNode.material.color.setHex(0x00ff00); // Green for decided
        } else {
          centralNode.material.color.setHex(0xffff00); // Yellow for in progress
        }
      };

      const consensusInterval = setInterval(() => {
        animateConsensus();
      }, 50);

      // Stop animation after 5 seconds
      setTimeout(() => {
        clearInterval(consensusInterval);
        consensusTreeRef.current.visible = false;
      }, 5000);
    }
  };

  const handleByzantineFaultVisualization = (faultData) => {
    const agentName = faultData.agent_name;
    const agentNode = agentNodesRef.current.get(agentName);

    if (agentNode) {
      // Create dramatic Byzantine fault visualization
      createByzantineEffect(agentNode);
      updateAgentState(agentName, "byzantine");

      // Show isolation effect after delay
      setTimeout(() => {
        updateAgentState(agentName, "isolated");
        createIsolationEffect(agentNode);
      }, 2000);
    }
  };

  const createIsolationEffect = (agentNode) => {
    // Create barrier effect around isolated agent
    const barrierGeometry = new THREE.SphereGeometry(5, 32, 32);
    const barrierMaterial = new THREE.MeshBasicMaterial({
      color: 0xff0000,
      transparent: true,
      opacity: 0.2,
      wireframe: true,
    });
    const barrier = new THREE.Mesh(barrierGeometry, barrierMaterial);
    barrier.position.copy(agentNode.mesh.position);

    sceneRef.current.add(barrier);

    // Animate barrier
    let opacity = 0.2;
    const animateBarrier = () => {
      opacity -= 0.005;
      barrier.material.opacity = Math.max(0, opacity);
      barrier.rotation.y += 0.02;

      if (opacity > 0) {
        requestAnimationFrame(animateBarrier);
      } else {
        sceneRef.current.remove(barrier);
      }
    };
    animateBarrier();
  };

  const updateParticleAnimations = () => {
    const time = Date.now() * 0.001;

    particleSystemsRef.current.forEach((particleData) => {
      if (particleData.material.uniforms) {
        particleData.material.uniforms.time.value = time;
      }

      // Animate particle positions for flowing effect
      const positions = particleData.positions;
      for (let i = 0; i < positions.length; i += 3) {
        positions[i + 1] += Math.sin(time + positions[i] * 0.01) * 0.1;
      }
      particleData.geometry.attributes.position.needsUpdate = true;
    });
  };

  const updateAgentAnimations = () => {
    const time = Date.now() * 0.001;

    agentNodesRef.current.forEach((agentNode, agentName) => {
      // Floating animation
      const baseY = 3;
      agentNode.mesh.position.y =
        baseY + Math.sin(time + agentName.length) * 0.3;

      // Ring rotation
      agentNode.ring.rotation.z += 0.01;

      // State-specific animations
      if (agentNode.state === "processing") {
        const pulse = Math.sin(time * 4) * 0.3 + 0.7;
        agentNode.mesh.material.opacity = pulse;
        agentNode.ring.scale.setScalar(1 + Math.sin(time * 3) * 0.2);
      } else {
        agentNode.mesh.material.opacity = 0.9;
        agentNode.ring.scale.setScalar(1);
      }

      // Status indicator animation
      agentNode.statusIndicator.rotation.y += 0.05;
    });
  };

  const cleanup = () => {
    if (mountRef.current && rendererRef.current?.domElement) {
      mountRef.current.removeChild(rendererRef.current.domElement);
    }
    if (rendererRef.current) {
      rendererRef.current.dispose();
    }
    if (wsConnection) {
      wsConnection.close();
    }
  };

  // Demo control functions
  const triggerDemoIncident = (type = "database_failure") => {
    if (wsConnection && wsConnection.readyState === WebSocket.OPEN) {
      wsConnection.send(
        JSON.stringify({
          action: "trigger_demo_incident",
          incident_type: type,
        })
      );
      setDemoMode("incident_active");
    }
  };

  const injectByzantineFault = () => {
    if (wsConnection && wsConnection.readyState === WebSocket.OPEN) {
      wsConnection.send(
        JSON.stringify({
          action: "inject_byzantine_fault",
          target_agent: "diagnosis", // Target specific agent
        })
      );
      setDemoMode("byzantine_active");
    }
  };

  const resetSystem = () => {
    if (wsConnection && wsConnection.readyState === WebSocket.OPEN) {
      wsConnection.send(JSON.stringify({ action: "reset_agents" }));
      setDemoMode("idle");
      setSelectedAgent(null);
      setCurrentIncident(null);
      setConsensusData(null);
    }
  };

  return (
    <div className="relative w-full h-screen bg-black">
      <div ref={mountRef} className="w-full h-full" />

      {/* Enhanced Control Panel */}
      <div className="absolute top-4 right-4 bg-black bg-opacity-80 text-white p-6 rounded-lg border border-cyan-500 min-w-80">
        <h3 className="text-xl font-bold mb-4 text-cyan-400">
          Mission Control
        </h3>

        <div className="space-y-3">
          <div className="grid grid-cols-2 gap-2">
            <button
              className="bg-blue-600 hover:bg-blue-700 px-3 py-2 rounded text-sm transition-colors"
              onClick={() => triggerDemoIncident("database_failure")}
            >
              Database Crisis
            </button>
            <button
              className="bg-orange-600 hover:bg-orange-700 px-3 py-2 rounded text-sm transition-colors"
              onClick={() => triggerDemoIncident("api_cascade")}
            >
              API Cascade
            </button>
            <button
              className="bg-purple-600 hover:bg-purple-700 px-3 py-2 rounded text-sm transition-colors"
              onClick={() => triggerDemoIncident("memory_leak")}
            >
              Memory Leak
            </button>
            <button
              className="bg-yellow-600 hover:bg-yellow-700 px-3 py-2 rounded text-sm transition-colors"
              onClick={() => triggerDemoIncident("network_partition")}
            >
              Network Split
            </button>
          </div>

          <div className="border-t border-gray-600 pt-3">
            <button
              className="bg-red-600 hover:bg-red-700 px-4 py-2 rounded w-full mb-2 transition-colors"
              onClick={injectByzantineFault}
            >
              🚨 Inject Byzantine Fault
            </button>
            <button
              className="bg-gray-600 hover:bg-gray-700 px-4 py-2 rounded w-full transition-colors"
              onClick={resetSystem}
            >
              Reset System
            </button>
          </div>
        </div>

        <div className="mt-4 text-xs text-gray-400">
          Mode: <span className="text-cyan-400">{demoMode}</span>
        </div>
      </div>

      {/* Agent Status Panel */}
      <div className="absolute top-4 left-4 bg-black bg-opacity-80 text-white p-4 rounded-lg border border-green-500 min-w-64">
        <h3 className="text-lg font-bold mb-3 text-green-400">Agent Status</h3>
        <div className="space-y-2">
          {Object.entries(agentStates).map(([agent, state]) => (
            <div key={agent} className="flex items-center justify-between">
              <div className="flex items-center">
                <div
                  className={`w-3 h-3 rounded-full mr-3 ${
                    state === "processing"
                      ? "bg-yellow-400 animate-pulse"
                      : state === "completed"
                      ? "bg-green-400"
                      : state === "failed"
                      ? "bg-red-400"
                      : state === "byzantine"
                      ? "bg-red-600 animate-ping"
                      : state === "isolated"
                      ? "bg-gray-500"
                      : "bg-gray-400"
                  }`}
                />
                <span className="capitalize text-sm">{agent}</span>
              </div>
              <span
                className={`text-xs px-2 py-1 rounded ${
                  state === "processing"
                    ? "bg-yellow-900 text-yellow-200"
                    : state === "completed"
                    ? "bg-green-900 text-green-200"
                    : state === "failed"
                    ? "bg-red-900 text-red-200"
                    : state === "byzantine"
                    ? "bg-red-800 text-red-100"
                    : state === "isolated"
                    ? "bg-gray-800 text-gray-200"
                    : "bg-gray-700 text-gray-300"
                }`}
              >
                {state}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Incident Information Panel */}
      {currentIncident && (
        <div className="absolute bottom-4 left-4 bg-black bg-opacity-80 text-white p-4 rounded-lg border border-orange-500 max-w-md">
          <h3 className="text-lg font-bold mb-2 text-orange-400">
            Active Incident
          </h3>
          <div className="space-y-1 text-sm">
            <div>
              <strong>ID:</strong> {currentIncident.id}
            </div>
            <div>
              <strong>Type:</strong> {currentIncident.title}
            </div>
            <div>
              <strong>Severity:</strong>
              <span
                className={`ml-2 px-2 py-1 rounded text-xs ${
                  currentIncident.severity === "critical"
                    ? "bg-red-900 text-red-200"
                    : currentIncident.severity === "high"
                    ? "bg-orange-900 text-orange-200"
                    : currentIncident.severity === "medium"
                    ? "bg-yellow-900 text-yellow-200"
                    : "bg-green-900 text-green-200"
                }`}
              >
                {currentIncident.severity}
              </span>
            </div>
            <div>
              <strong>Phase:</strong> {currentIncident.phase}
            </div>
          </div>
        </div>
      )}

      {/* Consensus Information Panel */}
      {consensusData && (
        <div className="absolute bottom-4 right-4 bg-black bg-opacity-80 text-white p-4 rounded-lg border border-purple-500 max-w-md">
          <h3 className="text-lg font-bold mb-2 text-purple-400">
            Byzantine Consensus
          </h3>
          <div className="space-y-1 text-sm">
            <div>
              <strong>Method:</strong>{" "}
              {consensusData.consensus_method || "PBFT"}
            </div>
            <div>
              <strong>Nodes:</strong> {consensusData.total_nodes || 5}
            </div>
            <div>
              <strong>Byzantine Detected:</strong>{" "}
              {consensusData.byzantine_nodes_detected || 0}
            </div>
            <div>
              <strong>Status:</strong>
              <span
                className={`ml-2 px-2 py-1 rounded text-xs ${
                  consensusData.decision
                    ? "bg-green-900 text-green-200"
                    : "bg-yellow-900 text-yellow-200"
                }`}
              >
                {consensusData.decision ? "Decided" : "In Progress"}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Instructions */}
      <div className="absolute bottom-4 center-4 left-1/2 transform -translate-x-1/2 bg-black bg-opacity-60 text-white p-3 rounded-lg text-center text-sm">
        <div className="text-cyan-400 font-semibold">
          🎮 Interactive Demo Controls
        </div>
        <div className="text-xs mt-1">
          Click agents for details • Use mouse to navigate • Try Byzantine fault
          injection
        </div>
      </div>
    </div>
  );
};

export default EnhancedAgentVisualization;
