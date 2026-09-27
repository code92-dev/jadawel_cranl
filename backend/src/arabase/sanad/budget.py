"""How much Sanad a workspace may use each month, and how much it has used.

Two limits, both per workspace and per calendar month (UTC):

- **Turns** — messages sent to Sanad. Counted when the message is accepted, so
  a burst of messages cannot slip past the limit while the first ones run.
  Resuming a turn after an approval is the same turn and is not counted again.
- **Tokens** — input plus output tokens, as the provider reports them. Recorded
  after every model run, successful or not, since a failed run is billed too. A
  running turn is also capped at what is left of the month
  (``UsageLimits.total_tokens_limit``), so one turn cannot overshoot the budget
  by more than a single model response.

A workspace's ``SanadBudget`` row sets its limits; a limit left empty there
falls back to ``JADAWEL_SANAD_MONTHLY_TURN_LIMIT`` /
``JADAWEL_SANAD_MONTHLY_TOKEN_LIMIT``, read at call time like the Page view's
CDN list, and a dimension with neither is unlimited.
"""

import os
from dataclasses import dataclass
from datetime import date
from typing import Optional

from django.db.models import F
from django.utils import timezone

from arabase.sanad.exceptions import SanadBudgetExceeded
from arabase.sanad.models import SanadBudget, SanadUsage
from jadawel.core.models import Workspace

TURN_LIMIT_ENV = "JADAWEL_SANAD_MONTHLY_TURN_LIMIT"
TOKEN_LIMIT_ENV = "JADAWEL_SANAD_MONTHLY_TOKEN_LIMIT"


def current_month() -> date:
    return timezone.now().date().replace(day=1)


def _default_limit(name: str) -> Optional[int]:
    """A positive integer from the environment; anything else means no limit."""

    try:
        value = int(os.getenv(name, "").strip())
    except ValueError:
        return None
    return value if value > 0 else None


@dataclass(frozen=True)
class BudgetStatus:
    month: date
    turn_limit: Optional[int]
    token_limit: Optional[int]
    turns: int
    tokens: int

    @property
    def remaining_tokens(self) -> Optional[int]:
        if self.token_limit is None:
            return None
        return max(self.token_limit - self.tokens, 0)

    @property
    def turns_exhausted(self) -> bool:
        return self.turn_limit is not None and self.turns >= self.turn_limit

    @property
    def tokens_exhausted(self) -> bool:
        return self.token_limit is not None and self.tokens >= self.token_limit


def get_limits(workspace: Workspace) -> tuple[Optional[int], Optional[int]]:
    """``(turn limit, token limit)``; ``None`` is unlimited."""

    budget = SanadBudget.objects.filter(workspace=workspace).first()
    turn_limit = budget.monthly_turn_limit if budget else None
    token_limit = budget.monthly_token_limit if budget else None
    if turn_limit is None:
        turn_limit = _default_limit(TURN_LIMIT_ENV)
    if token_limit is None:
        token_limit = _default_limit(TOKEN_LIMIT_ENV)
    return turn_limit, token_limit


def _status(workspace: Workspace, usage: Optional[SanadUsage]) -> BudgetStatus:
    turn_limit, token_limit = get_limits(workspace)
    return BudgetStatus(
        month=current_month(),
        turn_limit=turn_limit,
        token_limit=token_limit,
        turns=usage.turns if usage else 0,
        tokens=usage.tokens if usage else 0,
    )


def get_status(workspace: Workspace) -> BudgetStatus:
    usage = SanadUsage.objects.filter(
        workspace=workspace, month=current_month()
    ).first()
    return _status(workspace, usage)


def _locked_usage(workspace: Workspace) -> SanadUsage:
    """This month's usage row, locked. Call it inside a transaction."""

    SanadUsage.objects.get_or_create(workspace=workspace, month=current_month())
    return SanadUsage.objects.select_for_update().get(
        workspace=workspace, month=current_month()
    )


def start_turn(workspace: Workspace) -> BudgetStatus:
    """Count a new turn, or refuse it. Call it inside a transaction.

    :raises SanadBudgetExceeded: when the month's turns or tokens are used up.
    """

    usage = _locked_usage(workspace)
    status = _status(workspace, usage)
    if status.turns_exhausted or status.tokens_exhausted:
        raise SanadBudgetExceeded()
    usage.turns = F("turns") + 1
    usage.save(update_fields=["turns"])
    return status


def check_can_resume(workspace: Workspace) -> None:
    """A paused turn may resume while tokens are left; it is no new turn.

    :raises SanadBudgetExceeded: when the month's tokens are used up.
    """

    if get_status(workspace).tokens_exhausted:
        raise SanadBudgetExceeded()


def record_usage(workspace: Workspace, usage) -> None:
    """Add one model run's ``RunUsage`` to this month's total."""

    if not (usage.requests or usage.input_tokens or usage.output_tokens):
        return
    SanadUsage.objects.get_or_create(workspace=workspace, month=current_month())
    SanadUsage.objects.filter(workspace=workspace, month=current_month()).update(
        requests=F("requests") + usage.requests,
        input_tokens=F("input_tokens") + usage.input_tokens,
        output_tokens=F("output_tokens") + usage.output_tokens,
    )
