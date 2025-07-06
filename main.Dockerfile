FROM python:3.9-slim
WORKDIR /app
RUN apt-get update && apt-get install -y libgl1-mesa-glx libglib2.0-0
COPY requirements_main.txt .
RUN pip install --no-cache-dir -r requirements_main.txt
COPY . .
CMD ["python", "main.py"]