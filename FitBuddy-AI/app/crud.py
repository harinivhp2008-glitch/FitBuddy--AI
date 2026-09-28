from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .models import Plan, User
from .schemas import UserInput


def get_user(db: Session, user_id: str) -> User | None:
    return db.scalar(
        select(User)
        .where(User.user_id == user_id)
        .options(selectinload(User.plans))
    )


def save_user(db: Session, data: UserInput) -> User:
    user = get_user(db, data.user_id)

    if user:
        user.username = data.username
        user.age = data.age
        user.weight = data.weight
        user.goal = data.goal
        user.intensity = data.intensity
    else:
        user = User(
            user_id=data.user_id,
            username=data.username,
            age=data.age,
            weight=data.weight,
            goal=data.goal,
            intensity=data.intensity,
        )
        db.add(user)

    db.commit()
    db.refresh(user)

    return user


def save_plan(
    db: Session,
    user: User,
    workout_plan: str,
    nutrition_tip: str,
) -> Plan:
    plan = Plan(
        user_id=user.id,
        original_plan=workout_plan,
        nutrition_tip=nutrition_tip,
    )

    db.add(plan)
    db.commit()
    db.refresh(plan)

    return plan


def get_latest_plan(
    db: Session,
    user: User,
) -> Plan | None:
    return db.scalar(
        select(Plan)
        .where(Plan.user_id == user.id)
        .order_by(Plan.created_at.desc())
        .limit(1)
    )


def update_plan(
    db: Session,
    plan: Plan,
    updated_plan: str,
    feedback: str,
) -> Plan:
    plan.updated_plan = updated_plan
    plan.feedback = feedback

    db.commit()
    db.refresh(plan)

    return plan


def get_all_users(db: Session) -> list[User]:
    return list(
        db.scalars(
            select(User)
            .options(selectinload(User.plans))
            .order_by(User.created_at.desc())
        ).unique()
    )


def delete_user(
    db: Session,
    user: User,
) -> None:
    db.delete(user)
    db.commit()