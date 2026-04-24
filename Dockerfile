FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu                                                                                    
RUN pip install -r requirements.txt 
COPY . /app 
EXPOSE 8000
CMD ["bash", "entrypoint.sh"]