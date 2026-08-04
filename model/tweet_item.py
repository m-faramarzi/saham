from pydantic import BaseModel, Field
from datetime import datetime


class TweetItem(BaseModel):

id : str
sendTime: datetime
sendTimePersian: str
senderName: str
senderUsername: str
senderProfileImage: str
content: str
"parentSendTime": "2026-07-29T04:17:00Z",
 "parentSendTimePersian": "1405/05/07 07:47",
 "parentId": "464869909", 
 "parentSenderName": "hakim", 
 "parentSenderUsername": "hakim0373",
 "parentSenderProfileImage": "0415754d-3d0d-42e7-8640-ca0a8df4ff42",
 "parentContent": "#اروند بازم جنگ شد ؟ 🤐", 
lastLikeNickName:str
likeCount:str
type:str 
scoredPostDate: str
finalPullDatePersian: str
 
 
"id": "464833397",
"sendTime": "2026-07-27T12:38:34Z",
"sendTimePersian": "1405/05/05 16:08",
"retwitSendTime": "2026-07-29T05:50:38Z",
"retwitSendTimePersian": "1405/05/07 09:20", 
"retwitSenderName": "رو به صعود",
"retwitSenderUsername": "zamen1000", "retwitSenderProfileImage": "default", "senderName": "امین ", "senderUsername": "amin101", "senderProfileImage": "029cecd7-ed7f-4976-8321-f19700473246", "content": "#اروند \nیعنی واقعا نمیفهمید اروند در حال دور زدنه و میخواد برگرده؟!\nاصلا نمیتونم و نمیخوام باور کنم حقیقی سهم رو میفروشه. \nپرسود باشید.", "lastLikeNickName": "ققنوس", "likeCount": "6", "retwitCount": "1", "type": "retwit", "scoredPostDate": "1785156586134", "retwitId": "464871800", "finalPullDatePersian": ""}

    source: str = ""
    id: str = ""
    title: str = ""
    category: str = ""
    type: str = ""
    publish_date_j: str = ""
    publish_date_g: datetime | None = None
    author: str | None = None
    tags: list[str] = Field(default_factory=list)
    short_url: str = ""
    news_url: str = ""
    body: str = ""
