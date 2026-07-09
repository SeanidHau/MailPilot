# MailPilot 生产环境部署

## 环境变量

### 必须配置

| 变量 | 说明 |
|------|------|
| `DATABASE_URL` | PostgreSQL 连接字符串 |
| `JWT_SECRET_KEY` | JWT 签名密钥 |
| `ENCRYPTION_KEY` | Fernet 加密密钥 |

### 密钥生成

```bash
# JWT_SECRET_KEY（随机 64 字符）
python3 -c "import secrets; print(secrets.token_hex(32))"

# ENCRYPTION_KEY（Fernet 格式，44 字符）
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## JWT_SECRET_KEY

**作用：** 签名用户认证 token（HS256）。

**配置：**
```bash
# .env 或环境变量
JWT_SECRET_KEY=<生成的值>
```

**注意事项：**
- 未配置时会自动生成临时密钥并输出警告，**生产环境必须显式设置**
- 所有实例必须使用相同的 `JWT_SECRET_KEY`（多实例部署时保持一致）
- 更换密钥会使所有已签发的 token 失效，所有用户需要重新登录
- 建议轮换周期：90 天，轮换时先在旧密钥有效期内容忍新旧密钥共存

## ENCRYPTION_KEY

**作用：** 加密数据库中存储的敏感数据（AI API Key、Gmail/Outlook OAuth Token）。

**配置：**
```bash
# .env 或环境变量
ENCRYPTION_KEY=<生成的值>
```

**注意事项：**
- 未配置时会自动生成临时密钥并输出警告，**生产环境必须显式设置**
- 启动时密钥固定，**重启后必须使用相同的密钥**，否则无法解密已存储的数据
- 不要将密钥硬编码在代码中，建议通过密钥管理服务（AWS Secrets Manager、HashiCorp Vault 等）注入

## ENCRYPTION_KEY 轮换方案

轮换加密密钥需要重新加密所有已存储的敏感数据，因为旧密文无法用新密钥解密。

### 轮换步骤

1. **部署前备份数据库**

2. **编写迁移脚本** `backend/scripts/rotate_encryption_key.py`：
```python
"""重新加密所有已存储的敏感数据。"""
from app.db.session import SessionLocal
from app.db.models import Setting, GmailAccount, OutlookAccount
from app.core import crypto

def rotate():
    db = SessionLocal()
    try:
        # 1. 重新加密 AI 设置中的 API Key
        for row in db.query(Setting).all():
            if row.value and "openai_api_key" in row.value:
                import json
                data = json.loads(row.value)
                changed = False
                for key in ("openai_api_key", "anthropic_api_key"):
                    val = data.get(key, "")
                    if val and not val.startswith("gAAAAAB"):  # 未加密的明文
                        pass  # 已经是明文则跳过
                    elif val:
                        # 解密旧值，用新密钥重新加密
                        decrypted = crypto.decrypt(val)
                        if decrypted:  # 说明旧密钥还能用
                            data[key] = crypto.encrypt(decrypted)
                            changed = True
                if changed:
                    row.value = json.dumps(data)

        # 2. 重新加密 Gmail Token（同理）
        for row in db.query(GmailAccount).all():
            if row.access_token:
                decrypted = crypto.decrypt(row.access_token)
                if decrypted:
                    row.access_token = crypto.encrypt(decrypted)
            if row.refresh_token:
                decrypted = crypto.decrypt(row.refresh_token)
                if decrypted:
                    row.refresh_token = crypto.encrypt(decrypted)

        # 3. 重新加密 Outlook Token
        for row in db.query(OutlookAccount).all():
            if row.access_token:
                decrypted = crypto.decrypt(row.access_token)
                if decrypted:
                    row.access_token = crypto.encrypt(decrypted)
            if row.refresh_token:
                decrypted = crypto.decrypt(row.refresh_token)
                if decrypted:
                    row.refresh_token = crypto.encrypt(decrypted)

        db.commit()
        print("Encryption key rotation complete.")
    finally:
        db.close()

if __name__ == "__main__":
    rotate()
```

3. **轮换流程：**
   - （A）保持旧 `ENCRYPTION_KEY` 运行
   - （B）部署新密钥到服务器
   - （C）运行 `rotate_encryption_key.py` 脚本，用旧密钥解密、新密钥重新加密
   - （D）验证解密正常：登录后查看 Settings 页面 AI Key 是否正常显示
   - （E）删除旧密钥

### 轮换注意事项

- 必须在服务运行但无并发写操作时执行（建议维护窗口）
- 轮换完成后立即重启服务
- 如果轮换过程中出错，立即回滚到旧密钥
- 密钥永久丢失 = 数据不可恢复 = 用户需要重新输入 API Key 和重新 OAuth 授权

## 数据库迁移

```bash
cd backend
alembic upgrade head
```

## 启动服务

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

生产环境建议使用 Gunicorn + Uvicorn workers，或通过 systemd/Docker 管理进程。
