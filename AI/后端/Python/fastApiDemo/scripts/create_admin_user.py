# 创建管理员用户
# 用法（在项目根目录执行）：
#   poetry run python scripts/create_admin_user.py

from __future__ import annotations

import sys
from pathlib import Path

# 把项目根目录加入 sys.path，否则 scripts/ 下找不到 core、models
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import select

from core.database import SessionLocal
from core.security import hash_password
from models.user import UserEntity

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Admin@123"


def main() -> None:
    db = SessionLocal()
    try:
        exists = db.scalar(
            select(UserEntity).where(UserEntity.username == ADMIN_USERNAME)
        )
        if exists:
            print(f"管理员用户 {ADMIN_USERNAME} 已存在 (id={exists.id})")
            return

        user = UserEntity(
            username=ADMIN_USERNAME,
            password=hash_password(ADMIN_PASSWORD),
            nickname="管理员",
            status=1,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"管理员用户创建成功 id={user.id} username={user.username}")
    except Exception as e:
        db.rollback()
        print(f"创建管理员用户失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
