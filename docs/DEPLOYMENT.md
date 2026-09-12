# BlackSentinel Pulse - Deployment Guide

## Table of Contents
1. [Deployment Options](#deployment-options)
2. [Quick Start (Docker)](#quick-start)
3. [Production Deployment](#production-deployment)
4. [Kubernetes / Helm](#kubernetes)
5. [Cloud Deployment](#cloud-deployment)
6. [Multi-Tenant Setup](#multi-tenant)
7. [Security Configuration](#security)
8. [Monitoring & Observability](#monitoring)
9. [API Reference](#api-reference)
10. [Delivery Models](#delivery-models)

---

## Deployment Options

| Method | Best For | Time | Complexity |
|--------|----------|------|------------|
| Docker Compose | Single server, POC, small orgs | 5 min | Low |
| Manual Install | Development, customization | 30 min | Medium |
| Kubernetes/Helm | Enterprise, scaling, HA | 1 hour | High |
| Cloud Managed | Production, compliance | 1-2 hours | Medium |

---

## Quick Start

```bash
# Clone the repository
git clone https://github.com/blacksentinel/pulse.git
cd pulse

# One-command setup
bash setup.sh

# Access:
# Frontend: http://localhost:3000
# API: http://localhost:8000/api/docs
# Login: admin / admin123
```

---

## Production Deployment

### Prerequisites
- Linux server (Ubuntu 22.04+ recommended)
- Docker 24+ and Docker Compose v2
- 8GB+ RAM, 4+ CPU cores, 100GB+ storage
- Domain name with DNS configured

### Steps

1. **Server Setup**
```bash
# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Clone project
sudo mkdir -p /opt/blacksentinel-pulse
sudo git clone https://github.com/blacksentinel/pulse.git /opt/blacksentinel-pulse
cd /opt/blacksentinel-pulse
```

2. **Configure Environment**
```bash
cp config/envs/.env.production .env
nano .env
# Set: SECRET_KEY, DATABASE passwords, API keys, domain
```

3. **Deploy**
```bash
chmod +x deploy/scripts/deploy.sh
./deploy/scripts/deploy.sh deploy
```

4. **SSL/TLS (Optional)**
```bash
# Using Certbot
sudo apt install certbot
sudo certbot certonly --standalone -d pulse.yourdomain.com

# Copy certs
mkdir -p deploy/ssl
sudo cp /etc/letsencrypt/live/pulse.yourdomain.com/fullchain.pem deploy/ssl/
sudo cp /etc/letsencrypt/live/pulse.yourdomain.com/privkey.pem deploy/ssl/
```

---

## Kubernetes

### Prerequisites
- Kubernetes 1.27+
- Helm 3.12+
- kubectl configured

### Install
```bash
# Add Helm repo
helm repo add blacksentinel https://charts.blacksentinel.com
helm repo update

# Create namespace
kubectl create namespace blacksentinel-pulse

# Create secrets
kubectl create secret generic blacksentinel-pulse-secrets \
  --namespace blacksentinel-pulse \
  --from-literal=secret-key=$(openssl rand -hex 32) \
  --from-literal=database-url='postgresql+asyncpg://pulse:PASSWORD@postgres:5432/blacksentinel_pulse' \
  --from-literal=redis-url='redis://redis:6379/0' \
  --from-literal=neo4j-password='YOUR_NEO4J_PASSWORD'

# Install
helm install blacksentinel-pulse ./deploy/helm/blacksentinel-pulse \
  --namespace blacksentinel-pulse \
  --set env.secretKey=YOUR_SECRET_KEY \
  --set env.databaseUrl='postgresql+asyncpg://pulse:PASSWORD@postgres:5432/blacksentinel_pulse' \
  --set env.redisUrl='redis://redis:6379/0' \
  --set env.neo4jPassword='YOUR_NEO4J_PASSWORD'
```

---

## Cloud Deployment

### AWS (ECS/Fargate)
```bash
# Using AWS CDK or CloudFormation
# See /deploy/cloudformation/ for templates
```

### Azure (Container Apps)
```bash
# Using Azure Bicep
# See /deploy/azure/ for templates
```

### GCP (Cloud Run)
```bash
# Using gcloud
gcloud run deploy blacksentinel-pulse \
  --image ghcr.io/blacksentinel/pulse/backend:latest \
  --port 8000 \
  --memory 2Gi \
  --min-instances 1 \
  --max-instances 10
```

---

## Multi-Tenant

### Provision Organizations
```bash
cd backend

# Create organization
python provision.py create \
  --name "Acme Corporation" \
  --slug acme \
  --plan enterprise \
  --admin-email admin@acme.com

# List all organizations
python provision.py list

# Export organization data
python provision.py export --slug acme
```

### Tenant Plans

| Plan | Assets | Users | Scans/Day | Features |
|------|--------|-------|-----------|----------|
| Free | 100 | 3 | 10 | Basic discovery |
| Professional | 10,000 | 10 | 100 | Full ASM, API |
| Enterprise | 100,000 | 100 | 1,000 | All features, SSO, SLA |

---

## Security

### Environment Variables (Required)
```bash
SECRET_KEY=<random-64-char-hex>
POSTGRES_PASSWORD=<strong-password>
REDIS_PASSWORD=<strong-password>
NEO4J_PASSWORD=<strong-password>
ALLOWED_ORIGINS=https://pulse.yourdomain.com
ALLOWED_HOSTS=pulse.yourdomain.com
```

### Security Checklist
- [ ] Change all default passwords
- [ ] Generate strong SECRET_KEY
- [ ] Enable HTTPS/TLS
- [ ] Configure firewall (only 80/443 open)
- [ ] Set up database backups
- [ ] Enable audit logging
- [ ] Configure rate limiting
- [ ] Set up monitoring alerts

---

## Monitoring

### Endpoints
- Health: `GET /api/v1/health`
- Readiness: `GET /api/v1/health/ready`
- Metrics: `GET /api/v1/metrics` (Prometheus format)

### Grafana Dashboards
- Backend performance
- Discovery engine stats
- Vulnerability trends
- Alert response times

---

## API Reference

Full API documentation available at: `http://your-domain/api/docs`

### Key Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/login` | POST | Authenticate |
| `/api/v1/assets` | GET | List assets |
| `/api/v1/scans` | POST | Start scan |
| `/api/v1/vulnerabilities` | GET | List vulns |
| `/api/v1/alerts` | GET | List alerts |
| `/api/v1/discovery/start` | POST | Start discovery |
| `/api/v1/graph/overview` | GET | Attack surface graph |
| `/api/v1/threat-intel` | GET | Threat intelligence |
| `/api/v1/reports/executive` | GET | Executive report |

---

## Delivery Models

See [DELIVERY_MODELS.md](./DELIVERY_MODELS.md) for detailed options on how to
deliver BlackSentinel Pulse to organizations.
