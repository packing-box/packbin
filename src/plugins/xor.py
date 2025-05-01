import re

class XorPlugin:
	def __init__(self, args):
		pattern = r"^0x[a-fA-F0-9]{2}$"
		if re.match(pattern, args):
			self.key = args
		else:
			print("XorPlugin: Incorrect parameter")
			print("Please provide a key in the form: 0x[0-9A-F]{2}")
			print("Example: xor:0x5F")
			exit()

	def run(self, data):
		section_content = bytes([b ^ int(self.key, 16) for b in data])
		stub = """/*----- XOR-KEY STUB START -----*/
	{
		DWORD oldProtect;
		VirtualProtect(buf, size, PAGE_READWRITE, &oldProtect);

		DWORD key = KEY;
		for(DWORD i=0; i<size; ++i) {
			buf[i] = buf[i] ^ key;
		}
	}
	""".replace("KEY", self.key)
		return (
			section_content,
			[],
			[],
			[],
			stub
		)