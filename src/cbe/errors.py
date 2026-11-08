"""Stable exit codes, gate statuses, and structured errors for CBE."""

from __future__ import annotations

from typing import Any

EXIT_PASS = 0
EXIT_INPUT = 2
EXIT_GATE = 3
EXIT_SKIP = 4

PASS = "PASS"
FAIL = "FAIL"
SKIPPED_INFRA = "SKIPPED_INFRA"
PRECONDITION_FAIL = "PRECONDITION_FAIL"
NOT_UPLOADED = "NOT_UPLOADED"
SKIPPED = "SKIPPED"


class CbeError(Exception):
    """Base class for every error that must become a JSON response."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        exit_code: int = EXIT_GATE,
        gate_status: str = FAIL,
        details: list[dict[str, Any]] | None = None,
        warnings: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.exit_code = exit_code
        self.gate_status = gate_status
        self.details = list(details or [])
        self.warnings = list(warnings or [])


class InputError(CbeError):
    """Malformed or missing input. Exit 2, gate FAIL."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        details: list[dict[str, Any]] | None = None,
        gate_status: str = FAIL,
    ) -> None:
        super().__init__(
            code,
            message,
            exit_code=EXIT_INPUT,
            gate_status=gate_status,
            details=details,
        )


class PreconditionError(CbeError):
    """A release precondition (for example no eligible baseline). Exit 3."""

    def __init__(self, code: str, message: str, *, details: list[dict[str, Any]] | None = None) -> None:
        super().__init__(
            code,
            message,
            exit_code=EXIT_GATE,
            gate_status=PRECONDITION_FAIL,
            details=details,
        )


class InfraError(CbeError):
    """Infrastructure failure. Exit 3, gate SKIPPED_INFRA."""

    def __init__(self, code: str, message: str, *, details: list[dict[str, Any]] | None = None) -> None:
        super().__init__(
            code,
            message,
            exit_code=EXIT_GATE,
            gate_status=SKIPPED_INFRA,
            details=details,
        )


class GateError(CbeError):
    """Definite gate failure. Exit 3, gate FAIL."""

    def __init__(self, code: str, message: str, *, details: list[dict[str, Any]] | None = None) -> None:
        super().__init__(
            code,
            message,
            exit_code=EXIT_GATE,
            gate_status=FAIL,
            details=details,
        )


class SkipRatioError(CbeError):
    """SKIP ratio above 20 percent. Exit 4, gate FAIL."""

    def __init__(self, code: str, message: str, *, details: list[dict[str, Any]] | None = None) -> None:
        super().__init__(
            code,
            message,
            exit_code=EXIT_SKIP,
            gate_status=FAIL,
            details=details,
        )


class NotImplementedCommand(CbeError):
    """Skeleton-only placeholder. Exit 3 and never PASS."""

    def __init__(self, command: str) -> None:
        super().__init__(
            "NOT_IMPLEMENTED",
            f"{command} is not implemented in the skeleton commit",
            exit_code=EXIT_GATE,
            gate_status=FAIL,
        )


class InternalError(CbeError):
    """Unhandled internal error. Exit 3, gate FAIL, never PASS."""

    def __init__(self, message: str, *, details: list[dict[str, Any]] | None = None) -> None:
        super().__init__(
            "INTERNAL_ERROR",
            message,
            exit_code=EXIT_GATE,
            gate_status=FAIL,
            details=details,
        )
