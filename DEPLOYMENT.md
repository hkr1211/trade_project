# 部署说明

## 修复静态文件 404 错误

### 问题原因
Django 管理后台的 CSS 和 JS 文件返回 404 错误,是因为:
1. 使用了 Django 5.2.8,需要使用新的 STORAGES 配置而不是已废弃的 STATICFILES_STORAGE
2. 静态文件没有被收集到 staticfiles 目录
3. Vercel 部署时没有运行 collectstatic 命令

### 已修复的内容
1. ✅ 更新 settings.py 使用 Django 5.x 的 STORAGES 配置
2. ✅ 配置 WhiteNoise 正确服务静态文件
3. ✅ 更新 .gitignore 允许提交 staticfiles 目录
4. ✅ 创建 package.json 配置 Vercel 构建脚本
5. ✅ 创建 build.sh 和 collect_static.py 脚本

### 部署步骤

#### 方法 1: 使用 Vercel 自动构建 (推荐)
Vercel 会在部署时自动运行 `npm run build`,这会收集静态文件。
只需推送代码即可:
```bash
git add .
git commit -m "Fix static files configuration for Django 5.x"
git push
```

#### 方法 2: 手动收集静态文件并提交
如果 Vercel 自动构建不工作,可以手动收集并提交:

1. 安装依赖:
```bash
pip install -r requirements.txt
```

2. 收集静态文件:
```bash
python collect_static.py
# 或者
python manage.py collectstatic --noinput
```

3. 提交并推送:
```bash
git add staticfiles/
git add .
git commit -m "Add collected static files"
git push
```

### 验证
部署后访问管理后台 `/admin/`,页面应该正确显示样式。

### 技术细节
- **Django**: 5.2.8
- **WhiteNoise**: 6.11.0 (处理静态文件服务)
- **配置**: STORAGES["staticfiles"] 使用 CompressedManifestStaticFilesStorage
- **静态文件路径**: /staticfiles/ (由 STATIC_ROOT 配置)
