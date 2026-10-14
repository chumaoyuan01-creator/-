import json


class TestBasicRoutes:
    """基础路由测试"""

    def test_index_page(self, client):
        """首页应返回 200"""
        resp = client.get('/')
        assert resp.status_code == 200
        assert b'<!DOCTYPE html>' in resp.data

    def test_health_check(self, client):
        """健康检查接口应返回 healthy"""
        resp = client.get('/health')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['status'] == 'healthy'

    def test_404_page(self, client):
        """不存在的路由应返回 404"""
        resp = client.get('/nonexistent-page')
        assert resp.status_code == 404

    def test_genres_api(self, client):
        """体裁列表接口应返回数据"""
        resp = client.get('/api/genres')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert 'genres' in data


class TestUserAuth:
    """用户认证测试"""

    def test_register_success(self, client):
        """注册新用户应成功"""
        resp = client.post('/api/register', json={
            'username': 'newuser',
            'password': 'pass123456'
        })
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['message'] == '注册成功'

    def test_register_duplicate(self, client):
        """重复注册应返回 400"""
        client.post('/api/register', json={
            'username': 'dupuser',
            'password': 'pass123456'
        })
        resp = client.post('/api/register', json={
            'username': 'dupuser',
            'password': 'pass123456'
        })
        assert resp.status_code == 400

    def test_register_empty_params(self, client):
        """空参数注册应返回 400"""
        resp = client.post('/api/register', json={})
        assert resp.status_code == 400

    def test_login_success(self, client):
        """正确密码登录应成功"""
        client.post('/api/register', json={
            'username': 'loginuser',
            'password': 'pass123456'
        })
        client.post('/api/logout', json={})
        resp = client.post('/api/login', json={
            'username': 'loginuser',
            'password': 'pass123456'
        })
        assert resp.status_code == 200

    def test_login_wrong_password(self, client):
        """错误密码登录应返回 401"""
        client.post('/api/register', json={
            'username': 'wrongpw',
            'password': 'pass123456'
        })
        client.post('/api/logout', json={})
        resp = client.post('/api/login', json={
            'username': 'wrongpw',
            'password': 'wrongpassword'
        })
        assert resp.status_code == 401

    def test_user_status(self, client):
        """未登录时用户状态应返回 logged_in: false"""
        resp = client.get('/api/user/status')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['logged_in'] == False


class TestAuthRequired:
    """登录校验测试"""

    def test_ai_generate_requires_login(self, client):
        """未登录访问 AI 生成接口应重定向"""
        resp = client.post('/api/ai/generate', json={
            'genre': '散文',
            'topic': '测试',
            'keyword': '测试'
        })
        assert resp.status_code in (302, 401)

    def test_articles_list_requires_login(self, client):
        """未登录访问文章列表应返回 200 和空列表（游客模式）"""
        resp = client.get('/api/articles')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['logged_in'] == False
        assert data['articles'] == []

    def test_export_requires_login(self, client):
        """未登录访问导出接口应重定向"""
        resp = client.get('/api/articles/1/export/word')
        assert resp.status_code in (302, 401)

    def test_article_delete_requires_login(self, client):
        """未登录删除文章应重定向"""
        resp = client.delete('/api/articles/1')
        assert resp.status_code in (302, 401)


class TestParameterValidation:
    """参数校验测试"""

    def test_register_null_body(self, client):
        """空请求体注册不应崩溃"""
        resp = client.post('/api/register', data='', content_type='application/json')
        assert resp.status_code in (400, 200)

    def test_login_null_body(self, client):
        """空请求体登录不应崩溃"""
        resp = client.post('/api/login', data='', content_type='application/json')
        assert resp.status_code in (400, 401)

    def test_ai_generate_missing_params(self, auth_client):
        """缺少必填参数应返回 400"""
        resp = auth_client.post('/api/ai/generate', json={})
        assert resp.status_code == 400


class TestMembershipAPI:
    """会员与支付 API 测试"""

    def test_plans_public(self, client):
        """套餐列表无需登录即可访问"""
        resp = client.get('/api/membership/plans')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert 'plans' in data
        assert len(data['plans']) == 4

    def test_plans_contains_all_levels(self, client):
        """套餐列表包含所有等级"""
        resp = client.get('/api/membership/plans')
        data = json.loads(resp.data)
        plans = data['plans']
        assert 'basic_monthly' in plans
        assert 'basic_yearly' in plans
        assert 'gold_monthly' in plans
        assert 'gold_yearly' in plans
        assert plans['basic_monthly']['amount'] == 19
        assert plans['gold_monthly']['amount'] == 49

    def test_status_requires_login(self, client):
        """会员状态需要登录"""
        resp = client.get('/api/membership/status')
        assert resp.status_code in (302, 401)

    def test_status_logged_in(self, auth_client):
        """已登录用户可查询会员状态"""
        resp = auth_client.get('/api/membership/status')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert 'membership' in data
        assert 'daily_limit' in data
        assert data['membership']['level'] == 'free'

    def test_check_generate_requires_login(self, client):
        """生成次数检查需要登录"""
        resp = client.get('/api/membership/check-generate')
        assert resp.status_code in (302, 401)

    def test_check_generate_logged_in(self, auth_client):
        """已登录用户可检查生成次数"""
        resp = auth_client.get('/api/membership/check-generate')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert 'remaining' in data
        assert 'daily_limit' in data
        assert 'level' in data

    def test_create_order_requires_login(self, client):
        """创建订单需要登录"""
        resp = client.post('/api/orders/create', json={'plan': 'basic_monthly'})
        assert resp.status_code in (302, 401)

    def test_create_order_invalid_plan(self, auth_client):
        """无效套餐应返回 400"""
        resp = auth_client.post('/api/orders/create', json={'plan': 'invalid_plan'})
        assert resp.status_code == 400

    def test_create_order_success(self, auth_client):
        """创建订单成功"""
        resp = auth_client.post('/api/orders/create', json={
            'plan': 'basic_monthly',
            'pay_method': 'wechat'
        })
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert 'order' in data
        assert data['order']['status'] == 'pending'

    def test_orders_list_requires_login(self, client):
        """订单列表需要登录"""
        resp = client.get('/api/orders')
        assert resp.status_code in (302, 401)

    def test_pay_order_success(self, auth_client):
        """模拟支付成功"""
        # 先创建订单
        resp = auth_client.post('/api/orders/create', json={
            'plan': 'basic_monthly',
            'pay_method': 'wechat'
        })
        data = json.loads(resp.data)
        order_no = data['order']['order_no']

        # 模拟支付
        resp = auth_client.post(f'/api/orders/{order_no}/pay')
        assert resp.status_code == 200
        data = json.loads(resp.data)
        assert data['message'] == '支付成功'
        assert data['order']['status'] == 'paid'

    def test_pay_order_not_found(self, auth_client):
        """支付不存在的订单应返回 404"""
        resp = auth_client.post('/api/orders/INVALID_ORDER/pay')
        assert resp.status_code == 404
