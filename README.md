
<p align="center"><img src="https://github.com/packing-box/custom-packer/raw/main/docs/pages/imgs/logo.png" width="150" height="150" style="border-radius:50%;"></p>
<h1 align="center">PackBin</h1>
<h3 align="center">Custom extensible executable packer for experimenting with packing techniques </h3>

<div align="center">

[![Read The Docs](https://readthedocs.org/projects/custom-packer/badge/?version=latest)](http://custom-packer.readthedocs.io/en/latest/?badge=latest)
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


## :clap:  Supporters

[![Stargazers repo roster for @packing-box/custom-packer](https://reporoster.com/stars/dark/packing-box/custom-packer)](https://github.com/packing-box/custom-packer/stargazers)

[![Forkers repo roster for @packing-box/custom-packer](https://reporoster.com/forks/dark/packing-box/custom-packer)](https://github.com/packing-box/custom-packer/network/members)

<p align="center"><a href="#"><img src="https://img.shields.io/badge/Back%20to%20top--lightgrey?style=social" alt="Back to top" height="20"/></a></p>

