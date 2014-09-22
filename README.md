#Communication via Serial Port with Message Checking (CRC32)

This repo contains a simple implementation of the HDLC protocol until now.
This protocol is for the use with serial like objects for communication and coms with methods for reading and writing messages with checksums (CRC) so you can decide what to do if a message crc is not matching.

##Dependencies
Requires python3.
+ `msgpack-python`
You probably will need `pyserial` as well.

## Class: SimpleHDLC
This is a simplifyed version of the HDLC Protocol
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
`<HDLC_FLAG><Arbitrary Message Data><Frame Checksum><HDLC_FLAG>`
The overhead added by this Protocoll is exactly
10 bytes additionaly to the data you want to transmit.

###Example
```python
import serial
import pyserialmessage as psm


s = serial.Serial('COM3', 9600, timeout=0.1)
hdlc = psm.SimpleHDLC(com=s)

message = 'Hello World'
hdlc.write(message)
msg_read = hdlc.read()

print(msg_read)
>>> b'Hello World'

print('msg_read.decode()==message:',
      msg_read.decode()==message)
>>> Messages msg_read.decode()==message: True

message ={
    'a': [1, 2, 3],
    'b': {'c': 'Hello World'},
    }

hdlc.write(message)

msg_read = hdlc.read()
print(msg_read)
>>> {b'a': [1, 2, 3], b'b': {b'c': b'Hello World'}}

s.close()
```

As you can see all Datatypes are persistent except strings will be read as bytes, but you can decode them kike in the first example.

