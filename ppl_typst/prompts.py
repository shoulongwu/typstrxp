"""Versioned repair instruction shared by C0 and C2."""
REPAIR_INSTRUCTION = '''The following source was produced for the original Typst task.
The compiler reports an error in the specified target block; its cause may lie in earlier code.
Fix the error by modifying the target block and/or any necessary source before it.
You may edit only the prefix from the beginning of the document through the end of the target block.
Do not change any source after the target block. Preserve the intended semantics and formatting
of the target and all preceding content. Keep changes focused on the reported error and its dependencies.
Return the complete corrected Typst source only, without code fences or commentary.'''
