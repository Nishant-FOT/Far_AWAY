FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir fastapi uvicorn pydantic httpx python-multipart geopy folium networkx

# Copy shared code
COPY shared /app/shared

# Copy Disaster agents
COPY Disaster /app/Disaster

# Copy API code
COPY Disaster_agent_api /app/Disaster_agent_api

# Set environment
ENV PYTHONUNBUFFERED=1
# Ensure the Disaster_agent_api package is on PYTHONPATH so imports like `routes.*` resolve
ENV PYTHONPATH=/app/Disaster_agent_api:/app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
    CMD python -m pytest /app/Disaster_agent_api/routes || exit 1

# Run application
CMD ["python", "-m", "uvicorn", "Disaster_agent_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
