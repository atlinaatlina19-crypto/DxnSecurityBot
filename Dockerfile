FROM python:3.11-slim

# تثبيت أدوات النظام اللازمة لمكتبات الصوت وديسكورد
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    libopus0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
