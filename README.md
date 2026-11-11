
<p align="center"><img src="https://github.com/packing-box/custom-packer/raw/main/docs/pages/imgs/logo.png" width="150" height="150" style="border-radius:50%;"></p>
<h1 align="center">PackBin</h1>
<h3 align="center">Custom extensible executable packer for experimenting with packing techniques </h3>

<div align="center">

[![Read The Docs](https://readthedocs.org/projects/custom-packer/badge/?version=latest)](https://custom-packer.readthedocs.io/en/latest/?badge=latest)
[![Security](https://github.com/packing-box/custom-packer/actions/workflows/security.yml/badge.svg)](https://github.com/packing-box/custom-packer/actions/workflows/security.yml)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-orange.svg)](https://www.gnu.org/licenses/gpl-3.0)
![Status](https://img.shields.io/badge/status-beta-red.svg)

</div>

PackBin is a modular and extensible packer. It is designed with the final objective of handling different executable formats such as PE, Elf or Mach-O. Its architecture allows for activation and deactivation of unpacking stubs by means of plugins definition. Plugins can be used multiple times and in any order deemed useful by the user.

In the current version, the packer implements packing of PE file in both x86 and x64 architectures and plugins for compression (using the deflate algorithm) and xor encryption (using any 1 byte key).

## Requirements

- [Docker](https://www.docker.com/) installed and running.

## Installation

Clone the PackBin repository and build the Docker image:
```bash
git clone https://github.com/packing-box/custom-packer.git
cd packbin
sudo docker build -t packer .
```

Run the Docker container with volume bindings for source and output files:
```bash
sudo docker run -it --rm -v $(pwd)/src:/app/src -v $(pwd)/dist:/app/dist packer
```

## Usage

Inside the container, you can run the following to see the available options:
```bash
root@container:/app/src# python3 main.py -h
usage: main.py [-h] --input INPUT [--plugins PLUGINS]

Modular Packer with Plugins

options:
  -h, --help            show this help message and exit
  --input INPUT, -i INPUT
                        Input file
  --plugins PLUGINS, -p PLUGINS
                        Comma-separated list of plugins
```

### Example of usage

Basic usage:

```bash
python3 main.py -i <input>
python3 main.py -i <input> -p <plugins>
```

Practical examples:
```bash
python3 main.py -i input.exe
# No plugin — simple embedding
python3 main.py -i input.exe -p xor:0xAA
# Single plugin — XOR encoding with 0xAA key
python3 main.py -i input.exe -p xor:0xAA,compression:deflate,xor:0x53
# Chained plugins — XOR -> compression -> XOR
```

If successful, you should see:
```
Successfully parsed executable file: input.exe
Successfully wrote packed file to dist/packed.exe
```

## Contributing
Contributing can be achieved by many means:
1. Improving main logic (loader code, packer code, plugin code, etc.)
2. Implementing other file formats (very heavy: new plugin codes, new compilation, new loader, etc.)
3. Creating a new plugin (easiest and can improve the value of the packer quickly)

New plugins needs to follow a common format:
`template.py`
```py
class TemplatePlugin:
	def __init__(self, args):
		# Check if the argument to the plugin is correct and defined
		# ie: compression:deflate (is deflate defined ?)

	def run(self, data): # data is the be packed
		imports = [] # Add needed C imports
		signatures = [] # Add function's signatures you defined
		functions = [] # Add function code you want to define
		section_content = modified(data) # perform the modification
		stub = """/*----- TEMPLATE STUB START -----*/
	{
		// Some C code to do the unpacking. You have access to 2 variables:
		// 		buf - The buffer pointing to the data to be unpacked
		//		size - The size of the above-mentionned buffer
		// At the end of the unpacking stub:
		//		1. Size should contain the current size of buf
		//		2. Buf should contain the unpacked data
	}
	"""
		return (
			section_content,
			imports,
			signatures,
			functions,
			stub
		)
```
A simple, yet complete example can be taken from the compression plugin.

<p align="center"><a href="#"><img src="https://img.shields.io/badge/Back%20to%20top--lightgrey?style=social" alt="Back to top" height="20"/></a></p>

