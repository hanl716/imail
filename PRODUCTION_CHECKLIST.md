# Production Readiness Checklist for Email Management App

This document outlines critical considerations and steps for deploying the Email Management Application to a production environment.

## 1. Configuration Management

### 1.1. Environment Variables
Ensure all the following environment variables are set with **strong, unique, and production-appropriate values**. Do not use development defaults or example placeholders. These are typically managed via a `.env` file loaded by Docker Compose in production or through your deployment platform's secret management.

**Critical Secrets (MUST be unique & strong for production):**
*   `POSTGRES_USER`: Username for the PostgreSQL database.
*   `POSTGRES_PASSWORD`: **Strong password** for the PostgreSQL user.
*   `POSTGRES_DB`: Name of the PostgreSQL database.
*   `BACKEND_DATABASE_URL`: Full database connection string for the backend (e.g., `postgresql://<user>:<password>@<host>:<port>/<db_name>`). Ensure the password matches `POSTGRES_PASSWORD`.
*   `BACKEND_SECRET_KEY`: **Long, random, and secret string** for FastAPI JWT token generation.
*   `BACKEND_FERNET_KEY`: **Cryptographically strong Fernet key** for encrypting sensitive data in the database (e.g., email account passwords). Generate using `from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())`.
*   `BACKEND_CEREBRAS_API_KEY`: Your valid API key for the Cerebras AI service.

**Service URLs (point to production instances or remain for Docker Compose internal networking):**
*   `CELERY_BROKER_URL`: URL for the RabbitMQ broker (e.g., `amqp://<user>:<pass>@prod-rabbitmq-host:5672//`). Default `amqp://guest:guest@rabbitmq:5672//` is for dev.
*   `CELERY_RESULT_BACKEND`: URL for the Redis instance used by Celery for results (e.g., `redis://prod-redis-host:6379/0`). Default `redis://redis:6379/0` is for dev.
*   `REDIS_URL`: URL for the Redis instance used for rate limiting (e.g., `redis://prod-redis-host:6379/1`). Default `redis://redis:6379/1` is for dev.

**Operational Configuration:**
*   `PYTHON_LOG_LEVEL`: (Recommended to add) Set to `INFO` or `WARNING` for production to control application log verbosity. Can be configured in `app/core/config.py` to be loaded from this env var.
*   `CEREBRAS_LOG_LEVEL`: (If SDK supports it) Adjust Cerebras SDK logging if necessary for production.

### 1.2. Logging Levels
*   Configure application logging (FastAPI, Celery) to an appropriate level for production (e.g., `INFO` or `WARNING`). This can be managed via an environment variable like `LOGGING_LEVEL` that modifies the logging configuration in `app/core/config.py` or a dedicated logging setup module.

### 1.3. Cerebras Client Configuration
*   Review and potentially adjust `max_retries` and `timeout` settings for the `AsyncCerebras` client in `app/services/cerebras_ai_service.py` based on production network conditions and expected API performance.

### 1.4. Uvicorn Workers (Backend)
*   The Dockerfile's `CMD` for the backend uses a single Uvicorn worker, suitable for development. For production, deploy the backend with multiple Uvicorn workers. This is typically done in the deployment script or process manager (e.g., `uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers <num_workers>`). The number of workers usually depends on the server's CPU cores (e.g., `2 * num_cores + 1`).

## 2. Database Management (PostgreSQL)

### 2.1. Backups
*   Implement a robust, regular backup strategy for the PostgreSQL database.
*   Use tools like `pg_dump` for scheduled backups or leverage backup services provided by your cloud provider or database hosting solution.
*   Test backup restoration procedures periodically.

### 2.2. Alembic Migrations
*   Before deploying new application code that depends on schema changes, database migrations **must** be applied.
*   Run migrations using: `alembic upgrade head` (or target a specific revision).
*   This command should be run in a controlled manner, ideally during a maintenance window or as part of a blue/green deployment strategy to minimize downtime. The backend Docker container CMD currently runs this on startup, which is fine for simple setups but might need more control in complex production environments.

### 2.3. Connection Pooling
*   SQLAlchemy provides its own connection pool, which is generally sufficient.
*   For very high-concurrency applications, consider using an external connection pooler like PgBouncer in front of PostgreSQL to manage connections more efficiently across multiple application instances.

## 3. Security Hardening

### 3.1. HTTPS
*   **Mandatory**: All production traffic MUST be served over HTTPS.
*   Configure your reverse proxy (e.g., Nginx, which serves the frontend or a dedicated load balancer/API gateway) for SSL/TLS termination using valid certificates (e.g., from Let's Encrypt or a commercial CA).

### 3.2. Security Headers
*   Configure your web server/reverse proxy to add important security headers to HTTP responses:
    *   `Strict-Transport-Security (HSTS)`
    *   `X-Content-Type-Options: nosniff`
    *   `X-Frame-Options: DENY` or `SAMEORIGIN`
    *   `Content-Security-Policy (CSP)` (Requires careful configuration)
    *   `Referrer-Policy`
    *   `Permissions-Policy`

### 3.3. Firewall Rules
*   Restrict network access to your services. Only expose necessary ports to the public internet (typically port 443 for HTTPS).
*   Internal services like PostgreSQL, Redis, and RabbitMQ should **not** be directly accessible from the public internet. They should reside within a private network (e.g., Docker virtual network, VPC) and only allow connections from specific application services.

### 3.4. Regular Dependency Audits
*   Continuously monitor and update dependencies for known vulnerabilities:
    *   Backend (Python): Regularly run `pip_audit` or `safety check -r requirements.txt`.
    *   Frontend (Node.js): Regularly run `npm audit` or `yarn audit`.
*   Integrate these checks into your CI/CD pipeline.

### 3.5. Rate Limiting
*   Review the rate limits configured in `app/api/endpoints/` via `slowapi`.
*   Adjust limits (e.g., "5/minute", "100/hour") based on expected production traffic, user behavior, and resource capacity to prevent abuse and ensure service availability. Consider more granular limits if specific abuse patterns emerge.

### 3.6. Secrets Management (Advanced)
*   For enhanced security in production, especially outside managed container platforms that provide their own secret injection, consider using a dedicated secrets management solution like:
    *   HashiCorp Vault
    *   AWS Secrets Manager
    *   Google Cloud Secret Manager
    *   Azure Key Vault
*   These tools provide secure storage, access control, auditing, and rotation for secrets, reducing the risks associated with `.env` files on servers.

## 4. Production Logging & Monitoring

### 4.1. Logging
*   **Structured Logging**: Configure FastAPI/Uvicorn and Celery to output logs in a structured format (e.g., JSON) for easier parsing and analysis by log management systems.
*   **Centralized Logging**: Send all application, service (PostgreSQL, Nginx, RabbitMQ, Redis), and Celery logs to a centralized logging platform. Examples:
    *   ELK Stack (Elasticsearch, Logstash, Kibana)
    *   Grafana Loki
    *   Datadog, Splunk, Loggly, Papertrail, or cloud provider services (AWS CloudWatch Logs, Google Cloud Logging, Azure Monitor Logs).
*   Ensure log levels are appropriate for production (e.g., `INFO` or `WARNING`).

### 4.2. Monitoring
*   **Basic Health Checks**: Implement health check endpoints in your FastAPI backend and configure your deployment platform or monitoring system to regularly check them. Docker Compose healthchecks are a good start for container health.
*   **Application Performance Monitoring (APM)**:
    *   Integrate an APM tool (e.g., Sentry for error tracking & basic performance, Datadog, New Relic, Dynatrace for more comprehensive APM).
    *   This will help identify performance bottlenecks, track errors in real-time, and understand application behavior under load.
*   **Resource Monitoring**:
    *   Monitor CPU, memory, disk space, and network I/O for all servers and containers.
    *   Use tools provided by your hosting/cloud provider or self-hosted solutions (e.g., Prometheus with Grafana).
*   **Celery Queue Monitoring**:
    *   Use Flower (can be added as another service in `docker-compose.yml` for production monitoring) or monitor RabbitMQ/Redis queue lengths and task processing rates directly. This is crucial for ensuring background tasks are running smoothly.
    *   Set up alerts for long queue lengths or high task failure rates.

## 5. Deployment Strategy
*   Plan your deployment strategy (e.g., blue/green, canary, rolling updates) to minimize downtime.
*   Ensure rollback procedures are in place.
*   Automate deployments as much as possible using CI/CD pipelines.

By addressing these points, you can significantly improve the reliability, security, and maintainability of the Email Management Application in a production environment.This is a good start for the `PRODUCTION_CHECKLIST.md`. I'll proceed with creating/updating the README files.

**Step 5: Update Project READMEs**

**Root `README.md`**
