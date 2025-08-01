# Custom AI Server Deployment Guide

This guide explains how to deploy your custom AI server (`custom_server.py`) using Docker on a VPS with GPU support.

## Prerequisites

### VPS Requirements

- **Memory**: At least 16GB RAM (32GB+ recommended for 7B model)
- **GPU**: NVIDIA GPU with at least 8GB VRAM (for 4-bit quantization)
- **Storage**: At least 50GB free space
- **OS**: Ubuntu 20.04+ or similar Linux distribution

### Software Requirements

- Docker
- Docker Compose
- NVIDIA Docker runtime (for GPU support)

## Installation Steps

### 1. Install Docker

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

### 2. Install Docker Compose

```bash
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 3. Install NVIDIA Docker (for GPU support)

```bash
# Add NVIDIA package repositories
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

# Install nvidia-docker2
sudo apt-get update
sudo apt-get install -y nvidia-docker2

# Restart Docker daemon
sudo systemctl restart docker
```

### 4. Deploy the Application

```bash
# Clone your repository
git clone <your-repo-url>
cd eve

# Run the deployment script
./deploy-custom-ai.sh
```

## Manual Deployment

If you prefer manual deployment:

### 1. Build the Custom AI Server

```bash
docker-compose -f docker-compose.prod.yml build custom-ai-server
```

### 2. Start the Service

```bash
docker-compose -f docker-compose.prod.yml up -d custom-ai-server
```

### 3. Check Status

```bash
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs -f custom-ai-server
```

## Configuration

### Environment Variables

Create a `.env.prod` file with:

```env
# AI Model Configuration
AI_MODEL_URL=http://custom-ai-server:8000
AI_MODEL_AUTH_USERNAME=adam
AI_MODEL_AUTH_PASSWORD=eve2025

# GPU Configuration
CUDA_VISIBLE_DEVICES=0
```

### Port Configuration

- **8002**: Custom AI Server (external access)
- **8000**: Internal container port

## Usage

### Access Points

- **Chat Interface**: `http://your-vps-ip:8002/`
- **Test Interface**: `http://your-vps-ip:8002/test-bot`

### API Endpoints

- **POST /scenario**: Set conversation scenario
- **POST /chat**: Send chat messages
- **POST /tally-scenario**: Webhook for Tally form integration

### Authentication

- **Username**: adam
- **Password**: eve2025

## Monitoring

### Check Logs

```bash
docker-compose -f docker-compose.prod.yml logs -f custom-ai-server
```

### Monitor Resource Usage

```bash
docker stats custom-ai-server
nvidia-smi  # GPU usage
```

### Health Check

```bash
curl http://localhost:8002/
```

## Troubleshooting

### Common Issues

#### 1. Out of Memory

- Reduce model size or use CPU-only mode
- Increase swap space
- Use smaller batch sizes

#### 2. GPU Not Detected

```bash
# Check NVIDIA drivers
nvidia-smi

# Check Docker GPU support
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
```

#### 3. Model Download Issues

- Ensure internet connectivity
- Check Hugging Face model availability
- Verify disk space

#### 4. Port Conflicts

```bash
# Check port usage
sudo netstat -tulpn | grep :8002

# Change port in docker-compose.prod.yml if needed
```

### Performance Optimization

#### 1. GPU Memory Optimization

- Adjust `load_in_4bit` settings
- Modify `max_tokens` limits
- Use gradient checkpointing

#### 2. CPU Optimization

- Set appropriate thread counts
- Use CPU-only mode if GPU unavailable

## Scaling

### Multiple GPUs

Modify docker-compose.prod.yml:

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: all # Use all GPUs
          capabilities: [gpu]
```

### Load Balancing

Use nginx to distribute requests across multiple instances.

## Security

### Firewall Configuration

```bash
# Allow only necessary ports
sudo ufw allow 8002/tcp
sudo ufw enable
```

### SSL/TLS Setup

Configure nginx with SSL certificates for HTTPS access.

## Backup and Recovery

### Backup Configuration

```bash
# Backup docker-compose and env files
tar -czf eve-config-backup.tar.gz docker-compose.prod.yml .env.prod
```

### Recovery

```bash
# Restore and redeploy
tar -xzf eve-config-backup.tar.gz
./deploy-custom-ai.sh
```

## Support

For issues or questions:

1. Check the logs first
2. Verify system requirements
3. Test with smaller models if memory issues occur
4. Ensure all dependencies are installed correctly
