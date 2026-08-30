FROM node:22-alpine AS builder

WORKDIR /app

COPY package.json ./
RUN npm install --omit=dev

COPY . .

FROM node:22-alpine

WORKDIR /app

COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app .

# Remove the npm CLI and its bundled dependencies from the final runtime
# image. node:22-alpine ships npm pre-installed regardless of what the
# builder stage does — the app only needs `node` to run, never `npm`,
# and npm's own bundled deps (tar, brace-expansion, pacote, etc.) are
# what Trivy has been flagging this whole time.
RUN rm -rf /usr/local/lib/node_modules/npm \
    /usr/local/bin/npm \
    /usr/local/bin/npx \
    /usr/local/bin/corepack

RUN chown -R node:node /app
USER node

EXPOSE 3000

CMD ["node", "server.js"]