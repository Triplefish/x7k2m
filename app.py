"""
基金追踪器后端 - 数据库版
使用 Flask + SQLAlchemy + Flask-Login (Session) 认证
"""
from flask import Flask, render_template, request, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import timedelta
import os
import threading
import fund_tracker
from models import db, bcrypt, User, Fund, UserFund

app = Flask(__name__)

# ─── 配置 ──────────────────────────────────────────────────────────
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 'sqlite:///fund_tracker.db'
).replace('postgres://', 'postgresql://')  # Railway 兼容
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'change-me-in-production')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

# ─── 扩展初始化 ────────────────────────────────────────────────────
db.init_app(app)
bcrypt.init_app(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per minute"]
)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@login_manager.unauthorized_handler
def unauthorized():
    return jsonify({'success': False, 'message': '未登录'}), 401


# ─── 辅助函数 ──────────────────────────────────────────────────────
def _sync_vika_background(results):
    try:
        fund_tracker.update_vika_table(results)
    except Exception as e:
        print(f"⚠️  [后台] 维格表同步失败: {e}")


def _refresh_risk_levels_background(user_id):
    """后台更新指定用户所有基金的风险评级"""
    with app.app_context():
        holdings = UserFund.query.filter_by(user_id=user_id).all()
        import time
        for uf in holdings:
            fund = uf.fund
            if fund and not fund.risk_level:
                level = fund_tracker.get_fund_risk_level(fund.code)
                if level:
                    fund.risk_level = level
                time.sleep(0.5)
        db.session.commit()


# ─── 认证端点 ──────────────────────────────────────────────────────
@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'success': False, 'message': '用户名和密码不能为空'}), 400

    user = User.query.filter_by(username=username, is_active=True).first()
    if not user or not user.check_password(password):
        return jsonify({'success': False, 'message': '用户名或密码错误'}), 401

    login_user(user, remember=True)
    return jsonify({'success': True, 'user': user.to_dict()})


@app.route('/api/auth/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'success': True})


@app.route('/api/auth/me', methods=['GET'])
@login_required
def me():
    return jsonify(current_user.to_dict())


# ─── 基金管理端点 ───────────────────────────────────────────────────
@app.route('/api/funds', methods=['GET'])
@login_required
def get_funds():
    holdings = (
        UserFund.query
        .filter_by(user_id=current_user.id)
        .join(Fund)
        .all()
    )
    return jsonify([uf.to_dict() for uf in holdings])


@app.route('/api/funds', methods=['POST'])
@login_required
def add_fund():
    data = request.get_json() or {}

    code = data.get('code', '').strip()
    if not code or not code.isdigit() or len(code) != 6:
        return jsonify({'success': False, 'message': '基金代码必须是6位数字'}), 400

    # 检查是否已持有
    existing = UserFund.query.filter_by(user_id=current_user.id, fund_code=code).first()
    if existing:
        return jsonify({'success': False, 'message': '已在持仓中'}), 400

    # 获取或创建基金信息
    fund = Fund.query.get(code)
    if not fund:
        fund = Fund(
            code=code,
            name=data.get('name', code),
            type=data.get('type', 'active'),
            etf_code=data.get('etf_code') or None,
            etf_name=data.get('etf_name') or None,
            risk_level=data.get('risk_level') or None,
        )
        db.session.add(fund)
    else:
        if data.get('name'):
            fund.name = data['name']
        if data.get('risk_level'):
            fund.risk_level = data['risk_level']

    shares = data.get('shares', 0)
    try:
        shares = float(shares)
        if shares < 0:
            shares = 0
    except (TypeError, ValueError):
        shares = 0

    holding = UserFund(
        user_id=current_user.id,
        fund_code=code,
        source=data.get('source', '其他'),
        shares=shares,
        cost_price=data.get('cost_price') or None,
    )
    db.session.add(holding)
    db.session.commit()

    # 后台补全风险评级
    t = threading.Thread(target=_refresh_risk_levels_background, args=(current_user.id,), daemon=True)
    t.start()

    return jsonify({'success': True})


@app.route('/api/funds/<string:code>', methods=['PUT'])
@login_required
def update_fund(code):
    """更新持仓信息（份额、来源、成本）"""
    holding = UserFund.query.filter_by(user_id=current_user.id, fund_code=code).first_or_404()
    data = request.get_json() or {}

    if 'shares' in data:
        try:
            val = float(data['shares'])
            holding.shares = max(0, val)
        except (TypeError, ValueError):
            return jsonify({'success': False, 'message': '份额格式不正确'}), 400

    if 'source' in data:
        holding.source = data['source']

    if 'cost_price' in data:
        try:
            holding.cost_price = float(data['cost_price']) if data['cost_price'] else None
        except (TypeError, ValueError):
            pass

    db.session.commit()
    return jsonify({'success': True, 'holding': holding.to_dict()})


@app.route('/api/funds/<string:code>', methods=['DELETE'])
@login_required
def delete_fund(code):
    holding = UserFund.query.filter_by(user_id=current_user.id, fund_code=code).first_or_404()
    db.session.delete(holding)
    db.session.commit()
    return jsonify({'success': True})


# ─── 估值端点 ───────────────────────────────────────────────────────
@app.route('/api/estimates', methods=['GET'])
@login_required
def get_estimates():
    holdings = UserFund.query.filter_by(user_id=current_user.id).join(Fund).all()

    results = []
    for uf in holdings:
        fund_dict = uf.to_dict()
        try:
            res = fund_tracker.calculate_fund_estimate(fund_dict)
            if res:
                shares = float(uf.shares) if uf.shares else 0
                res['shares'] = shares
                if shares > 0:
                    try:
                        nav = float(res.get('当前估值', 0))
                        res['total_value'] = round(shares * nav, 2)
                    except (TypeError, ValueError):
                        res['total_value'] = 0
                else:
                    res['total_value'] = 0
                results.append(res)
            else:
                results.append({
                    '基金名称': fund_dict.get('name', uf.fund_code),
                    '基金代码': uf.fund_code,
                    '当前估值': '获取失败',
                    '涨跌幅': '0',
                    '风险评级': fund_dict.get('risk_level', ''),
                    'shares': float(uf.shares) if uf.shares else 0,
                    'total_value': 0,
                    'error': True,
                })
        except Exception as e:
            results.append({
                '基金名称': fund_dict.get('name', uf.fund_code),
                '基金代码': uf.fund_code,
                '当前估值': '出错',
                '涨跌幅': '0',
                '风险评级': fund_dict.get('risk_level', ''),
                'shares': float(uf.shares) if uf.shares else 0,
                'total_value': 0,
                'error': str(e),
            })

    # 后台同步维格表
    if results:
        t = threading.Thread(target=_sync_vika_background, args=(results,), daemon=True)
        t.start()

    return jsonify(results)


@app.route('/api/fund_info/<string:code>', methods=['GET'])
def get_fund_info(code):
    """公开接口：查询基金基础信息（用于添加前的预搜索）"""
    if not code.isdigit() or len(code) != 6:
        return jsonify({'success': False, 'message': '无效的基金代码'}), 400

    info = fund_tracker.get_fund_realtime_data(code)
    if info['success']:
        risk_level = fund_tracker.get_fund_risk_level(code)
        return jsonify({
            'fund_name':  info['fund_name'],
            'type':       'active',
            'risk_level': risk_level or '',
            'success':    True,
        })
    return jsonify({'success': False, 'message': '无法获取基金信息'}), 404


@app.route('/api/update_risk_levels', methods=['POST'])
@login_required
def update_risk_levels():
    t = threading.Thread(target=_refresh_risk_levels_background, args=(current_user.id,), daemon=True)
    t.start()
    return jsonify({'success': True, 'message': '已在后台开始更新，刷新估值后生效'})


@app.route('/api/sync', methods=['POST'])
@login_required
def sync_vika():
    holdings = UserFund.query.filter_by(user_id=current_user.id).join(Fund).all()
    results = []
    for uf in holdings:
        res = fund_tracker.calculate_fund_estimate(uf.to_dict())
        if res:
            results.append(res)

    if not results:
        return jsonify({'success': False, 'message': '无数据可同步'})

    success = fund_tracker.update_vika_table(results)
    return jsonify({'success': success, 'message': '' if success else '同步失败，请检查日志'})


# ─── 页面 ───────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')


# ─── 启动 ───────────────────────────────────────────────────────────
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=8888)
