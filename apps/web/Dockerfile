# Workbench Ledger web client.
#
# In compose the Vite dev server proxies `/api` to the `api` service by name
# (see vite.config.ts), so the browser only ever talks to relative paths. The
# dev server is the runtime here because the `/api` proxy is a dev-server
# feature; a static production build would move that proxy into a reverse proxy.
FROM node:25-alpine

WORKDIR /app

# Install dependencies first so the layer caches across source-only changes.
COPY package.json package-lock.json* ./
RUN npm install

COPY . .

EXPOSE 5173

# --host so the server is reachable from outside the container; the proxy
# target defaults to http://api:8000 (overridable via VITE_API_PROXY_TARGET).
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
