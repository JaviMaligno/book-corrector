# Docker Deployment Guide

## Quick Start

```bash
# 1. Create .env file
cp .env.example .env
# Edit .env and add GOOGLE_API_KEY

# 2. Build and run
docker-compose up -d

# 3. Check status
docker-compose ps

# 4. View logs
docker-compose logs -f corrector-api
```

## Environment Variables

Required in `.env` file:

```bash
# Required
GOOGLE_API_KEY=your_api_key_here

# Optional
GEMINI_MODEL=gemini-2.5-flash
DEMO_PLAN=free                    # free or premium
SYSTEM_MAX_WORKERS=2              # Max concurrent jobs
```

## Production Deployment

### Build Image
```bash
docker-compose build
```

### Run in Background
```bash
docker-compose up -d
```

### View Logs
```bash
# All logs
docker-compose logs -f

# Only API logs
docker-compose logs -f corrector-api
```

### Stop Service
```bash
docker-compose down
```

### Restart After Code Changes
```bash
docker-compose down
docker-compose build
docker-compose up -d
```

## Development Mode

For local development with hot-reload (code changes reflected immediately):

```bash
docker-compose -f docker-compose.dev.yml up
```

This mounts source code as volumes so you don't need to rebuild on every change.

## Health Check

```bash
# Check if service is healthy
curl http://localhost:8000/health

# Expected response
{"status":"ok"}
```

## API Documentation

Once running, access interactive API docs:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Troubleshooting

### Container Exits Immediately

Check logs:
```bash
docker-compose logs corrector-api
```

Common causes:
- Missing `GOOGLE_API_KEY` in `.env`
- Invalid environment variable format
- Port 8000 already in use

### Port Already in Use

Change port in `docker-compose.yml`:
```yaml
ports:
  - "8080:8000"  # Host:Container
```

### View Running Containers
```bash
docker-compose ps
```

### Exec Into Container
```bash
docker-compose exec corrector-api /bin/bash
```

### Remove All Data
```bash
docker-compose down -v  # Removes volumes
```

## Persistence

Outputs are persisted in `./outputs` directory mounted as volume. This directory survives container restarts.

## Multi-Stage Build

The Dockerfile uses multi-stage build:
1. **Builder stage**: Installs dependencies
2. **Final stage**: Copies only needed files, runs as non-root user

Benefits:
- Smaller final image
- Better security (non-root user)
- Faster rebuilds (cached layers)

## Security Notes

- Container runs as non-root user (uid 1000)
- Only necessary files copied to image
- Health check included for monitoring
- Environment variables for secrets (not baked into image)
