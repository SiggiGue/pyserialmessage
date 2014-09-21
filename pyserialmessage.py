import time
import msgpack
import struct
from binascii import crc32


# constants:
SLICE_MESSAGE_BODY = slice(1, -1)
HDLC_FLAG = 0x7e
HDLC_ESCAPE = 0x7d

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

def unescape_hdlc_flag_bytes(escaped):
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


class SimpleHDLC(object):

    """
    Packet definition:
    <HDLC_FLAG><Address><Control><Message Data><Frame Checksum><HDLC_FLAG>

    Overhead:
    This Protocol adds 10 bytes overhead to the data transmitted.

    """

    def __init__(self, com, only_crc_msg=True):
        self._com = com
        self._only_crc_msg = only_crc_msg
        self._raw_message_read = None
        self._raw_message_read = None
        self._crc_approoved = False

    @property
    def crc_approoved(self):
        return self._crc_approoved

    @property

    def _pack_message(self, message):
        return msgpack.packb(message)

    def _unpack_message(self, message):
        return msgpack.unpackb(message)

    def _escape(self, message):
        return escape_hdlc_flag_bytes(message)

    def _unescape(self, message):
        return unescape_hdlc_flag_bytes(message)

    def _read_byte(self):
        return struct.unpack('B', self._com.read(1))[0]

    def _read_message(self):
        """Returns message including HDLC_FLAG read from self._com"""
        message = []

        b = self._read_byte()
        if b != HDLC_FLAG:
            while b != HDLC_FLAG:
                b = self._read_byte()

        message.append(b)

        b = self._read_byte()
        while b == HDLC_FLAG:
            b = self._read_byte()

        message.append(b)

        while b != HDLC_FLAG:
            b = self._read_byte()
            message.append(b)

        self._raw_message_read = message
        return message

    def read(self, timeout=False):
        if timeout is not False:
            self._com.setTimeout(timeout)

        message = self._read_message()
        message_bytes = bytes(self._unescape(message))
        message, self._crc_recieved = self._unpack_message(message_bytes[SLICE_MESSAGE_BODY])
        self._crc_message = crc32(message)
        self._crc_approoved = (self._crc_recieved == self._crc_message)

        can_be_returned = ((self._only_crc_msg and self._crc_approoved)
                           or (not self._only_crc_msg))
        if can_be_returned:
            return  self._unpack_message(message)
        else:
            return None

    def write(self, message):
        if not isinstance(message, bytes):
            message = self._pack_message(message)
        message = self._pack_message((message, crc32(message)))
        message = [HDLC_FLAG] + self._escape(message) + [HDLC_FLAG]
        for b in message: self._com.write(
                struct.pack('B', b))
        self._raw_message_written = message
