# Docker Production Mastery

> **Philosophy**: Docker solves "it works on my machine" forever. Learn by doing, master what matters in production.

---

## Table of Contents
1. [Why Docker Exists](#why-docker-exists)
2. [Core Concepts](#core-concepts)
3. [Dockerfile - Build Images](#dockerfile---build-images)
4. [Docker Commands](#docker-commands)
5. [Docker Compose - Multi-Container Apps](#docker-compose---multi-container-apps)
6. [Volumes - Data Persistence](#volumes---data-persistence)
7. [Networking](#networking)
8. [Production Best Practices](#production-best-practices)
9. [Your Project Hands-On](#your-project-hands-on)

---

## Why Docker Exists

### The Problem (Before Docker)

**Developer**: "The app works on my laptop!"
**Ops**: "It crashes on the server!"

**Why?**
- Different Python versions (dev has 3.11, server has 3.8)
- Different OS (dev uses Windows, server uses Linux)
- Missing dependencies (dev installed PostgreSQL, server didn't)
- Different configurations (dev uses SQLite, server uses PostgreSQL)

### The Solution (Docker)

**Package everything** into a container:
- ✅ Your code
- ✅ Python 3.11
- ✅ All libraries (FastAPI, SQLAlchemy, etc.)
- ✅ System dependencies
- ✅ Configuration

**Result**: Same container runs **everywhere** - laptop, colleague's machine, server, cloud.

---

## Core Concepts

### 1. Image vs Container

**Image** = Recipe (Blueprint)
- Read-only template
- Contains your code + dependencies
- Example: `python:3.11`, `postgres:15`, `your-app:v1.0`

**Container** = Running instance of image
- Actual running application
- Created from image
- Can have multiple containers from one image

**Analogy**:
- Image = Class definition
- Container = Object instance

```bash
# Image: Recipe for a cake
docker build -t my-app .

# Container: Actual cake you can eat (run)
docker run my-app
```

### 2. Dockerfile

**What**: Text file with instructions to build an image

**Example**:
```dockerfile
# Start from Python 3.11 base image
FROM python:3.11-slim

# Copy your code
COPY . /app

# Install dependencies
RUN pip install -r requirements.txt

# Run your app
CMD ["python", "main.py"]
```

**Build it**:
```bash
docker build -t my-app .
```

**Run it**:
```bash
docker run my-app
```

### 3. Registry (Docker Hub)

**What**: GitHub for Docker images

- Public images: `python`, `postgres`, `redis`, `nginx`
- Your images: `your-username/your-app`

**Pull image**:
```bash
docker pull python:3.11
```

**Push your image**:
```bash
docker push your-username/my-app
```

---

## Dockerfile - Build Images

### 1. Basic Structure

```dockerfile
# 1. Base image (starting point)
FROM python:3.11-slim

# 2. Set working directory
WORKDIR /app

# 3. Copy dependency file first (caching optimization)
COPY requirements.txt .

# 4. Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy application code
COPY . .

# 6. Expose port (documentation only)
EXPOSE 8000

# 7. Command to run when container starts
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. Instruction Breakdown

**FROM** - Choose base image
```dockerfile
FROM python:3.11-slim           # Python pre-installed
FROM node:18-alpine            # Node.js (Alpine = tiny Linux)
FROM ubuntu:22.04              # Plain Ubuntu (you install everything)
```

**WORKDIR** - Set working directory
```dockerfile
WORKDIR /app                   # All commands run in /app
# Equivalent to: cd /app
```

**COPY** - Copy files from your machine → image
```dockerfile
COPY requirements.txt .        # Copy one file
COPY app/ /app/app/           # Copy directory
COPY . .                      # Copy everything
```

**RUN** - Execute command during build (install stuff)
```dockerfile
RUN pip install fastapi       # Install Python package
RUN apt-get update && apt-get install -y curl  # Install system package
```

**CMD** - Command to run when container starts
```dockerfile
CMD ["python", "main.py"]                    # Run Python
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0"]  # Run FastAPI
```

**EXPOSE** - Document which port app uses
```dockerfile
EXPOSE 8000                   # App listens on port 8000
```

**ENV** - Set environment variables
```dockerfile
ENV DATABASE_URL=postgresql://localhost/db
ENV DEBUG=False
```

### 3. Layer Caching (CRITICAL for speed)

**Docker caches each instruction**. If file hasn't changed, reuses cache.

**❌ Slow (rebuilds everything when code changes)**:
```dockerfile
FROM python:3.11-slim
COPY . .                      # Code changes → everything below rebuilds
RUN pip install -r requirements.txt  # Reinstalls all packages every time!
CMD ["python", "main.py"]
```

**✅ Fast (cache-optimized)**:
```dockerfile
FROM python:3.11-slim
COPY requirements.txt .       # Copy only requirements first
RUN pip install -r requirements.txt  # Cached unless requirements.txt changes
COPY . .                      # Code changes don't affect above layers
CMD ["python", "main.py"]
```

**Why it matters**: First build = 5 min, cached builds = 5 seconds!

### 4. Multi-Stage Builds (Production Pattern)

**Problem**: Build tools bloat image size (500MB → 1GB)

**Solution**: Build in one stage, copy only what's needed to final stage

```dockerfile
# Stage 1: Build
FROM python:3.11 as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Stage 2: Production (smaller!)
FROM python:3.11-slim
WORKDIR /app
# Copy only installed packages, not build tools
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0"]
```

**Result**: 1GB build image → 200MB production image

---

## Docker Commands

### 1. Building Images

```bash
# Build image from Dockerfile
docker build -t my-app .
# -t = tag (name)
# . = look for Dockerfile in current directory

# Build with custom Dockerfile name
docker build -t my-app -f Dockerfile.dev .

# Build with build arguments
docker build --build-arg VERSION=1.0 -t my-app .
```

### 2. Running Containers

```bash
# Run container (basic)
docker run my-app

# Run in background (-d = detached)
docker run -d my-app

# Run with port mapping (connect host:container)
docker run -p 8000:8000 my-app
# -p 8000:8000 = localhost:8000 → container:8000

# Run with environment variables
docker run -e DATABASE_URL=postgres://db my-app

# Run with custom name
docker run --name my-api my-app

# Run with volume mount (sync files)
docker run -v $(pwd):/app my-app

# Run interactively (get shell inside container)
docker run -it my-app /bin/bash

# All together (production pattern)
docker run -d \
  --name my-api \
  -p 8000:8000 \
  -e DATABASE_URL=postgres://db \
  -v $(pwd)/uploads:/app/uploads \
  my-app
```

### 3. Managing Containers

```bash
# List running containers
docker ps

# List all containers (including stopped)
docker ps -a

# Stop container
docker stop my-api
docker stop <container-id>

# Start stopped container
docker start my-api

# Restart container
docker restart my-api

# Remove container
docker rm my-api

# Remove running container (force)
docker rm -f my-api

# Remove all stopped containers
docker container prune
```

### 4. Viewing Logs & Debugging

```bash
# View logs
docker logs my-api

# Follow logs (like tail -f)
docker logs -f my-api

# Last 100 lines
docker logs --tail 100 my-api

# Execute command inside running container
docker exec my-api ls /app

# Get shell inside running container (debugging)
docker exec -it my-api /bin/bash

# View container details (ports, volumes, etc.)
docker inspect my-api

# View resource usage (CPU, memory)
docker stats
```

### 5. Managing Images

```bash
# List images
docker images

# Remove image
docker rmi my-app

# Remove unused images
docker image prune

# Tag image (rename/version)
docker tag my-app my-app:v1.0
docker tag my-app your-dockerhub/my-app:latest

# Push to Docker Hub
docker push your-dockerhub/my-app:latest

# Pull from Docker Hub
docker pull postgres:15
```

### 6. Clean Up (Free disk space!)

```bash
# Remove all stopped containers
docker container prune

# Remove unused images
docker image prune

# Remove unused volumes
docker volume prune

# Remove everything unused (nuclear option)
docker system prune -a

# See disk usage
docker system df
```

---

## Docker Compose - Multi-Container Apps

**Problem**: Your app needs PostgreSQL + Redis + FastAPI. Running 3 `docker run` commands sucks.

**Solution**: `docker-compose.yml` - Define all services in one file.

### 1. Basic docker-compose.yml

```yaml
version: '3.8'

services:
  # Service 1: Database
  db:
    image: postgres:15
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: mydb
    ports:
      - "5432:5432"
  
  # Service 2: Your API
  api:
    build: .                    # Build from Dockerfile
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://user:password@db:5432/mydb
    depends_on:
      - db                      # Start db before api
```

**Run everything**:
```bash
docker-compose up
```

**Stop everything**:
```bash
docker-compose down
```

**That's it!** No manual container management.

### 2. Your Project's docker-compose.yml

```yaml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    container_name: ml_platform_db
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: ml_platform
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: ml_platform_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  # FastAPI Application
  api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: ml_platform_api
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres:5432/ml_platform
      REDIS_URL: redis://redis:6379/0
      SECRET_KEY: your-secret-key-change-in-production
    volumes:
      - ./app:/app/app           # Hot reload in development
      - ./models:/app/models     # Persistent model storage
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Named volumes (persist data)
volumes:
  postgres_data:
  redis_data:
```

### 3. Docker Compose Commands

```bash
# Start all services
docker-compose up

# Start in background
docker-compose up -d

# Stop all services
docker-compose down

# Stop and remove volumes (delete data)
docker-compose down -v

# Rebuild images
docker-compose build

# Rebuild and start
docker-compose up --build

# View logs (all services)
docker-compose logs

# View logs (one service)
docker-compose logs api

# Follow logs
docker-compose logs -f api

# Execute command in service
docker-compose exec api python manage.py migrate

# Get shell in service
docker-compose exec api /bin/bash

# List running services
docker-compose ps

# Restart one service
docker-compose restart api
```

### 4. Compose File Breakdown

**image** - Use pre-built image
```yaml
services:
  db:
    image: postgres:15        # From Docker Hub
```

**build** - Build from Dockerfile
```yaml
services:
  api:
    build: .                  # Use Dockerfile in current dir
    # OR
    build:
      context: .
      dockerfile: Dockerfile.dev
```

**ports** - Map host:container
```yaml
ports:
  - "8000:8000"              # localhost:8000 → container:8000
  - "5432:5432"              # Access PostgreSQL at localhost:5432
```

**environment** - Set env vars
```yaml
environment:
  DATABASE_URL: postgres://db/mydb
  DEBUG: "true"
```

**volumes** - Persist data or sync files
```yaml
volumes:
  - postgres_data:/var/lib/postgresql/data  # Named volume (data survives)
  - ./app:/app/app                          # Bind mount (sync code)
```

**depends_on** - Start order
```yaml
depends_on:
  - db                       # Start db before this service
  # OR with health check
  postgres:
    condition: service_healthy  # Wait for postgres to be ready
```

**healthcheck** - Check if service is ready
```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U postgres"]
  interval: 5s               # Check every 5s
  timeout: 5s
  retries: 5
```

**command** - Override default command
```yaml
command: uvicorn app.main:app --reload  # Development mode
```

**container_name** - Custom name
```yaml
container_name: my_api      # Easier to reference
```

---

## Volumes - Data Persistence

**Problem**: Containers are ephemeral. Stop container → lose all data!

**Solution**: Volumes - Store data outside container.

### 1. Volume Types

**Named Volume** (Managed by Docker)
```yaml
volumes:
  - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:             # Define named volume
```
- Docker stores in `/var/lib/docker/volumes/`
- Survives container deletion
- **Use for**: Database data, uploads

**Bind Mount** (Sync with host directory)
```yaml
volumes:
  - ./app:/app/app           # Host ./app ↔ Container /app/app
```
- Changes on host instantly reflect in container
- **Use for**: Development (hot reload), logs

**Anonymous Volume** (Temporary)
```yaml
volumes:
  - /app/node_modules        # Don't sync this folder
```

### 2. Volume Commands

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect postgres_data

# Remove volume
docker volume rm postgres_data

# Remove unused volumes
docker volume prune
```

### 3. Common Patterns

**Development: Sync code for hot reload**
```yaml
api:
  volumes:
    - ./app:/app/app         # Code changes → auto-reload
```

**Production: Persist uploads**
```yaml
api:
  volumes:
    - uploads:/app/uploads   # User uploads survive restarts
```

**Database: Don't lose data!**
```yaml
postgres:
  volumes:
    - postgres_data:/var/lib/postgresql/data
```

---

## Networking

**Default**: Docker Compose creates a network. Services talk using service names.

### 1. Service Discovery

```yaml
services:
  db:
    image: postgres:15
  
  api:
    environment:
      DATABASE_URL: postgresql://user:pass@db:5432/mydb
      #                                    ^^^ Use service name!
```

**How it works**: Docker DNS resolves `db` → container IP

### 2. Access from Host

```yaml
services:
  api:
    ports:
      - "8000:8000"          # localhost:8000 → container
```

**Access**: `http://localhost:8000`

### 3. Container-to-Container (No port mapping needed)

```yaml
services:
  db:
    # NO ports exposed to host
  
  api:
    environment:
      DATABASE_URL: postgresql://user:pass@db:5432/mydb
      # Works! api can reach db directly
```

---

## Production Best Practices

### 1. Multi-Stage Builds

```dockerfile
# Build stage
FROM python:3.11 as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0"]
```

**Benefits**:
- ✅ Smaller image (150MB vs 1GB)
- ✅ Faster deploys
- ✅ More secure (no build tools in production)

### 2. Non-Root User

```dockerfile
FROM python:3.11-slim

# Create non-root user
RUN useradd -m -u 1000 appuser

# Switch to non-root
USER appuser

WORKDIR /home/appuser/app
COPY . .

CMD ["uvicorn", "app.main:app"]
```

**Why**: Security - If attacker breaks in, they're not root.

### 3. .dockerignore (Like .gitignore)

```
# .dockerignore
__pycache__/
*.pyc
.git/
.env
venv/
node_modules/
.pytest_cache/
*.log
```

**Benefits**:
- ✅ Smaller image
- ✅ Faster builds
- ✅ Don't leak secrets

### 4. Health Checks

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
```

```yaml
# docker-compose.yml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 3s
  retries: 3
```

**Why**: Orchestrators (Kubernetes) know when app is ready.

### 5. Environment Variables (12-Factor App)

```yaml
# docker-compose.yml
environment:
  DATABASE_URL: ${DATABASE_URL}  # From .env file
  SECRET_KEY: ${SECRET_KEY}

# .env file (NOT in git!)
DATABASE_URL=postgresql://user:pass@db/mydb
SECRET_KEY=super-secret-key
```

### 6. Logging to stdout

```python
# Good (Docker captures stdout)
import logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

# Bad (logs trapped in container)
logging.basicConfig(filename='app.log')
```

**View logs**:
```bash
docker-compose logs -f api
```

---

## Your Project Hands-On

### **🎯 Exercise 1: Start Your Project with Docker**

```bash
# 1. Make sure Docker Desktop is running

# 2. Navigate to your project
cd ML-Model-Serving-Platform

# 3. Start everything
docker-compose up

# What happens:
# - Downloads postgres:15-alpine image (~80MB)
# - Downloads redis:7-alpine image (~30MB)
# - Builds your FastAPI image (reads Dockerfile)
# - Creates network for services to talk
# - Starts PostgreSQL (port 5432)
# - Starts Redis (port 6379)
# - Starts your FastAPI app (port 8000)
```

**Expected output**:
```
Creating ml_platform_db    ... done
Creating ml_platform_redis ... done
Creating ml_platform_api   ... done
Attaching to ml_platform_db, ml_platform_redis, ml_platform_api
```

**Test it**:
```bash
# Open browser: http://localhost:8000/docs
# You'll see FastAPI Swagger UI!
```

### **🎯 Exercise 2: Make a Code Change (Hot Reload)**

```bash
# 1. docker-compose is still running from Exercise 1

# 2. Edit app/main.py
# Change:
#   return {"message": "Hello World"}
# To:
#   return {"message": "Docker is awesome!"}

# 3. Save file

# 4. Check logs
docker-compose logs -f api

# You'll see:
# "Detected file change, reloading..."
# App restarted automatically!

# 5. Refresh http://localhost:8000
# See your change instantly!
```

**Why it works**: Volume mount in docker-compose.yml
```yaml
volumes:
  - ./app:/app/app           # Host code synced to container
```

### **🎯 Exercise 3: Access Database**

```bash
# Get shell in PostgreSQL container
docker-compose exec postgres psql -U postgres -d ml_platform

# You're now in PostgreSQL!
# Try:
\dt                          # List tables (empty for now)
\l                           # List databases
\q                           # Quit
```

### **🎯 Exercise 4: Check Redis**

```bash
# Get shell in Redis container
docker-compose exec redis redis-cli

# You're now in Redis!
# Try:
PING                         # Should return PONG
SET test "Hello Redis"
GET test                     # Returns "Hello Redis"
KEYS *                       # List all keys
exit
```

### **🎯 Exercise 5: View Logs**

```bash
# All services
docker-compose logs

# Just API
docker-compose logs api

# Follow API logs (live)
docker-compose logs -f api

# Last 50 lines
docker-compose logs --tail 50 api
```

### **🎯 Exercise 6: Restart One Service**

```bash
# Restart just the API (PostgreSQL and Redis keep running)
docker-compose restart api

# Check it's back
docker-compose ps
```

### **🎯 Exercise 7: Execute Commands in Container**

```bash
# Run Python in API container
docker-compose exec api python --version

# Get shell in API container
docker-compose exec api /bin/bash

# Now you're inside container!
ls                           # See /app directory
python -c "import fastapi; print(fastapi.__version__)"
exit
```

### **🎯 Exercise 8: Clean Shutdown**

```bash
# Stop all services (keeps data)
docker-compose down

# Stop and delete volumes (delete database data)
docker-compose down -v

# Next time you run docker-compose up, fresh database!
```

### **🎯 Exercise 9: Rebuild After Changing Dockerfile**

```bash
# If you edit Dockerfile or requirements.txt:

# Stop services
docker-compose down

# Rebuild images and start
docker-compose up --build

# Or rebuild without starting
docker-compose build
```

### **🎯 Exercise 10: Production Build**

```bash
# Build production image
docker build -t ml-platform:v1.0 .

# Run production container (no volumes, no reload)
docker run -d \
  --name ml-api-prod \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@db/mydb \
  ml-platform:v1.0

# Check it's running
docker ps

# View logs
docker logs -f ml-api-prod

# Stop
docker stop ml-api-prod
docker rm ml-api-prod
```

---

## Common Workflows

### Development Workflow

```bash
# Day 1: First time setup
docker-compose up --build    # Build images and start

# Day 2-N: Daily development
docker-compose up            # Just start (uses cached images)
# Code in your editor, changes auto-reload
docker-compose down          # Stop when done

# When you change requirements.txt or Dockerfile:
docker-compose up --build    # Rebuild
```

### Debugging Workflow

```bash
# Problem: API not starting

# 1. Check logs
docker-compose logs api

# 2. Get shell in container
docker-compose exec api /bin/bash

# 3. Try running command manually
python -c "from app.main import app"  # See actual error

# 4. Check environment
echo $DATABASE_URL

# 5. Test database connection
python -c "import psycopg2; psycopg2.connect('postgresql://postgres:postgres@postgres/ml_platform')"
```

### Database Workflow

```bash
# Create tables (run migrations)
docker-compose exec api alembic upgrade head

# Create migration
docker-compose exec api alembic revision --autogenerate -m "Add users table"

# Access database directly
docker-compose exec postgres psql -U postgres -d ml_platform

# Backup database
docker-compose exec postgres pg_dump -U postgres ml_platform > backup.sql

# Restore database
docker-compose exec -T postgres psql -U postgres ml_platform < backup.sql
```

---

## Docker vs Local Development

| Aspect | Local (venv) | Docker |
|--------|-------------|--------|
| **Setup** | Install Python, PostgreSQL, Redis | `docker-compose up` |
| **Switching projects** | Deactivate venv, activate other | Stop one, start other |
| **Team onboarding** | "Install X, Y, Z... good luck!" | "Run `docker-compose up`" |
| **Production parity** | Different OS, versions | Identical environment |
| **Cleanup** | Manually uninstall | `docker-compose down` |
| **Version conflicts** | One PostgreSQL version system-wide | Multiple isolated versions |

**When to use Docker**: Always (in production). Development too (after this tutorial).

**When NOT to use Docker**: Simple scripts, learning basics of a language.

---

## Next Steps: Kubernetes

**You've learned**: Run containers on one machine
**Kubernetes**: Run containers on many machines (production scale)

**What Kubernetes adds**:
- Auto-scaling (1 container → 100 containers based on traffic)
- Self-healing (container crashes → auto-restart)
- Load balancing (distribute traffic across containers)
- Rolling updates (update app without downtime)
- Multi-cloud (run on AWS, GCP, Azure)

**When you need Kubernetes**: 
- 10,000+ users
- High availability required
- Auto-scaling needed

**For now**: Docker Compose is enough. Master this first.

---

## Cheat Sheet

```bash
# DOCKER BASICS
docker build -t name .              # Build image
docker run name                     # Run container
docker ps                           # List running containers
docker logs container-name          # View logs
docker exec -it container-name bash # Get shell
docker stop container-name          # Stop
docker rm container-name            # Remove

# DOCKER COMPOSE
docker-compose up                   # Start all
docker-compose up -d                # Start in background
docker-compose down                 # Stop all
docker-compose logs -f service      # Follow logs
docker-compose exec service bash    # Get shell
docker-compose restart service      # Restart one
docker-compose build                # Rebuild images
docker-compose up --build           # Rebuild and start

# CLEANUP
docker system prune -a              # Delete everything unused
docker volume prune                 # Delete unused volumes
docker-compose down -v              # Stop and delete volumes
```

---

## The 20% You'll Use 80% of the Time

**Master these**:
1. ✅ `docker-compose up` / `docker-compose down`
2. ✅ `docker-compose logs -f service`
3. ✅ `docker-compose exec service bash`
4. ✅ Understanding `docker-compose.yml` structure
5. ✅ Volumes for data persistence
6. ✅ Port mapping (`-p 8000:8000`)
7. ✅ Environment variables
8. ✅ `docker-compose up --build` (rebuild after changes)

**Everything else is bonus.**

---

## Resources

- **Official Docs**: https://docs.docker.com/
- **Docker Hub** (find images): https://hub.docker.com/
- **Your Project**: Already configured! Just run `docker-compose up`

**Next**: Actually run your project with Docker. Break things. Learn by doing. That's how you master Docker.
