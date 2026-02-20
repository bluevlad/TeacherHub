# Build stage
FROM node:18-alpine AS builder
WORKDIR /app

# 1. Copy package files first (for Docker layer caching)
COPY package.json package-lock.json* ./

# 2. Install dependencies (cached if package.json didn't change)
RUN npm ci --production=false

# 3. Copy source code
COPY public ./public
COPY src ./src

# 4. Build
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=builder /app/build /usr/share/nginx/html

# React Router support (SPA fallback)
RUN echo 'server { \
    listen 3000; \
    root /usr/share/nginx/html; \
    index index.html; \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]
