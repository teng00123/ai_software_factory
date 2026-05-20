from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, UserInfo
from app.core.security import (
    verify_password,
    hash_password,
    create_access_token,
    get_current_user,
)

router = APIRouter()


@router.post("/login", response_model=LoginResponse, summary="用户登录")
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    用户登录接口，验证用户名和密码，返回JWT Token
    """
    # 查询用户
    result = await db.execute(
        select(User).where(User.username == request.username)
    )
    user = result.scalar_one_or_none()

    # 验证用户存在且密码正确
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 验证用户是否激活
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    # 生成token
    token = create_access_token(data={"sub": str(user.id)})

    return LoginResponse(token=token, username=user.username)


@router.get("/me", response_model=UserInfo, summary="获取当前用户信息")
async def get_me(current_user: User = Depends(get_current_user)):
    """
    获取当前登录用户的信息
    """
    return current_user


@router.post("/init", summary="初始化管理员账号")
async def init_admin(db: AsyncSession = Depends(get_db)):
    """
    初始化默认管理员账号（仅当没有任何用户时可用）
    默认账号：admin / admin123
    """
    # 检查是否已有用户
    result = await db.execute(select(User).limit(1))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin user already exists",
        )

    # 创建默认管理员
    admin = User(
        username="admin",
        hashed_password=hash_password("admin123"),
        email="admin@example.com",
        is_active=True,
        is_superuser=True,
    )
    db.add(admin)
    await db.commit()

    return {"message": "Admin user created successfully", "username": "admin"}
