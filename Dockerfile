# Use an official Python runtime as a parent image.
FROM python:3.12-alpine

# Set environment variables for Python to improve Docker behavior
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set the working directory inside the container.
# All subsequent commands will run from this directory.
WORKDIR /app

# Install any necessary system dependencies for Python packages.
# For example, if your Python packages require build tools or specific libraries.
# This step is optional and depends on your specific Python dependencies.
# RUN apk add --no-cache gcc musl-dev python3-dev

# Create a non-root user and group
# 'addgroup -S appgroup' creates a system group named 'appgroup'
# 'adduser -S appuser -G appgroup' creates a system user 'appuser' and adds them to 'appgroup'
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

# Set the ownership of the /app directory to the new user and group.
# This ensures the non-root user has permissions to read/write in the working directory.
RUN chown -R appuser:appgroup /app

# Switch to the non-root user.
# All subsequent commands will be run as 'appuser'.
USER appuser

# Copy the requirements.txt file into the container's working directory.
# This is done separately to leverage Docker's layer caching.
# If requirements.txt doesn't change, this layer won't be rebuilt.
COPY requirements.txt .

# Install any Python dependencies specified in requirements.txt.
# The --no-cache-dir flag helps keep the image size small by not storing cache.
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application code into the container's working directory.
# This copies app.py and any other files in your current directory.
COPY . .

# Expose the port your application will run on.
# For a typical Flask application, this is often 5000. Adjust if your app uses a different port.
EXPOSE 5000

# Define the command to run your application when the container starts.
# Option 1: Run directly with Python (suitable for development/simple apps)
CMD ["python", "app.py"]

# Option 2: Recommended for production using Gunicorn (uncomment and adjust if needed)
# First, ensure gunicorn is in your requirements.txt:
# gunicorn
# Then, use this CMD:
# CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
# (Replace 'app:app' with 'your_module_name:your_flask_app_object_name' if different.
# For example, if your Flask app is named 'my_app' in 'main.py', it would be 'main:my_app')
