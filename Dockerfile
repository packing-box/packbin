FROM ubuntu:latest

RUN apt update
RUN apt install -y python3 python3-pip git
RUN apt install -y mingw-w64 build-essential mingw-w64-tools

RUN apt install -y make curl unzip

RUN rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip3 install -r requirements.txt --break-system-packages

COPY src /app/src

RUN mkdir -p /app/dist


# --------------------------------
# Vendorize libs
# --------------------------------
WORKDIR /app/vendor
#RUN git clone https://github.com/madler/zlib.git
ADD https://github.com/madler/zlib/releases/download/v1.3.1/zlib131.zip zlib.zip
RUN unzip zlib.zip && mv zlib-1.3.1 zlib && rm zlib.zip

# --------------------------------
# Zlib specifics
# --------------------------------
WORKDIR /app/vendor/zlib

# Build zlib for x86
RUN mkdir -p build-x86 && cd build-x86 && \
    CFLAGS="-fno-exceptions -fno-asynchronous-unwind-tables -fno-unwind-tables" \
    CC=i686-w64-mingw32-gcc \
    AR=i686-w64-mingw32-ar \
    RANLIB=i686-w64-mingw32-ranlib \
    ../configure \
      --prefix="$(pwd)/install-x86" \
      --static && \
    make && make install

# Build zlib for x64
RUN mkdir -p build-x64 && cd build-x64 && \
    CFLAGS="-fno-exceptions -fno-asynchronous-unwind-tables -fno-unwind-tables" \
    CC=x86_64-w64-mingw32-gcc \
    AR=x86_64-w64-mingw32-ar \
    RANLIB=x86_64-w64-mingw32-ranlib \
    ../configure \
      --prefix="$(pwd)/install-x64" \
      --static \
      --64 && \
    make && make install

# ------------------------------------
# Move to the entrypoint of the packer
# ------------------------------------
WORKDIR /app/src
ENTRYPOINT ["/bin/bash"]