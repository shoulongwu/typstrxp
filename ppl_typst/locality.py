"""Check repair scope with code-point coordinates and an immutable downstream suffix."""
from dataclasses import dataclass


@dataclass(frozen=True)
class LocalityResult:
    compliant: bool
    prefix_unchanged: bool
    suffix_unchanged: bool
    replacement: str | None
    new_end: int | None
    repair_scope: str


def check_locality(before: str, after: str, start: int, end: int,
                   repair_scope: str = 'prefix_through_target') -> LocalityResult:
    """Default: permit edits from offset zero through the target block's original end.

    In prefix mode replacement is the whole repaired prefix, not a relocated target
    block. Recover the semantic target separately. block_only is a legacy control.
    """
    if not 0 <= start < end <= len(before):
        raise ValueError('Expected a nonempty [start, end) target block within source')
    if repair_scope not in {'prefix_through_target', 'block_only'}:
        raise ValueError('Unknown repair scope')
    prefix, suffix = before[:start], before[end:]
    p_ok, q_ok = after.startswith(prefix), after.endswith(suffix)
    required_prefix = prefix if repair_scope == 'block_only' else ''
    compliant = (q_ok and (p_ok or repair_scope == 'prefix_through_target')
                 and len(after) >= len(required_prefix) + len(suffix))
    new_end = len(after) - len(suffix) if compliant else None
    replacement_start = start if repair_scope == 'block_only' else 0
    return LocalityResult(compliant, p_ok, q_ok,
                          after[replacement_start:new_end] if compliant else None,
                          new_end, repair_scope)
