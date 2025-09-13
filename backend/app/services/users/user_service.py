from sqlmodel import Session, func, select

from app.models import User


class UserService:
    @staticmethod
    def get_users_with_pagination(session: Session, skip: int = 0, limit: int = 100):
        """Get paginated users with total count"""
        count_statement = select(func.count()).select_from(User)
        count = session.exec(count_statement).one()

        users_statement = (
            select(User).offset(skip).limit(limit).order_by(User.created_at.desc())
        )
        users = session.exec(users_statement).all()

        return count, users
