# Standalone media engine builds

Public build recipes for FFmpeg and x264. No Ekklyra application code, data,
credentials or signing keys belong in this repository.

Manual workflow only. Standard Windows, Intel macOS and ARM macOS runners.
No paid larger runners, Actions artifact uploads, caching, installers, deployment,
signing or notarization. Outputs are attached to an unpublished draft release.

Sources are pinned in sources.json and checked before extraction. Only x264 is
enabled as an external codec library; automatic external-library detection is
disabled. No nonfree components. FFmpeg's native AAC encoder is used.

Each output contains FFmpeg, ffprobe, source archives, source lock, licence texts,
build scripts, configure logs, toolchain evidence, tests and SHA256 manifest.
These are unsigned engine candidates, not an application release or legal
clearance. Validate app integration and target OS support before distribution.

Run: bash build.sh win32 x64 (MSYS2 MINGW64), or bash build.sh darwin x64/arm64
on the matching native Mac. Requires compiler, make, nasm, pkg-config, curl,
Python 3 and tar. Workflow captures toolchain versions. Dependency packages and
runner images may evolve; this is a source-pinned recipe, not a claim of
bit-for-bit reproducibility across runner revisions.

Original build scripts in this repository: MIT (see LICENSE). FFmpeg and x264
retain their own licences, included in each bundle. GPL obligations and any
applicable codec patent requirements must be evaluated before redistribution.
