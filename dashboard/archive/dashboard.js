/**
 * Autonomous Incident Commander Dashboard
 * Interactive real-time visualization for hackathon demo
 */

class IncidentCommanderDashboard {
  constructor() {
    this.baseUrl = "http://localhost:8000"; // FastAPI backend
    this.isConnected = false;
    this.currentIncident = null;
    this.mttrTimer = null;
    this.startTime = null;

    // Initialize dashboard
    this.init();
  }

  async init() {
    console.log("🚀 Initializing Autonomous Incident Commander Dashboard");

    // Start real-time updates
    this.startRealTimeUpdates();

    // Initialize agent connections
    this.initializeAgentConnections();

    // Setup event listeners
    this.setupEventListeners();

    // Test backend connection
    await this.testConnection();
  }

  async testConnection() {
    try {
      const response = await fetch(`${this.baseUrl}/system/health`);
      if (response.ok) {
        this.isConnected = true;
        console.log("✅ Connected to Incident Commander backend");
        this.updateConnectionStatus(true);
      }
    } catch (error) {
      console.log("⚠️ Backend not available, running in demo mode");
      this.isConnected = false;
      this.updateConnectionStatus(false);
      this.startDemoMode();
    }
  }

  updateConnectionStatus(connected) {
    const statusIndicator = document.querySelector(".status-indicator");
    const statusDot = document.querySelector(".status-dot");
    const statusText = statusIndicator.querySelector("span");

    if (connected) {
      statusDot.style.background = "#00ff88";
      statusText.textContent = "System Operational";
    } else {
      statusDot.style.background = "#f9ca24";
      statusText.textContent = "Demo Mode";
    }
  }

  startDemoMode() {
    console.log("🎭 Starting demo mode with simulated data");

    // Simulate real-time metrics
    this.simulateMetrics();

    // Simulate incident feed
    this.simulateIncidentFeed();

    // Animate agent activities
    this.animateAgents();
  }

  simulateMetrics() {
    setInterval(() => {
      // Update concurrent incidents (800-1000 range)
      const concurrent = 800 + Math.floor(Math.random() * 200);
      document.getElementById("concurrent-incidents").textContent = concurrent;

      // Update alert processing rate (450-600 range)
      const alertRate = 450 + Math.floor(Math.random() * 150);
      document.getElementById("alert-rate").textContent = `${alertRate}/sec`;

      // Update cost savings (incremental)
      const currentSavings = parseFloat(
        document
          .getElementById("cost-savings")
          .textContent.replace("$", "")
          .replace("M", "")
      );
      const newSavings = currentSavings + Math.random() * 0.01;
      document.getElementById(
        "cost-savings"
      ).textContent = `$${newSavings.toFixed(1)}M`;

      // Update incidents resolved
      const currentResolved = parseInt(
        document.getElementById("incidents-resolved").textContent
      );
      if (Math.random() < 0.1) {
        // 10% chance to increment
        document.getElementById("incidents-resolved").textContent =
          currentResolved + 1;
      }
    }, 2000);
  }

  simulateIncidentFeed() {
    const incidentTypes = [
      {
        name: "Database Connection Pool Exhausted",
        severity: "critical",
        icon: "database",
      },
      {
        name: "API Gateway Rate Limit Exceeded",
        severity: "high",
        icon: "server",
      },
      {
        name: "Memory Usage Above Threshold",
        severity: "medium",
        icon: "memory",
      },
      { name: "Disk Space Low Warning", severity: "low", icon: "hdd" },
      {
        name: "SSL Certificate Expiring",
        severity: "medium",
        icon: "certificate",
      },
      {
        name: "Load Balancer Health Check Failed",
        severity: "high",
        icon: "network-wired",
      },
      {
        name: "Cache Hit Rate Degraded",
        severity: "low",
        icon: "tachometer-alt",
      },
    ];

    setInterval(() => {
      if (Math.random() < 0.3) {
        // 30% chance to add new incident
        const incident =
          incidentTypes[Math.floor(Math.random() * incidentTypes.length)];
        this.addIncidentToFeed(incident);
      }
    }, 5000);
  }

  addIncidentToFeed(incident) {
    const incidentList = document.getElementById("incident-list");
    const incidentElement = document.createElement("div");
    incidentElement.className = `incident-item incident-${incident.severity}`;
    incidentElement.innerHTML = `
            <div class="incident-status"></div>
            <div>
                <div style="font-weight: 600;">${incident.name}</div>
                <div style="font-size: 0.8rem; color: #888;">Detected ${new Date().toLocaleTimeString()}</div>
            </div>
        `;

    // Add to top of list
    incidentList.insertBefore(incidentElement, incidentList.firstChild);

    // Remove oldest if more than 5 incidents
    if (incidentList.children.length > 5) {
      incidentList.removeChild(incidentList.lastChild);
    }

    // Animate in
    incidentElement.style.opacity = "0";
    incidentElement.style.transform = "translateX(-20px)";
    setTimeout(() => {
      incidentElement.style.transition = "all 0.3s ease";
      incidentElement.style.opacity = "1";
      incidentElement.style.transform = "translateX(0)";
    }, 100);
  }

  animateAgents() {
    const agents = document.querySelectorAll(".agent-node");

    setInterval(() => {
      agents.forEach((agent) => {
        if (Math.random() < 0.2) {
          // 20% chance to pulse
          agent.style.transform = "scale(1.1)";
          agent.style.boxShadow = "0 0 20px rgba(0, 212, 255, 0.5)";
          setTimeout(() => {
            agent.style.transform = "scale(1)";
            agent.style.boxShadow = "none";
          }, 500);
        }
      });
    }, 1000);
  }

  startRealTimeUpdates() {
    // Update MTTR timer
    this.updateMTTRTimer();

    // Update every second
    setInterval(() => {
      this.updateMTTRTimer();
    }, 1000);
  }

  updateMTTRTimer() {
    if (!this.startTime) {
      this.startTime = Date.now();
    }

    const elapsed = Date.now() - this.startTime;
    const minutes = Math.floor(elapsed / 60000);
    const seconds = Math.floor((elapsed % 60000) / 1000);

    const display = `${minutes.toString().padStart(2, "0")}:${seconds
      .toString()
      .padStart(2, "0")}`;
    document.getElementById("mttr-display").textContent = display;

    // Reset after 3 minutes to simulate resolution
    if (elapsed > 180000) {
      // 3 minutes
      this.startTime = Date.now();
      this.showResolutionAnimation();
    }
  }

  showResolutionAnimation() {
    const mttrDisplay = document.getElementById("mttr-display");
    mttrDisplay.style.color = "#00ff88";
    mttrDisplay.style.transform = "scale(1.2)";

    setTimeout(() => {
      mttrDisplay.style.color = "#00ff88";
      mttrDisplay.style.transform = "scale(1)";
    }, 1000);

    // Show success message
    this.showNotification("✅ Incident Resolved Autonomously", "success");
  }

  initializeAgentConnections() {
    // Create connection lines between agents and consensus center
    const swarmContainer = document.querySelector(".swarm-container");
    const agents = document.querySelectorAll(".agent-node");
    const consensusCenter = document.querySelector(".consensus-center");

    agents.forEach((agent, index) => {
      const line = document.createElement("div");
      line.className = "connection-line";
      line.style.animationDelay = `${index * 0.5}s`;
      swarmContainer.appendChild(line);

      // Position line from agent to center
      this.positionConnectionLine(line, agent, consensusCenter);
    });
  }

  positionConnectionLine(line, agent, center) {
    const agentRect = agent.getBoundingClientRect();
    const centerRect = center.getBoundingClientRect();
    const containerRect = agent.parentElement.getBoundingClientRect();

    const agentX = agentRect.left - containerRect.left + agentRect.width / 2;
    const agentY = agentRect.top - containerRect.top + agentRect.height / 2;
    const centerX = centerRect.left - containerRect.left + centerRect.width / 2;
    const centerY = centerRect.top - containerRect.top + centerRect.height / 2;

    const length = Math.sqrt(
      Math.pow(centerX - agentX, 2) + Math.pow(centerY - agentY, 2)
    );
    const angle =
      (Math.atan2(centerY - agentY, centerX - agentX) * 180) / Math.PI;

    line.style.width = `${length}px`;
    line.style.left = `${agentX}px`;
    line.style.top = `${agentY}px`;
    line.style.transformOrigin = "0 50%";
    line.style.transform = `rotate(${angle}deg)`;
  }

  setupEventListeners() {
    // Window resize handler for responsive connection lines
    window.addEventListener("resize", () => {
      setTimeout(() => {
        this.initializeAgentConnections();
      }, 100);
    });
  }

  showNotification(message, type = "info") {
    const notification = document.createElement("div");
    notification.style.cssText = `
            position: fixed;
            top: 100px;
            right: 20px;
            padding: 1rem 1.5rem;
            background: ${
              type === "success"
                ? "rgba(0, 255, 136, 0.1)"
                : "rgba(0, 212, 255, 0.1)"
            };
            border: 1px solid ${type === "success" ? "#00ff88" : "#00d4ff"};
            border-radius: 8px;
            color: white;
            font-weight: 600;
            z-index: 1000;
            animation: slideIn 0.3s ease;
        `;
    notification.textContent = message;

    document.body.appendChild(notification);

    setTimeout(() => {
      notification.style.animation = "slideOut 0.3s ease";
      setTimeout(() => {
        document.body.removeChild(notification);
      }, 300);
    }, 3000);
  }
}

// Global functions for UI interactions
async function triggerScenario(scenarioName) {
  console.log(`🎯 Triggering scenario: ${scenarioName}`);

  const dashboard = window.dashboard;

  try {
    if (dashboard.isConnected) {
      // Call real API
      const response = await fetch(
        `${dashboard.baseUrl}/demo/scenarios/${scenarioName}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      if (response.ok) {
        const result = await response.json();
        dashboard.showNotification(
          `✅ ${scenarioName.replace("_", " ")} scenario triggered`,
          "success"
        );
        dashboard.startTime = Date.now(); // Reset MTTR timer
      }
    } else {
      // Demo mode
      dashboard.showNotification(
        `🎭 Demo: ${scenarioName.replace("_", " ")} scenario`,
        "info"
      );
      dashboard.startTime = Date.now(); // Reset MTTR timer

      // Add demo incident to feed
      const scenarioDetails = {
        database_cascade: {
          name: "Database Cascade Failure",
          severity: "critical",
        },
        ddos_attack: { name: "DDoS Attack Detected", severity: "critical" },
        memory_leak: { name: "Memory Leak in Service", severity: "high" },
        api_overload: { name: "API Rate Limit Exceeded", severity: "high" },
        storage_failure: {
          name: "Storage System Failure",
          severity: "critical",
        },
      };

      if (scenarioDetails[scenarioName]) {
        dashboard.addIncidentToFeed(scenarioDetails[scenarioName]);
      }
    }

    // Animate agents responding
    animateAgentResponse();
  } catch (error) {
    console.error("Error triggering scenario:", error);
    dashboard.showNotification("❌ Failed to trigger scenario", "error");
  }
}

function animateAgentResponse() {
  const agents = document.querySelectorAll(".agent-node");

  agents.forEach((agent, index) => {
    setTimeout(() => {
      agent.style.transform = "scale(1.2)";
      agent.style.boxShadow = "0 0 25px rgba(0, 212, 255, 0.8)";
      agent.style.borderColor = "#00d4ff";

      setTimeout(() => {
        agent.style.transform = "scale(1)";
        agent.style.boxShadow = "none";
        agent.style.borderColor = "";
      }, 800);
    }, index * 200);
  });
}

function showAgentDetails(agentType) {
  const agentInfo = {
    detection: {
      name: "Detection Agent",
      description:
        "Monitors 50K+ alerts/sec across multiple sources with intelligent correlation and deduplication.",
      capabilities: [
        "Multi-source alert correlation",
        "Anomaly detection",
        "Alert storm handling",
        "Pattern recognition",
      ],
      status: "Active - Processing 523 alerts/sec",
    },
    diagnosis: {
      name: "Diagnosis Agent",
      description:
        "Performs root cause analysis using RAG-powered historical incident knowledge.",
      capabilities: [
        "Log analysis",
        "Trace correlation",
        "Historical pattern matching",
        "Evidence chain construction",
      ],
      status: "Active - Analyzing 12 incidents",
    },
    prediction: {
      name: "Prediction Agent",
      description:
        "Forecasts cascading failures 15-30 minutes in advance using time-series analysis.",
      capabilities: [
        "Time-series forecasting",
        "Risk assessment",
        "Trend analysis",
        "Preventive recommendations",
      ],
      status: "Active - Monitoring trends",
    },
    resolution: {
      name: "Resolution Agent",
      description:
        "Executes zero-trust automated remediation with sandbox validation and rollback.",
      capabilities: [
        "Automated remediation",
        "Zero-trust execution",
        "Rollback mechanisms",
        "Safety validation",
      ],
      status: "Active - 3 resolutions in progress",
    },
    communication: {
      name: "Communication Agent",
      description:
        "Manages stakeholder notifications with intelligent routing and escalation.",
      capabilities: [
        "Multi-channel notifications",
        "Stakeholder routing",
        "Escalation policies",
        "Status updates",
      ],
      status: "Active - 15 notifications sent",
    },
  };

  const info = agentInfo[agentType];
  if (!info) return;

  const modal = document.createElement("div");
  modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.8);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
        animation: fadeIn 0.3s ease;
    `;

  modal.innerHTML = `
        <div style="
            background: linear-gradient(135deg, #1a1f2e, #2d3748);
            border: 1px solid rgba(0, 212, 255, 0.3);
            border-radius: 16px;
            padding: 2rem;
            max-width: 500px;
            width: 90%;
            color: white;
        ">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
                <h2 style="color: #00d4ff; margin: 0;">${info.name}</h2>
                <button onclick="this.parentElement.parentElement.parentElement.remove()" style="
                    background: none;
                    border: none;
                    color: #888;
                    font-size: 1.5rem;
                    cursor: pointer;
                ">×</button>
            </div>
            <p style="margin-bottom: 1.5rem; line-height: 1.6;">${
              info.description
            }</p>
            <div style="margin-bottom: 1.5rem;">
                <h3 style="color: #00ff88; margin-bottom: 0.5rem;">Capabilities:</h3>
                <ul style="margin: 0; padding-left: 1.5rem;">
                    ${info.capabilities
                      .map(
                        (cap) =>
                          `<li style="margin-bottom: 0.25rem;">${cap}</li>`
                      )
                      .join("")}
                </ul>
            </div>
            <div style="
                padding: 1rem;
                background: rgba(0, 255, 136, 0.1);
                border-radius: 8px;
                border-left: 3px solid #00ff88;
            ">
                <strong>Status:</strong> ${info.status}
            </div>
        </div>
    `;

  document.body.appendChild(modal);

  // Close on background click
  modal.addEventListener("click", (e) => {
    if (e.target === modal) {
      modal.remove();
    }
  });
}

// Add CSS animations
const style = document.createElement("style");
style.textContent = `
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);

// Initialize dashboard when page loads
document.addEventListener("DOMContentLoaded", () => {
  window.dashboard = new IncidentCommanderDashboard();
});

// Export for testing
if (typeof module !== "undefined" && module.exports) {
  module.exports = { IncidentCommanderDashboard };
}
