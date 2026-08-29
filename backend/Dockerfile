FROM node:22-alpine

WORKDIR /app

COPY package.json ./
RUN npm install --omit=dev

COPY . .

# Alpine's node:* images already include a built-in non-root "node" user —
# no need to create one manually (that required groupadd/useradd, which
# don't exist on Alpine). This also satisfies the earlier Semgrep
# "missing-user" finding.
RUN chown -R node:node /app
USER node

EXPOSE 3000

CMD ["node", "server.js"]