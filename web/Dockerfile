FROM node:22-alpine AS build

WORKDIR /app/web

ARG APP_VERSION=1.0.0

COPY web/package.json web/package-lock.json ./
RUN npm ci

COPY web/ .

RUN npm run build

FROM nginx:alpine

ARG APP_VERSION=1.0.0
LABEL org.opencontainers.image.version="${APP_VERSION}"

COPY --from=build /app/web/dist /usr/share/nginx/html
COPY web/nginx.conf /etc/nginx/conf.d/default.conf
COPY web/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

EXPOSE 80

ENTRYPOINT ["/docker-entrypoint.sh"]
