# --- 构建阶段 ---
# 使用 CentOS 7.9 作为基础环境进行编译
FROM centos:7.9.2009 AS build-stage

WORKDIR /app

# 1. 配置 CentOS 7 阿里云 Vault 源
RUN sed -i s/mirror.centos.org/mirrors.aliyun.com/g /etc/yum.repos.d/CentOS-Base.repo && \
    sed -i s/^#.*baseurl=http/baseurl=http/g /etc/yum.repos.d/CentOS-Base.repo && \
    sed -i s/^mirrorlist=http/#mirrorlist=http/g /etc/yum.repos.d/CentOS-Base.repo

# 2. 安装 Node.js (CentOS 7 需要手动配置 NodeSource 源)
RUN curl -sL https://rpm.nodesource.com/setup_20.x | bash - && \
    yum install -y nodejs && \
    yum clean all

# 3. 安装依赖并构建
COPY package*.json ./
# 使用淘宝镜像源加速安装
RUN npm config set registry https://registry.npmmirror.com && \
    npm install

COPY . .
RUN npm run build


# --- 运行阶段 ---
# 同样使用 CentOS 7.9 并在上面安装 Nginx 来提供服务
FROM centos:7.9.2009 AS production-stage

# 1. 配置 CentOS 7 阿里云 Vault 源
RUN sed -i s/mirror.centos.org/mirrors.aliyun.com/g /etc/yum.repos.d/CentOS-Base.repo && \
    sed -i s/^#.*baseurl=http/baseurl=http/g /etc/yum.repos.d/CentOS-Base.repo && \
    sed -i s/^mirrorlist=http/#mirrorlist=http/g /etc/yum.repos.d/CentOS-Base.repo

# 2. 安装 Nginx
RUN yum install -y epel-release && \
    yum install -y nginx && \
    yum clean all

# 3. 将构建好的静态文件复制到 Nginx 目录
COPY --from=build-stage /app/dist /usr/share/nginx/html

# 4. 暴露 80 端口
EXPOSE 80

# 5. 启动 Nginx
CMD ["nginx", "-g", "daemon off;"]
