"""
Gunicorn Configuration for the LLM Document Intelligence System

This file provides a centralized configuration for the Gunicorn production server.
It is optimized for performance and reliability in a containerized environment.

For more information on Gunicorn settings, see the official documentation:
https://docs.gunicorn.org/en/stable/settings.html
"""

import multiprocessing
import os

# --- Server Socket ---
# The address and port to bind the server to.
# Using '0.0.0.0' makes the server accessible from outside the container.
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"

# --- Worker Processes ---
# The number of worker processes to spawn. A common recommendation is
# (2 * number of CPU cores) + 1.
workers = int(os.getenv('WORKERS', multiprocessing.cpu_count() * 2 + 1))

# The type of worker to use. 'uvicorn.workers.UvicornWorker' is ideal for
# running ASGI applications like FastAPI.
worker_class = "uvicorn.workers.UvicornWorker"

# The maximum number of simultaneous connections a worker can handle.
worker_connections = 1000

# The maximum number of requests a worker will process before restarting.
# This helps prevent memory leaks.
max_requests = 1000
max_requests_jitter = 50  # Adds randomness to the restart timing.

# --- Logging ---
# Redirect access and error logs to stdout and stderr, which is standard
# for containerized applications.
accesslog = "-"
errorlog = "-"
loglevel = os.getenv('LOG_LEVEL', 'info').lower()

# --- Process Naming ---
# A descriptive name for the Gunicorn process.
proc_name = 'llm-doc-intelligence-server'

# --- Security ---
# Limits on request line and header sizes to mitigate certain types of attacks.
limit_request_line = 8190
limit_request_fields = 100
limit_request_field_size = 8190

# --- Server Hooks ---
# These functions are called at different points in the server's lifecycle.
# They are useful for logging and other setup/teardown tasks.

def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info("Gunicorn master process is starting.")

def when_ready(server):
    """Called just after the server is started."""
    server.log.info(f"Server is ready. Spawning {server.cfg.workers} workers.")

def on_exit(server):
    """Called just before Gunicorn exits."""
    server.log.info("Gunicorn is shutting down.")