import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.core.config import Settings


class TestSettings(Settings):
    database_url: str = "sqlite:///:memory:"
    secret_key: str = "test-secret-key-for-unit-tests"
    agent_ingest_key: str = "test-agent-key"


@pytest.fixture
def test_settings():
    return TestSettings()


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(db_session):
    from app.auth.models import User
    from app.core.security import hash_password

    user = User(
        username="testanalyst",
        email="analyst@devinciwatch.local",
        password_hash=hash_password("TestPass123!"),
        role="analyst",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_admin(db_session):
    from app.auth.models import User
    from app.core.security import hash_password

    admin = User(
        username="testadmin",
        email="admin@devinciwatch.local",
        password_hash=hash_password("AdminPass123!"),
        role="admin",
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture
def test_agent(db_session):
    from app.telemetry.models import Agent

    agent = Agent(
        sensor_id="test-sensor-01",
        hostname="test-endpoint",
        ip_address="192.168.1.100",
        mode="passive_lite",
        interfaces=["eth0"],
    )
    db_session.add(agent)
    db_session.commit()
    db_session.refresh(agent)
    return agent
