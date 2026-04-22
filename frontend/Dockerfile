FROM node:18-alpine AS builder
WORKDIR /frontend
COPY package.json .
RUN npm install 
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /frontend/dist /usr/share/nginx/html
COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf

