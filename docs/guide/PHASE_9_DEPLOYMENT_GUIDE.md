# 🚀 Phase 9: Deployment - Learning Guide

**What You'll Learn:**
- Cloud deployment platforms
- Deploying to Railway
- Deploying to Render
- Deploying to AWS/GCP/Azure
- CI/CD with GitHub Actions
- Domain and SSL setup
- Database migration in production
- Monitoring and logging in production
- Rollback strategies

---

## 🎯 Deployment Options

### Platform Comparison

| Platform | Pros | Cons | Best For |
|----------|------|------|----------|
| **Railway** | ✅ Easy setup<br>✅ Free tier<br>✅ Auto SSL<br>✅ GitHub integration | ❌ Limited free tier<br>❌ Can get expensive | Small projects, demos |
| **Render** | ✅ Free PostgreSQL<br>✅ Auto SSL<br>✅ Simple pricing | ❌ Cold starts on free tier<br>❌ Limited customization | Startups, MVPs |
| **Heroku** | ✅ Very easy<br>✅ Lots of addons | ❌ Expensive<br>❌ Less control | Quick deploys |
| **AWS ECS** | ✅ Full control<br>✅ Scalable<br>✅ Many services | ❌ Complex setup<br>❌ Steep learning curve | Large applications |
| **DigitalOcean** | ✅ Good pricing<br>✅ Simple VPS | ❌ Manual setup<br>❌ Need DevOps skills | Custom setups |
| **GCP Cloud Run** | ✅ Pay per use<br>✅ Scales to zero<br>✅ Fast deploys | ❌ Cold starts<br>❌ GCP ecosystem lock-in | Serverless apps |

---

## 🚂 Deploying to Railway

### Why Railway?

- ✅ Easiest deployment
- ✅ Free tier (500 hours/month)
- ✅ Automatic HTTPS
- ✅ Built-in PostgreSQL and Redis
- ✅ GitHub integration

### Step-by-Step Railway Deployment

**1. Prepare Your Code**

Create `railway.json` in project root:
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "startCommand": "gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 100,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

**2. Create Railway Project**

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Link to GitHub repo
railway link
```

**3. Add Database**

In Railway dashboard:
- Click "New Service"
- Select "PostgreSQL"
- Note the connection URL

**4. Add Redis**

- Click "New Service"
- Select "Redis"
- Note the connection URL

**5. Set Environment Variables**

```bash
# In Railway dashboard or CLI
railway variables set SECRET_KEY="your-secret-key"
railway variables set DATABASE_URL="${{Postgres.DATABASE_URL}}"
railway variables set REDIS_URL="${{Redis.REDIS_URL}}"
railway variables set ENVIRONMENT="production"
railway variables set LOG_LEVEL="INFO"
```

**6. Deploy**

```bash
# Deploy from CLI
railway up

# Or connect GitHub repo for automatic deploys
# Every push to main branch will auto-deploy
```

**7. Run Migrations**

```bash
# Run migrations in Railway
railway run alembic upgrade head
```

**8. Get Your URL**

```bash
# Generate domain
railway domain

# Your app is live at: https://your-app-production.up.railway.app
```

### Railway Configuration Tips

**Dockerfile for Railway:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Railway provides $PORT environment variable
CMD gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:$PORT \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
```

**Common Issues:**

❌ **Port binding error**
```python
# Solution: Use Railway's $PORT
import os
port = int(os.getenv("PORT", 8000))
```

❌ **Database connection error**
```python
# Solution: Use DATABASE_URL from Railway
DATABASE_URL = os.getenv("DATABASE_URL")
```

❌ **Static files not found**
```python
# Solution: Set correct paths
UPLOAD_DIR = os.path.join(os.getcwd(), "models")
```

---

## 🎨 Deploying to Render

### Why Render?

- ✅ Free tier with PostgreSQL
- ✅ Automatic SSL
- ✅ Easy setup
- ✅ Good documentation

### Step-by-Step Render Deployment

**1. Create `render.yaml`**

```yaml
services:
  # Web service
  - type: web
    name: ml-platform-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
    healthCheckPath: /health
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: DATABASE_URL
        fromDatabase:
          name: ml-platform-db
          property: connectionString
      - key: SECRET_KEY
        generateValue: true
      - key: ENVIRONMENT
        value: production
      - key: LOG_LEVEL
        value: INFO
    
  # PostgreSQL database
databases:
  - name: ml-platform-db
    databaseName: mlplatform
    user: mlplatform_user
    plan: free  # Free tier: 256MB RAM, 1GB storage
```

**2. Connect to GitHub**

1. Go to https://dashboard.render.com
2. Click "New +"
3. Select "Blueprint"
4. Connect your GitHub repository
5. Render will detect `render.yaml` and configure everything

**3. Deploy**

- Render automatically deploys on every push to main
- First deploy takes ~5 minutes

**4. Run Migrations**

In Render dashboard:
1. Go to your service
2. Click "Shell"
3. Run: `alembic upgrade head`

**5. Access Your App**

Your app is live at: `https://your-app-name.onrender.com`

### Render Configuration Tips

**requirements.txt must include:**
```txt
gunicorn==21.2.0
uvicorn[standard]==0.24.0
```

**Environment variables:**
```env
# Render provides these automatically
PORT=10000
RENDER=true

# You need to set these
SECRET_KEY=your-secret-key
ENVIRONMENT=production
```

**Common Issues:**

❌ **Disk space error**
```bash
# Solution: Clean up in build command
pip install -r requirements.txt && pip cache purge
```

❌ **Cold starts on free tier**
```bash
# Solution: Upgrade to paid tier or use a keep-alive service
# Free tier spins down after 15 minutes of inactivity
```

---

## ☁️ Deploying to AWS (ECS + RDS)

### Architecture Overview

```
Internet
    ↓
[Application Load Balancer]
    ↓
[ECS Cluster]
    ├─ Task 1 (Docker container)
    ├─ Task 2 (Docker container)
    └─ Task 3 (Docker container)
    ↓
[RDS PostgreSQL]
[ElastiCache Redis]
[S3 for files]
```

### AWS Deployment Steps

**1. Build and Push Docker Image**

```bash
# Login to ECR (Elastic Container Registry)
aws ecr get-login-password --region us-east-1 | \
    docker login --username AWS --password-stdin \
    123456789.dkr.ecr.us-east-1.amazonaws.com

# Build image
docker build -t ml-platform .

# Tag for ECR
docker tag ml-platform:latest \
    123456789.dkr.ecr.us-east-1.amazonaws.com/ml-platform:latest

# Push to ECR
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/ml-platform:latest
```

**2. Create RDS Database**

```bash
# Using AWS CLI
aws rds create-db-instance \
    --db-instance-identifier ml-platform-db \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --engine-version 15.3 \
    --master-username postgres \
    --master-user-password YourSecurePassword123! \
    --allocated-storage 20 \
    --vpc-security-group-ids sg-xxxxx \
    --db-subnet-group-name my-db-subnet-group \
    --backup-retention-period 7 \
    --preferred-backup-window "03:00-04:00" \
    --preferred-maintenance-window "Mon:04:00-Mon:05:00" \
    --publicly-accessible false
```

**3. Create ECS Task Definition**

`task-definition.json`:
```json
{
  "family": "ml-platform-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "ml-platform-api",
      "image": "123456789.dkr.ecr.us-east-1.amazonaws.com/ml-platform:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "ENVIRONMENT",
          "value": "production"
        },
        {
          "name": "LOG_LEVEL",
          "value": "INFO"
        }
      ],
      "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789:secret:db-url"
        },
        {
          "name": "SECRET_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:123456789:secret:jwt-secret"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/ml-platform",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "api"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

**4. Create ECS Service**

```bash
aws ecs create-service \
    --cluster ml-platform-cluster \
    --service-name ml-platform-service \
    --task-definition ml-platform-task \
    --desired-count 2 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx,subnet-yyy],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \
    --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=ml-platform-api,containerPort=8000"
```

**5. Setup Auto Scaling**

```bash
# Register scalable target
aws application-autoscaling register-scalable-target \
    --service-namespace ecs \
    --resource-id service/ml-platform-cluster/ml-platform-service \
    --scalable-dimension ecs:service:DesiredCount \
    --min-capacity 2 \
    --max-capacity 10

# Create scaling policy (CPU-based)
aws application-autoscaling put-scaling-policy \
    --service-namespace ecs \
    --resource-id service/ml-platform-cluster/ml-platform-service \
    --scalable-dimension ecs:service:DesiredCount \
    --policy-name cpu-scaling-policy \
    --policy-type TargetTrackingScaling \
    --target-tracking-scaling-policy-configuration '{
        "TargetValue": 70.0,
        "PredefinedMetricSpecification": {
            "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
        },
        "ScaleOutCooldown": 60,
        "ScaleInCooldown": 60
    }'
```

### AWS Cost Estimation

**Monthly costs (approximate):**
- ECS Fargate (2 tasks, 0.5 vCPU, 1GB): ~$30
- RDS PostgreSQL (db.t3.micro): ~$15
- ElastiCache Redis (cache.t3.micro): ~$12
- Application Load Balancer: ~$20
- Data transfer: ~$10
- CloudWatch logs: ~$5
- **Total: ~$92/month**

---

## 🔄 CI/CD with GitHub Actions

### Continuous Deployment Workflow

**`.github/workflows/deploy.yml`:**
```yaml
name: Deploy to Production

on:
  push:
    branches:
      - main  # Deploy on push to main

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Run tests
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
          REDIS_URL: redis://localhost:6379
          SECRET_KEY: test-secret-key
        run: |
          pytest tests/ -v --cov=app --cov-report=term
      
      - name: Check code quality
        run: |
          pip install black flake8
          black --check app/
          flake8 app/ --max-line-length=100
  
  deploy:
    needs: test  # Only deploy if tests pass
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Deploy to Railway
        uses: bervProject/railway-deploy@main
        with:
          railway_token: ${{ secrets.RAILWAY_TOKEN }}
          service: ml-platform-api
      
      # Or deploy to Render
      # - name: Deploy to Render
      #   uses: johnbeynon/render-deploy-action@v0.0.8
      #   with:
      #     service-id: ${{ secrets.RENDER_SERVICE_ID }}
      #     api-key: ${{ secrets.RENDER_API_KEY }}
      
      # Or build and push to AWS ECR
      # - name: Configure AWS credentials
      #   uses: aws-actions/configure-aws-credentials@v2
      #   with:
      #     aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
      #     aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
      #     aws-region: us-east-1
      
      # - name: Login to Amazon ECR
      #   id: login-ecr
      #   uses: aws-actions/amazon-ecr-login@v1
      
      # - name: Build and push Docker image
      #   env:
      #     ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
      #     ECR_REPOSITORY: ml-platform
      #     IMAGE_TAG: ${{ github.sha }}
      #   run: |
      #     docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
      #     docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
      
      # - name: Update ECS service
      #   run: |
      #     aws ecs update-service \
      #       --cluster ml-platform-cluster \
      #       --service ml-platform-service \
      #       --force-new-deployment
  
  notify:
    needs: deploy
    runs-on: ubuntu-latest
    if: always()
    
    steps:
      - name: Send deployment notification
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          text: 'Deployment to production: ${{ job.status }}'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

### GitHub Secrets Setup

Add these secrets in GitHub repository settings:

```
Settings → Secrets and variables → Actions → New repository secret
```

**Required secrets:**
- `RAILWAY_TOKEN` - Get from Railway dashboard
- `RENDER_API_KEY` - Get from Render dashboard
- `RENDER_SERVICE_ID` - Your service ID
- `AWS_ACCESS_KEY_ID` - For AWS deployments
- `AWS_SECRET_ACCESS_KEY` - For AWS deployments
- `SLACK_WEBHOOK` - For notifications (optional)

---

## 🌐 Domain and SSL Setup

### Custom Domain on Railway

**1. Add Custom Domain**

In Railway dashboard:
1. Go to your service
2. Click "Settings"
3. Click "Domains"
4. Click "Add Domain"
5. Enter your domain: `api.yourdomain.com`

**2. Configure DNS**

Add CNAME record in your DNS provider:
```
Type: CNAME
Name: api
Value: your-app.up.railway.app
TTL: 3600
```

**3. SSL Certificate**

Railway automatically provisions Let's Encrypt SSL certificates.

### Custom Domain on Render

**1. Add Custom Domain**

In Render dashboard:
1. Go to your service
2. Click "Settings"
3. Scroll to "Custom Domains"
4. Click "Add Custom Domain"
5. Enter your domain

**2. Configure DNS**

Add CNAME record:
```
Type: CNAME
Name: api
Value: your-app.onrender.com
```

**3. SSL Certificate**

Render automatically provisions SSL certificates.

### Custom Domain on AWS

**1. Create Route 53 Hosted Zone**

```bash
aws route53 create-hosted-zone \
    --name yourdomain.com \
    --caller-reference $(date +%s)
```

**2. Request SSL Certificate (ACM)**

```bash
aws acm request-certificate \
    --domain-name yourdomain.com \
    --subject-alternative-names *.yourdomain.com \
    --validation-method DNS \
    --region us-east-1
```

**3. Add DNS Validation Records**

AWS will provide CNAME records to add to your DNS.

**4. Configure Load Balancer**

Add HTTPS listener with SSL certificate to your Application Load Balancer.

---

## 📊 Production Monitoring

### Set up Monitoring

**1. Error Tracking with Sentry**

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[FastApiIntegration()],
        environment=settings.ENVIRONMENT,
        traces_sample_rate=0.1,  # 10% of requests
        profiles_sample_rate=0.1  # 10% profiling
    )
```

**2. Application Performance Monitoring (APM)**

Use services like:
- **New Relic** - Full APM
- **Datadog** - Monitoring and logs
- **AWS CloudWatch** - If on AWS

**3. Uptime Monitoring**

Use services like:
- **UptimeRobot** (free)
- **Pingdom**
- **StatusCake**

Configure to check `/health` endpoint every 5 minutes.

### Logging in Production

**Aggregate logs:**
- **CloudWatch** (AWS)
- **Railway Logs** (Railway)
- **Render Logs** (Render)
- **LogDNA** / **Papertrail** (third-party)

**View logs:**
```bash
# Railway
railway logs

# Render (in dashboard or CLI)
render logs

# AWS CloudWatch
aws logs tail /ecs/ml-platform --follow
```

---

## 🔄 Rollback Strategy

### Quick Rollback

**Railway:**
```bash
# View deployments
railway deployments list

# Rollback to previous
railway rollback <deployment-id>
```

**Render:**
- Go to dashboard
- Click "Deploys"
- Click "Rollback" on previous deployment

**AWS ECS:**
```bash
# Update to previous task definition revision
aws ecs update-service \
    --cluster ml-platform-cluster \
    --service ml-platform-service \
    --task-definition ml-platform-task:2  # Previous revision
```

### Database Rollback

**If migration fails:**
```bash
# Rollback migration
alembic downgrade -1

# Or to specific revision
alembic downgrade <revision_id>
```

**Best practice:** Test migrations in staging first!

---

## ✅ Post-Deployment Checklist

After deployment, verify:

- [ ] Application is accessible at domain
- [ ] HTTPS is working (green lock icon)
- [ ] Health check endpoint responds
- [ ] Database connection works
- [ ] Redis connection works
- [ ] User registration works
- [ ] User login works
- [ ] Model upload works
- [ ] Predictions work
- [ ] API keys work
- [ ] Logs are being collected
- [ ] Error tracking is working
- [ ] Backups are scheduled
- [ ] Monitoring is active
- [ ] DNS is propagated
- [ ] CORS is configured correctly

---

## 📚 Key Takeaways

### Concepts Learned
1. **Platform Selection**: Choose based on needs and budget
2. **Docker Deployment**: Containerize for consistency
3. **Environment Configuration**: Different settings for prod
4. **CI/CD Pipeline**: Automate testing and deployment
5. **Domain Setup**: Custom domains and SSL
6. **Monitoring**: Track errors and performance
7. **Rollback**: Quickly recover from bad deployments

### Best Practices
✅ Test before deploying to production
✅ Use CI/CD for automatic deployments
✅ Set up monitoring and alerts
✅ Have a rollback strategy
✅ Use environment variables for secrets
✅ Enable HTTPS
✅ Configure health checks
✅ Set up automated backups
✅ Monitor logs in real-time
✅ Document deployment process

### Common Mistakes to Avoid
❌ Deploying without testing → Production bugs
❌ No health checks → Can't detect failures
❌ No monitoring → Don't know when things break
❌ Hardcoded secrets → Security breach
❌ No rollback plan → Extended downtime
❌ Wrong environment config → App crashes
❌ No database backups → Data loss risk
❌ Not setting up SSL → Insecure

---

## 🔗 Related Documentation

- Railway docs: https://docs.railway.app/
- Render docs: https://render.com/docs
- AWS ECS docs: https://docs.aws.amazon.com/ecs/
- GitHub Actions docs: https://docs.github.com/en/actions

**Congratulations! Your ML Model Serving Platform is now live! 🎉**
