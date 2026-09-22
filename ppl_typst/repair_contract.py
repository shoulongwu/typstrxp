"""Provider-neutral validation and assembly for C0 repair packets/responses."""
import json


ALLOWED_PACKET_FIELDS = {
    'event_id', 'original_task', 'source_before', 'target_start', 'target_end',
    'target_block', 'selected_diagnostic', 'target_diagnostics', 'dependency_spans',
}


def validate_repair_packet(packet):
    required = {
        'event_id', 'original_task', 'source_before', 'target_start', 'target_end',
        'target_block', 'selected_diagnostic', 'target_diagnostics',
    }
    if (not isinstance(packet, dict) or set(packet) - ALLOWED_PACKET_FIELDS
            or not required <= set(packet)):
        raise ValueError('Invalid C0 repair packet fields')
    if any(not isinstance(packet[name], str) or not packet[name]
           for name in ('event_id', 'original_task', 'source_before', 'target_block',
                        'selected_diagnostic')):
        raise ValueError('C0 repair packet text fields must be nonempty')
    start, end, source = packet['target_start'], packet['target_end'], packet['source_before']
    if (isinstance(start, bool) or isinstance(end, bool) or not isinstance(start, int)
            or not isinstance(end, int) or not 0 <= start < end <= len(source)):
        raise ValueError('Invalid target coordinates')
    if source[start:end] != packet['target_block']:
        raise ValueError('Target text does not match frozen source coordinates')
    dependencies = packet.get('dependency_spans', [])
    if not isinstance(dependencies, list):
        raise ValueError('Dependency spans must be an array')
    for dependency in dependencies:
        if (not isinstance(dependency, dict)
                or set(dependency) != {'start', 'end', 'evidence'}):
            raise ValueError('Each dependency span requires start, end, and evidence')
        dep_start, dep_end = dependency['start'], dependency['end']
        if (isinstance(dep_start, bool) or isinstance(dep_end, bool)
                or not isinstance(dep_start, int) or not isinstance(dep_end, int)
                or not 0 <= dep_start < dep_end <= start
                or not isinstance(dependency['evidence'], str)
                or not dependency['evidence'].strip()):
            raise ValueError('Invalid prior dependency span')
    diagnostics = packet['target_diagnostics']
    if (not isinstance(diagnostics, list) or not diagnostics
            or any(not isinstance(item, str) or not item for item in diagnostics)
            or packet['selected_diagnostic'] not in diagnostics):
        raise ValueError('Target diagnostics must include the selected primary diagnostic')
    return packet


def validate_repair_response(data, response_mode='prefix', source_before=None,
                             target_end=None):
    """Return the assembled editable prefix after strict response validation."""
    if response_mode == 'prefix':
        if not isinstance(data, dict) or set(data) != {'prefix_after'}:
            raise ValueError('Repair response must contain only prefix_after')
        if not isinstance(data['prefix_after'], str) or not data['prefix_after']:
            raise ValueError('Repair response returned no candidate prefix')
        return data['prefix_after']
    if response_mode != 'edits' or source_before is None or target_end is None:
        raise ValueError('Invalid repair response mode')
    if not isinstance(data, dict) or set(data) != {'edits'} or not isinstance(data['edits'], list):
        raise ValueError('Repair response must contain only edits')
    if not 1 <= len(data['edits']) <= 32:
        raise ValueError('Repair response must contain between 1 and 32 edits')
    edits = []
    for edit in data['edits']:
        if not isinstance(edit, dict) or set(edit) != {'start', 'end', 'replacement'}:
            raise ValueError('Each edit requires start, end, and replacement')
        start, end, replacement = edit['start'], edit['end'], edit['replacement']
        if (isinstance(start, bool) or isinstance(end, bool) or not isinstance(start, int)
                or not isinstance(end, int) or not 0 <= start < end <= target_end
                or not isinstance(replacement, str)):
            raise ValueError('Invalid edit coordinates or replacement')
        edits.append((start, end, replacement))
    ordered = sorted(edits)
    if any(left[1] > right[0] for left, right in zip(ordered, ordered[1:])):
        raise ValueError('Repair edits overlap')
    prefix = source_before[:target_end]
    for start, end, replacement in reversed(ordered):
        prefix = prefix[:start] + replacement + prefix[end:]
    return prefix


def parse_repair_response(text, response_mode='prefix', source_before=None,
                          target_end=None):
    return validate_repair_response(
        json.loads(text.strip()), response_mode, source_before, target_end)
