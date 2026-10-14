-- 添加手机号字段
ALTER TABLE users ADD COLUMN phone VARCHAR(20);

-- 创建会员表
CREATE TABLE IF NOT EXISTS memberships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    level VARCHAR(20) NOT NULL DEFAULT 'free',
    start_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    expire_date DATETIME,
    auto_renew BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 创建订单表
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_no VARCHAR(32) NOT NULL UNIQUE,
    user_id INTEGER NOT NULL,
    plan VARCHAR(20) NOT NULL,
    amount FLOAT NOT NULL,
    pay_method VARCHAR(20),
    status VARCHAR(20) DEFAULT 'pending',
    paid_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_memberships_user_id ON memberships(user_id);
