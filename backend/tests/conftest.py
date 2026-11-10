
import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.database import Base


@pytest.fixture
def test_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    # Import models before creating tables.
    from app.models.user import User
    from app.models.device import Device
    from app.models.incident import Incident
    from app.models.emergency import Emergency
    from app.models.trusted_contact import TrustedContact
    from app.models.notification import NotificationDelivery

    Base.metadata.create_all(bind=engine)

    yield TestingSessionLocal

    Base.metadata.drop_all(bind=engine)
    engine.dispose()
