from dataclasses import dataclass
from datetime import datetime

from bson import ObjectId


@dataclass
class FeedbackItem:
    _id: ObjectId

    author: int
    date: datetime

    feedback: str
    feedbackid: int

    guild_id: int

    rating: str

    staff: int
