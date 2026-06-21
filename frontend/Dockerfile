# --- 构建阶段 ---
FROM node:20-bookworm-slim AS build-stage

WORKDIR /app

# 1. 安装依赖并构建
COPY package*.json ./
# 使用淘宝镜像源加速安装
RUN npm config set registry https://registry.npmmirror.com && \
    npm install

COPY . .
RUN npm run build


# --- 运行阶段 ---
# 使用 Nginx 官方镜像（基于 Debian/Ubuntu）来提供服务
FROM nginx:alpine-slim AS production-stage

# 将构建好的静态文件复制到 Nginx 目录
COPY --from=build-stage /app/dist /usr/share/nginx/html

# 覆盖默认 nginx 配置：增加 /api 反向代理到 backend + SSE 流式支持
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露 80 端口
EXPOSE 80

# 启动 Nginx
CMD ["nginx", "-g", "daemon off;"]
