"""Versioned repair task with stage-specific response contracts."""
REPAIR_TASK = '''The following source was produced for the original Typst task.
The compiler reports an error in the specified target block; its cause may lie in earlier code.
Fix the error by modifying the target block and/or any necessary source before it.
You may edit only the prefix from the beginning of the document through the end of the target block.
Do not change any source after the target block. Preserve the intended semantics and formatting
of the target and all preceding content. Keep changes focused on the reported error and its dependencies.'''

REPAIR_INSTRUCTION = REPAIR_TASK + '''
Return the complete corrected Typst source only, without code fences or commentary.'''

ORACLE_REPAIR_INSTRUCTION = REPAIR_TASK + '''
Return only the complete corrected editable prefix from document start through the repaired target,
in the requested response field, without code fences or commentary.'''
