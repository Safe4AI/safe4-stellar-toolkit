from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from decimal import Decimal

from packages.middleware.models import PolicyDecision


@dataclass(frozen=True)
class PolicyConfig:
    max_spend_per_request: Decimal
    rate_limit_requests: int
    rate_limit_window_seconds: int
    denied_tools: tuple[str, ...] = ()


class RateLimiter:
    def __init__(self, *, limit: int, window_seconds: int) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str) -> tuple[bool, int]:
        now = time.time()
        with self._lock:
            window = self._events[key]
            while window and now - window[0] > self.window_seconds:
                window.popleft()
            if len(window) >= self.limit:
                return False, 0
            window.append(now)
            return True, max(0, self.limit - len(window))

    def peek(self, key: str) -> tuple[bool, int]:
        now = time.time()
        with self._lock:
            window = self._events[key]
            while window and now - window[0] > self.window_seconds:
                window.popleft()
            if len(window) >= self.limit:
                return False, 0
            return True, max(0, self.limit - len(window) - 1)


class PolicyEngine:
    def __init__(self, config: PolicyConfig) -> None:
        self.config = config
        self.rate_limiter = RateLimiter(
            limit=config.rate_limit_requests,
            window_seconds=config.rate_limit_window_seconds,
        )

    def evaluate(
        self,
        *,
        tool_name: str,
        client_id: str,
        amount: Decimal,
        risk_flag: str,
        consume_rate_limit: bool = True,
    ) -> PolicyDecision:
        reasons: list[str] = []
        if tool_name in self.config.denied_tools:
            reasons.append("tool_denied_by_policy")
        if amount > self.config.max_spend_per_request:
            reasons.append("amount_exceeds_max_spend_per_request")
        if risk_flag == "high":
            reasons.append("risk_flag_high")
        rate_ok, remaining = (
            self.rate_limiter.check(client_id)
            if consume_rate_limit
            else self.rate_limiter.peek(client_id)
        )
        if not rate_ok:
            reasons.append("rate_limit_exceeded")
        return PolicyDecision(
            decision="deny" if reasons else "allow",
            reasons=reasons,
            rate_limit_remaining=remaining,
        )
