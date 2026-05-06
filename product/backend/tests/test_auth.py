from app.auth.service import authenticate, create_user, AuthError
from app.core.security import verify_password, create_access_token, decode_token, hash_password
from app.core.deps import require_admin


def test_password_hashing():
    plain = "SecureP@ssw0rd!"
    hashed = hash_password(plain)
    assert hashed != plain
    assert verify_password(plain, hashed)
    assert not verify_password("WrongPassword", hashed)


def test_create_and_authenticate_user(db_session):
    user = create_user(
        db_session,
        username="authuser",
        email="auth@test.local",
        password="AuthTest123!",
        role="analyst",
    )
    assert user.id is not None
    assert user.username == "authuser"

    authenticated_user, token = authenticate(db_session, "authuser", "AuthTest123!")
    assert authenticated_user.id == user.id
    assert token is not None
    assert isinstance(token, str)


def test_auth_invalid_credentials(db_session, test_user):
    try:
        authenticate(db_session, test_user.username, "WrongPassword")
        assert False, "Should have raised AuthError"
    except AuthError:
        pass

    try:
        authenticate(db_session, "nonexistent", "AnyPassword")
        assert False, "Should have raised AuthError"
    except AuthError:
        pass


def test_jwt_token_lifecycle(test_user):
    token = create_access_token(test_user.username, test_user.role)
    assert isinstance(token, str)
    assert len(token) > 0

    payload = decode_token(token)
    assert payload["sub"] == test_user.username
    assert payload["role"] == test_user.role


def test_jwt_invalid_token():
    try:
        decode_token("invalid-token-string")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_require_admin_rejects_analyst(db_session, test_user):
    try:
        require_admin(test_user)
        assert False, "Should have raised HTTPException"
    except Exception as e:
        assert "403" in str(e) or "admin" in str(e).lower()


def test_admin_access_granted(db_session, test_admin):
    result = require_admin(test_admin)
    assert result is not None
    assert result.role == "admin"
