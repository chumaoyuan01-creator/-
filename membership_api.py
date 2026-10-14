"""会员与支付 API 模块"""
import random
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, User, Article, Membership, Order

membership_bp = Blueprint('membership', __name__)

# 会员套餐配置
MEMBERSHIP_PLANS = {
    'basic_monthly': {'name': '一般会员（月付）', 'level': 'basic', 'amount': 19, 'days': 30},
    'basic_yearly': {'name': '一般会员（年付）', 'level': 'basic', 'amount': 199, 'days': 365},
    'gold_monthly': {'name': '黄金会员（月付）', 'level': 'gold', 'amount': 49, 'days': 30},
    'gold_yearly': {'name': '黄金会员（年付）', 'level': 'gold', 'amount': 499, 'days': 365},
}


def safe_get(data, key, default='', coerce=None):
    """安全获取请求参数"""
    if data is None:
        return default
    val = data.get(key, default)
    if coerce is not None and val != default:
        try:
            val = coerce(val)
        except (ValueError, TypeError):
            val = default
    return val


@membership_bp.route('/api/membership/status')
@login_required
def api_membership_status():
    """查询当前用户会员状态（含到期提醒）"""
    membership = Membership.query.filter_by(user_id=current_user.id).first()
    if membership:
        days = membership.days_remaining()
        is_expiring = days is not None and days <= 7
        return jsonify({
            'membership': membership.to_dict(),
            'daily_limit': current_user.get_daily_limit(),
            'reminder': {
                'is_expiring': is_expiring,
                'days_remaining': days,
                'should_renew': is_expiring,
                'message': f'您的会员还有 {days} 天到期，建议续费' if is_expiring and days > 0 else (
                    '您的会员已到期，请续费' if days == 0 else None
                ),
            },
        })
    return jsonify({
        'membership': {'level': 'free', 'is_active': True, 'days_remaining': None, 'expire_date': None, 'auto_renew': False},
        'daily_limit': 3,
        'reminder': None,
    })


@membership_bp.route('/api/membership/plans')
def api_membership_plans():
    """获取所有会员套餐"""
    return jsonify({'plans': MEMBERSHIP_PLANS})


@membership_bp.route('/api/orders/create', methods=['POST'])
@login_required
def api_order_create():
    """创建订单"""
    data = request.get_json(silent=True) or {}
    plan_key = safe_get(data, 'plan', '')
    pay_method = safe_get(data, 'pay_method', 'wechat')

    if plan_key not in MEMBERSHIP_PLANS:
        return jsonify({'error': '无效的套餐'}), 400

    plan = MEMBERSHIP_PLANS[plan_key]
    order_no = 'MO' + datetime.utcnow().strftime('%Y%m%d%H%M%S') + str(random.randint(1000, 9999))

    order = Order(
        order_no=order_no,
        user_id=current_user.id,
        plan=plan_key,
        amount=plan['amount'],
        pay_method=pay_method,
        status='pending'
    )
    db.session.add(order)
    db.session.commit()

    return jsonify({
        'order': order.to_dict(),
        'plan_name': plan['name'],
    })


@membership_bp.route('/api/orders/<order_no>/pay', methods=['POST'])
@login_required
def api_order_pay(order_no):
    """模拟支付（后期接入真实支付网关）"""
    order = Order.query.filter_by(order_no=order_no, user_id=current_user.id).first()
    if not order:
        return jsonify({'error': '订单不存在'}), 404
    if order.status != 'pending':
        return jsonify({'error': '订单状态异常'}), 400

    order.status = 'paid'
    order.paid_at = datetime.utcnow()

    plan = MEMBERSHIP_PLANS.get(order.plan)
    if plan:
        membership = Membership.query.filter_by(user_id=current_user.id).first()
        now = datetime.utcnow()
        if membership and membership.is_active() and membership.level == plan['level']:
            if membership.expire_date and membership.expire_date > now:
                membership.expire_date = membership.expire_date + timedelta(days=plan['days'])
            else:
                membership.expire_date = now + timedelta(days=plan['days'])
        else:
            if membership:
                db.session.delete(membership)
                db.session.flush()
            membership = Membership(
                user_id=current_user.id,
                level=plan['level'],
                start_date=now,
                expire_date=now + timedelta(days=plan['days'])
            )
            db.session.add(membership)

    db.session.commit()

    return jsonify({
        'message': '支付成功',
        'order': order.to_dict(),
        'membership': membership.to_dict() if membership else None,
    })


@membership_bp.route('/api/orders', methods=['GET'])
@login_required
def api_order_list():
    """查询用户订单列表"""
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).limit(20).all()
    return jsonify({'orders': [o.to_dict() for o in orders]})


@membership_bp.route('/api/membership/check-generate', methods=['GET'])
@login_required
def api_check_generate():
    """检查今日剩余生成次数"""
    today = datetime.utcnow().date()
    today_count = Article.query.filter(
        Article.user_id == current_user.id,
        db.func.date(Article.created_at) == today
    ).count()
    daily_limit = current_user.get_daily_limit()
    remaining = max(0, daily_limit - today_count)
    return jsonify({
        'today_count': today_count,
        'daily_limit': daily_limit,
        'remaining': remaining,
        'level': current_user.get_membership_level(),
    })
