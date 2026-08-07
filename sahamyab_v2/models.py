from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TweetItem(BaseModel):
    """Validated representation of every known Sahamyab tweet shape.

    Sahamyab has added fields over time. ``extra="allow"`` deliberately keeps
    future fields in the stored payload instead of silently dropping them.
    """

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    id: str = Field(min_length=1)
    send_time: datetime = Field(alias="sendTime")
    send_time_persian: str = Field(alias="sendTimePersian")
    sender_name: str = Field(alias="senderName")
    sender_username: str = Field(alias="senderUsername")
    sender_profile_image: str = Field(alias="senderProfileImage")
    sender_is_official: bool | str | None = Field(
        default=None, alias="senderIsOfficial"
    )
    content: str

    parent_send_time: datetime | None = Field(default=None, alias="parentSendTime")
    parent_send_time_persian: str | None = Field(
        default=None, alias="parentSendTimePersian"
    )
    parent_id: str | None = Field(default=None, alias="parentId")
    parent_sender_name: str | None = Field(default=None, alias="parentSenderName")
    parent_sender_username: str | None = Field(
        default=None, alias="parentSenderUsername"
    )
    parent_sender_profile_image: str | None = Field(
        default=None, alias="parentSenderProfileImage"
    )
    parent_sender_is_official: bool | str | None = Field(
        default=None, alias="parentSenderIsOfficial"
    )
    parent_content: str | None = Field(default=None, alias="parentContent")
    parent_deleted: bool | str | None = Field(default=None, alias="parentDeleted")
    parent_type: str | None = Field(default=None, alias="parentType")
    parent_image_uid: str | None = Field(default=None, alias="parentImageUid")
    parent_video_uid: str | None = Field(default=None, alias="parentVideoUid")
    parent_file_uid: str | None = Field(default=None, alias="parentFileUid")
    parent_options: list[Any] | None = Field(default=None, alias="parentOptions")
    parent_vote_count: int | None = Field(default=None, alias="parentVoteCount")
    parent_pull_status: str | None = Field(default=None, alias="parentPullStatus")
    parent_duration_per_hour: float | None = Field(
        default=None, alias="parentDurationPerHour"
    )
    parent_duration_per_day: float | None = Field(
        default=None, alias="parentDurationPerDay"
    )

    retwit_send_time: datetime | None = Field(default=None, alias="retwitSendTime")
    retwit_send_time_persian: str | None = Field(
        default=None, alias="retwitSendTimePersian"
    )
    retwit_id: str | None = Field(default=None, alias="retwitId")
    retwit_sender_name: str | None = Field(default=None, alias="retwitSenderName")
    retwit_sender_username: str | None = Field(
        default=None, alias="retwitSenderUsername"
    )
    retwit_sender_profile_image: str | None = Field(
        default=None, alias="retwitSenderProfileImage"
    )
    retwit_sender_is_official: bool | str | None = Field(
        default=None, alias="retwitSenderIsOfficial"
    )

    last_like_nickname: str | None = Field(default=None, alias="lastLikeNickName")
    like_count: int | None = Field(default=None, alias="likeCount")
    comment_count: int | None = Field(default=None, alias="commentCount")
    quote_count: int | None = Field(default=None, alias="quoteCount")
    retwit_count: int | None = Field(default=None, alias="retwitCount")
    vote_count: int | None = Field(default=None, alias="voteCount")

    type: str
    scored_post_date: str | None = Field(default=None, alias="scoredPostDate")
    final_pull_date: datetime | str | None = Field(default=None, alias="finalPullDate")
    final_pull_date_persian: str | None = Field(
        default=None, alias="finalPullDatePersian"
    )
    pull_status: str | None = Field(default=None, alias="pullStatus")
    pinned: bool | str | None = None

    image_uid: str | None = Field(default=None, alias="imageUid")
    video_uid: str | None = Field(default=None, alias="videoUid")
    file_uid: str | None = Field(default=None, alias="fileUid")
    media_content_type: str | None = Field(default=None, alias="mediaContentType")
    has_chart: bool | str | None = Field(default=None, alias="hasChart")
    options: list[Any] | None = None
    duration_per_hour: float | None = Field(default=None, alias="durationPerHour")
    duration_per_day: float | None = Field(default=None, alias="durationPerDay")

    @field_validator("id", mode="before")
    @classmethod
    def normalize_id(cls, value: Any) -> str:
        if value is None:
            raise ValueError("tweet id is required")
        value = str(value).strip()
        if not value:
            raise ValueError("tweet id cannot be empty")
        return value

    @field_validator(
        "like_count",
        "comment_count",
        "quote_count",
        "retwit_count",
        "vote_count",
        "parent_vote_count",
        mode="before",
    )
    @classmethod
    def empty_count_is_none(cls, value: Any) -> Any:
        return None if value == "" else value


class TweetPage(BaseModel):
    """The relevant part of a Sahamyab list API response."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    items: list[TweetItem] = Field(default_factory=list)
    has_more: bool = Field(default=False, alias="hasMore")
