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
        """未登录访问文章列表应重定向"""
        resp = client.get('/api/articles')
        assert resp.status_code in (302, 401)

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
