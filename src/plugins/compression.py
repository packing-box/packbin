import zlib, struct

class CompressionPlugin:
	implemented_compression_method = ["deflate"]

	def __init__(self, args):
		if args in self.implemented_compression_method:
			self.method = args
		else:
			print("CompressionPlugin: Incorrect parameter")
			print(f"Please provide one of the implemented compression method: {self.implemented_compression_method}")
			print("Example: compression:deflate")
			exit()

	def run(self, arch, data):
		original_length = len(data)
		compressed = zlib.compress(data, 9)
		compressed_length = len(compressed)
		section_content = struct.pack('<II', compressed_length, original_length)
		section_content += compressed
		zlib_dir = f"/app/vendor/zlib/build-{arch}/install-{arch}"
		compilation_params = [
			f"-I{zlib_dir}/include",
			f"-L{zlib_dir}/lib",
			"-lz"
		]
		decompress_signature = "void decompress(void *compressed, size_t length, void *decompressed, size_t decompressed_length);"
		decompress_function = """void decompress(void *compressed, size_t length, void *decompressed, size_t decompressed_length) {
	z_stream inflate_stream;
	inflate_stream.zalloc = Z_NULL;
	inflate_stream.zfree = Z_NULL;
	inflate_stream.opaque = Z_NULL;
	inflate_stream.avail_in = (uInt)length;
	inflate_stream.next_in = (Bytef *)compressed;
	inflate_stream.avail_out = (uInt)decompressed_length;
	inflate_stream.next_out = (Bytef *)decompressed;
	inflateInit(&inflate_stream);

	int err = inflate(&inflate_stream, Z_NO_FLUSH);
	if (err != Z_STREAM_END) {
		inflateEnd(&inflate_stream);
		MessageBoxA(NULL, "zlib decompression failed", "zlib", MB_OK);
		return;
	}
	inflateEnd(&inflate_stream);
	return;
}"""
		stub = """/*----- DEFLATE STUB START -----*/
	{
		DWORD compressed_size = *((DWORD *)buf);         // compressed size little-endian
		DWORD decompressed_size = *((DWORD *)(buf + 4)); // decompressed size little-endian
		void *compressed = (void *)(buf + 8);            // compressed buffer
		void *decompressed = malloc(decompressed_size);  // decompressed buffer

		if (decompressed == NULL) {
			MessageBoxA(NULL, "memory allocate failed", "malloc", MB_OK);
			return 0;
		}

		decompress(compressed, compressed_size, decompressed, decompressed_size);

		size = decompressed_size;
		buf = decompressed;
	}
	"""
		return (
			section_content,
			compilation_params,
			["#include <zlib.h>"],
			[decompress_signature],
			[decompress_function],
			stub
		)