from app.schemas.common import ApiModel


class LoginRequest(ApiModel):
    email: str
    password: str


class Operator(ApiModel):
    id: str
    email: str
    name: str


class LoginResponse(ApiModel):
    access_token: str
    operator: Operator
