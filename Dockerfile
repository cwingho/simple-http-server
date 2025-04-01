FROM python:3.9-slim

WORKDIR /

# Copy the application code
COPY . /

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose the default port
EXPOSE 8000

# Set the entrypoint
ENTRYPOINT ["python", "main.py"]

# Default command (can be overridden)
CMD ["-H", "0.0.0.0", "-p", "8000"] 