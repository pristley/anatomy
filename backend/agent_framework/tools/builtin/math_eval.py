"""Safe math expression evaluator."""
from __future__ import annotations

import ast
import operator as op
from typing import Any

# supported operators
_ops = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.USub: op.neg,
}


def _eval(node: ast.AST) -> Any:
    if isinstance(node, ast.Num):
        return node.n
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.BinOp):
        return _ops[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp):
        return _ops[type(node.op)](_eval(node.operand))
    raise ValueError("unsupported expression")


def evaluate_expression(expr: str) -> float:
    tree = ast.parse(expr, mode="eval")
    return float(_eval(tree.body))


__all__ = ["evaluate_expression"]
