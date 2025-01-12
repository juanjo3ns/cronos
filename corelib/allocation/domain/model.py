# -*- coding: utf-8 -*-
"""This module contains the Domain Model use to capture the business logic.

Created on: 20/6/22
@author: Heber Trujillo <heber.trj.urt@gmail.com>
Licence,
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import (
    List,
    NewType,
    Optional,
)

from corelib.exceptions import OutOfStock

OrderId = NewType("OrderId", str)
Quantity = NewType("Quantity", int)
Sku = NewType("Quantity", int)
Reference = NewType("Reference", str)


@dataclass(unsafe_hash=True)
class OrderLine:
    """Represent an order line within a Customer order."""

    orderid: OrderId
    sku: Sku
    qty: Quantity


class Batch:
    """Model for the batches of stock that the purchasing department orders."""

    def __init__(
        self, ref: Reference, sku: Sku, qty: Quantity, eta: Optional[date]
    ):
        """Initialize a Batch instance.

        Args:
            ref: Reference number to track the batch.
            sku: Product identifier.
            qty: Purchased quantity.
            eta: Estimated time of arrival.
        """
        self.reference = ref
        self.sku = sku
        self.eta = eta
        self._purchased_quantity = qty
        self._allocations = set()

    def allocate(self, line: OrderLine):
        """Allocate customer order line to order batch.

         The order line quantity only gets allocated to batch if order
         quantity is less or equal than batch available quantity and the SKUs
         matched.

        Args:
            line: Customer order line.

        Returns:
            None
        """
        if self.can_allocate(line):
            self._allocations.add(line)

    def deallocate(self, line: OrderLine):
        """Deallocate customer order line to order batch.

         The order line only gets deallocated if it as previously allocated
         to the batch.

        Args:
            line: Customer order line.

        Returns:
            None
        """
        if line in self._allocations:
            self._allocations.remove(line)

    @property
    def allocated_quantity(self) -> int:
        """Calculate number of allocated items inside the batch."""
        return sum(line.qty for line in self._allocations)

    @property
    def available_quantity(self) -> int:
        """Calculate number of available items inside the batch."""
        return self._purchased_quantity - self.allocated_quantity

    def can_allocate(self, line: OrderLine) -> bool:
        """Test if the customer order line can be allocated to the batch.

        An order line only can be allocated if its sku matches the batch sku
        and its quantity <= batch available quantity.

        Args:
            line: Customer order line.

        Returns:
            True if customer order line can be allocated to batch.
        """
        return self.sku == line.sku and line.qty <= self.available_quantity

    def __gt__(self, other: Batch) -> bool:
        """Greater than operator use ETAs."""
        if self.eta is None:
            return False
        if other.eta is None:
            return True
        return self.eta > other.eta

    def __repr__(self):
        """Batch representation."""
        return f"<Batch {self.reference}>"

    def __eq__(self, other: Batch):
        """Two batches are equal if they have the same reference."""
        if not isinstance(other, Batch):
            return False
        return other.reference == self.reference

    def __hash__(self):
        """Batches are uniquely identified by their ref."""
        return hash(self.reference)


def allocate(line: OrderLine, batches: List[Batch]) -> str:
    """Allocate order line to the earliest Batch.

    Args:
        line: Order line.
        batches: List of order batches

    Returns:
        batch_reference:
            Reference of the batch in which the line was allocated.

    """
    try:
        batch = next(b for b in sorted(batches) if b.can_allocate(line))

    except StopIteration:
        raise OutOfStock(f"Out of stock for sku: {line.sku}")

    batch.allocate(line)

    return batch.reference
