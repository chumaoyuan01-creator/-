#!/bin/bash
# 每日数据库备份脚本
BACKUP_DIR="/var/backups/flask-app"
DB_FILE="/var/lib/flask-app/articles.db"
RETENTION_DAYS=30

mkdir -p "$BACKUP_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/articles_$TIMESTAMP.db.gz"

if [ -f "$DB_FILE" ]; then
    gzip -c "$DB_FILE" > "$BACKUP_FILE"
    chmod 640 "$BACKUP_FILE"
    echo "[$(date)] Backup created: $BACKUP_FILE" >> /var/log/flask-app/backup.log
    # 清理超过保留天数的备份
    find "$BACKUP_DIR" -name "articles_*.db.gz" -mtime +$RETENTION_DAYS -delete 2>/dev/null
else
    echo "[$(date)] ERROR: Database file not found: $DB_FILE" >> /var/log/flask-app/backup.log
fi
