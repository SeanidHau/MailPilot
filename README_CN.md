# MailPilot

MailPilot 是一款智能邮件助手 Web 应用，支持 AI 辅助分类、摘要生成、回复草稿和提醒提取。

项目文档：

- [开发计划](docs/development-plan.md)
- [执行计划](docs/execution-plan.md)
- [生产环境部署](docs/production.md)
- [English](README.md) | [英文文档](README.md)

## 快速开始

### 环境要求

- Python 3.9+
- Node.js 18+
- Docker（用于 PostgreSQL）

### 后端

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 启动 PostgreSQL
docker compose up -d db

# 执行数据库迁移
alembic upgrade head

# 启动服务
uvicorn app.main:app --reload --port 8000
```

API 地址：`http://localhost:8000/api/`

### 前端

```bash
cd frontend
npm install
npm run dev
```

访问地址：`http://localhost:5173`。开发服务器自动将 `/api` 请求代理到后端。

### 运行测试

```bash
cd backend
source .venv/bin/activate
pytest tests/ -v
```

### 本地 demo 数据 CLI

后端安装后自带一个本地 demo 数据 seed/reset 命令行工具。

```bash
cd backend
source .venv/bin/activate

# 填充 demo 数据（创建 demo 用户、导入 mock 邮件、运行 AI 处理）
mailpilot seed

# 重置数据库并重新填充 demo 数据。PostgreSQL 下会执行 Alembic 迁移，
# 因此只有迁移里定义的对象（例如部分索引）也会被重建。
mailpilot reset --yes --seed

# 使用自定义 demo 用户
mailpilot seed --email admin@example.com --password changeme

# 跳过 AI 分类/摘要/草稿/提醒，以节省时间或 API 额度
mailpilot seed --no-ai
```

**默认 demo 用户：** `demo@mailpilot.dev` / `demo123`  
**安全保护：** `mailpilot reset` 默认仅允许 localhost/127.0.0.1 的 SQLite 或 PostgreSQL 数据库。非本地数据库需要加 `--force` 才会执行；未加 `--yes` 时仍会提示确认。  
**注意：** `mailpilot reset` 会删除并重建所有表，请仅在本地开发环境使用。

## 环境变量

| 变量 | 默认值 | 说明 |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://mailpilot:mailpilot@localhost:5432/mailpilot` | 数据库连接字符串 |
| `AI_PROVIDER` | `mock` | 默认 AI 提供商（`mock`、`openai` 或 `anthropic`） |
| `CORS_ORIGINS` | `http://localhost:5173` | 逗号分隔的跨域来源 |
| `OPENAI_API_KEY` | 空 | 默认 OpenAI 兼容 API Key |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | 默认 OpenAI 兼容 Base URL |
| `OPENAI_MODEL` | `gpt-4o` | 默认 OpenAI 兼容模型 |
| `ANTHROPIC_API_KEY` | 空 | 默认 Anthropic API Key |
| `ANTHROPIC_BASE_URL` | `https://api.anthropic.com` | 默认 Anthropic Base URL |
| `ANTHROPIC_MODEL` | `claude-sonnet-4-5-20250929` | 默认 Anthropic 模型 |
| `AI_REQUEST_TIMEOUT` | `60.0` | OpenAI 兼容和 Anthropic 调用的单次请求超时，单位秒 |
| `AI_MAX_RETRIES` | `2` | AI 提供商可重试失败的最大重试次数 |
| `AI_RATE_LIMIT_PER_MINUTE` | `30` | 全局 AI 提供商请求限流 |
| `JWT_SECRET_KEY` | 未配置时自动生成 | JWT 签名密钥。非本地开发环境应配置稳定密钥 |
| `ENCRYPTION_KEY` | 未配置时自动生成 | 用于加密存储 AI API Key 的 Fernet 密钥。必须保持稳定，否则重启后无法解密旧值 |
| `GMAIL_CLIENT_ID` | 空 | Gmail 集成使用的 Google OAuth client ID |
| `GMAIL_CLIENT_SECRET` | 空 | Gmail 集成使用的 Google OAuth client secret |
| `GMAIL_REDIRECT_URI` | `http://localhost:8000/api/gmail/oauth/callback` | Google OAuth 回调地址，必须与 Google Cloud OAuth client 配置一致 |
| `GMAIL_SCOPES` | `openid email https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/gmail.send` | 空格分隔的 Google OAuth scope |
| `GMAIL_OAUTH_SUCCESS_URL` | `http://localhost:5173/settings?gmail=connected` | Gmail OAuth 成功后跳回的前端地址 |
| `GMAIL_OAUTH_FAILURE_URL` | `http://localhost:5173/settings?gmail=error` | Gmail OAuth 失败后跳回的前端地址 |
| `OUTLOOK_CLIENT_ID` | 空 | Outlook / Microsoft Graph 集成使用的 Microsoft OAuth client ID |
| `OUTLOOK_CLIENT_SECRET` | 空 | Outlook / Microsoft Graph 集成使用的 Microsoft OAuth client secret |
| `OUTLOOK_REDIRECT_URI` | `http://localhost:8000/api/outlook/oauth/callback` | Microsoft OAuth 回调地址，必须与 Azure 应用注册配置一致 |
| `OUTLOOK_SCOPES` | `offline_access User.Read Mail.Read Mail.Send` | 空格分隔的 Microsoft Graph OAuth scope |
| `OUTLOOK_OAUTH_SUCCESS_URL` | `http://localhost:5173/settings?outlook=connected` | Outlook OAuth 成功后跳回的前端地址 |
| `OUTLOOK_OAUTH_FAILURE_URL` | `http://localhost:5173/settings?outlook=error` | Outlook OAuth 失败后跳回的前端地址 |
| `VITE_API_BASE_URL` | `/api` | 前端 API 基础 URL |

## API 端点

### 健康检查
- `GET /api/health`

### 认证
- `POST /api/auth/register` — 注册用户并返回 JWT
- `POST /api/auth/login` — 登录并返回 JWT
- `GET /api/auth/me` — 获取当前用户信息，需要 Bearer token

### 邮件
- `POST /api/emails/import` — 导入模拟邮件数据
- `GET /api/emails` — 邮件列表（支持 `q`、`category`、`is_read`、`min_importance`、`max_importance`、`page`、`page_size` 参数）
- `GET /api/emails/{id}` — 邮件详情（含草稿和提醒）
- `PATCH /api/emails/{id}` — 更新已读状态、分类或重要性评分
- `POST /api/emails/{id}/classify` — AI 自动分类
- `POST /api/emails/{id}/summarize` — AI 生成摘要
- `POST /api/emails/{id}/drafts` — 生成回复草稿（请求体：`{"tone": "formal|brief|polite_decline|ask_info"}`）
- `POST /api/emails/{id}/reminders/extract` — 从邮件中提取提醒

### 草稿
- `GET /api/drafts` — 草稿列表
- `GET /api/drafts/{id}` — 草稿详情
- `PATCH /api/drafts/{id}` — 更新草稿内容或状态

### 提醒
- `GET /api/reminders` — 提醒列表（支持 `status` 筛选）
- `PATCH /api/reminders/{id}` — 更新提醒（完成等）
- `DELETE /api/reminders/{id}` — 软删除提醒

### 仪表盘
- `GET /api/dashboard/summary` — 仪表盘统计数据

### 反馈
- `GET /api/feedback` — 分类变更历史

### 设置
- `GET /api/settings/ai` — 读取 AI 提供商配置。已登录时读取当前用户配置，未登录时返回默认配置
- `PUT /api/settings/ai` — 保存按用户隔离、加密存储的 AI 提供商配置，需要 Bearer token

### Gmail
- `GET /api/gmail/authorize` — 生成 Google OAuth 授权地址，需要 Bearer token
- `GET /api/gmail/oauth/callback` — Google OAuth 回调；交换授权码，加密存储 token，然后跳回前端
- `GET /api/gmail/status` — 读取当前用户 Gmail 连接状态，需要 Bearer token
- `POST /api/gmail/refresh` — 强制刷新当前用户 Gmail access token，需要 Bearer token
- `DELETE /api/gmail/disconnect` — 删除当前用户已保存的 Gmail token，需要 Bearer token

### Outlook / Microsoft Graph
- `GET /api/outlook/authorize` — 生成 Microsoft OAuth 授权地址，需要 Bearer token
- `GET /api/outlook/oauth/callback` — Microsoft OAuth 回调；交换授权码，加密存储 token，然后跳回前端
- `GET /api/outlook/status` — 读取当前用户 Outlook 连接状态，需要 Bearer token
- `POST /api/outlook/refresh` — 强制刷新当前用户 Outlook access token，需要 Bearer token
- `DELETE /api/outlook/disconnect` — 删除当前用户已保存的 Outlook token，需要 Bearer token

### 邮箱同步
- `POST /api/sync/gmail` — 从 Gmail 收件箱同步邮件，按 provider message ID 去重，需要 Bearer token
- `POST /api/sync/outlook` — 从 Outlook 收件箱同步邮件，按 provider message ID 去重，需要 Bearer token

## 邮件分类

| 分类 | 说明 |
|----------|-------------|
| `important` | 紧急、关键、有截止日期 |
| `normal` | 普通邮件 |
| `promotion` | 营销、折扣、促销活动 |
| `bill` | 发票、付款、订阅 |
| `school_work` | 学业或工作任务 |
| `needs_reply` | 需要回复或确认 |
| `spam` | 可疑或垃圾邮件 |

## 草稿语气

| 语气 | 说明 |
|------|-------------|
| `formal` | 完整专业 |
| `brief` | 简洁直接 |
| `polite_decline` | 礼貌拒绝 |
| `ask_info` | 询问澄清或补充信息 |

## MVP 局限性

- 无高级垃圾邮件检测模型
- 已支持 Gmail/Outlook OAuth 授权及邮箱同步，支持按 provider message ID 去重和已读/未读状态更新
- 不支持自动发送邮件
- 已有用户认证及按用户隔离的数据管理；未登录访问数据 API 返回 401
- AI 提供商已可配置，并支持超时、重试和限流处理，但生产级观测和成本控制尚未完善

## 技术栈

**后端：** FastAPI、SQLAlchemy、Alembic、Pydantic、PostgreSQL

**前端：** React 18、TypeScript、Vite、TanStack Query、React Router

**AI：** 基于规则的 Mock 提供商、OpenAI 兼容提供商、Anthropic 提供商

## TODO

### 账号与数据隐私

- [x] 为 `emails`、`drafts`、`reminders`、`classification_feedback` 增加 `user_id` 归属，并让所有列表、详情、更新、删除 API 按当前用户过滤。
- [x] 在加入用户级数据归属后，明确匿名/demo mock 邮件数据的使用方式。
- [x] 为需要登录的页面和操作增加前端路由保护，尤其是保存 AI 设置和后续真实邮箱数据相关功能。
- [x] 增加认证专项测试：注册、登录、`/auth/me`、重复注册、错误密码、过期/非法 token、退出登录。
- [x] 增加加密专项测试：验证 AI API Key 会加密落库，并能用稳定的 `ENCRYPTION_KEY` 正常解密。

### 邮箱集成

- [x] 实现 Gmail OAuth 授权和 token 刷新。
- [x] 实现 Outlook/Microsoft Graph OAuth 授权和 token 刷新。
- [x] 增加邮箱同步任务：收件箱拉取、增量更新、已读/未读状态同步、按邮箱服务商 message ID 去重。
- [x] 增加手动 JSON 上传/导入 UI，而不是只能导入后端内置 mock 文件。
- [x] 增加附件元数据支持，并明确是否需要索引或摘要附件内容。

### 邮件操作

- [x] 实现从已保存草稿发送真实邮件的可选流程，并加入明确的发送确认步骤。
- [x] 增加草稿发送状态，例如 `ready_to_send`、`sent`、`send_failed`。
- [ ] 增加用户触发邮件操作和 AI 内容编辑的审计日志。

### AI 可靠性

- [x] 为 OpenAI 兼容和 Anthropic 调用增加超时、重试、限流处理。
- [x] 当真实 AI 提供商失败时返回结构化错误，而不是只返回通用 fallback 文本。
- [x] 在核心数据完成用户隔离后，确保后台任务和服务调用也一致使用当前用户的 AI 提供商配置。
- [ ] 为生成的摘要、草稿、分类和提醒提取结果记录 prompt/version 元数据。
- [x] 增加分类准确率、提醒提取质量、回复草稿质量的评估测试，覆盖当前 mock provider 单元测试之外的场景。

### 产品与体验

- [x] 增加新用户引导，串联注册、mock 导入和 AI 提供商配置。
- [x] 用户未登录且尝试保存认证设置时，提供更清晰的设置页状态提示。
- [x] 在未导入任何邮件前，为仪表盘增加更好的空状态。
- [ ] 对完整登录流程做响应式/移动端 QA。

### 运维

- [x] 补充生产环境配置文档，说明稳定 `JWT_SECRET_KEY` 和 `ENCRYPTION_KEY` 的配置方式；轮换 `ENCRYPTION_KEY` 需要再加密方案。
- [x] 增加 CI：后端测试、前端类型检查/构建、基于全新 PostgreSQL 数据库的 Alembic 迁移验证。
- [x] 增加本地 demo 数据 seed/reset 命令。
- [x] 增加认证失败、AI 提供商失败、导入数量、提醒提取数量等日志。
