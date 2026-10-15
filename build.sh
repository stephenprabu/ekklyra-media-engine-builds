#!/usr/bin/env bash
set -euo pipefail
platform=${1:?platform}; arch=${2:?arch}
case "$platform/$arch" in win32/x64|darwin/x64|darwin/arm64) ;; *) exit 2;; esac
root="$PWD"
# Source archives must never discover the enclosing recipe repository's Git data.
export GIT_CEILING_DIRECTORIES="$root/work"
mkdir -p work/source work/prefix work/evidence out
python3 - <<'PY'
import json, hashlib, urllib.request, pathlib, tarfile
lock=json.load(open('sources.json'))
for name, src in lock.items():
    file=pathlib.Path('work/source')/(name+'.tar.gz')
    urllib.request.urlretrieve(src['url'],file)
    assert hashlib.sha256(file.read_bytes()).hexdigest()==src['sha256'], name+' checksum mismatch'
    destination=pathlib.Path('work')/name
    destination.mkdir(exist_ok=True)
    with tarfile.open(file) as archive:
        members=archive.getmembers()
        prefix=members[0].name.split('/')[0]+'/'
        for member in members:
            if not member.name.startswith(prefix): continue
            member.name=member.name[len(prefix):]
            if member.name: archive.extract(member,destination,filter='data')
PY
{
 uname -a
 cc --version
 make --version
 nasm -v
 pkg-config --version
 python3 --version
} > work/evidence/toolchain.txt 2>&1
export PKG_CONFIG_PATH="$root/work/prefix/lib/pkgconfig"
cd work/x264
./configure --prefix="$root/work/prefix" --enable-static --disable-cli --disable-opencl --disable-lavf --disable-swscale 2>&1 | tee "$root/work/evidence/x264-configure.txt"
cp config.log "$root/work/evidence/x264-config.log"
make -j2
make install
cd "$root/work/ffmpeg"
flags=(--prefix="$root/work/prefix" --disable-autodetect --disable-shared --enable-static --enable-gpl --enable-version3 --enable-libx264 --disable-ffplay --disable-doc --disable-debug --disable-network --disable-devices --enable-indev=lavfi --pkg-config-flags=--static)
if [[ "$platform" == win32 ]]; then flags+=(--extra-ldflags=-static); fi
./configure "${flags[@]}" 2>&1 | tee "$root/work/evidence/ffmpeg-configure.txt"
cp ffbuild/config.log "$root/work/evidence/ffmpeg-config.log"
cp config.h "$root/work/evidence/ffmpeg-config.h"
make -j2
make install
cd "$root"
python3 package.py "$platform" "$arch"
