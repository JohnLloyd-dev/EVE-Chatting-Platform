# 🚀 EVE Chatting Platform - Deployment Guide

## 📋 **Overview**

This guide covers deploying the fully integrated EVE Chatting Platform where the AI model is now part of the backend service, eliminating the need for a separate AI server.

## 🏗️ **Architecture Changes**

### **Before (Separate Services)**

```
Frontend → Backend → AI Server (separate container)
```

### **After (Integrated)**

```
Frontend → Backend (with AI model inside) → No external calls needed
```

## 🚀 **Deployment Steps**

### **Step 1: Pull Latest Changes**

```bash
cd ~/EVE-Chatting-Platform
git pull origin main
```

### **Step 2: Verify Integration Files**

Ensure these files exist and are updated:

- ✅ `backend/ai_model_manager.py` - AI model integration
- ✅ `backend/main.py` - AI endpoints added
- ✅ `backend/config.py` - AI configuration updated
- ✅ `docker-compose.yml` - AI server removed, volumes added
- ✅ `frontend/components/AIModelStatus.tsx` - AI status component
- ✅ `frontend/lib/api.ts` - AI endpoints integrated

### **Step 3: Rebuild Backend with AI Dependencies**

```bash
# Stop services
docker-compose down

# Rebuild backend with new AI dependencies
docker-compose build backend

# Start services
docker-compose up -d
```

### **Step 4: Monitor Backend Startup**

```bash
# Watch backend logs for AI model loading
docker-compose logs -f backend
```

**Expected Output:**

```
🚀 Loading AI model: teknium/OpenHermes-2.5-Mistral-7B
✅ Model loaded on GPU: cuda:0
✅ AI Model loaded successfully!
```

### **Step 5: Test AI Integration**

```bash
# Test AI health endpoint
curl http://localhost:8001/ai/health

# Expected response:
{
  "model_name": "teknium/OpenHermes-2.5-Mistral-7B",
  "device": "cuda:0",
  "status": "ready",
  "gpu_memory_allocated": "2.1",
  "gpu_memory_reserved": "3.2"
}
```

### **Step 6: Test Frontend**

```bash
# Rebuild frontend
docker-compose build frontend
docker-compose up -d frontend

# Check frontend logs
docker-compose logs -f frontend
```

## 🔧 **Configuration Details**

### **Backend AI Configuration**

```python
# backend/config.py
ai_model_name: str = "teknium/OpenHermes-2.5-Mistral-7B"
ai_model_cache_dir: str = "/app/.cache/huggingface"
ai_generation_timeout: float = 30.0
ai_request_timeout: float = 60.0
```

### **Docker Compose Changes**

```yaml
backend:
  environment:
    - TRANSFORMERS_CACHE=/app/.cache/huggingface
    - HF_HOME=/app/.cache/huggingface
  volumes:
    - ai_model_cache:/app/.cache/huggingface

volumes:
  ai_model_cache: # Persistent AI model storage
```

### **AI Endpoints**

- `POST /ai/init-session` - Initialize AI chat session
- `POST /ai/chat` - Send message and get AI response
- `GET /ai/health` - AI model health status
- `POST /ai/optimize-memory` - Optimize GPU memory

## 🧪 **Testing the Integration**

### **1. Run Integration Tests**

```bash
python test_integration.py
```

**Expected Results:**

```
✅ Backend Health
✅ AI Model Health
✅ AI Session Init
✅ AI Chat
✅ AI Memory Optimization
✅ Legacy Endpoints
```

### **2. Manual Testing**

```bash
# Test session creation
curl -X POST http://localhost:8001/ai/init-session \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test123", "system_prompt": "You are a helpful assistant"}'

# Test chat
curl -X POST http://localhost:8001/ai/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test123", "message": "Hello!", "max_tokens": 100}'
```

### **3. Frontend Testing**

1. Open `http://your-vps-ip:3000`
2. Start a new chat session
3. Verify AI responses appear immediately (no polling)
4. Check admin dashboard for AI Model Status panel

## 📊 **Monitoring & Debugging**

### **Backend Logs**

```bash
# Real-time backend logs
docker-compose logs -f backend

# AI-specific logs
docker-compose logs backend | grep -E "(AI|Model|GPU)"
```

### **AI Model Status**

```bash
# Check AI health
curl http://localhost:8001/ai/health

# Check GPU memory
nvidia-smi
```

### **Common Issues & Solutions**

#### **Issue: AI Model Not Loading**

```bash
# Check if model cache exists
docker-compose exec backend ls -la /app/.cache/huggingface

# Check GPU availability
docker-compose exec backend python -c "import torch; print(torch.cuda.is_available())"
```

#### **Issue: Out of Memory**

```bash
# Optimize memory
curl -X POST http://localhost:8001/ai/optimize-memory

# Check GPU memory
nvidia-smi
```

#### **Issue: Frontend Can't Connect to AI**

```bash
# Verify backend is running
docker-compose ps

# Check backend logs
docker-compose logs backend | tail -20
```

## 🔄 **Rollback Plan**

If issues occur, you can rollback to the previous version:

```bash
# Stop services
docker-compose down

# Checkout previous version
git checkout HEAD~1

# Rebuild and restart
docker-compose build
docker-compose up -d
```

## 📈 **Performance Expectations**

### **Response Times**

- **Before**: 4-6 seconds (with HTTP overhead)
- **After**: 2-4 seconds (direct model access)

### **Memory Usage**

- **GPU Memory**: ~3-4 GB for model
- **System Memory**: ~2-3 GB additional
- **Total**: ~5-7 GB for full AI functionality

### **Concurrent Users**

- **Single Model**: 1-2 concurrent conversations
- **Multiple Models**: 2-4 concurrent conversations (future enhancement)

## 🚀 **Future Enhancements**

### **Multiple AI Models**

```yaml
# Future docker-compose.yml
backend-ai-1:
  build: ./backend
  environment:
    - AI_MODEL_INSTANCE=1
    - AI_MODEL_NAME=model1

backend-ai-2:
  build: ./backend
  environment:
    - AI_MODEL_INSTANCE=2
    - AI_MODEL_NAME=model2
```

### **Load Balancing**

- Round-robin between model instances
- Health-based routing
- Performance monitoring

## ✅ **Deployment Checklist**

- [ ] Git repository updated
- [ ] Backend rebuilt with AI dependencies
- [ ] Services restarted
- [ ] AI model loaded successfully
- [ ] AI endpoints responding
- [ ] Frontend rebuilt and working
- [ ] Chat interface functional
- [ ] Admin dashboard updated
- [ ] Integration tests passing
- [ ] Performance verified

## 🆘 **Support & Troubleshooting**

### **Log Locations**

- **Backend**: `docker-compose logs backend`
- **Frontend**: `docker-compose logs frontend`
- **Database**: `docker-compose logs postgres`

### **Useful Commands**

```bash
# Restart specific service
docker-compose restart backend

# Check service status
docker-compose ps

# View all logs
docker-compose logs

# Access backend shell
docker-compose exec backend bash
```

---

**🎯 Ready to deploy? Follow the steps above and enjoy your integrated EVE Chatting Platform!**
