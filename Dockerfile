FROM python:3.9-slim
WORKDIR /app
COPY . /app 
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu                                                                                    
RUN pip install -r requirements.txt 
EXPOSE 8000
CMD ["bash", "entrypoint.sh"]