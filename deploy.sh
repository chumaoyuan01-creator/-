#!/bin/bash
# 墨韵 · 文章创作工作台 - 本地部署脚本
# 支持零停机滚动更新

set -e

APP_DIR="/home/ubuntu/flask-app"
SERVICE_NAME="flask-app"
BACKUP_DIR="/var/backups/flask-app"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "[$(date)] ===== 开始部署 (${TIMESTAMP}) ====="

# 1. 备份当前版本
cd "$APP_DIR"
echo "[1/6] 备份当前版本..."
mkdir -p "$BACKUP_DIR/releases"
tar -czf "$BACKUP_DIR/releases/backup_${TIMESTAMP}.tar.gz" \
    --exclude='venv' --exclude='.git' --exclude='__pycache__' \
    --exclude='*.db' --exclude='*.log' \
    app.py generator.py ai_generator.py models.py genre_rules.py \
    templates/ static/ requirements.txt 2>/dev/null || true

# 2. 运行测试
echo "[2/6] 运行自动化测试..."
if [ -f "$APP_DIR/venv/bin/python3" ]; then
    $APP_DIR/venv/bin/python3 -m pytest tests/ -v --tb=short 2>&1 || {
        echo "[ERROR] 测试失败，部署中止"
        exit 1
    }
else
    echo "[WARN] 虚拟环境不存在，跳过测试"
fi

# 3. 语法检查
echo "[3/6] Python 语法检查..."
$APP_DIR/venv/bin/python3 -m py_compile app.py && echo "语法检查通过"

# 4. 重载服务（Gunicorn 支持优雅重启）
echo "[4/6] 重载应用服务..."
sudo -n systemctl reload $SERVICE_NAME 2>/dev/null || {
    echo "[INFO] reload 不支持，使用 restart"
    sudo -n systemctl restart $SERVICE_NAME
}

# 5. 等待服务就绪
echo "[5/6] 等待服务就绪..."
for i in $(seq 1 30); do
    if curl -sf http://127.0.0.1:8000/health > /dev/null 2>&1; then
        echo "服务已就绪"
        break
    fi
    sleep 1
done

# 6. 健康检查
echo "[6/6] 健康检查..."
HEALTH=$(curl -s http://127.0.0.1:8000/health)
echo "$HEALTH"

if echo "$HEALTH" | grep -q '"status":"healthy"'; then
    echo "[$(date)] ===== 部署成功 ====="
else
    echo "[$(date)] ===== 部署异常，请检查 ====="
    exit 1
fi
