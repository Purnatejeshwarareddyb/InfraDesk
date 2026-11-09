from math import ceil
from typing import Annotated, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, StringConstraints

T = TypeVar("T")

# A string that is trimmed before its length is checked.
def text(min_length: int = 1, max_length: int = 255):
    return Annotated[str, StringConstraints(strip_whitespace=True, min_length=min_length, max_length=max_length)]


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int

    @classmethod
    def build(cls, items: list[T], total: int, page: int, page_size: int) -> "Page[T]":
        return cls(items=items, total=total, page=page, page_size=page_size, pages=max(1, ceil(total / page_size)))


class Message(BaseModel):
    message: str
