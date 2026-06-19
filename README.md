# ChatGPT Clone

这是一个使用 FastAPI 和 Vite (Vue 3 + Element Plus) 构建的类似 ChatGPT 的网页端应用。

## 技术栈

- **后端**: FastAPI, SQLAlchemy, PostgreSQL, asyncpg
- **前端**: Vite, Vue 3, TypeScript, Element Plus, Tailwind CSS
- **部署**: Docker, Docker Compose

## 项目结构

- `backend/`: FastAPI 后端代码。
- `frontend/`: Vue 3 前端代码。
- `docker-compose.yml`: 一键启动配置。

## 如何运行

### 使用 Docker (推荐)

```bash
docker-compose up --build
```

### 本地开发

#### 后端

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

#### 前端

```bash
cd frontend
npm install
npm run dev
```

## 部署到服务器 (CentOS 7.9)

如果您使用的是 CentOS 7.9 服务器，可以使用我们提供的初始化脚本快速搭建环境：

### 1. 初始化环境

```bash
# 下载并运行脚本
chmod +x scripts/setup_centos.sh
./scripts/setup_centos.sh
```

该脚本会自动完成：
- 更新系统软件。
- 安装 Docker 引擎。
- 安装 Docker Compose (V2)。
- 开放防火墙端口 (80, 8000, 5432)。

### 2. 部署应用

```bash
# 进入项目目录
docker-compose up -d --build
```

## GitHub 上传指南

1. 在 GitHub 上创建一个新的仓库。
2. 在本地执行以下命令：

```bash
git init
git add .
git commit -m "Initial commit: ChatGPT clone project structure"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

3. 在 GitHub 仓库设置中配置 `Settings -> Environments`，分别创建 `dev` 和 `prod` 环境，并添加必要的 Secrets (如 `DATABASE_URL`, `OPENAI_API_KEY` 等)。
