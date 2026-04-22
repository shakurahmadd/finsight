FROM node:18-alpine AS builder
WORKDIR /frontend
COPY frontend/package.json .
RUN npm install 
COPY frontend/ .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /frontend/dist /usr/share/nginx/html
COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf

