from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth.repository import UserRepository
from app.modules.auth.schemas import (
    CitizenRegisterInput,
    CitizenRegisterOutput,
    LoginInput,
    LoginOutput,
)
from app.modules.auth.service import (
    AuthService,
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    InvalidRoleError,
)

router = APIRouter(prefix="/auth", tags=["Autenticacion y Roles"])


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(UserRepository(db))


@router.post(
    "/register",
    response_model=CitizenRegisterOutput,
    status_code=status.HTTP_201_CREATED,
)
def register_citizen(
    payload: CitizenRegisterInput,
    service: AuthService = Depends(get_auth_service),
) -> CitizenRegisterOutput:
    try:
        return service.register_citizen(payload)
    except EmailAlreadyRegisteredError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Correo electrónico ya registrado",
        )


@router.post("/login", response_model=LoginOutput)
def login_by_role(
    payload: LoginInput,
    service: AuthService = Depends(get_auth_service),
) -> LoginOutput:
    try:
        return service.login(payload)
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas o usuario inactivo",
        )
    except InvalidRoleError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Acceso denegado: la cuenta no cuenta con el rol "
                f"{error.expected_role.value}"
            ),
        )
