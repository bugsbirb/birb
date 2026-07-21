from dataclasses import dataclass
from datetime import datetime
from datamodels.LazyModel import LazyValues


@dataclass(init=False)
class ObjectId(LazyValues):
    oid: str = None


@dataclass(init=False)
class Multi(LazyValues):
    Department: str = None
    SkipTo: str | None = None


@dataclass(init=False)
class Single(LazyValues):
    SkipTo: str | None = None


@dataclass(init=False)
class PromotionItem(LazyValues):
    _id: ObjectId = None

    staff: object = None
    management: object = None

    new: int = None
    previous: int | None = None

    reason: str = None
    random_string: str = None
    guild_id: int = None

    annonymous: bool = False

    jump_url: str | None = None
    msg_id: int = None

    multi: Multi = None
    single: Single = None

    timestamp: datetime = None

    voided: bool = False

    notes: str = "N/A"
