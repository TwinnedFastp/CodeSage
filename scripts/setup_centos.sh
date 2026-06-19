#!/bin/bash

# CentOS 7.9 环境初始化脚本
# 功能：安装 Docker, Docker Compose 并配置防火墙

set -e

echo "开始初始化 CentOS 7.9 环境..."

# 1. 更新系统并安装基础工具
echo "更新系统软件包..."
sudo yum update -y
sudo yum install -y yum-utils device-mapper-persistent-data lvm2 git curl

# 2. 安装 Docker
echo "正在安装 Docker..."
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install -y docker-ce docker-ce-cli containerd.io

# 启动并设置 Docker 开机自启
sudo systemctl start docker
sudo systemctl enable docker

# 3. 安装 Docker Compose
echo "正在安装 Docker Compose..."
DOCKER_COMPOSE_VERSION="v2.24.5"
sudo curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 4. 配置防火墙 (Firewalld)
echo "配置防火墙开放端口..."
# 检查 firewalld 是否在运行
if systemctl is-active --quiet firewalld; then
    sudo firewall-cmd --permanent --add-port=80/tcp
    sudo firewall-cmd --permanent --add-port=8000/tcp
    sudo firewall-cmd --permanent --add-port=5432/tcp
    sudo firewall-cmd --reload
    echo "防火墙端口已开放：80 (前端), 8000 (后端), 5432 (数据库)"
else
    echo "firewalld 未运行，跳过防火墙配置。请确保您的安全组/防火墙已手动开放 80, 8000, 5432 端口。"
fi

echo "------------------------------------------------"
echo "环境初始化完成！"
echo "Docker 版本: $(docker --version)"
echo "Docker Compose 版本: $(docker-compose --version)"
echo "------------------------------------------------"
echo "接下来您可以执行以下步骤部署应用："
echo "1. git clone <您的仓库地址>"
echo "2. cd <项目目录>"
echo "3. docker-compose up -d --build"
