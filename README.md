# InsightFlow - Adaptive Decision Intelligence Engine

InsightFlow is a cross-platform, self-learning intelligence layer that routes tasks and responses to the most suitable AI agent, continuously improving through analytics, feedback, and context signals.

## 🚀 Features

- **Intelligent Agent Routing**: Q-learning based adaptive routing with multiple strategies
- **API Versioning**: Dual v1/v2 support with seamless migration path
- **Enhanced Responses**: Alternative agents, metadata, and structured error handling (v2)
- **Batch Processing**: Process multiple requests simultaneously (v2)
- **Real-time Analytics**: Live performance monitoring and metrics visualization
- **Multi-Agent Support**: NLP, TTS, Computer Vision, and custom agent types
- **WebSocket Integration**: Real-time event streaming for instant updates
- **Performance Tracking**: Comprehensive feedback loop and learning system
- **Modern Dashboard**: React + TypeScript + Tailwind CSS admin interface
- **Production Ready**: Docker containerization with health checks
- **Migration Tools**: Built-in migration tracking and conversion utilities

## 📋 Prerequisites

- Docker & Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)
- Supabase account (for database)

## 🛠️ Installation & Setup

### 1. Clone Repository

```bash
git clone https://github.com/blackholeinfiverse54-creator/Insight_Flow.git
cd Insight_Flow
```

### 2. Configure Environment Variables

Create `.env` file in the root directory:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key

# JWT Configuration
JWT_SECRET_KEY=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256

# Application
ENVIRONMENT=production
DEBUG=False
```

### 3. Set Up Supabase Database

Run these SQL commands in your Supabase SQL editor:

```sql
-- Create agents table
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    capabilities JSONB DEFAULT '[]',
    performance_score FLOAT DEFAULT 0.5,
    success_rate FLOAT DEFAULT 0.5,
    average_latency FLOAT DEFAULT 0,
    total_requests INTEGER DEFAULT 0,
    successful_requests INTEGER DEFAULT 0,
    failed_requests INTEGER DEFAULT 0,
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create routing_logs table
CREATE TABLE routing_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id TEXT NOT NULL,
    user_id TEXT,
    input_type TEXT NOT NULL,
    input_data JSONB NOT NULL,
    selected_agent_id UUID REFERENCES agents(id),
    agent_name TEXT,
    confidence_score FLOAT,
    routing_reason TEXT,
    routing_strategy TEXT,
    status TEXT DEFAULT 'pending',
    execution_time_ms FLOAT,
    response_data JSONB,
    error_message TEXT,
    context JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create feedback_events table
CREATE TABLE feedback_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    routing_log_id UUID REFERENCES routing_logs(id),
    agent_id UUID REFERENCES agents(id),
    feedback_type TEXT NOT NULL,
    success BOOLEAN NOT NULL,
    latency_ms FLOAT NOT NULL,
    accuracy_score FLOAT,
    user_satisfaction INTEGER CHECK (user_satisfaction BETWEEN 1 AND 5),
    error_details TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create Q-learning table
CREATE TABLE q_learning_table (
    state TEXT NOT NULL,
    action TEXT NOT NULL,
    q_value FLOAT DEFAULT 0,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (state, action)
);

-- Create indexes
CREATE INDEX idx_routing_logs_created_at ON routing_logs(created_at DESC);
CREATE INDEX idx_routing_logs_agent_id ON routing_logs(selected_agent_id);
CREATE INDEX idx_feedback_agent_id ON feedback_events(agent_id);
CREATE INDEX idx_agents_status ON agents(status);

-- Insert sample agents
INSERT INTO agents (name, type, status, tags, capabilities) VALUES
('NLP Processor', 'nlp', 'active', ARRAY['text', 'classification'], 
 '[{"name": "text_classification", "description": "Classify text", "confidence_threshold": 0.8}]'::jsonb),
('TTS Generator', 'tts', 'active', ARRAY['audio', 'speech'], 
 '[{"name": "text_to_speech", "description": "Convert text to audio", "confidence_threshold": 0.7}]'::jsonb),
('Vision Analyzer', 'computer_vision', 'active', ARRAY['image', 'detection'], 
 '[{"name": "object_detection", "description": "Detect objects in images", "confidence_threshold": 0.75}]'::jsonb);
```

### 4. Build and Run with Docker Compose

```bash
# Build and start all services
docker-compose up --build

# Run in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 5. Access the Application

- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 🧪 Local Development

### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build
```

## 📚 API Usage Examples

### Route a Request (v2 Enhanced)

```bash
curl -X POST http://localhost:8000/api/v2/routing/route \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Accept-Version: v2" \
  -d '{
    "input_data": {"text": "What is the weather today?"},
    "input_type": "text",
    "strategy": "q_learning",
    "context": {
      "priority": "high",
      "domain": "weather"
    },
    "preferences": {
      "max_latency_ms": 500,
      "min_confidence": 0.8
    }
  }'
```

### Batch Processing (v2 Only)

```bash
curl -X POST http://localhost:8000/api/v2/routing/batch \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Accept-Version: v2" \
  -d '{
    "requests": [
      {"input_data": {"text": "Query 1"}, "input_type": "text"},
      {"input_data": {"text": "Query 2"}, "input_type": "text"}
    ],
    "strategy": "q_learning"
  }'
```

### Submit Feedback

```bash
curl -X POST http://localhost:8000/api/v2/routing/feedback \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Accept-Version: v2" \
  -d '{
    "routing_log_id": "log_123",
    "success": true,
    "latency_ms": 145.5,
    "accuracy_score": 0.88,
    "user_satisfaction": 4
  }'
```

### Get Analytics

```bash
curl http://localhost:8000/api/v1/analytics/overview?time_range=24h \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Migration Status

```bash
curl http://localhost:8000/api/migration/status \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 🧪 Testing

### Backend Tests

```bash
cd backend
pytest tests/ -v
```

### Frontend Tests

```bash
cd frontend
npm run test
```

## 🚀 Deployment

### Deploy to Cloud Platforms

#### AWS ECS

```bash
# Build and push Docker images to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ECR_URL
docker build -t insightflow-backend ./backend
docker tag insightflow-backend:latest YOUR_ECR_URL/insightflow-backend:latest
docker push YOUR_ECR_URL/insightflow-backend:latest
```

#### Kubernetes

```bash
# Apply Kubernetes configurations
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
```

#### Render/Railway

1. Connect your GitHub repository
2. Set environment variables
3. Deploy with automatic builds

## 📊 System Architecture

```
User Request → API Version Detection → Enhanced Decision Engine → Agent Selection
                        ↓                           ↓
                Migration Tracking              Q-Learning Router
                        ↓                           ↓
                Analytics Dashboard         Selected Agent + Alternatives
                                                    ↓
                                            Feedback Collection
                                                    ↓
                                      Performance Metrics Update
                                                    ↓
                                          Q-Table Update (Learning)
```

## 🔄 API Migration

InsightFlow supports both v1 (legacy) and v2 (enhanced) APIs:

- **Current**: Both versions available with backward compatibility
- **30 days**: v1 deprecation warnings
- **60 days**: v1 removal

### Migration Resources
- **Migration Guide**: [docs/MIGRATION_GUIDE.md](docs/MIGRATION_GUIDE.md)
- **API Versioning**: [docs/API_VERSIONING.md](docs/API_VERSIONING.md)
- **Migration Status**: `GET /api/migration/status`
- **Conversion Tools**: `POST /api/migration/convert/request`

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📝 License

MIT License - see LICENSE file for details

## 👥 Team

- **Lead Developer**: Ashmit
- **Analytics Core**: Nisarg
- **Infrastructure**: Bucket Team

## 📧 Support

For support, email support@insightflow.ai or open an issue on GitHub.

---

**Built with ❤️ using FastAPI, React, Supabase, and Q-Learning**

## 🎯 Quick Start Commands Summary

```bash
# Complete setup in 3 commands
git clone https://github.com/blackholeinfiverse54-creator/Insight_Flow.git
cd Insight_Flow
cp .env.example .env  # Edit with your Supabase credentials
docker-compose up --build

# Access at http://localhost:3000
```

## 📦 Project Size & Complexity

- **Backend**: ~25 files, ~3500 lines of Python
- **Frontend**: ~12 files, ~1200 lines of TypeScript/React
- **Documentation**: Comprehensive migration and API guides
- **Total**: Production-ready full-stack application with migration support
- **Build Time**: ~5 minutes
- **Deployment Time**: ~10 minutes
- **Migration**: Automated tracking and conversion tools

---

**Ready to deploy! 🚀**
