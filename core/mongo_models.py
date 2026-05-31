from mongoengine import (
    Document,
    StringField,
    DateTimeField
)

from datetime import datetime


class ActivityLog(Document):

    user = StringField()

    action = StringField()

    created_at = DateTimeField(
        default=datetime.utcnow
    )

    meta = {
        "collection": "activity_logs"
    }