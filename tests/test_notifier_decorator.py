from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.modules.drop_and_go.models import CitizenAlertNotification, DropAndGoRequest
from app.modules.drop_and_go.notifiers import (
    EmailAuditDecorator,
    InAppDatabaseNotifier,
    WebPushBannerDecorator,
)
from app.modules.drop_and_go.observers import CitizenSectorAlertObserver


def _create_memory_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(
        bind=engine,
        tables=[DropAndGoRequest.__table__, CitizenAlertNotification.__table__],
    )
    return sessionmaker(bind=engine)()


def test_decorator_chain_composes_channels():
    db = _create_memory_session()
    notifier = EmailAuditDecorator(WebPushBannerDecorator(InAppDatabaseNotifier()))

    result = notifier.send(
        db,
        citizen_id=10,
        title="Camión en ruta",
        message="Acercándose a Rímac Centro",
    )
    db.commit()

    assert result.channel == "IN_APP+WEB_PUSH+EMAIL_AUDIT"
    saved = db.query(CitizenAlertNotification).filter_by(citizen_id=10).one()
    assert saved.title == "Camión en ruta"
    assert saved.channel == "IN_APP+WEB_PUSH+EMAIL_AUDIT"
    db.close()


def test_sector_observer_uses_decorated_notifier():
    db = _create_memory_session()
    db.add(
        DropAndGoRequest(
            package_code="PKG-DEC-01",
            citizen_id=42,
            container_code="CONT-RIMAC-01",
            material_type="PLASTICO",
            weight_range_declared="1-5kg",
            zone_sector="Rimac Centro",
            status="REGISTRADA",
        )
    )
    db.commit()

    observer = CitizenSectorAlertObserver()
    observer.update(db, {"event_type": "TRUCK_NEAR_SECTOR", "zone_sector": "Rímac Centro"})
    db.commit()

    alerts = db.query(CitizenAlertNotification).filter_by(citizen_id=42).all()
    assert len(alerts) == 1
    assert alerts[0].channel == "IN_APP+WEB_PUSH+EMAIL_AUDIT"
    assert "PKG-DEC-01" in alerts[0].message
    db.close()
