"""
SQLAlchemy 数据模型
"""
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()
bcrypt = Bcrypt()


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(50), unique=True, nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    is_active     = db.Column(db.Boolean, default=True)

    holdings = db.relationship('UserFund', back_populates='user', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {'id': self.id, 'username': self.username, 'email': self.email}


class Fund(db.Model):
    """全局基金信息缓存（按代码去重）"""
    __tablename__ = 'funds'

    code       = db.Column(db.String(10), primary_key=True)
    name       = db.Column(db.String(100), nullable=False)
    type       = db.Column(db.String(20))        # etf_linked / active / bond
    etf_code   = db.Column(db.String(10))        # ETF联接基金对应的ETF代码
    etf_name   = db.Column(db.String(100))
    risk_level = db.Column(db.String(20))        # R1 低风险 … R5 高风险
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    holders = db.relationship('UserFund', back_populates='fund')

    def to_dict(self):
        return {
            'code':       self.code,
            'name':       self.name,
            'type':       self.type,
            'etf_code':   self.etf_code,
            'etf_name':   self.etf_name,
            'risk_level': self.risk_level,
        }


class UserFund(db.Model):
    """用户持仓（用户 × 基金，记录份额和来源）"""
    __tablename__ = 'user_funds'
    __table_args__ = (db.UniqueConstraint('user_id', 'fund_code', name='uq_user_fund'),)

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    fund_code  = db.Column(db.String(10), db.ForeignKey('funds.code'), nullable=False)
    source     = db.Column(db.String(20))             # 理财通 / 支付宝 / 其他
    shares     = db.Column(db.Numeric(18, 4), default=0)   # 持有份额
    cost_price = db.Column(db.Numeric(10, 4))         # 成本净值（可选）
    added_at   = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', back_populates='holdings')
    fund = db.relationship('Fund', back_populates='holders')

    def to_dict(self):
        f = self.fund
        return {
            'code':       self.fund_code,
            'name':       f.name if f else self.fund_code,
            'type':       f.type if f else None,
            'etf_code':   f.etf_code if f else None,
            'etf_name':   f.etf_name if f else None,
            'source':     self.source,
            'risk_level': f.risk_level if f else None,
            'shares':     float(self.shares) if self.shares else 0,
            'cost_price': float(self.cost_price) if self.cost_price else None,
        }
