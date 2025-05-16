import lief, subprocess

class Packer:
	def __init__(self, raw, file, arch, file_format):
		self.raw = raw
		self.file = file
		self.arch = arch
		self.file_format = file_format
		self.stub_alterations = {
			"imports": [],
			"signatures": [],
			"functions": [],
			"unpacking_code": []
		}

	def align(self, x, al):
		""" return <x> aligned to <al> """
		return x if x % al == 0 else x - (x % al) + al

	def compile_stub(self, more_parameters = []):
		self.stub_path = f"stubs/{self.file_format}/{self.arch}/"
		with open(f"{self.stub_path}stub.c", "r") as f:
			stub = f.read()
		# Import, signatures and functions should only be defined once
		stub = stub.replace("//PLUGINS-IMPORTS", "\n".join(set(self.stub_alterations["imports"])))
		stub = stub.replace("//PLUGINS-SIGNATURES", "\n".join(set(self.stub_alterations["signatures"])))
		stub = stub.replace("//PLUGINS-FUNCTIONS", "\n".join(set(self.stub_alterations["functions"])))
		# Unpacking stub should be done as much as required
		stub = stub.replace("//PLUGINS-STUBS", "\n\t".join(self.stub_alterations["unpacking_code"]))
		with open(f"{self.stub_path}generated_stub.c", "w") as f:
			f.write(stub)

		if self.file_format == "pe":
			if self.arch == "x86":
				compilation_cmd = [
					"i686-w64-mingw32-gcc", f"{self.stub_path}generated_stub.c",
					"-o", f"{self.stub_path}stub.exe",
					*set(more_parameters),
					"-Wl,--entry=__start",  # Define the entry point
					"-nostartfiles", "-nostdlib",
					"-lmsvcrt", "-lkernel32", "-luser32", # memcpy, strcmp, etc + win api calls
					"-fno-ident", "-fno-asynchronous-unwind-tables", "-fno-exceptions",  # Remove unnecessary sections
					"-g0"
				]
				strip_cmd = [
					"i686-w64-mingw32-strip",
					"--strip-all",
					f"{self.stub_path}stub.exe"
				]
			elif self.arch == "x64":
				compilation_cmd = [
					"x86_64-w64-mingw32-gcc", f"{self.stub_path}generated_stub.c",
					"-o", f"{self.stub_path}stub.exe",
					*set(more_parameters),
					"-Wl,--entry=_start",  # Define the entry point
					# We remove an _ because of: https://learn.microsoft.com/en-us/cpp/build/reference/decorated-names?view=msvc-170#FormatC
					"-nostartfiles", "-nostdlib",
					"-lmsvcrt", "-lkernel32", "-luser32", # memcpy, strcmp, etc + win api calls
					"-fno-ident", "-fno-asynchronous-unwind-tables", "-fno-exceptions",  # Remove unnecessary sections
					"-g0"
				]
				strip_cmd = [
					"x86_64-w64-mingw32-strip",
					"--strip-all",
					f"{self.stub_path}stub.exe"
				]
			else:
				print(f"Unknown architecture {self.arch}")
		elif self.file_format == "elf":
			raise NotYetImplementedError
		elif self.file_format == "macho":
			raise NotYetImplementedError
		else:
			print(f"Unknown file format {self.file_format}")

		#print(" ".join(compilation_cmd))
		subprocess.run(compilation_cmd)
		subprocess.run(strip_cmd)

	def main(self, plugins):
		compile_parameters = []
		for plugin in plugins:
			self.raw, compil, imports, signs, funcs, unpack_code = plugin.run(self.arch, self.raw)
			compile_parameters += compil
			self.stub_alterations["imports"] += imports
			self.stub_alterations["signatures"] += signs
			self.stub_alterations["functions"] += funcs
			self.stub_alterations["unpacking_code"].insert(0, unpack_code) # Stubs needs to be executed in reverse order

		has_aslr = (self.file.optional_header.dll_characteristics & lief.PE.OptionalHeader.DLL_CHARACTERISTICS.DYNAMIC_BASE != 0)
		if has_aslr:
			self.compile_stub(compile_parameters)
			stub = lief.PE.parse(f"{self.stub_path}stub.exe")
			packed = stub # we can use the current state of stub as our output
		else:
			compile_parameters += ["-Wl,--disable-dynamicbase", "-Wl,--disable-reloc-section"] # Disable relocations
			self.compile_stub(compile_parameters)
			stub = lief.PE.parse(f"{self.stub_path}stub.exe")
			# We need to modify the stub and add a section just after the headers
			# Like this when unpacking happens it will occur in the .alloc section

			min_RVA = min([x.virtual_address for x in self.file.sections]) # Start of the first section in memory
			max_RVA = max([x.virtual_address + x.virtual_size for x in self.file.sections]) # End of the last section in memory

			# Now we create the section
			alloc_section = lief.PE.Section(".alloc")
			alloc_section.virtual_address = min_RVA
			alloc_section.virtual_size = self.align(max_RVA - min_RVA, stub.optional_header.section_alignment)
			alloc_section.characteristics = (
				lief.PE.Section.CHARACTERISTICS.MEM_READ |
				lief.PE.Section.CHARACTERISTICS.MEM_WRITE |
				lief.PE.Section.CHARACTERISTICS.CNT_UNINITIALIZED_DATA |
				lief.PE.Section.CHARACTERISTICS.MEM_EXECUTE
			)

			# Compute how much we need to shift all the other sections to place .alloc before
			min_stub_RVA = min([x.virtual_address for x in stub.sections])
			shift_RVA = (min_RVA + alloc_section.virtual_size) - min_stub_RVA

			# Recompile the stub with enough room for the ".alloc" section
			compile_parameters += [f"-Wl,--image-base={hex(self.file.optional_header.imagebase)}"]
			for s in stub.sections:
				compile_parameters += [f"-Wl,--section-start={s.name}={hex(self.file.optional_header.imagebase + s.virtual_address + shift_RVA )}"]
			
			self.compile_stub(compile_parameters)
			stub = lief.PE.parse(f"{self.stub_path}stub.exe")

			# Create a completely new binary
			if self.arch == "x86":
				packed = lief.PE.Binary(lief.PE.PE_TYPE.PE32)
				# Fix some issues:
				# https://github.com/lief-project/LIEF/issues/1118
				packed.header.sizeof_optional_header = 0xE0
				packed.header.add_characteristic(lief.PE.Header.CHARACTERISTICS.NEED_32BIT_MACHINE)
			elif self.arch == "x64":
				packed = lief.PE.Binary(lief.PE.PE_TYPE.PE32_PLUS)
				packed.header.sizeof_optional_header = 0xF0

			# Add standard characteristics for .exe file
			packed.header.add_characteristic(lief.PE.Header.CHARACTERISTICS.RELOCS_STRIPPED)
			packed.header.add_characteristic(lief.PE.Header.CHARACTERISTICS.EXECUTABLE_IMAGE)

			# Copy important informations
			packed.optional_header.imagebase = stub.optional_header.imagebase
			packed.optional_header.addressof_entrypoint = stub.optional_header.addressof_entrypoint
			packed.optional_header.section_alignment = stub.optional_header.section_alignment
			packed.optional_header.file_alignment = stub.optional_header.file_alignment
			packed.optional_header.sizeof_image = stub.optional_header.sizeof_image

			# Make the file look more legit
			packed.dos_stub = stub.dos_stub
			packed.header.time_date_stamps = stub.header.time_date_stamps
			packed.header.pointerto_symbol_table = 0
			packed.header.add_characteristic(lief.PE.Header.CHARACTERISTICS.LINE_NUMS_STRIPPED)
			packed.header.add_characteristic(lief.PE.Header.CHARACTERISTICS.DEBUG_STRIPPED)
			packed.optional_header.major_linker_version = stub.optional_header.major_linker_version
			packed.optional_header.minor_linker_version = stub.optional_header.minor_linker_version
			packed.optional_header.sizeof_code = stub.optional_header.sizeof_code
			packed.optional_header.sizeof_initialized_data = stub.optional_header.sizeof_initialized_data
			packed.optional_header.baseof_code = stub.optional_header.baseof_code
			packed.optional_header.major_operating_system_version = stub.optional_header.major_operating_system_version
			packed.optional_header.minor_operating_system_version = stub.optional_header.minor_operating_system_version
			packed.optional_header.major_image_version = stub.optional_header.major_image_version
			packed.optional_header.minor_image_version = stub.optional_header.minor_image_version
			packed.optional_header.major_subsystem_version = stub.optional_header.major_subsystem_version
			packed.optional_header.minor_subsystem_version = stub.optional_header.minor_subsystem_version

			# Make sure ASLR is disabled
			packed.optional_header.dll_characteristics = 0

			# Copy the data directories (imports most notably)
			for i in range(0, 15):
				packed.data_directories[i].rva = stub.data_directories[i].rva
				packed.data_directories[i].size = stub.data_directories[i].size   

			# Add the sections in order
			packed.add_section(alloc_section)
			for s in stub.sections:
				s.offset = 0 # Let LIEF place the sections itself in the binary
				s.sizeof_raw_data = 0
				packed.add_section(s)
			# The continue the rest

		packed_section = lief.PE.Section(".packed")
		packed_section.content =  list(self.raw) # Here self.raw will be modified by the different plugins
		packed_section.characteristics = (
			lief.PE.Section.CHARACTERISTICS.MEM_READ |
			lief.PE.Section.CHARACTERISTICS.MEM_WRITE |
			lief.PE.Section.CHARACTERISTICS.CNT_INITIALIZED_DATA
		)
		packed.add_section(packed_section)
		packed.optional_header.sizeof_image = 0 # Automatically computed by LIEF

		builder = lief.PE.Builder(packed)
		builder.build()
		builder.write("../dist/packed.exe")
		print("Successfully wrote packed file to dist/packed.exe")