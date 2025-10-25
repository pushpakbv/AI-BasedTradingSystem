FROM node:18-alpine

WORKDIR /app

# Copy package files from correct path
COPY api_service/package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy application code
COPY api_service/ .

EXPOSE 8000

CMD ["node", "server.js"]