FROM python:3.11-slim
WORKDIR /app/server
COPY server/ /app/server/
RUN pip install -r requirements.txt
EXPOSE 5000
CMD ["python", "server.py"]
