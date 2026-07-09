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

### 轮换流程

1. **进入维护窗口，停止服务**（避免并发写）。

2. **备份数据库**。

3. **运行轮换脚本**（服务停止状态），同时传入旧密钥和新密钥：
   ```bash
   OLD_ENCRYPTION_KEY=<旧密钥> NEW_ENCRYPTION_KEY=<新密钥> \
     python3 backend/scripts/rotate_encryption_key.py
   ```

4. **验证**：启动服务并确认敏感数据可正常解密。

5. **更新环境变量**：将 `ENCRYPTION_KEY` 替换为新密钥，启动服务，删除旧密钥。

### 轮换脚本

`backend/scripts/rotate_encryption_key.py`：

```python
"""用旧密钥解密、新密钥重新加密所有已存储的敏感数据。

用法：
  OLD_ENCRYPTION_KEY=<旧密钥> NEW_ENCRYPTION_KEY=<新密钥> python3 rotate_encryption_key.py
"""
import json
import os
import sys

from cryptography.fernet import Fernet

# 显式读取旧/新密钥，不依赖 app.core.crypto 的单密钥模型
old_key = os.environ.get("OLD_ENCRYPTION_KEY")
new_key = os.environ.get("NEW_ENCRYPTION_KEY")
if not old_key or not new_key:
    print("Must set both OLD_ENCRYPTION_KEY and NEW_ENCRYPTION_KEY")
    sys.exit(1)

old_fernet = Fernet(old_key.encode())
new_fernet = Fernet(new_key.encode())

from app.db.session import SessionLocal
from app.db.models import Setting, GmailAccount, OutlookAccount


def rotate():
    db = SessionLocal()
    try:
        # 1. 重新加密 AI 设置中的 API Key
        for row in db.query(Setting).all():
            if not row.value:
                continue
            try:
                data = json.loads(row.value)
            except json.JSONDecodeError:
                continue
            changed = False
            for key in ("openai_api_key", "anthropic_api_key"):
                val = data.get(key, "")
                if not val:
                    continue
                if not val.startswith("gAAAAAB"):
                    # 明文值 → 直接用新密钥加密
                    data[key] = new_fernet.encrypt(val.encode()).decode()
                    changed = True
                else:
                    # Fernet 密文 → 旧密钥解密，新密钥重新加密
                    try:
                        plain = old_fernet.decrypt(val.encode()).decode()
                        data[key] = new_fernet.encrypt(plain.encode()).decode()
                        changed = True
                    except Exception:
                        print(f"  WARNING: cannot decrypt key '{key}' for setting id={row.id}, skipping")
            if changed:
                row.value = json.dumps(data)

        # 2. 重新加密 Gmail Token
        for row in db.query(GmailAccount).all():
            _re_encrypt_token(row, "access_token")
            _re_encrypt_token(row, "refresh_token")

        # 3. 重新加密 Outlook Token
        for row in db.query(OutlookAccount).all():
            _re_encrypt_token(row, "access_token")
            _re_encrypt_token(row, "refresh_token")

        db.commit()
        print("Encryption key rotation complete.")
    finally:
        db.close()


def _re_encrypt_token(row, field: str):
    val = getattr(row, field, None)
    if not val:
        return
    if not val.startswith("gAAAAAB"):
        # 明文 → 新密钥加密
        setattr(row, field, new_fernet.encrypt(val.encode()).decode())
        return
    try:
        plain = old_fernet.decrypt(val.encode()).decode()
        setattr(row, field, new_fernet.encrypt(plain.encode()).decode())
    except Exception:
        print(f"  WARNING: cannot decrypt {field} for {type(row).__name__} id={row.id}, skipping")


if __name__ == "__main__":
    rotate()
```

### 轮换注意事项

- 必须在**服务停止状态**下运行脚本（或维护窗口内禁止写入）
- 脚本同时持有旧密钥和新密钥，用旧密钥解密、新密钥加密
- 明文值（如历史遗留的未加密数据）在轮换中**会被加密**
- 轮换完成后验证解密正常，再更新环境变量并重启服务
- 如果轮换过程中出错，立即回滚到旧密钥，从备份恢复
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
