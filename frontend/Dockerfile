FROM node:20 AS build

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json* ./
RUN npm install

# Copy the rest of the application code
COPY . .

# Build the frontend application
RUN npm run build

# Use a lightweight web server to serve the built frontend
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf