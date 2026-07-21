from dataclasses import dataclass, field
from datetime import datetime

from bson import ObjectId

from datamodels.LazyModel import LazyValues


@dataclass(init=False)
class IEscalation:
    action: str = None
    count: int = 0
    threshold: int = 0


@dataclass(init=False)
class IUpdated:
    AddedRoles: list[int] = field(default_factory=list)
    Channel: int = None
    DbRemoval: None = None
    RemovedRoles: list[int] = field(default_factory=list)
    VoidedShift: bool = False


@dataclass(init=False)
class InfractionItem(LazyValues):
    _id: ObjectId | None = None

    action: str = None

    annonymous: bool | str | None = False

    ApprovalMSG: int = None
    ApprovalStatus: bool = False

    EscalatedFrom: str = None
    EscalationChain: list[IEscalation] = field(default_factory=list)

    expiration: datetime | None = None
    expired: bool = False

    guild_id: int = None
    jump_url: str = None

    management: int = None
    msg_id: int = None

    notes: str | None = None
    random_string: str = None

    reason: str = None

    SkipExec: None = None

    staff: int = None

    timestamp: datetime = None

    Updated: IUpdated = None

    Upscaled: bool = False
    voided: bool = False

    WebhookID: None = None
