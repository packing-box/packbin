# Pack-It-Easy!

[![Security](https://github.com/packing-box/pack-it-easy/actions/workflows/security.yml/badge.svg)](https://github.com/packing-box/pack-it-easy/actions/workflows/security.yml)

Pack-It-Easy is a modular and extensible packer. It is designed with the final objective of handling different executable formats such as PE, ELF or Mach-O. Its architecture allows for activation and deactivation of unpacking stubs by means of plugin definitions. Plugins can be used multiple times and in any order deemed useful by the user.

In the current version, the packer implements packing of PE files in both x86 and x64 architectures and plugins for compression (using the deflate algorithm) and XOR encryption (using any 1-byte key).

## Requirements

- [Docker](https://www.docker.com/) installed and running.

## Installation

Clone the Pack-It-Easy repository and build the Docker image:

```bash
git clone https://github.com/packing-box/pack-it-easy.git
cd pack-it-easy
sudo docker build -t packer .
```

## Usage

Run the Docker container with volume bindings for source and output files:

```bash
sudo docker run -it --rm -v $(pwd)/src:/app/src -v $(pwd)/dist:/app/dist packer
```

Inside the container, run the packer:

```bash
python3 main.py -i input.exe
python3 main.py -i input.exe -p xor:0xAA,compression:deflate,xor:0x53
```

See the [repository README](https://github.com/packing-box/pack-it-easy) for the full plugin reference and contribution guide.
