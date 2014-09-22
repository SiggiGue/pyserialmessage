import serial
import pyserialmessage as psm


s = serial.Serial('COM3', 9600, timeout=0.1)
hdlc = psm.SimpleHDLC(com=s)

message = 'Hello World'
hdlc.write(message)
msg_read = hdlc.read()

print(msg_read)
print('msg_read.decode()==message:',
      msg_read.decode()==message)


message ={
    'a': [1, 2, 3],
    'b': {'c': 'Hello World'},
    }

hdlc.write(message)

msg_read = hdlc.read()
print(msg_read)

s.close()
