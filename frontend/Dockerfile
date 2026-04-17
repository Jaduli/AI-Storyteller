FROM node:20 AS build

WORKDIR /app
COPY . .
RUN npm install && npm run build

# Use a lightweight web server to serve the built frontend
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html

COPY nginx.conf /etc/nginx/conf.d/default.conf