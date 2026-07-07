# MailPilot

MailPilot 是一款智能邮件助手 Web 应用，支持 AI 辅助分类、摘要生成、回复草稿和提醒提取。

项目文档：

- [开发计划](docs/development-plan.md)
- [执行计划](docs/execution-plan.md)
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

## 环境变量

| 变量 | 默认值 | 说明 |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://mailpilot:mailpilot@localhost:5432/mailpilot` | 数据库连接字符串 |
| `AI_PROVIDER` | `mock` | AI 提供商（当前仅支持 `mock`） |
| `CORS_ORIGINS` | `http://localhost:5173` | 逗号分隔的跨域来源 |
| `VITE_API_BASE_URL` | `/api` | 前端 API 基础 URL |

## API 端点

### 健康检查
- `GET /api/health`

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

- 不支持 Gmail 或 Outlook 集成（仅支持 mock JSON 导入）
- 无 OAuth 或多用户认证
- 不支持自动发送邮件
- 基于规则的 AI 提供商（关键词 + 正则）；尚未接入真实大模型
- 无高级垃圾邮件检测模型

## 技术栈

**后端：** FastAPI、SQLAlchemy、Alembic、Pydantic、PostgreSQL

**前端：** React 18、TypeScript、Vite、TanStack Query、React Router

**AI：** 基于规则的 Mock 提供商，预留真实大模型 API 扩展接口
