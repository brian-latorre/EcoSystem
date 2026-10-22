from app.modules.auth.models import User, UserRole
from app.modules.auth.repository import UserRepository
from app.modules.auth.schemas import (
    CitizenRegisterInput,
    CitizenRegisterOutput,
    LoginInput,
    LoginOutput,
)
from app.modules.auth.security import hash_password


class EmailAlreadyRegisteredError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class InvalidRoleError(Exception):
    def __init__(self, expected_role: UserRole):
        self.expected_role = expected_role


class AuthService:
    def __init__(self, users: UserRepository):
        self._users = users

    def register_citizen(
        self, payload: CitizenRegisterInput
    ) -> CitizenRegisterOutput:
        if self._users.find_by_email(payload.email):
            raise EmailAlreadyRegisteredError

        user = self._users.save(
            User(
                full_name=payload.full_name,
                email=payload.email,
                password_hash=hash_password(payload.password),
                role=UserRole.CIUDADANO,
                zone_sector=payload.zone_sector,
            )
        )
        return CitizenRegisterOutput(
            id=user.id,
            full_name=user.full_name,
            role=UserRole(user.role),
            sector=user.zone_sector,
        )

    def login(self, payload: LoginInput) -> LoginOutput:
        user = self._users.find_by_credentials(
            payload.email, hash_password(payload.password)
        )
        if not user or not user.is_active:
            raise InvalidCredentialsError

        user_role = UserRole(user.role)
        if user_role != payload.expected_role:
            raise InvalidRoleError(payload.expected_role)

        return LoginOutput(
            user_id=user.id,
            full_name=user.full_name,
            role=user_role,
            eco_points=user.eco_points_balance,
        )
