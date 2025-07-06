FROM python:3.9-slim
WORKDIR /app
COPY requirements_api.txt .
RUN pip install --no-cache-dir -r requirements_api.txt
COPY . .
CMD ["python", "api_flask.py"]