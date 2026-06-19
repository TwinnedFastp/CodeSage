#!/bin/bash

# 启动开发环境脚本
echo "正在启动 ChatGPT Clone 开发环境..."

# 检查 docker-compose 是否安装
if ! command -v docker-compose &> /dev/null
then
    echo "错误: 未找到 docker-compose 命令，请先安装。"
    exit 1
fi

# 启动容器
docker-compose up --build
