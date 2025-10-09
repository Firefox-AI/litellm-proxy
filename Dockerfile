# Use a slim Python image for a smaller container
FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file and install dependencies first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Install the package in editable mode to make the `litellm-proxy` executable available
RUN pip install --no-cache-dir -e .

# Expose the application port
EXPOSE 8080

# Run the litellm-proxy command using its full path inside the container
CMD ["/usr/local/bin/litellm-proxy"]
