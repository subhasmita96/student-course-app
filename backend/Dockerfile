FROM node:22-slim

WORKDIR /app

COPY package.json ./
RUN npm install --omit=dev

COPY . .

# Create a dedicated non-root user and switch to it before running the app —
# fixes the Semgrep "missing-user" finding (CWE-250: running as root).
RUN groupadd -r appgroup && useradd -r -g appgroup -d /app -s /sbin/nologin appuser \
    && chown -R appuser:appgroup /app
USER appuser

EXPOSE 3000

CMD ["node", "server.js"]