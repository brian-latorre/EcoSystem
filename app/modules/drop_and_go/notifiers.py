from abc import ABC, abstractmethod
from sqlalchemy.orm import Session

from app.modules.drop_and_go.models import CitizenAlertNotification


class INotifier(ABC):
    @abstractmethod
    def send(
        self, db: Session, citizen_id: int, title: str, message: str
    ) -> CitizenAlertNotification:
        raise NotImplementedError


class InAppDatabaseNotifier(INotifier):
    def send(
        self, db: Session, citizen_id: int, title: str, message: str
    ) -> CitizenAlertNotification:
        notification = CitizenAlertNotification(
            citizen_id=citizen_id,
            title=title,
            message=message,
            channel="IN_APP",
        )
        db.add(notification)
        return notification


class NotifierDecorator(INotifier):
    def __init__(self, wrapped: INotifier) -> None:
        self._wrapped = wrapped

    def send(
        self, db: Session, citizen_id: int, title: str, message: str
    ) -> CitizenAlertNotification:
        return self._wrapped.send(db, citizen_id, title, message)


class WebPushBannerDecorator(NotifierDecorator):
    def send(
        self, db: Session, citizen_id: int, title: str, message: str
    ) -> CitizenAlertNotification:
        notification = super().send(db, citizen_id, title, message)
        if "WEB_PUSH" not in notification.channel:
            notification.channel = f"{notification.channel}+WEB_PUSH"
        return notification


class EmailAuditDecorator(NotifierDecorator):
    def send(
        self, db: Session, citizen_id: int, title: str, message: str
    ) -> CitizenAlertNotification:
        notification = super().send(db, citizen_id, title, message)
        if "EMAIL_AUDIT" not in notification.channel:
            notification.channel = f"{notification.channel}+EMAIL_AUDIT"
        return notification
