FROM node:20 AS build

WORKDIR /app
COPY . .
RUN npm install && npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html

# Simple proxy config
COPY nginx.conf /etc/nginx/conf.d/default.conf