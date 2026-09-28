from pathlib import Path

from fastapi import APIRouter, Depends, Form, Header, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from .crud import (
    delete_user,
    get_all_users,
    get_latest_plan,
    get_user,
    save_plan,
    save_user,
    update_plan,
)
from .database import get_db
from .gemini_flash_generator import generate_nutrition_tip_with_flash
from .gemini_generator import generate_workout_gemini
from .schemas import FeedbackRequest, UserInput
from .updated_plan import update_workout_plan


BASE_DIR = Path(__file__).resolve().parent.parent

templates = Jinja2Templates(
    directory=str(BASE_DIR / "templates")
)

router = APIRouter()


def render_error(
    request: Request,
    message: str,
    status_code: int = 400,
):
    return templates.TemplateResponse(
        request=request,
        name="error.html",
        context={
            "message": message,
        },
        status_code=status_code,
    )


def check_admin_token(
    admin_token: str | None,
    configured_token: str,
) -> None:
    if configured_token:
        if admin_token != configured_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid admin token.",
            )


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "title": "FitBuddy AI",
        },
    )


@router.post("/generate-workout", response_class=HTMLResponse)
async def generate_workout(
    request: Request,
    username: str = Form(...),
    user_id: str = Form(...),
    age: int = Form(...),
    weight: float = Form(...),
    goal: str = Form(...),
    intensity: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        data = UserInput(
            username=username,
            user_id=user_id,
            age=age,
            weight=weight,
            goal=goal,
            intensity=intensity,
        )
    except Exception as exc:
        return render_error(
            request,
            f"Invalid profile information: {exc}",
            422,
        )

    try:
        user = save_user(db, data)

        workout_plan = generate_workout_gemini(data)

        nutrition_tip = generate_nutrition_tip_with_flash(
            data.goal
        )

        plan = save_plan(
            db=db,
            user=user,
            workout_plan=workout_plan,
            nutrition_tip=nutrition_tip,
        )

        return templates.TemplateResponse(
            request=request,
            name="result.html",
            context={
                "user": user,
                "plan": plan,
                "title": "Your FitBuddy Plan",
            },
        )

    except Exception as exc:
        import traceback
        traceback.print_exc()
        
        return render_error(
            request,
            f"Unable to generate the plan: {exc}",
            500,
        )


@router.post("/submit-feedback", response_class=HTMLResponse)
async def submit_feedback(
    request: Request,
    user_id: str = Form(...),
    feedback: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        feedback_data = FeedbackRequest(
            user_id=user_id,
            feedback=feedback,
        )
    except Exception as exc:
        return render_error(
            request,
            f"Invalid feedback: {exc}",
            422,
        )

    user = get_user(db, feedback_data.user_id)

    if not user:
        return render_error(
            request,
            "User not found.",
            404,
        )

    plan = get_latest_plan(db, user)

    if not plan:
        return render_error(
            request,
            "No workout plan was found for this user.",
            404,
        )

    try:
        revised_plan = update_workout_plan(
            original_plan=plan.original_plan,
            feedback=feedback_data.feedback,
            goal=user.goal,
            intensity=user.intensity,
        )

        update_plan(
            db=db,
            plan=plan,
            updated_plan=revised_plan,
            feedback=feedback_data.feedback,
        )

        return templates.TemplateResponse(
            request=request,
            name="result.html",
            context={
                "user": user,
                "plan": plan,
                "title": "Updated FitBuddy Plan",
            },
        )

    except Exception as exc:
        return render_error(
            request,
            f"Unable to update the workout plan: {exc}",
            500,
        )


@router.get("/view-all-users", response_class=HTMLResponse)
async def view_all_users(
    request: Request,
    db: Session = Depends(get_db),
):
    users = get_all_users(db)

    return templates.TemplateResponse(
        request=request,
        name="all_users.html",
        context={
            "users": users,
            "title": "FitBuddy Admin",
        },
    )


@router.post("/users/{user_id}/delete")
async def remove_user(
    user_id: str,
    x_admin_token: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    from .config import get_settings

    settings = get_settings()

    check_admin_token(
        admin_token=x_admin_token,
        configured_token=settings.admin_token,
    )

    user = get_user(db, user_id)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )

    delete_user(db, user)

    return {
        "message": "User deleted successfully.",
        "user_id": user_id,
    }


@router.post("/api/plans")
async def create_plan_api(
    data: UserInput,
    db: Session = Depends(get_db),
):
    try:
        user = save_user(db, data)

        workout_plan = generate_workout_gemini(data)

        nutrition_tip = generate_nutrition_tip_with_flash(
            data.goal
        )

        plan = save_plan(
            db=db,
            user=user,
            workout_plan=workout_plan,
            nutrition_tip=nutrition_tip,
        )

        return {
            "success": True,
            "user_id": user.user_id,
            "plan_id": plan.id,
            "workout_plan": plan.original_plan,
            "nutrition_tip": plan.nutrition_tip,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to generate plan: {exc}",
        ) from exc


@router.post("/api/plans/{user_id}/feedback")
async def feedback_api(
    user_id: str,
    data: FeedbackRequest,
    db: Session = Depends(get_db),
):
    if data.user_id != user_id:
        raise HTTPException(
            status_code=400,
            detail="The user_id in the URL and request body must match.",
        )

    user = get_user(db, user_id)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )

    plan = get_latest_plan(db, user)

    if not plan:
        raise HTTPException(
            status_code=404,
            detail="No workout plan found for this user.",
        )

    try:
        revised_plan = update_workout_plan(
            original_plan=plan.original_plan,
            feedback=data.feedback,
            goal=user.goal,
            intensity=user.intensity,
        )

        update_plan(
            db=db,
            plan=plan,
            updated_plan=revised_plan,
            feedback=data.feedback,
        )

        return {
            "success": True,
            "user_id": user.user_id,
            "plan_id": plan.id,
            "feedback": plan.feedback,
            "updated_plan": plan.updated_plan,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to update plan: {exc}",
        ) from exc


@router.get("/api/users/{user_id}")
async def get_user_api(
    user_id: str,
    db: Session = Depends(get_db),
):
    user = get_user(db, user_id)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )

    latest_plan = get_latest_plan(db, user)

    return {
        "id": user.id,
        "user_id": user.user_id,
        "username": user.username,
        "age": user.age,
        "weight": user.weight,
        "goal": user.goal,
        "intensity": user.intensity,
        "created_at": user.created_at,
        "latest_plan": (
            {
                "id": latest_plan.id,
                "original_plan": latest_plan.original_plan,
                "updated_plan": latest_plan.updated_plan,
                "nutrition_tip": latest_plan.nutrition_tip,
                "feedback": latest_plan.feedback,
                "created_at": latest_plan.created_at,
                "updated_at": latest_plan.updated_at,
            }
            if latest_plan
            else None
        ),
    }