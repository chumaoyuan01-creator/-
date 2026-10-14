# 墨韵 · 文章创作工作台

基于 Flask 的文章/小说 AI 生成网页应用。

## 技术栈

- **后端**: Python 3.12 + Flask 3.1 + Gunicorn
- **数据库**: SQLite（存储于 `/var/lib/flask-app/articles.db`）
- **前端**: 原生 HTML/CSS/JS（响应式布局）
- **反向代理**: Nginx
- **AI 引擎**: DeepSeek API

## 项目结构

```
/home/ubuntu/flask-app/
├── app.py                 # Flask 主应用（路由、认证、频率限制）
├── generator.py           # 模板生成引擎（5 种文体）
├── ai_generator.py        # AI 生成核心逻辑
├── models.py              # 数据库模型（User、Article、Chapter）
├── backup.sh              # 数据库每日备份脚本
├── requirements.txt       # Python 依赖
├── .env                   # 环境变量（SECRET_KEY 等，权限 600）
├── templates/
│   ├── index.html         # 主页面
│   ├── 404.html           # 404 错误页面
│   └── 500.html           # 500 错误页面
└── static/
    └── favicon.svg        # 站点图标
```

## 部署说明

### 环境要求

- Ubuntu 24.04+
- Python 3.12+
- Nginx

### 安装步骤

```bash
# 1. 克隆项目
cd /home/ubuntu
# git clone ...

# 2. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 填入 SECRET_KEY 和 DEEPSEEK_API_KEY
chmod 600 .env

# 5. 创建数据和日志目录
sudo mkdir -p /var/lib/flask-app /var/log/flask-app /var/backups/flask-app
sudo chown -R ubuntu:www-data /var/lib/flask-app /var/log/flask-app /var/backups/flask-app

# 6. 配置 systemd 服务
sudo cp flask-app.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now flask-app

# 7. 配置 Nginx
sudo cp nginx-flask-app.conf /etc/nginx/sites-available/flask-app
sudo ln -s /etc/nginx/sites-available/flask-app /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# 8. 配置每日备份
(crontab -l 2>/dev/null; echo "0 2 * * * /home/ubuntu/flask-app/backup.sh") | crontab -
```

### 服务管理

```bash
# 启动/停止/重启
sudo systemctl start flask-app
sudo systemctl stop flask-app
sudo systemctl restart flask-app

# 查看状态
sudo systemctl status flask-app

# 查看日志
sudo journalctl -u flask-app -f
tail -f /var/log/flask-app/app.log
```

## 安全配置

- **会话密钥**: 通过 `.env` 文件的 `SECRET_KEY` 环境变量配置
- **Debug 模式**: 生产环境已关闭，仅当 `FLASK_ENV=development` 时启用
- **登录校验**: 所有 AI 生成和文章管理接口需要登录
- **频率限制**: AI 生成接口 3-10 次/分钟，注册 10 次/分钟，登录 20 次/分钟
- **安全响应头**: X-Frame-Options、X-Content-Type-Options、X-XSS-Protection 等
- **数据库权限**: 640，属主 ubuntu:www-data

## 备份策略

- 每日凌晨 2:00 自动备份数据库到 `/var/backups/flask-app/`
- 备份文件格式: `articles_YYYYMMDD_HHMMSS.db.gz`
- 保留最近 30 天的备份

## 日志

- 应用日志: `/var/log/flask-app/app.log`（按日轮转，保留 30 天）
- 备份日志: `/var/log/flask-app/backup.log`
- 系统日志: `journalctl -u flask-app`
