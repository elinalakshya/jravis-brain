# web/Dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY web/package.json web/package-lock.json ./
COPY web/ ./
RUN npm ci
RUN npm run build

FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app/ ./
ENV NODE_ENV=production
EXPOSE 3000
CMD ["npm", "start"]
