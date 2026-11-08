"""Unit tests for the restricted workflow-condition evaluator."""

from __future__ import annotations

from cbe.commands.enforce_no_bypass import _evaluate_condition


def test_env_function_call_is_unknown_and_not_executed() -> None:
    status, reason = _evaluate_condition("${{ env.FOO() }}")
    assert status == "unknown"
    assert "dynamic expression" in reason


def test_python_import_expression_is_unknown_and_not_executed() -> None:
    status, reason = _evaluate_condition("${{ __import__('os').system('echo pwned') }}")
    assert status == "unknown"
    assert "dynamic expression" in reason


def test_attribute_access_and_indexing_are_unknown() -> None:
    assert _evaluate_condition("${{ github.event.name }}")[0] == "unknown"
    assert _evaluate_condition("${{ matrix[0] }}")[0] == "unknown"
    assert _evaluate_condition("${{ 'a'.upper() }}")[0] == "unknown"


def test_literal_boolean_expressions_are_evaluated() -> None:
    assert _evaluate_condition("${{ !true }}")[0] == "false"
    assert _evaluate_condition("${{ 1 == 2 }}")[0] == "false"
    assert _evaluate_condition("${{ 1 == 1 }}")[0] == "true"
    assert _evaluate_condition("${{ true && false }}")[0] == "false"
    assert _evaluate_condition("${{ true || false }}")[0] == "true"
    assert _evaluate_condition("${{ false }}")[0] == "false"


def test_dynamic_context_is_unknown() -> None:
    assert _evaluate_condition("${{ inputs.skip_cbe == 'true' }}")[0] == "unknown"
    assert _evaluate_condition("${{ inputs.foo == inputs.bar }}")[0] == "unknown"
    assert _evaluate_condition("${{ env.FOO() == true }}")[0] == "unknown"
    assert _evaluate_condition("${{ vars.SKIP_CBE }}")[0] == "unknown"
    assert _evaluate_condition("${{ github.event_name == 'pull_request' }}")[0] == "unknown"
    assert _evaluate_condition("${{ needs.preflight.result == 'success' }}")[0] == "unknown"
