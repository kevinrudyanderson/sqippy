FROM python:3.12-slim

# Set consistent working directory
WORKDIR /code

# Copy requirements first for better caching
COPY ./requirements.txt /code/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy the entire project (including app directory)
COPY ./app /code/app

# Add the code directory to Python path
ENV PYTHONPATH=/code

# Expose port 80
EXPOSE 80

# Run the FastAPI application
CMD ["fastapi", "run", "app/main.py", "--proxy-headers", "--port", "80", "--host", "0.0.0.0"]