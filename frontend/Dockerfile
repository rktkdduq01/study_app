# Multi-stage build for optimized React application
# Stage 1: Dependencies
FROM node:24-alpine as deps

# Install build tools for native dependencies
RUN apk add --no-cache libc6-compat python3 make g++

WORKDIR /app

# Copy package files
COPY package*.json yarn.lock* ./

# Install ALL dependencies (including devDependencies for build)
RUN npm ci

# Stage 2: Builder
FROM node:24-alpine as builder

# Build arguments
ARG VITE_API_URL
ARG VITE_WEBSOCKET_URL
ARG VITE_ENVIRONMENT=production
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION=1.0.0

WORKDIR /app

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules

# Copy source code
COPY . .

# Set environment variables for build
ENV VITE_API_URL=$VITE_API_URL \
    VITE_WEBSOCKET_URL=$VITE_WEBSOCKET_URL \
    VITE_ENVIRONMENT=$VITE_ENVIRONMENT \
    NODE_ENV=production

# Build the application with optimizations
RUN npm run build

# Stage 3: Production runtime
FROM nginx:alpine as runtime

# Metadata
LABEL org.opencontainers.image.created=$BUILD_DATE \
      org.opencontainers.image.revision=$VCS_REF \
      org.opencontainers.image.version=$VERSION \
      org.opencontainers.image.title="Quest Education Frontend" \
      org.opencontainers.image.description="Educational gamification platform frontend"

# Install curl for health checks and runtime env substitution
RUN apk add --no-cache curl bash

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf
COPY default.conf /etc/nginx/conf.d/default.conf

# Copy built application from builder
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy environment variable runtime script
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Create nginx cache and run directories
RUN mkdir -p /var/cache/nginx /var/run/nginx

# Create non-root user and set permissions
RUN adduser -D -H -u 1000 -s /sbin/nologin nginx-user && \
    chown -R nginx-user:nginx-user /usr/share/nginx/html && \
    chown -R nginx-user:nginx-user /var/cache/nginx && \
    chown -R nginx-user:nginx-user /var/log/nginx && \
    chown -R nginx-user:nginx-user /var/run/nginx && \
    chown -R nginx-user:nginx-user /etc/nginx/conf.d

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# Switch to non-root user
USER nginx-user

# Expose port
EXPOSE 80

# Use entrypoint for runtime environment variable substitution
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]