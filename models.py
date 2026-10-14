from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """用户表"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    articles = db.relationship('Article', backref='author', lazy=True, cascade='all, delete-orphan')
    membership = db.relationship('Membership', backref='user', uselist=False, lazy=True, cascade='all, delete-orphan')
    orders = db.relationship('Order', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_membership_level(self):
        """获取当前会员等级"""
        if self.membership and self.membership.is_active():
            return self.membership.level
        return 'free'

    def get_daily_limit(self):
        """获取每日 AI 生成次数限制"""
        limits = {'free': 3, 'basic': 30, 'gold': 999999}
        return limits.get(self.get_membership_level(), 3)


class Membership(db.Model):
    """会员表"""
    __tablename__ = 'memberships'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    level = db.Column(db.String(20), nullable=False, default='free')  # free / basic / gold
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    expire_date = db.Column(db.DateTime, nullable=True)
    auto_renew = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def is_active(self):
        """检查会员是否有效"""
        if self.level == 'free':
            return True
        if self.expire_date is None:
            return True
        return datetime.utcnow() < self.expire_date

    def days_remaining(self):
        """剩余天数"""
        if self.expire_date is None:
            return None
        delta = self.expire_date - datetime.utcnow()
        return max(0, delta.days)

    def to_dict(self):
        return {
            'level': self.level,
            'is_active': self.is_active(),
            'days_remaining': self.days_remaining(),
            'expire_date': self.expire_date.strftime('%Y-%m-%d') if self.expire_date else None,
            'auto_renew': self.auto_renew,
        }


class Order(db.Model):
    """订单表"""
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    order_no = db.Column(db.String(32), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    plan = db.Column(db.String(20), nullable=False)  # basic_monthly / basic_yearly / gold_monthly / gold_yearly
    amount = db.Column(db.Float, nullable=False)  # 金额（元）
    pay_method = db.Column(db.String(20), nullable=True)  # wechat / alipay / unionpay
    status = db.Column(db.String(20), default='pending')  # pending / paid / cancelled / expired
    paid_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'order_no': self.order_no,
            'plan': self.plan,
            'amount': self.amount,
            'pay_method': self.pay_method,
            'status': self.status,
            'paid_at': self.paid_at.strftime('%Y-%m-%d %H:%M') if self.paid_at else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M'),
        }


class Article(db.Model):
    """文章表"""
    __tablename__ = 'articles'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    genre = db.Column(db.String(50), nullable=False)
    topic = db.Column(db.String(100), nullable=False)
    keyword = db.Column(db.String(100), nullable=False)
    length = db.Column(db.String(20), nullable=False, default='medium')
    word_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='completed')  # completed / generating
    is_favorite = db.Column(db.Boolean, default=False)  # 是否收藏
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # 允许匿名用户

    chapters = db.relationship('Chapter', backref='article', lazy=True, cascade='all, delete-orphan', order_by='Chapter.chapter_index')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'genre': self.genre,
            'topic': self.topic,
            'keyword': self.keyword,
            'length': self.length,
            'word_count': self.word_count,
            'status': self.status,
            'is_favorite': bool(self.is_favorite),
            'chapter_count': len(self.chapters),
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None,
        }


class Chapter(db.Model):
    """章节表 - 支持长文分章节存储"""
    __tablename__ = 'chapters'

    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=False)
    chapter_index = db.Column(db.Integer, nullable=False)
    chapter_title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    word_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'chapter_index': self.chapter_index,
            'chapter_title': self.chapter_title,
            'content': self.content,
            'word_count': self.word_count,
        }
