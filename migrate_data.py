"""
一次性数据迁移脚本：将 data/funds*.json 迁移到 PostgreSQL 数据库

用法：
    python migrate_data.py

前提：
    1. 已配置好 DATABASE_URL 环境变量（或使用默认 SQLite）
    2. 已通过 create_user.py 创建对应用户账号
       python create_user.py user1 <password>
       python create_user.py user2 <password>
"""
import json
import os
import sys
from app import app
from models import db, User, Fund, UserFund

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')

# 用户名 → JSON 文件 的映射（与旧 app.py 一致）
USER_FILE_MAP = {
    'user1': os.path.join(DATA_DIR, 'funds.json'),
    'user2': os.path.join(DATA_DIR, 'funds_user2.json'),
}


def migrate_user(username, data_file):
    if not os.path.exists(data_file):
        print(f"  ⚠️  文件不存在，跳过: {data_file}")
        return 0

    user = User.query.filter_by(username=username).first()
    if not user:
        print(f"  ❌ 用户 '{username}' 不存在，请先运行 create_user.py 创建该用户")
        return 0

    with open(data_file, 'r', encoding='utf-8') as f:
        funds_raw = json.load(f)

    added = 0
    for item in funds_raw:
        code = item.get('code', '').strip()
        if not code:
            continue

        # 获取或创建全局基金记录
        fund = Fund.query.get(code)
        if not fund:
            fund = Fund(
                code=code,
                name=item.get('name', code),
                type=item.get('type', 'active'),
                etf_code=item.get('etf_code') or None,
                etf_name=item.get('etf_name') or None,
                risk_level=item.get('risk_level') or None,
            )
            db.session.add(fund)
        else:
            # 如果已存在（另一个用户导入过），用当前数据补全缺失字段
            if not fund.name or fund.name == fund.code:
                fund.name = item.get('name', fund.name)
            if not fund.risk_level and item.get('risk_level'):
                fund.risk_level = item['risk_level']

        # 检查是否已有持仓
        existing = UserFund.query.filter_by(user_id=user.id, fund_code=code).first()
        if existing:
            print(f"    跳过（已存在）: {code}")
            continue

        holding = UserFund(
            user_id=user.id,
            fund_code=code,
            source=item.get('source', '其他'),
            shares=0,  # 迁移时份额为 0，需用户自行填写
        )
        db.session.add(holding)
        added += 1

    db.session.commit()
    return added


def main():
    with app.app_context():
        db.create_all()
        print("数据库表已就绪\n")

        total = 0
        for username, data_file in USER_FILE_MAP.items():
            print(f"迁移用户: {username}  ({data_file})")
            n = migrate_user(username, data_file)
            print(f"  ✅ 新增 {n} 条持仓记录\n")
            total += n

        print(f"迁移完成，共迁移 {total} 条记录。")
        print("注意：份额（shares）已全部设为 0，请登录后在界面上填写实际持有份额。")


if __name__ == '__main__':
    main()
