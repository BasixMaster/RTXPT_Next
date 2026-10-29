"""Decode pinned PresentMon console logs before checking reported ETW loss."""

def decode_log(raw):
    codec='utf-16' if raw.startswith((b'\xff\xfe',b'\xfe\xff')) else 'utf-8-sig'
    return raw.decode(codec,errors='replace')

def reported_loss(raw):
    return 'ETW events were lost' in decode_log(raw)
