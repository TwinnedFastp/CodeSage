# 使用 CentOS 7.9 作为基础镜像
FROM centos:7.9.2009

# 设置工作目录
WORKDIR /app

# 1. 解决 CentOS 7 EOL (End of Life) 导致的 yum 源失效问题
# 将 yum 源更换为阿里云的 CentOS 7 Vault 源（因为官方源已关闭）
RUN sed -i s/mirror.centos.org/mirrors.aliyun.com/g /etc/yum.repos.d/CentOS-Base.repo && \
    sed -i s/^#.*baseurl=http/baseurl=http/g /etc/yum.repos.d/CentOS-Base.repo && \
    sed -i s/^mirrorlist=http/#mirrorlist=http/g /etc/yum.repos.d/CentOS-Base.repo

# 2. 安装基础开发工具和依赖
# CentOS 7 默认 Python 版本是 2.7，我们需要安装 Python 3
RUN yum install -y epel-release && \
    yum install -y \
    gcc \
    make \
    openssl-devel \
    bzip2-devel \
    libffi-devel \
    postgresql-devel \
    python3 \
    python3-devel && \
    yum clean all

# 3. 升级 pip 并安装后端依赖
# 提示：CentOS 7 的 python3 可能是 3.6，对于最新版的 FastAPI 建议手动安装 3.9+
# 这里我们先使用系统自带的 python3 (3.6+) 演示
COPY requirements.txt .
RUN pip3 install --no-cache-dir --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip3 install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 4. 复制项目源代码到镜像中
COPY . .

# 5. 暴露容器内部的 8000 端口
EXPOSE 8000

# 6. 启动 FastAPI 服务
# 使用 uvicorn 运行 main.py 中的 app 实例
CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
