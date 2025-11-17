FROM node:18-alpine

WORKDIR /app

# Copy package files from correct path
COPY api_service/package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy application code
COPY api_service/ .

# --- Additions for Python API compatibility and dynamic updates ---
# Install Python and pip (since node:18-alpine does not include Python)
RUN apk add --no-cache python3 py3-pip

# Create a virtual environment for Python dependencies
RUN python3 -m venv /pyenv

# Activate venv and install Flask, Flask-Cors, Flask-Sock, watchdog
RUN /pyenv/bin/pip install flask flask-cors flask-sock watchdog

# Add venv to PATH for subsequent RUN/CMD instructions
ENV PATH="/pyenv/bin:$PATH"

# Expose the API/WebSocket port
EXPOSE 3000

# Ensure the API can access the predictions directory
VOLUME ["/app/data_processor_service/final_predictions"]

EXPOSE 8000

VOLUME ["/app/data_processor_service/final_predictions"]
VOLUME ["/app/final_predictions"]

# --- End additions ---

CMD ["node", "server.js"]