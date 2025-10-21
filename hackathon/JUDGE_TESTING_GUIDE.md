# 🏆 Judge Testing Guide - Live AWS & Local Testing

## 🌐 **Live AWS Deployment Available!**

Judges can test your submission using **both local setup AND live AWS URLs**:

### **Live AWS API Gateway URL:**

```
https://h8xlzr74h8.execute-api.us-east-1.amazonaws.com
```

## 🚀 **Option 1: Test Live AWS Deployment (30 seconds)**

### **Quick Live Tests**

```bash
# System health check
curl https://h8xlzr74h8.execute-api.us-east-1.amazonaws.com/health

# Real AWS AI services status
curl https://h8xlzr74h8.execute-api.us-east-1.amazonaws.com/real-aws-ai/services/status

# Prize eligibility verification
curl https://h8xlzr74h8.execute-api.us-east-1.amazonaws.com/real-aws-ai/prize-eligibility

# Full AWS AI showcase
curl https://h8xlzr74h8.execute-api.us-east-1.amazonaws.com/real-aws-ai/demo/full-showcase

# Test Amazon Q Business integration
curl -X POST https://h8xlzr74h8.execute-api.us-east-1.amazonaws.com/real-aws-ai/amazon-q/analyze \
  -H "Content-Type: application/json" \
  -d '{"type": "database_cascade", "description": "Connection pool exhaustion"}'

# Test Nova Models integration
curl -X POST https://h8xlzr74h8.execute-api.us-east-1.amazonaws.com/real-aws-ai/nova-models/reason \
  -H "Content-Type: application/json" \
  -d '{"incident_type": "database_cascade", "severity": "high"}'
```

### **Live Demo Endpoints**

| Endpoint                          | Purpose             | Prize Relevant |
| --------------------------------- | ------------------- | -------------- |
| `/health`                         | System status       | General        |
| `/real-aws-ai/services/status`    | All AWS AI services | All prizes     |
| `/real-aws-ai/amazon-q/analyze`   | Amazon Q Business   | $3K Prize      |
| `/real-aws-ai/nova-models/reason` | Nova Models         | $3K Prize      |
| `/real-aws-ai/prize-eligibility`  | Prize verification  | All prizes     |
| `/demo/incident`                  | Incident simulation | General        |
| `/demo/stats`                     | Performance metrics | General        |

### **Interactive Dashboard URLs**

_Copy and paste these URLs into your browser after starting the local servers:_

- **Auto-Demo**: http://localhost:3000/agent_actions_dashboard.html?auto-demo=true
- **Manual Demo**: http://localhost:3000/agent_actions_dashboard.html
- **Judge Controls**: Interactive buttons for custom incident scenarios

### **Clickable Live Links for Judges**

- [🔗 System Health](https://h8xlzr74h8.execute-api.us-east-1.amazonaws.com/health)
- [🔗 AWS AI Services Status](https://h8xlzr74h8.execute-api.us-east-1.amazonaws.com/real-aws-ai/services/status)
- [🔗 Prize Eligibility Check](https://h8xlzr74h8.execute-api.us-east-1.amazonaws.com/real-aws-ai/prize-eligibility)
- [🔗 Full AWS AI Showcase](https://h8xlzr74h8.execute-api.us-east-1.amazonaws.com/real-aws-ai/demo/full-showcase)
- [🔗 Demo Incident](https://h8xlzr74h8.execute-api.us-east-1.amazonaws.com/demo/incident)
- [🔗 Performance Stats](https://h8xlzr74h8.execute-api.us-east-1.amazonaws.com/demo/stats)

## 💻 **Option 2: Local Setup Testing (3 minutes)**

### **Quick Local Setup**

```bash
# Clone and setup
git clone <repository-url>
cd incident-commander

# Start backend API
python -m uvicorn src.main:app --reload --port 8000 &

# Start dashboard server
python -m http.server 3000 --directory dashboard &

# Open auto-demo dashboard (cross-platform)
# For macOS:
# open http://localhost:3000/agent_actions_dashboard.html?auto-demo=true
# For Windows:
# start http://localhost:3000/agent_actions_dashboard.html?auto-demo=true
# For Linux:
# xdg-open http://localhost:3000/agent_actions_dashboard.html?auto-demo=true
#
# OR manually open your browser and navigate to:
# http://localhost:3000/agent_actions_dashboard.html?auto-demo=true

# Test API endpoints
curl http://localhost:8000/real-aws-ai/services/status
curl http://localhost:8000/real-aws-ai/prize-eligibility
```

## 🎯 **Prize Verification Tests**

### **Amazon Q Business Integration Prize ($3,000)**

```bash
# Live AWS test
curl -X POST https://h8xlzr74h8.execute-api.us-east-1.amazonaws.com/real-aws-ai/amazon-q/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "type": "database_cascade",
    "description": "Production database experiencing connection pool exhaustion",
    "severity": "critical"
  }'

# Expected response: Real Amazon Q Business analysis with business insights
```

### **Amazon Nova Models Integration Prize ($3,000)**

```bash
# Live AWS test
curl -X POST https://h8xlzr74h8.execute-api.us-east-1.amazonaws.com/real-aws-ai/nova-models/reason \
  -H "Content-Type: application/json" \
  -d '{
    "incident_type": "database_cascade",
    "severity": "high",
    "action_id": "judge_test_001"
  }'

# Expected response: Real Nova model multimodal reasoning and action planning
```

### **Best Bedrock AgentCore Implementation ($3,000)**

```bash
# Live AWS test
curl https://h8xlzr74h8.execute-api.us-east-1.amazonaws.com/aws-ai-services/bedrock/status

# Expected response: Complete Bedrock integration with Claude models, Titan embeddings
```

## 📊 **Real AWS AI Services Verification**

### **Service Integration Status**

```bash
# Check all real AWS AI services
curl https://h8xlzr74h8.execute-api.us-east-1.amazonaws.com/real-aws-ai/services/status

# Expected services:
# ✅ Amazon Q Business - Real API integration
# ✅ Amazon Nova Models - Real multimodal reasoning
# ✅ Amazon Comprehend - NLP and sentiment analysis
# ✅ Amazon Textract - Document processing
# ✅ Amazon Translate - Multi-language support
# ✅ Amazon Polly - Voice synthesis
# ✅ Amazon Bedrock - Claude models and Titan embeddings
```

## 🎬 **Demo Video Verification**

### **HD Demo Recording**

- **File**: Available in repository at `scripts/demo_recordings/videos/`
- **Duration**: 2 minutes 49 seconds
- **Quality**: HD 1920x1080
- **Content**: Complete incident response workflow demonstration

### **Screenshots Package**

- **Count**: 10 key decision points
- **Location**: `scripts/demo_recordings/screenshots/`
- **Coverage**: Full workflow from trigger to resolution

## 🔧 **Fallback Testing**

### **Graceful Degradation**

The system includes intelligent fallback handling:

```bash
# Test fallback behavior (simulates AWS service unavailable)
curl https://h8xlzr74h8.execute-api.us-east-1.amazonaws.com/real-aws-ai/services/status

# System will show:
# - Real AWS API calls attempted first
# - Intelligent simulation if services unavailable
# - Maintains functionality during outages
# - Clear indication of real vs fallback mode
```

## 📋 **Judge Evaluation Checklist**

### **✅ Real AWS AI Integration Verification**

- [ ] Amazon Q Business API calls working
- [ ] Nova Models via Bedrock Runtime functional
- [ ] Multiple additional AWS AI services integrated
- [ ] Comprehensive AI orchestration operational
- [ ] Prize eligibility endpoints responding correctly

### **✅ System Functionality**

- [ ] Live AWS deployment accessible
- [ ] Local setup works (if tested)
- [ ] Demo video plays correctly
- [ ] Screenshots show complete workflow
- [ ] Documentation is comprehensive

### **✅ Prize Category Evidence**

- [ ] Amazon Q Business: Real API integration confirmed
- [ ] Nova Models: Real multimodal reasoning demonstrated
- [ ] Bedrock AgentCore: Complete multi-agent system
- [ ] Additional AI Services: Multiple services integrated

## 🏆 **Expected Judge Experience**

### **30-Second Quick Test**

1. Click live AWS URL: `https://h8xlzr74h8.execute-api.us-east-1.amazonaws.com/real-aws-ai/prize-eligibility`
2. Verify real AWS AI services are integrated
3. Confirm prize eligibility for multiple categories

### **3-Minute Deep Test**

1. Test Amazon Q Business integration
2. Test Nova Models reasoning
3. Verify comprehensive AI orchestration
4. Check system performance and reliability

### **Complete Evaluation**

1. Review HD demo video
2. Examine technical documentation
3. Test both live AWS and local deployment
4. Verify business impact claims

## 📞 **Judge Support**

### **If Issues Occur**

- **Live AWS URL not responding**: Try local setup as backup
- **Local setup issues**: Use live AWS URL as primary
- **API errors**: Check fallback responses (system designed to handle AWS outages)
- **Questions**: Complete documentation available in repository

### **Contact Information**

- **Repository**: Complete source code and documentation
- **Demo Video**: HD recording showing full capabilities
- **Live System**: Always available at AWS URL
- **Fallback**: Local setup instructions provided

---

## 🎉 **Judge Testing Summary**

**Primary Testing Method**: Live AWS URL (30 seconds)  
**Backup Method**: Local setup (3 minutes)  
**Prize Verification**: Real AWS AI service integrations confirmed  
**Documentation**: Comprehensive guides and evidence provided

**Status**: ✅ **READY FOR IMMEDIATE JUDGE EVALUATION**

Judges can verify your real AWS AI integrations and prize eligibility in under 30 seconds using the live deployment, with local setup as a backup option.
