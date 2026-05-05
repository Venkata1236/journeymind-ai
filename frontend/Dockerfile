# ─── Stage 1: Build React App ─────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .
RUN npm run build


# ─── Stage 2: Serve with Nginx ────────────────────────────────────────────────
FROM nginx:alpine AS runtime

# Copy built React app to nginx html folder
COPY --from=builder /app/dist /usr/share/nginx/html

# Nginx config to handle React Router (SPA routing)
RUN echo 'server { \
    listen 80; \
    location / { \
        root /usr/share/nginx/html; \
        index index.html; \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]