# ---- Build stage: installs dependencies (npm CLI and its own deps live here only) ----
FROM node:22-alpine AS builder

WORKDIR /app

COPY package.json ./
RUN npm install --omit=dev

COPY . .

# ---- Final stage: clean runtime image, no npm CLI bundled ----
FROM node:22-alpine

WORKDIR /app

# Copy only what's needed to run the app — not npm itself
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app .

RUN chown -R node:node /app
USER node

EXPOSE 3000

CMD ["node", "server.js"]