# 使用 Ubuntu 22.04 作为基础镜像（推荐使用，比 CentOS 7.9 更新且维护更简单）
FROM ubuntu:22.04

# 设置工作目录
WORKDIR /app

# 1. 设置非交互模式，防止 apt-get install 时出现交互式提示
ENV DEBIAN_FRONTEND=noninteractive

# 2. 配置国内 apt 镜像源（阿里云源）
RUN sed -i 's/archive.ubuntu.com/mirrors.aliyun.com/g' /etc/apt/sources.list && \
    sed -i 's/security.ubuntu.com/mirrors.aliyun.com/g' /etc/apt/sources.list

# 3. 更新软件包并安装 Python 3 和依赖
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    gcc \
    make \
    libpq-dev \
    git \
    wget \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 4. 升级 pip 并安装后端依赖
# 使用国内阿里云源加速
COPY requirements.txt .
RUN pip3 install --no-cache-dir --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/ && \
    pip3 install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 5. tiktoken 编码文件由代码层自动处理（rag/service.py 中 monkey-patch 降级方案）
#    无需在构建时预下载（国内网络无法访问 Azure Blob Storage）

# 6. 复制项目源代码到镜像中
# 注意：代码里使用了 from backend.xxx import ... 这种包路径，
# 所以镜像内也要保留 /app/backend 这一层目录。
COPY . ./backend

# 7. 暴露容器内部的 8000 端口
EXPOSE 8000

# 8. 启动 FastAPI 服务
CMD ["python3", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
