"""模型层和生成器单元测试"""
import os
import pytest

os.environ['FLASK_ENV'] = 'testing'
os.environ['SECRET_KEY'] = 'test-secret'

from app import app as flask_app
from models import db, User, Article, Chapter
from generator import get_genres


@pytest.fixture
def app():
    flask_app.config['TESTING'] = True
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with flask_app.app_context():
        db.create_all()
    yield flask_app
    with flask_app.app_context():
        db.drop_all()


class TestUserModel:
    """用户模型测试"""

    def test_create_user(self, app):
        with app.app_context():
            user = User(username='testuser')
            user.set_password('pass123456')
            db.session.add(user)
            db.session.commit()
            assert user.id is not None
            assert user.username == 'testuser'

    def test_password_hashing(self, app):
        with app.app_context():
            user = User(username='hashuser')
            user.set_password('mypassword')
            assert user.password_hash != 'mypassword'
            assert user.check_password('mypassword') is True
            assert user.check_password('wrongpassword') is False

    def test_unique_username(self, app):
        with app.app_context():
            u1 = User(username='uniqueuser')
            u1.set_password('pass123456')
            db.session.add(u1)
            db.session.commit()

            u2 = User(username='uniqueuser')
            u2.set_password('pass123456')
            db.session.add(u2)
            with pytest.raises(Exception):
                db.session.commit()
            db.session.rollback()


class TestArticleModel:
    """文章模型测试"""

    def test_create_article(self, app):
        with app.app_context():
            article = Article(
                title='测试文章',
                genre='散文',
                topic='测试主题',
                keyword='测试',
                length='medium',
                word_count=1000
            )
            db.session.add(article)
            db.session.commit()
            assert article.id is not None
            assert article.title == '测试文章'
            assert article.is_favorite == False

    def test_article_to_dict(self, app):
        with app.app_context():
            article = Article(
                title='字典测试',
                genre='小说',
                topic='测试',
                keyword='测试',
                length='short',
                word_count=500
            )
            db.session.add(article)
            db.session.commit()
            d = article.to_dict()
            assert d['title'] == '字典测试'
            assert d['genre'] == '小说'
            assert 'id' in d
            assert 'created_at' in d

    def test_favorite_toggle(self, app):
        with app.app_context():
            article = Article(
                title='收藏测试',
                genre='散文',
                topic='测试',
                keyword='测试',
                length='medium',
                word_count=800
            )
            db.session.add(article)
            db.session.commit()
            assert article.is_favorite == False
            article.is_favorite = True
            db.session.commit()
            assert article.is_favorite == True


class TestChapterModel:
    """章节模型测试"""

    def test_create_chapter(self, app):
        with app.app_context():
            article = Article(
                title='章节测试',
                genre='散文',
                topic='测试',
                keyword='测试',
                length='long',
                word_count=0
            )
            db.session.add(article)
            db.session.flush()

            chapter = Chapter(
                article_id=article.id,
                chapter_index=1,
                chapter_title='第一章',
                content='这是测试内容。' * 50,
                word_count=350
            )
            db.session.add(chapter)
            db.session.commit()
            assert chapter.id is not None
            assert chapter.chapter_index == 1
            assert chapter.article_id == article.id

    def test_chapter_to_dict(self, app):
        with app.app_context():
            article = Article(
                title='章节字典测试',
                genre='小说',
                topic='测试',
                keyword='测试',
                length='long',
                word_count=0
            )
            db.session.add(article)
            db.session.flush()

            chapter = Chapter(
                article_id=article.id,
                chapter_index=1,
                chapter_title='序章',
                content='测试内容',
                word_count=4
            )
            db.session.add(chapter)
            db.session.commit()
            d = chapter.to_dict()
            assert d['chapter_title'] == '序章'
            assert d['chapter_index'] == 1
            assert 'id' in d


class TestGenerator:
    """生成器模块测试"""

    def test_get_genres_returns_list(self):
        genres = get_genres()
        assert isinstance(genres, list)
        assert len(genres) >= 5

    def test_get_genres_structure(self):
        genres = get_genres()
        for g in genres:
            assert isinstance(g, str)
            assert len(g) > 0

    def test_get_genres_contains_expected(self):
        genres = get_genres()
        assert '散文' in genres
        assert len(genres) >= 5
