#!/usr/bin/env python3
"""
数据库迁移管理脚本
用法:
  python migrate.py status          # 查看当前迁移状态
  python migrate.py migrate         # 执行所有未应用的迁移
  python migrate.py rollback <id>   # 回滚到指定迁移版本
  python migrate.py create <name>   # 创建新迁移文件
"""
import os
import sys
import json
import hashlib
from datetime import datetime

MIGRATIONS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'migrations')
MIGRATIONS_TABLE = '_migrations'


def get_db():
    from app import app, db
    return app, db


def ensure_migrations_table(db):
    db.session.execute(db.text(f'''
        CREATE TABLE IF NOT EXISTS {MIGRATIONS_TABLE} (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            checksum TEXT NOT NULL
        )
    '''))
    db.session.commit()


def get_applied_migrations(db):
    result = db.session.execute(db.text(f'SELECT id, name, checksum FROM {MIGRATIONS_TABLE} ORDER BY id'))
    return {row[0]: {'name': row[1], 'checksum': row[2]} for row in result}


def get_migration_files():
    if not os.path.exists(MIGRATIONS_DIR):
        return []
    files = sorted(f for f in os.listdir(MIGRATIONS_DIR) if f.endswith('.sql'))
    return files


def compute_checksum(filepath):
    with open(filepath, 'r') as f:
        return hashlib.sha256(f.read().encode()).hexdigest()[:16]


def cmd_status():
    app, db = get_db()
    with app.app_context():
        ensure_migrations_table(db)
        applied = get_applied_migrations(db)
        files = get_migration_files()

        print(f"{'迁移ID':<40} {'状态':<10} {'名称'}")
        print("-" * 80)
        for f in files:
            mig_id = f.replace('.sql', '')
            status = '已应用' if mig_id in applied else '待应用'
            name = applied[mig_id]['name'] if mig_id in applied else f
            print(f"{mig_id:<40} {status:<10} {name}")

        if not files:
            print("暂无迁移文件")


def cmd_migrate():
    app, db = get_db()
    with app.app_context():
        ensure_migrations_table(db)
        applied = get_applied_migrations(db)
        files = get_migration_files()

        pending = [f for f in files if f.replace('.sql', '') not in applied]
        if not pending:
            print("所有迁移已应用")
            return

        for f in pending:
            mig_id = f.replace('.sql', '')
            filepath = os.path.join(MIGRATIONS_DIR, f)
            checksum = compute_checksum(filepath)

            print(f"应用迁移: {mig_id}")
            with open(filepath, 'r') as sf:
                sql = sf.read()
                for stmt in sql.split(';'):
                    stmt = stmt.strip()
                    if stmt:
                        db.session.execute(db.text(stmt))

            db.session.execute(db.text(
                f"INSERT INTO {MIGRATIONS_TABLE} (id, name, checksum) VALUES (:id, :name, :checksum)"
            ), {'id': mig_id, 'name': f, 'checksum': checksum})
            db.session.commit()
            print(f"  完成: {mig_id}")

        print(f"成功应用 {len(pending)} 个迁移")


def cmd_rollback(target_id):
    app, db = get_db()
    with app.app_context():
        ensure_migrations_table(db)
        applied = get_applied_migrations(db)

        if target_id not in applied:
            print(f"迁移 {target_id} 未应用或不存在")
            return

        rollback_file = os.path.join(MIGRATIONS_DIR, f"{target_id}_rollback.sql")
        if not os.path.exists(rollback_file):
            print(f"回滚文件不存在: {rollback_file}")
            return

        print(f"回滚迁移: {target_id}")
        with open(rollback_file, 'r') as f:
            sql = f.read()
            for stmt in sql.split(';'):
                stmt = stmt.strip()
                if stmt:
                    db.session.execute(db.text(stmt))

        db.session.execute(db.text(f"DELETE FROM {MIGRATIONS_TABLE} WHERE id = :id"), {'id': target_id})
        db.session.commit()
        print(f"已回滚: {target_id}")


def cmd_create(name):
    os.makedirs(MIGRATIONS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    mig_id = f"{timestamp}_{name}"

    mig_file = os.path.join(MIGRATIONS_DIR, f"{mig_id}.sql")
    rollback_file = os.path.join(MIGRATIONS_DIR, f"{mig_id}_rollback.sql")

    with open(mig_file, 'w') as f:
        f.write(f"-- 迁移: {name}\n")
        f.write(f"-- 创建时间: {datetime.now()}\n\n")
        f.write("-- 在此编写 SQL 语句\n")

    with open(rollback_file, 'w') as f:
        f.write(f"-- 回滚: {name}\n")
        f.write(f"-- 创建时间: {datetime.now()}\n\n")
        f.write("-- 在此编写回滚 SQL 语句\n")

    print(f"已创建迁移: {mig_id}")
    print(f"  迁移文件: {mig_file}")
    print(f"  回滚文件: {rollback_file}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]

    if command == 'status':
        cmd_status()
    elif command == 'migrate':
        cmd_migrate()
    elif command == 'rollback':
        if len(sys.argv) < 3:
            print("用法: python migrate.py rollback <migration_id>")
            sys.exit(1)
        cmd_rollback(sys.argv[2])
    elif command == 'create':
        if len(sys.argv) < 3:
            print("用法: python migrate.py create <name>")
            sys.exit(1)
        cmd_create(sys.argv[2])
    else:
        print(f"未知命令: {command}")
        print(__doc__)
        sys.exit(1)
