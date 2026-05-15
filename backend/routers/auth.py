import hashlib

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import Employee
from services.security_service import create_access_token

from schemas.auth_schema import (
    RegisterRequest,
    LoginRequest,
    AuthResponse
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


def hash_password(password: str):
    return hashlib.sha256(password.encode()).hexdigest()


@router.post("/register")
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):
    existing = db.query(Employee).filter(
        Employee.email == request.email
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Email already exists."
        )

    employee = Employee(
        name=request.name,
        email=request.email,
        password_hash=hash_password(request.password),
        role=request.role
    )

    db.add(employee)
    db.commit()
    db.refresh(employee)

    token = create_access_token({
    "id": employee.id,
    "name": employee.name,
    "email": employee.email,
    "role": employee.role
})

    return {
     "token": token,
     "user": {
        "id": employee.id,
        "name": employee.name,
        "email": employee.email,
        "role": employee.role
    }
}

@router.post("/login")
def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    employee = db.query(Employee).filter(
        Employee.email == request.email
    ).first()

    if not employee:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials."
        )

    if employee.password_hash != hash_password(
        request.password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials."
        )

    token = create_access_token({
        "id": employee.id,
        "name": employee.name,
        "email": employee.email,
        "role": employee.role
    })

    return {
        "token": token,

        "user": {
            "id": employee.id,
            "name": employee.name,
            "email": employee.email,
            "role": employee.role
        }
    }