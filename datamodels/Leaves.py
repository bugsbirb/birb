from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from bson import ObjectId


@dataclass
class LeaveUser:
    id: int
    name: str
    thumbnail: str


@dataclass
class LeaveAccepted:
    user: int
    time: datetime


@dataclass
class LeaveDeclined:
    user: int
    time: datetime
    reason: str


@dataclass
class LeaveAddedLog:
    duration: int
    reason: Optional[str]
    time: datetime
    user: int


@dataclass
class LeaveRemovedLog:
    duration: int
    time: datetime
    user: int


@dataclass
class LeaveTime:
    Time: int = 0
    Reason: Optional[str] = None
    Log: list[LeaveAddedLog] = field(default_factory=list)
    RequestExt: None = None


@dataclass
class LeaveRemovedTime:
    Duration: int = 0
    Log: list[LeaveRemovedLog] = field(default_factory=list)
    Time: int = 0


@dataclass
class LeaveItem:
    _id: ObjectId

    active: bool

    end_time: datetime
    start_time: datetime

    guild_id: int
    user: int

    reason: str

    Accepted: Optional[LeaveAccepted] = None
    Declined: Optional[LeaveDeclined] = None

    AddedTime: LeaveTime = field(default_factory=LeaveTime)
    RemovedTime: LeaveRemovedTime = field(default_factory=LeaveRemovedTime)

    Created: LeaveUser = None
    ExtendedUser: LeaveUser = None

    LoaID: str = None

    channel_id: int = None
    messageid: int = None

    request: bool = False
    scheduled: bool = False
