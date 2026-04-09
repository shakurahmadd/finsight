FROM python:3.9-slim
WORKDIR /app
COPY . /app 
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu                                                                                    
RUN pip install -r requirements.txt 
EXPOSE 8000
CMD ["bash", "entrypoint.sh"]