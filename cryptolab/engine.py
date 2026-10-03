"""Compute constant-product swap execution and reject quotes outside user-defined price-impact and output bounds."""

from .common import (
    number,
    integer,
    identity,
    records,
    chronology,
    allocate,
    result,
    validate_document,
)
from decimal import Decimal


def _analyze(d):
    x = integer(d["reserve_in"], 1)
    y = integer(d["reserve_out"], 1)
    fee = integer(d["fee_bps"], maximum=9999)
    rows = []
    for q in records(d["quotes"], "id"):
        amount = integer(q["amount_in"], 1)
        minimum = integer(q["minimum_output"])
        limit = number(q["maximum_impact"], maximum=1)
        effective = amount * (10000 - fee)
        output = effective * y // (x * 10000 + effective)
        spot = number(y) / x
        execution = number(output) / amount
        impact = 1 - execution / spot
        reasons = []
        if output < minimum:
            reasons.append("minimum_output")
        if impact > limit:
            reasons.append("price_impact")
        rows.append(
            {
                "id": q["id"],
                "output": output,
                "execution_price": execution,
                "impact": impact,
                "accepted": not reasons,
                "reasons": reasons,
                "post_swap_product": (x + amount) * (y - output),
            }
        )
    return result({"quotes": rows, "initial_product": x * y})


def analyze(document):
    validate_document(document)
    try:
        return result(_analyze(document))
    except (KeyError, TypeError, ArithmeticError, RecursionError) as error:
        raise ValueError("invalid domain input: " + str(error)) from error
