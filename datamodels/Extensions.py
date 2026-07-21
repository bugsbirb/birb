from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from bson import ObjectId


@dataclass
class ExtensionUser:
    id: int
    name: str
    thumbnail: str


@dataclass
class ExtensionAction:
    reason: str
    time: datetime
    user: int


@dataclass
class ExtensionItem:
    _id: ObjectId

    Accepted: Optional[ExtensionAction]
    Declined: Optional[ExtensionAction]

    channel_id: int

    duration: int
    durationstr: str

    ExtendedUser: ExtensionUser

    guild: int

    LoaID: Optional[str]

    messageid: int

    reason: str

    requested_at: datetime
    requested_by: int

    status: str

    user: int
