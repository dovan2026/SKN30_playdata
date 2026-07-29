from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class ChatMessage(BaseModel):
    """One user or assistant message in the browser-managed conversation."""

    role: Literal["user", "assistant"]
    content: str = Field(
        min_length=1,
        max_length=4000,
        description="Plain-text chat message",
    )

    @field_validator("content")
    @classmethod
    def strip_content(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Message content must not be blank.")
        return stripped


class ChatRequest(BaseModel):
    """A bounded conversation sent to the OpenAI Responses API."""

    messages: list[ChatMessage] = Field(
        min_length=1,
        max_length=20,
        description="Conversation history ending with a user message",
    )

    @model_validator(mode="after")
    def validate_conversation(self) -> "ChatRequest":
        if self.messages[-1].role != "user":
            raise ValueError("The last message must have the user role.")

        if sum(len(message.content) for message in self.messages) > 12_000:
            raise ValueError("The conversation is too long.")

        for previous, current in zip(self.messages, self.messages[1:]):
            if previous.role == current.role:
                raise ValueError("User and assistant roles must alternate.")

        return self


class ChatResponse(BaseModel):
    reply: str
    model: str
    response_id: str
