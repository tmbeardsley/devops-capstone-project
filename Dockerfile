FROM python:3.9-slim

# Create working folder and install dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application contents
COPY service/ ./service/

# Create a non-root user called theia
RUN useradd --uid 1000 theia

# change the ownership of the /app folder recursively to theia
RUN chown -R theia /app

# switch to the user theia
USER theia

# expose port 8080
EXPOSE 8080

CMD ["gunicorn", "--bind=0.0.0.0:8080", "--log-level=info", "service:app"]