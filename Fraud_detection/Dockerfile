# Base image
FROM python:3.10

# Set working directory
WORKDIR /app

# Copy files
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir fastapi uvicorn pandas scikit-learn joblib streamlit requests

# Expose port
EXPOSE 8000

# Run API
CMD ["uvicorn", "backend.fraud_detection_api:app", "--host", "0.0.0.0", "--port", "8000"]