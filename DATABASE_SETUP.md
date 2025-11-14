# 数据库连接配置指南

## 问题诊断

如果遇到 Vercel 和 Supabase 连接问题，请按以下步骤检查：

### 1. 检查 Supabase 数据库连接字符串

在 Supabase 项目设置中获取正确的连接字符串：

1. 登录 [Supabase Dashboard](https://app.supabase.com)
2. 选择你的项目
3. 点击左侧菜单的 "Settings" → "Database"
4. 找到 "Connection string" 部分
5. **重要**: 选择 "Connection pooling" 标签（不是 "Direct connection"）
6. 复制连接字符串，格式类似：
   ```
   postgresql://postgres.[PROJECT-REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
   ```

### 2. 配置 Vercel 环境变量

在 Vercel 项目中设置环境变量：

1. 登录 [Vercel Dashboard](https://vercel.com)
2. 选择你的项目
3. 进入 "Settings" → "Environment Variables"
4. 添加以下环境变量：

   | Name | Value | Environment |
   |------|-------|-------------|
   | `DATABASE_URL` | 你的 Supabase 连接字符串 | Production, Preview, Development |
   | `SECRET_KEY` | Django secret key | Production, Preview, Development |
   | `DEBUG` | `False` | Production |

5. 保存后重新部署项目

### 3. 验证连接字符串格式

确保你的 `DATABASE_URL` 格式正确：

```
postgresql://[user]:[password]@[host]:6543/[database]
```

**关键点**：
- 必须使用端口 `6543`（连接池），而不是 `5432`（直接连接）
- 密码中的特殊字符需要 URL 编码（如 `@` → `%40`，`#` → `%23`）
- 使用 `postgresql://` 前缀（不是 `postgres://`）

### 4. 常见错误及解决方案

#### 错误 1: "SSL connection is required"
**原因**: 缺少 SSL 配置
**解决**: 代码已经添加了 `sslmode: 'require'`，确保使用最新代码

#### 错误 2: "Connection timeout"
**原因**: 使用了错误的端口或主机
**解决**:
- 确认使用端口 6543（连接池）
- 确认主机地址正确（应该是 `*.pooler.supabase.com`）

#### 错误 3: "Authentication failed"
**原因**: 密码错误或格式问题
**解决**:
- 重置 Supabase 数据库密码
- 确保密码中的特殊字符已 URL 编码
- 在 Vercel 中更新 `DATABASE_URL`

#### 错误 4: "too many connections"
**原因**: 连接数超过限制
**解决**:
- 确保使用连接池端口 6543
- 代码已优化 `conn_max_age=60` 适合无服务器环境

### 5. 本地测试

在本地测试数据库连接：

```bash
# 创建 .env 文件
cp .env.example .env

# 编辑 .env，填入你的 DATABASE_URL
nano .env

# 测试连接
python manage.py check --database default

# 运行迁移
python manage.py migrate
```

### 6. 查看 Vercel 部署日志

部署后检查日志以诊断问题：

1. 在 Vercel Dashboard 中选择你的项目
2. 点击 "Deployments"
3. 选择最新的部署
4. 查看 "Build Logs" 和 "Function Logs"
5. 寻找以下调试信息：
   - "Using Supabase pooler connection: ..."
   - "Database configured: ..."
   - 任何错误消息

### 7. 代码中的修复

以下修复已应用到 `settings.py`:

1. ✅ 移除了无效的 `ssl_require=True` 参数
2. ✅ 添加了 `sslmode: 'require'` 到 OPTIONS
3. ✅ 优化了 `conn_max_age=60` 适合 Vercel 无服务器环境
4. ✅ 保留了自动端口转换（5432 → 6543）
5. ✅ 添加了更多调试日志

### 8. 部署清单

在部署前确认：

- [ ] Supabase 项目已创建并运行
- [ ] 数据库连接字符串使用连接池端口 6543
- [ ] Vercel 环境变量 `DATABASE_URL` 已设置
- [ ] Vercel 环境变量 `SECRET_KEY` 已设置
- [ ] 代码已推送到 Git 仓库
- [ ] Vercel 自动部署已触发

### 9. 需要帮助？

如果问题仍然存在：

1. 检查 Supabase 项目是否正常运行（Dashboard 中查看）
2. 在 Vercel Function Logs 中查找具体错误信息
3. 确认 Supabase 项目的区域和 Vercel 部署区域（延迟可能影响连接）
4. 尝试在 Supabase Dashboard 中重置数据库密码

## 相关文档

- [Supabase 连接文档](https://supabase.com/docs/guides/database/connecting-to-postgres)
- [Vercel 环境变量](https://vercel.com/docs/concepts/projects/environment-variables)
- [Django 数据库配置](https://docs.djangoproject.com/en/stable/ref/settings/#databases)
