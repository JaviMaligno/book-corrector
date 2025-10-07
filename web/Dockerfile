# syntax=docker/dockerfile:1
FROM node:20-alpine AS base
WORKDIR /app
COPY web/package.json /app/package.json
COPY web/package-lock.json /app/package-lock.json
RUN npm ci --omit=optional && npm install --no-save @rollup/rollup-linux-x64-musl
COPY web /app

# Development uses vite dev server
EXPOSE 5173
CMD ["npm","run","dev","--","--host","0.0.0.0"]

