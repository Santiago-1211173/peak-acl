from peak_acl import parse

raw = '(inform :sender sensor-1 :receiver monitor :content "23.4")'
msg = parse(raw)

print("Performative:", msg.performative)
print("Sender      :", msg['sender'])
print("Content      :", msg['content'])
