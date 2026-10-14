# 墨韵 · AI 智能写作平台 — API 接口文档

## 基础信息

- 基础路径：`http://115.159.118.54`
- 认证方式：Session Cookie（Flask-Login）
- 频率限制：AI 生成接口 3-10 次/分钟，注册 10 次/分钟，登录 20 次/分钟

## 页面路由

| 方法 | 路径 | 说明 | 登录 |
|------|------|------|------|
| GET | `/` | 首页（创作工作台） | 否 |
| GET | `/history` | 创作历史页 | 否 |
| GET | `/article/<id>` | 文章详情页 | 否 |

## 用户认证

| 方法 | 路径 | 说明 | 登录 |
|------|------|------|------|
| POST | `/api/register` | 注册 | 否 |
| POST | `/api/login` | 登录 | 否 |
| POST | `/api/logout` | 登出 | 否 |
| GET | `/api/user/status` | 用户状态 | 否 |

### 注册
```json
POST /api/register
{"username": "test", "password": "123456"}
→ {"message": "注册成功", "username": "test"}
```

### 登录
```json
POST /api/login
{"username": "test", "password": "123456"}
→ {"message": "登录成功", "username": "test"}
```

## AI 生成

| 方法 | 路径 | 说明 | 登录 | 频率限制 |
|------|------|------|------|----------|
| GET | `/api/ai/test` | AI 连接测试 | ✅ | - |
| POST | `/api/ai/generate` | 短篇生成（异步） | ✅ | 5/分钟 |
| POST | `/api/ai/generate/long` | 长篇生成（异步） | ✅ | 3/分钟 |
| POST | `/api/ai/outline` | 大纲生成 | ✅ | 5/分钟 |
| POST | `/api/ai/generate/chapter` | 章节生成 | ✅ | 10/分钟 |
| POST | `/api/generate/async` | 异步生成 | ✅ | 3/分钟 |
| GET | `/api/generate/status/<id>` | 任务状态 | ✅ | - |
| POST | `/api/generate/cancel/<id>` | 取消任务 | ✅ | - |

### 短篇生成
```json
POST /api/ai/generate
{"genre": "散文", "topic": "秋天", "keyword": "银杏", "length": "medium"}
→ {"task_id": "uuid", "status": "pending"}
```

## 文章管理

| 方法 | 路径 | 说明 | 登录 |
|------|------|------|------|
| GET | `/api/articles` | 文章列表 | 否（游客返回空） |
| GET | `/api/articles/<id>` | 文章详情 | ✅ |
| PUT | `/api/articles/<id>/rename` | 重命名 | ✅ |
| POST | `/api/articles/<id>/favorite` | 收藏切换 | ✅ |
| DELETE | `/api/articles/<id>` | 删除 | ✅ |
| POST | `/api/articles/<id>/chapters` | 添加章节 | ✅ |
| PUT | `/api/articles/<id>/chapters/<cid>` | 更新章节 | ✅ |
| POST | `/api/articles/<id>/chapters/<cid>/regenerate` | 重新生成章节 | ✅ |

## 导出与评分

| 方法 | 路径 | 说明 | 登录 |
|------|------|------|------|
| GET | `/api/articles/<id>/export/word` | Word 导出 | ✅ |
| GET | `/api/articles/<id>/export/pdf` | PDF 导出 | ✅ |
| GET | `/api/articles/<id>/score` | 文章评分 | ✅ |

## 会员与支付

| 方法 | 路径 | 说明 | 登录 |
|------|------|------|------|
| GET | `/api/membership/plans` | 套餐列表 | 否 |
| GET | `/api/membership/status` | 会员状态（含到期提醒） | ✅ |
| GET | `/api/membership/check-generate` | 今日剩余次数 | ✅ |
| POST | `/api/orders/create` | 创建订单 | ✅ |
| POST | `/api/orders/<no>/pay` | 模拟支付 | ✅ |
| GET | `/api/orders` | 订单列表 | ✅ |

### 套餐列表
```json
GET /api/membership/plans
→ {"plans": {"basic_monthly": {"amount": 19, "days": 30, "level": "basic"}, ...}}
```

### 会员状态
```json
GET /api/membership/status
→ {"membership": {"level": "free"}, "daily_limit": 3, "reminder": null}
```

## 系统

| 方法 | 路径 | 说明 | 登录 |
|------|------|------|------|
| GET | `/api/genres` | 体裁列表 | 否 |
| GET | `/health` | 健康检查 | 否 |
| GET | `/metrics` | Prometheus 指标 | 否 |

## 错误码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 302 | 重定向（未登录） |
| 400 | 参数错误 |
| 401 | 未授权 |
| 404 | 资源不存在 |
| 429 | 频率限制 / 次数用完 |
| 500 | 服务器错误 |
