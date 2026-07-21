from __future__ import annotations

from uuid import UUID


class AgentExecutionError(RuntimeError):
    def __init__(
        self,
        *,
        run_id: UUID,
        code: str,
        message: str,
        retryable: bool,
    ) -> None:
        super().__init__(message)
        self.run_id = run_id
        self.code = code
        self.message = message
        self.retryable = retryable

