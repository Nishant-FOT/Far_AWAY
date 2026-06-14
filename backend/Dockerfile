FROM python:3.11-slim
WORKDIR /app

# Use backend requirements and copy only the backend app and shared package
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend application package into /app/app so imports remain `app.*`
COPY backend/app ./app

# Include the top-level shared package so it can be imported by the app
COPY shared ./shared

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
