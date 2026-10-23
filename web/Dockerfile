# syntax=docker/dockerfile:1
FROM node:24.22.1-alpine AS base
WORKDIR /app
COPY web/package.json /app/package.json
COPY web/package-lock.json /app/package-lock.json
RUN npm ci --ignore-scripts
COPY web /app

# Development uses vite dev server
EXPOSE 5173
CMD ["npm","run","dev","--","--host","0.0.0.0"]

