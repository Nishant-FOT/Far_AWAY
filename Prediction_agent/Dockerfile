FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir fastapi uvicorn pydantic

# Copy Prediction Agent code
COPY Prediction_agent /app/Prediction_agent

# Set environment
ENV PYTHONUNBUFFERED=1
# Ensure the Prediction_agent package is on PYTHONPATH so `prediction_engine` imports work
ENV PYTHONPATH=/app/Prediction_agent:/app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/v1/health')" || exit 1

# Run application
CMD ["python", "-m", "uvicorn", "Prediction_agent.main:app", "--host", "0.0.0.0", "--port", "8000"]
