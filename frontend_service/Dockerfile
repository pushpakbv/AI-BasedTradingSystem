FROM node:18-alpine as build

WORKDIR /app

# Copy package files
COPY frontend_service/package*.json ./

# Install dependencies
RUN npm ci

# Copy application code
COPY frontend_service/ .

# Build the app
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy build output
COPY --from=build /app/build /usr/share/nginx/html

# Copy nginx configuration
COPY frontend_service/nginx.conf /etc/nginx/conf.d/default.conf

# Copy the startup script
COPY frontend_service/startup.sh /startup.sh
RUN chmod +x /startup.sh

EXPOSE 80

ENTRYPOINT ["/startup.sh"]