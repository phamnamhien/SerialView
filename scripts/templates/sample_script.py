"""
Sample Script Template
Gửi command và đợi response
"""

# Log message
ctx.log("Starting communication...")

# Gửi command (HEX)
ctx.send_hex("01 03 00 00 00 0A C5 CD")
ctx.log("Sent: Read Holding Registers")

# Đợi 100ms
ctx.wait(0.1)

# Hoặc gửi string
ctx.send_string("AT\r\n")
ctx.log("Sent: AT command")

# Lặp gửi
for i in range(5):
    ctx.send_hex(f"AA {i:02X} BB")
    ctx.wait(0.5)
    ctx.log(f"Sent packet {i}")

# Sử dụng biến
counter = ctx.get_var("counter", 0)
counter += 1
ctx.set_var("counter", counter)
ctx.log(f"Counter: {counter}")
