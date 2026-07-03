# Simple LMS - Learning Management System

Learning Management System built with Django, PostgreSQL, and Docker.

## 📋 Prerequisites

- Docker Desktop (version 20.10+)
- Docker Compose (version 2.0+)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Copy environment variables
cp .env.example .env

# Edit .env file with your settings (optional)

<img width="1920" height="1008" alt="image" src="https://github.com/user-attachments/assets/1058d4e1-b4e8-4aa3-9e93-3eeb1337cdc7" />

## Cara Menjalankan

docker compose up -d

## Migration

docker exec -it simple-lms-web python manage.py migrate

## Swagger

http://localhost:8000/api/docs

## Flower

http://localhost:5555

## MongoDB

docker exec -it simple-lms-mongo mongosh

## Redis

docker exec -it simple-lms-redis redis-cli