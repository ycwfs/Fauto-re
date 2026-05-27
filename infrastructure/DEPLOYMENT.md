# Deployment Guide

This guide covers deploying Full-Auto-Research to production using Kubernetes on DigitalOcean.

## Prerequisites

- DigitalOcean account with billing enabled
- `doctl` CLI installed and configured
- `kubectl` installed
- Docker installed locally
- Domain name configured (optional but recommended)

## Infrastructure Setup

### 1. Create Kubernetes Cluster

```bash
# Create cluster with 3 worker nodes
doctl kubernetes cluster create full-auto-research \
  --region nyc1 \
  --version 1.28.2-do.0 \
  --node-pool "name=worker-pool;size=s-2vcpu-4gb;count=3;auto-scale=true;min-nodes=2;max-nodes=5"

# Configure kubectl
doctl kubernetes cluster kubeconfig save full-auto-research
```

### 2. Create Managed Databases

```bash
# PostgreSQL
doctl databases create full-auto-research-db \
  --engine pg \
  --version 16 \
  --region nyc1 \
  --size db-s-2vcpu-4gb \
  --num-nodes 1

# Redis
doctl databases create full-auto-research-redis \
  --engine redis \
  --version 7 \
  --region nyc1 \
  --size db-s-1vcpu-1gb \
  --num-nodes 1

# Get connection strings
doctl databases connection full-auto-research-db
doctl databases connection full-auto-research-redis
```

### 3. Create Container Registry

```bash
# Create registry
doctl registry create full-auto-research

# Login to registry
doctl registry login
```

### 4. Create Spaces (Object Storage)

```bash
# Create space for user data
doctl spaces create full-auto-research-data --region nyc3
```

## Application Deployment

### 1. Create Kubernetes Namespace

```bash
kubectl create namespace production
```

### 2. Create Secrets

```bash
# Database and Redis URLs from step 2
export DATABASE_URL="postgresql://user:pass@host:port/db?sslmode=require"
export REDIS_URL="rediss://default:pass@host:port"

# Generate secret key
export SECRET_KEY=$(openssl rand -hex 32)

# Stripe keys (from Stripe dashboard)
export STRIPE_SECRET_KEY="sk_live_..."
export STRIPE_WEBHOOK_SECRET="whsec_..."

# Create Kubernetes secret
kubectl create secret generic app-secrets \
  --from-literal=database-url="$DATABASE_URL" \
  --from-literal=redis-url="$REDIS_URL" \
  --from-literal=secret-key="$SECRET_KEY" \
  --from-literal=stripe-secret-key="$STRIPE_SECRET_KEY" \
  --from-literal=stripe-webhook-secret="$STRIPE_WEBHOOK_SECRET" \
  -n production
```

### 3. Build and Push Docker Images

```bash
# Backend
cd backend
docker build -t registry.digitalocean.com/full-auto-research/backend:latest .
docker push registry.digitalocean.com/full-auto-research/backend:latest

# Frontend
cd ../frontend
docker build -f Dockerfile.prod -t registry.digitalocean.com/full-auto-research/frontend:latest .
docker push registry.digitalocean.com/full-auto-research/frontend:latest
```

### 4. Deploy to Kubernetes

```bash
# Apply all manifests
kubectl apply -f infrastructure/k8s/ -n production

# Verify deployments
kubectl get pods -n production
kubectl get services -n production
kubectl get ingress -n production
```

### 5. Run Database Migrations

```bash
# Get backend pod name
BACKEND_POD=$(kubectl get pods -n production -l app=full-auto-research,component=backend -o jsonpath='{.items[0].metadata.name}')

# Run migrations
kubectl exec -it $BACKEND_POD -n production -- alembic upgrade head
```

## DNS Configuration

### 1. Get Load Balancer IP

```bash
kubectl get ingress full-auto-research-ingress -n production -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
```

### 2. Configure DNS Records

Add A records in your DNS provider:
- `full-auto-research.com` → Load Balancer IP
- `api.full-auto-research.com` → Load Balancer IP

### 3. Wait for SSL Certificate

```bash
# Check certificate status
kubectl get certificate -n production
kubectl describe certificate full-auto-research-tls -n production
```

## CI/CD Setup

### 1. Configure GitHub Secrets

In your GitHub repository settings, add these secrets:
- `DIGITALOCEAN_ACCESS_TOKEN` - DigitalOcean API token
- `CLUSTER_NAME` - `full-auto-research`

### 2. Verify CI/CD Pipeline

```bash
# Push to main branch triggers deployment
git push origin main

# Monitor deployment
kubectl rollout status deployment/backend -n production
kubectl rollout status deployment/frontend -n production
```

## Monitoring Setup

### 1. Install Prometheus

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace
```

### 2. Access Grafana

```bash
# Get Grafana password
kubectl get secret -n monitoring prometheus-grafana -o jsonpath="{.data.admin-password}" | base64 --decode

# Port forward
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80

# Access at http://localhost:3000
# Username: admin
# Password: (from above)
```

### 3. Configure Dashboards

Import these dashboard IDs in Grafana:
- 315 - Kubernetes cluster monitoring
- 6417 - Kubernetes pod monitoring
- 1860 - Node exporter

## Backup Strategy

### 1. Database Backups

```bash
# DigitalOcean automatically backs up managed databases daily
# Configure backup retention
doctl databases backups list full-auto-research-db
```

### 2. User Data Backups

```bash
# Set up automated backups to Spaces
# Configure in backend/.env:
BACKUP_ENABLED=true
BACKUP_SCHEDULE="0 2 * * *"  # Daily at 2 AM
BACKUP_RETENTION_DAYS=30
```

## Scaling

### 1. Horizontal Pod Autoscaling

```bash
# Backend autoscaling
kubectl autoscale deployment backend \
  --cpu-percent=70 \
  --min=3 \
  --max=10 \
  -n production

# Celery worker autoscaling
kubectl autoscale deployment celery-worker \
  --cpu-percent=80 \
  --min=2 \
  --max=8 \
  -n production
```

### 2. Cluster Autoscaling

Already configured with `--auto-scale` flag during cluster creation.

## Troubleshooting

### Check Pod Logs

```bash
# Backend logs
kubectl logs -f deployment/backend -n production

# Celery worker logs
kubectl logs -f deployment/celery-worker -n production

# Frontend logs
kubectl logs -f deployment/frontend -n production
```

### Check Pod Status

```bash
kubectl get pods -n production
kubectl describe pod <pod-name> -n production
```

### Database Connection Issues

```bash
# Test database connection
kubectl run -it --rm debug --image=postgres:16 --restart=Never -n production -- \
  psql "$DATABASE_URL"
```

### Redis Connection Issues

```bash
# Test Redis connection
kubectl run -it --rm debug --image=redis:7 --restart=Never -n production -- \
  redis-cli -u "$REDIS_URL"
```

## Security Hardening

### 1. Network Policies

```bash
kubectl apply -f infrastructure/k8s/network-policies.yaml -n production
```

### 2. Pod Security Standards

```bash
kubectl label namespace production pod-security.kubernetes.io/enforce=restricted
```

### 3. Enable Audit Logging

Configure in DigitalOcean dashboard:
- Kubernetes → Cluster → Settings → Audit Logging

## Cost Optimization

### Current Estimated Costs (Monthly)

- Kubernetes cluster (3 nodes): ~$72
- PostgreSQL (2vCPU, 4GB): ~$60
- Redis (1vCPU, 1GB): ~$15
- Load Balancer: ~$12
- Spaces (100GB): ~$5
- Container Registry: ~$5
- **Total: ~$169/month**

### Optimization Tips

1. Use spot instances for non-critical workloads
2. Enable cluster autoscaling to scale down during low usage
3. Use smaller database instances for development
4. Set up budget alerts in DigitalOcean

## Maintenance

### Update Application

```bash
# Update backend
docker build -t registry.digitalocean.com/full-auto-research/backend:v1.1.0 backend/
docker push registry.digitalocean.com/full-auto-research/backend:v1.1.0
kubectl set image deployment/backend backend=registry.digitalocean.com/full-auto-research/backend:v1.1.0 -n production

# Update frontend
docker build -f frontend/Dockerfile.prod -t registry.digitalocean.com/full-auto-research/frontend:v1.1.0 frontend/
docker push registry.digitalocean.com/full-auto-research/frontend:v1.1.0
kubectl set image deployment/frontend frontend=registry.digitalocean.com/full-auto-research/frontend:v1.1.0 -n production
```

### Update Kubernetes

```bash
# Check available versions
doctl kubernetes options versions

# Upgrade cluster
doctl kubernetes cluster upgrade full-auto-research --version 1.29.0-do.0
```

## Disaster Recovery

### Restore from Backup

```bash
# Restore database
doctl databases backups list full-auto-research-db
doctl databases backups restore full-auto-research-db <backup-id>

# Restore user data from Spaces
# Use s3cmd or AWS CLI to restore from backup
```

### Rollback Deployment

```bash
# Rollback to previous version
kubectl rollout undo deployment/backend -n production
kubectl rollout undo deployment/frontend -n production
```

## Support

For deployment issues:
- Check logs: `kubectl logs -f deployment/<name> -n production`
- Check events: `kubectl get events -n production --sort-by='.lastTimestamp'`
- Contact support: support@full-auto-research.com
