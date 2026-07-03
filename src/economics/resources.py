"""Disposable-resource component helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResourceComponents:
    """Components of a broad disposable-resource measure.

    Amounts should be expressed in the same dollar year before combining.
    """

    money_income: float = 0.0
    realized_capital_gains: float = 0.0
    noncash_benefits: float = 0.0
    health_insurance_value: float = 0.0
    federal_income_taxes: float = 0.0
    payroll_taxes: float = 0.0
    state_local_income_taxes: float = 0.0

    def comprehensive_disposable_resources(self) -> float:
        """Return broad household resources after taxes."""

        resources = (
            self.money_income
            + self.realized_capital_gains
            + self.noncash_benefits
            + self.health_insurance_value
        )
        taxes = (
            self.federal_income_taxes
            + self.payroll_taxes
            + self.state_local_income_taxes
        )
        return resources - taxes
