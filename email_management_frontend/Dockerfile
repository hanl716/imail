# Stage 1: Build the Vue.js application
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./

# Check if node_modules exists and is not empty, to potentially skip npm install if cache is effective
# This is more advanced and might be handled by Docker layer caching itself if package-lock.json doesn't change.
# For simplicity, we run npm install.
RUN npm install

COPY . .
RUN npm run build

# Stage 2: Serve the built application with Nginx
FROM nginx:1.25-alpine
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy the custom Nginx configuration
COPY ./nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
