FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python -c "import os; f=open('start.sh','rb'); d=f.read().replace(b'\r\n', b'\n'); f.close(); f=open('start.sh','wb'); f.write(d); f.close()"
RUN chmod +x start.sh

EXPOSE 8080
EXPOSE 5001

CMD ["./start.sh"]