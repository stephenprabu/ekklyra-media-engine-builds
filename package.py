import hashlib, json, os, pathlib, shutil, struct, subprocess, sys, tarfile

platform, arch=sys.argv[1:]
root=pathlib.Path.cwd()
bundle=root/'out'/f'engine-{platform}-{arch}'
bundle.mkdir(parents=True,exist_ok=True)
ext='.exe' if platform=='win32' else ''
ff=root/'work/prefix/bin'/('ffmpeg'+ext)
probe=root/'work/prefix/bin'/('ffprobe'+ext)
def run(args):
    return subprocess.run([str(a) for a in args],check=True,capture_output=True,text=True,timeout=180).stdout
version=run([ff,'-version'])
assert '--enable-nonfree' not in version
assert '--enable-libx264' in version and '--disable-autodetect' in version
assert '7.1.5' in version
data=ff.read_bytes()
if platform=='win32':
    pe=struct.unpack_from('<I',data,60)[0]
    assert data[:2]==b'MZ' and data[pe:pe+4]==b'PE\0\0'
    assert struct.unpack_from('<H',data,pe+4)[0]==0x8664
    deps=run(['objdump','-p',ff])
    forbidden=['libgcc','libwinpthread','libstdc++','libx264']
    dlls=[line for line in deps.splitlines() if 'DLL Name:' in line]
    assert not any(token in '\n'.join(dlls).lower() for token in forbidden),dlls
else:
    assert struct.unpack_from('<I',data)[0]==0xfeedfacf
    assert struct.unpack_from('<I',data,4)[0]==({'x64':0x1000007,'arm64':0x100000c}[arch])
    deps=run(['otool','-L',ff])
    for line in deps.splitlines()[1:]:
        assert line.strip().startswith(('/usr/lib/','/System/Library/')),line
(root/'work/evidence/runtime-dependencies.txt').write_text(deps)
(root/'work/evidence/ffmpeg-version.txt').write_text(version)
tests=root/'work/tests'; tests.mkdir(exist_ok=True)
source=tests/'source.mkv'
run([ff,'-y','-f','lavfi','-i','testsrc2=size=1920x1080:rate=30','-f','lavfi','-i','sine=frequency=440:sample_rate=48000','-t','2','-c:v','ffv1','-c:a','pcm_s16le',source])
original=hashlib.sha256(source.read_bytes()).hexdigest()
results=[]
for height in [720,1080]:
    output=tests/f'copy-{height}.mp4'
    run([ff,'-y','-i',source,'-vf',f'scale=-2:{height},fps=30','-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p','-threads','2','-c:a','aac','-b:a','192k','-movflags','+faststart',output])
    info=json.loads(run([probe,'-v','error','-show_streams','-show_format','-of','json',output]))
    video=next(s for s in info['streams'] if s['codec_type']=='video')
    audio=next(s for s in info['streams'] if s['codec_type']=='audio')
    assert video['codec_name']=='h264' and video['height']==height and video['pix_fmt']=='yuv420p'
    assert audio['codec_name']=='aac' and abs(float(info['format']['duration'])-2)<0.2
    run([ff,'-v','error','-i',output,'-f','null','-'])
    results.append({'height':height,'decode':'pass','duration':info['format']['duration']})
assert hashlib.sha256(source.read_bytes()).hexdigest()==original
(root/'work/evidence/tests.json').write_text(json.dumps({'tests':results,'originalUnchanged':True},indent=2))
for binary in [ff,probe]: shutil.copy2(binary,bundle/binary.name)
notices=bundle/'notices'; notices.mkdir(exist_ok=True)
for file in (root/'work/ffmpeg').glob('COPYING*'): shutil.copy2(file,notices/file.name)
shutil.copy2(root/'work/ffmpeg/LICENSE.md',notices/'FFmpeg-LICENSE.md')
shutil.copy2(root/'work/x264/COPYING',notices/'x264-COPYING')
shutil.copy2(root/'LICENSE',notices/'build-scripts-MIT.txt')
shutil.copytree(root/'work/evidence',bundle/'evidence',dirs_exist_ok=True)
shutil.copy2(root/'README.md',bundle/'BUILD.md')
source_archive=bundle/'corresponding-source.tar.gz'
with tarfile.open(source_archive,'w:gz') as archive:
    for name in ['ffmpeg.tar.gz','x264.tar.gz']:
        archive.add(root/'work/source'/name,arcname='sources/'+name)
    for name in ['sources.json','build.sh','package.py','README.md','LICENSE','.github/workflows/build.yml']:
        archive.add(root/name,arcname='recipe/'+name)
    archive.add(root/'work/evidence',arcname='evidence')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest={'platform':platform,'arch':arch,'version':'7.1.5','license':'GPL-3.0-or-later','upstreamUrl':'https://github.com/FFmpeg/FFmpeg','sha256':sha(bundle/ff.name),'notices':['notices/'+p.name for p in notices.iterdir()],'buildInstructions':'BUILD.md','sourceArchive':source_archive.name,'sourceSha256':sha(source_archive),'signed':False,'notarized':False,'buildCommit':os.getenv('GITHUB_SHA'),'runId':os.getenv('GITHUB_RUN_ID')}
(bundle/'manifest.json').write_text(json.dumps(manifest,indent=2))
(bundle/'SHA256SUMS').write_text('\n'.join(f'{sha(p)}  {p.relative_to(bundle).as_posix()}' for p in sorted(bundle.rglob('*')) if p.is_file())+'\n')
with tarfile.open(root/'out'/f'engine-{platform}-{arch}.tar.gz','w:gz') as archive:
    archive.add(bundle,arcname=bundle.name)
