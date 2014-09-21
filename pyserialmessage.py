from serial import Serial, EIGHTBITS, PARITY_NONE, STOPBITS_ONE
from binascii import crc32


HDLC_FLAG = 0x7e
HDLC_ESCAPE = 0x7d

"""
Packet definition:
<HDLC_FLAG_BYTE
"""

def escape_hdlc_flag_bytes(message):
    """Returns list of integers of escaped message
    suitable for hdlc packaging.
    Parameters
    ----------
    message : bytes
        The message bytestring toi be escaped.

    Returns
    -------
    escaped : list
        A list of integers representing the escaped bytes.

    """
        escaped = []
        for b in message:
            if (b == HDLC_FLAG or
                b == HDLC_ESCAPE):
                escaped.append(HDLC_ESCAPE)
                escaped.append(b ^ 0x20)
            else:
                escaped.append(b)
        return escaped

def unescape_hdlc_flag_bythes(escaped):
    """Returns unescaped list of integers of escaped message
    suitable for hdlc packaging.
    Parameters
    ----------
    message : list
        The message bytestring toi be escaped.

    Returns
    -------
    escaped : list
        A list of integers representing the escaped bytes.

    """
    message = []
    is_esc = False
    for b in escaped:
        if is_esc:
            message.append(b ^ 0x20)
            is_esc = False
        elif b == HDLC_ESCAPE:
            is_esc = True
        else:
            message.append(b)
    return message


class SimpleHDLC(obj):

    def __init__(self, com, client_id=None):
        self._com = com
        self._client_id = client_id

    def read(self):
        message = []
        data = self.read(1)
        while data != HDLC_FLAG

            message.append(self._com.read(1)

    def write(self, message):
        pass
