import time
import msgpack
import struct
from binascii import crc32


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
    """This is a simplifyed version of the HDLC Protocol
    addressing the second layer of the OSI-Model.

    This class can be used in combination with the serial port
    or similar, to transmit data combined with CRC32 checksum, so the
    correctness of the recieved data can be checked.

    The most important methods are the read() and write() method.
    You can write arbitrary data types supported by the msgpack-
    module. The written data will be packed with a checksum and
    concluding flags. So the read() method will return exactly the
    same data put into the write method (strings will be bytes).
    The raw transmitted message will have the strucure as follows:

    Packet definition:
    <HDLC_FLAG><Arbitrary Message Data><Frame Checksum><HDLC_FLAG>


    The overhead added by this Protocoll is exactly
    10 bytes additionaly to the data you want to transmit.


    """

    def __init__(self, com=None, timeout=0.1, only_crc_msg=True):
        self._timeout = timeout
        self.com = com
        self._only_crc_msg = only_crc_msg
        self._raw_message_read = None
        self._raw_message_written = None
        self._crc_approoved = False

    @property
    def com(self):
        """This is the com object used for communication via read and write."""
        return self._com
    @com.setter
    def com(self, value):
        if all([hasattr(value, attr) for attr in ['read', 'write']]):
            self._com = value
            if self.timeout and not self._com.getTimeout():
                self._com.setTimeout(self.timeout)
        elif not value:
            pass
        else:
            raise(AttributeError(
                """The assigned object has to provide at least
                a read() and write()-method."""))

    @property
    def crc_approoved(self):
        """Returns a boolean denoting wether the crc32 checksum of
        the recieved message was approoved or not.
        If it was not approved, there may be a transmission fault.
        """
        return self._crc_approoved

    @property
    def timeout(self):
        """The timeout for read() method."""
        return self._timeout
    @timeout.setter
    def timeout(self, value):
        self._timeout = value

    def _pack_message(self, message):
        """Returns a packed message as bytes."""
        return msgpack.packb(message)

    def _unpack_message(self, message):
        """Returns unpacked message."""
        return msgpack.unpackb(message)

    def _escape(self, message):
        """Inserts escape bytes to the message (bytes)."""
        return escape_hdlc_flag_bytes(message)

    def _unescape(self, message):
        """Removes escape bytes from message (list)."""
        return unescape_hdlc_flag_bytes(message)

    def _read_byte(self):
        """Returns a byte from the com (Serial) buffer."""
        b = self._com.read(1)
        if b:
            return struct.unpack('B',b )[0]
        else:
            return None

    def _timer(self, ts, timeout):
        """Returns True if timeout is not exceeded else False."""
        if timeout:
            return (time.time()-ts) <= timeout
        else:
            return True

    def _read_message(self, timeout):
        """Returns message including HDLC_FLAG read from self._com"""
        if not timeout:
            timeout = self.timeout
        message = []
        ts = time.time()
        b = self._read_byte()
        if b != HDLC_FLAG:
            while b != HDLC_FLAG and self._timer(ts, timeout):
                b = self._read_byte()

        message.append(b)

        b = self._read_byte()
        while b == HDLC_FLAG and self._timer(ts, timeout):
            b = self._read_byte()

        message.append(b)

        while b != HDLC_FLAG and self._timer(ts, timeout):
            b = self._read_byte()
            message.append(b)

        self._raw_message_read = message
        return message

    def _decompose_message(self, message):
        """Returns message and crc from recieved data."""
        message_bytes = bytes(self._unescape(message))
        message, crc_recieved = self._unpack_message(message_bytes[SLICE_MESSAGE_BODY])
        return message, crc_recieved

    def _check_message(self, message, crc_recieved):
        """Returns boolean wether message can be returned."""
        self._crc_message = crc32(message)
        self._crc_approoved = (crc_recieved == self._crc_message)
        can_be_returned = ((self._only_crc_msg and self._crc_approoved)
                               or (not self._only_crc_msg))
        return can_be_returned

    def read(self, timeout=False):
        """Returns a message from the com buffer, if available.
        """
        message = self._read_message(timeout)

        if len(message) > 2:
            message, self._crc_recieved = self._decompose_message(message)
            can_be_returned = self._check_message(message, self._crc_recieved)
            if can_be_returned:
                return  self._unpack_message(message)

        return None

    def write(self, message):
        """Writes `message` to the provided com object (e.g. serial port)
        adding start and stop flag and adding a crc checksum.
        The message can be a arbitrary serializable data type, supported by the
        msgpack module or by the module used in the methods `self._unpack_message()`
        and `self._pack_message()`.
        """
        if not isinstance(message, bytes):
            message = self._pack_message(message)
        message = self._pack_message((message, crc32(message)))
        message = [HDLC_FLAG] + self._escape(message) + [HDLC_FLAG]
        for b in message: self._com.write(
                struct.pack('B', b))
        self._raw_message_written = message
