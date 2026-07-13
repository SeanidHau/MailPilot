# MailPilot

MailPilot 是一个面向实际使用的智能邮件工作台 MVP。它将邮箱同步、AI 邮件处理、摘要、提醒、回复草稿和用户确认后的邮件发送整合到一个 Web 应用中。

默认使用本地 Mock AI 提供商，因此不配置外部模型 API 也可以运行。用户可以在设置页按账号配置 OpenAI 兼容接口或 Anthropic。

## 功能概览

- 用户注册、登录、JWT 认证和按用户隔离数据
- Gmail OAuth 与 Microsoft Graph OAuth，访问令牌和刷新令牌加密存储
- Gmail/Outlook 收件箱同步、服务商消息 ID 去重、已读状态同步
- JSON 文件或文本数据导入邮件
- 自动分类：重要、普通、促销、账单、学业/工作、待回复、垃圾邮件
- 重要程度评分、多信号垃圾邮件检测、中文摘要
- 提取截止日期、会议、付款和待回复任务，生成提醒
- 按正式、简洁、礼貌拒绝、询问信息等语气生成回复草稿
- 主动写邮件、草稿编辑、删除、选择发送邮箱和确认发送
- 仪表盘统计、审计日志、搜索、筛选、排序、分页和批量操作
- 导入、同步和 AI 处理使用后台任务，并持久化任务进度

## 页面

- 仪表盘：待处理邮件、重要邮件、待办提醒和无数据引导
- 邮件：搜索、分类筛选、已读筛选、重要性筛选、按接收时间/重要性排序
- 邮件详情：正文、摘要、AI 操作、草稿和提醒
- 草稿：回复草稿、主动写邮件、编辑、发送确认和失败重试
- 提醒：截止日期、完成、软删除、多选、批量完成和批量删除
- 设置：AI 提供商、JSON 导入、Gmail 连接和 Outlook 连接

## 整体架构

```text
React + TypeScript + Vite
        |
        | REST / JSON，通过 /api 代理
        v
FastAPI + SQLAlchemy + Alembic
        |
        +-- PostgreSQL
        +-- AI：Mock / OpenAI 兼容接口 / Anthropic
        +-- 进程内后台任务执行器
```

后端负责认证、权限、数据校验、邮箱服务商集成、后台任务记录和敏感信息加密。前端使用 TanStack Query 管理服务端状态，使用 React Router 管理页面和登录保护。

## 环境要求

- Python 3.9 或更高版本
- Node.js 18 或更高版本
- Docker 和 Docker Compose（用于本地 PostgreSQL）

## 快速开始

### 1. 启动 PostgreSQL

在项目根目录执行：

```bash
docker compose up -d db
```

### 2. 配置后端

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

本地首次运行可以保留默认的 `AI_PROVIDER=mock`。在本地开发之外的环境中，请先配置稳定密钥：

```bash
# 生成 JWT_SECRET_KEY
python3 -c "import secrets; print(secrets.token_hex(32))"

# 生成 ENCRYPTION_KEY
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

第一条命令的结果用于 `JWT_SECRET_KEY`，第二条用于 `ENCRYPTION_KEY`。数据库中存在加密的 AI Key 或 OAuth Token 后，不能随意更换 `ENCRYPTION_KEY`。

### 3. 执行迁移并启动后端

```bash
cd backend
source .venv/bin/activate
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

API 地址：`http://localhost:8000/api/`。OpenAPI 文档：`http://localhost:8000/docs`。

### 4. 启动前端

新开终端执行：

```bash
cd frontend
npm install
npm run dev
```

访问 `http://localhost:5173`。Vite 会将 `/api` 请求代理到 `http://localhost:8000`。

### 5. 创建本地数据

可以直接在页面注册，也可以使用 CLI 创建本地 demo 账号：

```bash
cd backend
source .venv/bin/activate
mailpilot seed
```

默认 demo 账号：

```text
邮箱：  demo@mailpilot.dev
密码：  demo123
```

常用选项：

```bash
mailpilot seed --email admin@example.com --password changeme
mailpilot seed --no-ai
mailpilot seed --no-drafts --no-reminders
mailpilot reset --yes --seed
```

`mailpilot reset` 会删除所有表并重新执行迁移，仅用于本地开发。对于非本机数据库，必须显式传入 `--force` 才允许重置。

## 配置项

完整模板见 [backend/.env.example](backend/.env.example)。常用配置如下：

| 变量 | 默认值 | 说明 |
|---|---|---|
| `DATABASE_URL` | 本地 PostgreSQL URL | SQLAlchemy 数据库连接地址 |
| `AI_PROVIDER` | `mock` | 后端默认提供商：`mock`、`openai`、`anthropic` |
| `OPENAI_API_KEY` | 空 | OpenAI 兼容接口 Key |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | OpenAI 兼容接口地址 |
| `OPENAI_MODEL` | `gpt-4o` | OpenAI 兼容模型 |
| `ANTHROPIC_API_KEY` | 空 | Anthropic Key |
| `ANTHROPIC_BASE_URL` | `https://api.anthropic.com` | Anthropic 接口地址 |
| `ANTHROPIC_MODEL` | `claude-sonnet-4-5-20250929` | Anthropic 模型 |
| `AI_REQUEST_TIMEOUT` | `30` | AI 请求超时时间，单位秒 |
| `AI_MAX_RETRIES` | `1` | 可重试 AI 错误的最大重试次数 |
| `AI_RATE_LIMIT_PER_MINUTE` | `30` | AI 提供商全局请求限流 |
| `JWT_SECRET_KEY` | `change-me-in-production` | JWT 签名密钥 |
| `ENCRYPTION_KEY` | 空 | 加密 API Key 和 OAuth Token 的 Fernet 密钥 |
| `CORS_ORIGINS` | `http://localhost:5173` | 允许的跨域来源，逗号分隔 |
| `VITE_API_BASE_URL` | `/api` | 前端 API 基础地址 |

AI Key 在设置页按用户保存，并在数据库中加密。环境变量中的 AI 配置用于用户尚未保存个人配置时的默认值。

## Gmail 和 Outlook 配置

要使用真实邮箱同步和发送，必须先配置服务商 OAuth 凭证。

### 通过 Vite 代理的本地回调地址

在服务商控制台登记以下精确地址：

```text
Google：    http://localhost:5173/api/gmail/oauth/callback
Microsoft： http://localhost:5173/api/outlook/oauth/callback
```

然后在 `backend/.env` 中配置：

```dotenv
GMAIL_CLIENT_ID=...
GMAIL_CLIENT_SECRET=...
OUTLOOK_CLIENT_ID=...
OUTLOOK_CLIENT_SECRET=...
```

默认 scope 包含 Gmail 读写/发送权限，以及 Microsoft Graph 的 `Mail.Read` 和 `Mail.Send`。OAuth 使用签名 state 和 HttpOnly nonce Cookie 防止 CSRF，Token 加密后才会落库。

如果前端通过 `VITE_API_BASE_URL=http://localhost:8000/api` 直接访问后端，则登记：

```text
Google：    http://localhost:8000/api/gmail/oauth/callback
Microsoft： http://localhost:8000/api/outlook/oauth/callback
```

生产环境请将 `GMAIL_REDIRECT_URI` 和 `OUTLOOK_REDIRECT_URI` 设置为已在 Google/Microsoft 控制台登记的公网回调地址，并参考 [docs/production.md](docs/production.md) 管理密钥和执行密钥轮换。

## API 概览

除公开接口外，数据接口均需要 `Authorization: Bearer <token>`。完整接口定义可访问 `/docs`。

### 系统和认证

```text
GET  /api/health
POST /api/auth/register
POST /api/auth/login
GET  /api/auth/me
```

### 邮件和 AI 处理

```text
POST /api/emails/import                  将内置 mock 导入任务放入后台
POST /api/emails/import/upload            将 JSON 邮件导入任务放入后台
GET  /api/emails                         列表、筛选、排序和分页
PATCH /api/emails/{id}                   更新已读、分类、重要性
POST /api/emails/bulk                    批量标记已读或软删除
GET  /api/emails/{id}                   邮件详情，含草稿和提醒
POST /api/emails/{id}/classify           处理单封邮件分类
POST /api/emails/{id}/summarize          处理单封邮件摘要
POST /api/emails/process-ai              后台处理尚未完成的邮件
```

`GET /api/emails` 支持 `q`、`category`、`is_read`、`min_importance`、`max_importance`、`sort_by`、`sort_order`、`page` 和 `page_size`。`sort_by` 可选 `received_at` 或 `importance`，默认按 `received_at` 倒序。

### 草稿和发送

```text
POST /api/emails/{id}/drafts             根据已有邮件生成回复草稿
POST /api/drafts                         创建一封主动写邮件草稿
GET  /api/drafts                         草稿列表
GET  /api/drafts/{id}                    草稿详情
PATCH /api/drafts/{id}                   编辑正文、收件人、主题或状态
DELETE /api/drafts/{id}                  软删除草稿
POST /api/drafts/{id}/send               用户确认后发送草稿
```

发送请求可指定 `{"provider":"gmail"}` 或 `{"provider":"outlook"}`。前端只有在邮箱已连接并完成确认后才会发送。可发送状态为 `draft`、`saved`、`ready_to_send` 和 `send_failed`，成功后变为 `sent`。

### 提醒和仪表盘

```text
GET  /api/reminders
PATCH /api/reminders/{id}
DELETE /api/reminders/{id}
POST /api/reminders/bulk                 批量完成或删除选中的提醒
POST /api/emails/{id}/reminders/extract  从单封邮件提取提醒
GET  /api/dashboard/summary
```

### 邮箱连接和后台任务

```text
GET    /api/gmail/authorize
GET    /api/gmail/oauth/callback
GET    /api/gmail/status
POST   /api/gmail/refresh
DELETE /api/gmail/disconnect

GET    /api/outlook/authorize
GET    /api/outlook/oauth/callback
GET    /api/outlook/status
POST   /api/outlook/refresh
DELETE /api/outlook/disconnect

POST /api/sync/gmail
POST /api/sync/outlook
GET  /api/jobs/{id}
GET  /api/jobs/active?job_type=ai_process
```

导入、同步和 AI 处理接口返回任务 ID。客户端可以轮询任务接口，读取 `queued`、`running`、`completed`、`failed` 状态及进度数据。

### 设置、反馈和审计

```text
GET  /api/settings/ai
PUT  /api/settings/ai
GET  /api/feedback
GET  /api/audit
```

## 数据和安全

- 用户密码使用 bcrypt 哈希存储。
- API 使用 JWT 认证。
- 邮件、草稿、提醒、反馈、设置、OAuth 账号、审计和任务查询均按当前用户隔离。
- AI API Key 以及 Gmail/Outlook access token、refresh token 使用 Fernet 加密存储。
- OAuth 使用签名 state 和 HttpOnly nonce Cookie 防止 CSRF。
- 分类修改、AI 操作、导入、草稿发送和批量操作会记录审计日志。
- Gmail/Outlook 同步目前只保存附件元数据，不索引或摘要附件内容。

## 测试

后端测试覆盖认证、用户隔离、加密、OAuth state/token、AI 提供商、重试、同步解析、垃圾邮件检测、后台任务、草稿发送、提醒和 API 校验。

```bash
cd backend
source .venv/bin/activate
pytest -q
```

前端类型检查和生产构建：

```bash
cd frontend
npm run build
```

数据库迁移验证：

```bash
cd backend
alembic upgrade head
```

## 项目结构

```text
backend/
  app/
    ai/                 AI 提供商、提示词、解析、重试、垃圾邮件规则
    api/                FastAPI 路由和认证依赖
    db/                 SQLAlchemy 模型和数据库会话
    schemas/            Pydantic 请求/响应模型
    services/           业务逻辑、OAuth、同步、任务和发送
  alembic/              数据库迁移
  tests/                后端测试
frontend/
  src/api/              类型化 API 客户端
  src/components/       可复用界面组件
  src/pages/            受保护的应用页面
  src/types/            TypeScript 类型
  src/styles/            全局响应式样式
docs/
  development-plan.md   产品和实现计划
  execution-plan.md     分阶段执行计划
  production.md         生产环境密钥和部署说明
```

## 当前边界和后续路线

- 暂不提取 PDF、图片和 Office 文件内容，仅保存附件元数据。
- 后台任务执行器目前是进程内实现，多实例生产部署前应替换为分布式队列和独立 Worker。
- AI 分类目前结合模型输出和确定性规则，后续可增加训练型分类器与独立评估流水线。
- 暂无团队共享邮箱和组织级权限模型。
- 任务进度目前通过轮询获取，尚未使用 WebSocket 或 Server-Sent Events。

## 相关文档

- [生产环境部署](docs/production.md)
- [开发计划](docs/development-plan.md)
- [执行计划](docs/execution-plan.md)
- [English README](README.md)
