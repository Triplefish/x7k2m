"""
命令行用户管理工具（仅在服务器端使用，不对外开放）

用法：
    python create_user.py <username> <password> [email]
    python create_user.py --list
    python create_user.py --deactivate <username>
    python create_user.py --reset-password <username> <new_password>

示例：
    python create_user.py user1 mySecretPass123
    python create_user.py user2 anotherPass user2@example.com
    python create_user.py --list
"""
import sys
from app import app
from models import db, User


def cmd_create(username, password, email=None):
    with app.app_context():
        db.create_all()
        if User.query.filter_by(username=username).first():
            print(f"❌ 用户 '{username}' 已存在")
            sys.exit(1)
        u = User(username=username, email=email)
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
        print(f"✅ 用户 '{username}' 创建成功 (id={u.id})")


def cmd_list():
    with app.app_context():
        users = User.query.order_by(User.id).all()
        if not users:
            print("暂无用户")
            return
        print(f"{'ID':<6} {'用户名':<20} {'邮箱':<30} {'状态':<6} {'创建时间'}")
        print('-' * 80)
        for u in users:
            status = '启用' if u.is_active else '禁用'
            print(f"{u.id:<6} {u.username:<20} {(u.email or ''):<30} {status:<6} {u.created_at.strftime('%Y-%m-%d %H:%M')}")


def cmd_deactivate(username):
    with app.app_context():
        u = User.query.filter_by(username=username).first()
        if not u:
            print(f"❌ 用户 '{username}' 不存在")
            sys.exit(1)
        u.is_active = False
        db.session.commit()
        print(f"✅ 用户 '{username}' 已禁用")


def cmd_reset_password(username, new_password):
    with app.app_context():
        u = User.query.filter_by(username=username).first()
        if not u:
            print(f"❌ 用户 '{username}' 不存在")
            sys.exit(1)
        u.set_password(new_password)
        db.session.commit()
        print(f"✅ 用户 '{username}' 密码已重置")


def print_usage():
    print(__doc__)


if __name__ == '__main__':
    args = sys.argv[1:]

    if not args or args[0] in ('-h', '--help'):
        print_usage()
    elif args[0] == '--list':
        cmd_list()
    elif args[0] == '--deactivate' and len(args) >= 2:
        cmd_deactivate(args[1])
    elif args[0] == '--reset-password' and len(args) >= 3:
        cmd_reset_password(args[1], args[2])
    elif len(args) >= 2 and not args[0].startswith('--'):
        email = args[2] if len(args) >= 3 else None
        cmd_create(args[0], args[1], email)
    else:
        print_usage()
        sys.exit(1)
