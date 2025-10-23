# 🏗️ SwarmAI Incident Commander - Architecture Diagram

**Visual representation of the complete system architecture using Mermaid architecture diagrams.**

## System Architecture Diagram

```mermaid
graph TB
    subgraph judge_layer["Judge Interface Layer"]
        judge_interface[Judge Interface]
        demo_controller[Demo Controller]
        interactive_metrics[Interactive Metrics]
        business_viz[Business Visualization]
        fault_tolerance[Fault Tolerance]
        conversation_replay[Conversation Replay]
        compliance_dash[Compliance Dashboard]
    end

    subgraph agent_core["Multi-Agent Core"]
        detection_agent[Detection Agent]
        diagnosis_agent[Diagnosis Agent]
        prediction_agent[Prediction Agent]
        resolution_agent[Resolution Agent]
        communication_agent[Communication Agent]
        byzantine_consensus[Byzantine Consensus]
    end

    subgraph aws_services["AWS AI Services"]
        bedrock_core[Bedrock Agent Core]
        claude_sonnet[Claude Sonnet]
        claude_haiku[Claude Haiku]
        titan_embeddings[Titan Embeddings]
        amazon_q[Amazon Q]
        nova_act[Nova Act]
        strands_sdk[Strands SDK]
        bedrock_guardrails[Bedrock Guardrails]
    end

    subgraph infrastructure["Infrastructure & Data"]
        event_store[DynamoDB Event Store]
        rag_memory[OpenSearch RAG Memory]
        circuit_breakers[Circuit Breakers]
        rate_limiters[Rate Limiters]
        message_bus[Message Bus]
        health_monitor[Health Monitor]
    end

    subgraph security["Security & Compliance"]
        zero_trust[Zero Trust]
        audit_logging[Audit Logging]
        sec_validation[Security Validation]
        compliance_monitor[Compliance Monitor]
    end

    judge_interface --> demo_controller
    demo_controller --> detection_agent
    demo_controller --> diagnosis_agent
    demo_controller --> prediction_agent
    demo_controller --> resolution_agent
    demo_controller --> communication_agent

    detection_agent --> byzantine_consensus
    diagnosis_agent --> byzantine_consensus
    prediction_agent --> byzantine_consensus
    resolution_agent --> byzantine_consensus
    communication_agent --> byzantine_consensus

    byzantine_consensus --> bedrock_core
    detection_agent --> claude_sonnet
    diagnosis_agent --> claude_sonnet
    prediction_agent --> claude_haiku
    resolution_agent --> nova_act
    communication_agent --> amazon_q

    titan_embeddings --> rag_memory

    detection_agent --> event_store
    diagnosis_agent --> event_store
    prediction_agent --> event_store
    resolution_agent --> event_store
    communication_agent --> event_store

    agent_core -.-> infrastructure
    agent_core -.-> security
```

## Component Integration Diagram

```mermaid
graph LR
    subgraph aws_integration["AWS AI Services"]
        bedrock[Bedrock Core]
        guardrails[Guardrails]
        reasoning[Claude Sonnet]
        fast_response[Claude Haiku]
        embeddings[Titan Embeddings]
        business_intel[Amazon Q]
        action_plan[Nova Act]
        lifecycle[Strands SDK]
    end

    subgraph agent_network["Agent Network"]
        consensus[Byzantine Consensus]
        agents[Agent Swarm]
        coordination[Coordination Layer]
    end

    subgraph data_layer["Data Layer"]
        events[Event Store]
        memory[RAG Memory]
        cache[Redis Cache]
    end

    agents --> consensus
    consensus --> bedrock
    bedrock --> guardrails
    reasoning --> agents
    fast_response --> agents
    action_plan --> agents
    business_intel --> agents
    lifecycle --> coordination
    embeddings --> memory
    agents --> events
    agents --> cache
```

## Performance & Scalability Architecture

```mermaid
graph TB
    subgraph load_balance["Load Balancing"]
        alb[Application LB]
        nlb[Network LB]
    end

    subgraph compute["Compute Layer"]
        ecs[ECS Fargate]
        lambda[Lambda]
        autoscale[Auto Scaling]
    end

    subgraph storage["Data Layer"]
        dynamodb[DynamoDB]
        opensearch[OpenSearch]
        s3[S3 Storage]
    end

    subgraph monitoring["Monitoring"]
        metrics[CloudWatch]
        traces[X-Ray]
        logs[Log Aggregation]
    end

    alb --> ecs
    nlb --> lambda
    ecs --> autoscale
    lambda --> dynamodb
    autoscale --> opensearch
    dynamodb --> s3
    compute -.-> monitoring
```

## Security & Compliance Architecture

```mermaid
graph LR
    subgraph identity["Identity & Access"]
        agent_identity[Agent Identity]
        access_control[Access Control]
        mfa[Multi-Factor Auth]
    end

    subgraph protection["Data Protection"]
        encryption_rest[Encryption at Rest]
        encryption_transit[Encryption in Transit]
        dlp[Data Loss Prevention]
    end

    subgraph audit["Monitoring & Audit"]
        audit_log[Audit Logging]
        threat_monitor[Threat Monitoring]
        compliance[Compliance Check]
    end

    agent_identity --> access_control
    access_control --> mfa
    encryption_rest --> encryption_transit
    encryption_transit --> dlp
    audit_log --> threat_monitor
    threat_monitor --> compliance
```

---

**Architecture diagrams provide a comprehensive visual representation of the SwarmAI Incident Commander system, showcasing the integration of all 8 AWS AI services, Byzantine fault-tolerant multi-agent core, and enterprise-grade infrastructure.**
