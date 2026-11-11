#!/usr/bin/env python3
"""Golden lock: prove that a refactor leaves every rendered byte unchanged.

Since v0.11.1 the renderer embeds a committed sRGB profile (assets/profiles/),
so outputs are byte-reproducible and every byte is compared. Revisions older
than that built the profile at run time and LittleCMS stamped the current second
into it; to compare against one of them, pass --ignore-icc-dates, which zeroes
the ICC creation date (bytes 24-35 of an embedded profile) before hashing.

The renderer's exact output bytes depend on the installed Pillow, zlib and
LittleCMS builds, so a committed list of hashes would break across the CI
matrix. Instead this tool renders one fixed synthetic corpus with two versions
of the skill on the same machine and compares SHA-256 hashes of every output
file, plus the JSON notes and error messages.

    # Compare the working tree with a git revision (default: HEAD).
    python tools/golden.py compare --base 97c89fc

    # Record one skill folder into a manifest (used by compare).
    python tools/golden.py record skills/photo-framer manifest.json

Only synthetic images are used; no personal photos are read or written.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import struct
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / 'skills' / 'photo-framer'
STYLES = 'ABCDEFGH'
CODES = [f'{a}-{b}-{c}' for a in '123' for b in '123' for c in '123']


# ---------------------------------------------------------------- corpus ----

def _icc(color_space, tags):
    """Minimal ICC v2 display profile from (signature, payload) tags."""
    u32 = lambda n: struct.pack('>I', n)
    header = bytearray(128)
    header[8:12] = u32(0x02100000)
    header[12:24] = b'mntr' + color_space + b'XYZ '
    header[24:36] = struct.pack('>6H', 2026, 1, 1, 0, 0, 0)
    header[36:40] = b'acsp'
    header[68:80] = _xyz((0.9642, 1.0, 0.8249))[8:]
    offset = 128 + 4 + 12 * len(tags)
    directory, payload = bytearray(u32(len(tags))), bytearray()
    for signature, value in tags:
        directory += signature + u32(offset) + u32(len(value))
        padded = value + bytes((-len(value)) % 4)
        payload += padded
        offset += len(padded)
    header[:4] = u32(offset)
    return bytes(header + directory + payload)


def _xyz(values):
    return b'XYZ ' + bytes(4) + b''.join(struct.pack('>i', round(v * 65536)) for v in values)


def _desc(name):
    name = name.encode() + b'\0'
    return b'desc' + bytes(4) + struct.pack('>I', len(name)) + name + bytes(8 + 2 + 1 + 67)


def _curve(gamma):
    return b'curv' + bytes(4) + struct.pack('>I', 1) + struct.pack('>H', round(gamma * 256))


def gray_profile():
    return _icc(b'GRAY', [(b'desc', _desc('Golden synthetic gray')),
                          (b'wtpt', _xyz((0.9642, 1.0, 0.8249))),
                          (b'kTRC', _curve(2.2)),
                          (b'cprt', b'text' + bytes(4) + b'Synthetic\0')])


def wide_rgb_profile():
    """Wide-gamut RGB (Adobe-RGB-like D50 primaries) so sRGB decoration converts."""
    return _icc(b'RGB ', [(b'desc', _desc('Golden synthetic wide RGB')),
                          (b'wtpt', _xyz((0.9642, 1.0, 0.8249))),
                          (b'rXYZ', _xyz((0.6097, 0.3111, 0.0195))),
                          (b'gXYZ', _xyz((0.2053, 0.6257, 0.0609))),
                          (b'bXYZ', _xyz((0.1492, 0.0632, 0.7446))),
                          (b'rTRC', _curve(2.2)), (b'gTRC', _curve(2.2)),
                          (b'bTRC', _curve(2.2)),
                          (b'cprt', b'text' + bytes(4) + b'Synthetic\0')])


def xmp_packet(**overrides):
    fields = {'tiff:Make': 'OLYMPUS CORPORATION', 'tiff:Model': 'E-M10MarkIV',
              'exif:LensModel': 'OM 12-45mm F4.0', 'exif:ISOSpeedRatings': '800',
              'exif:FNumber': '4/1', 'exif:ExposureTime': '1/200',
              'exif:FocalLength': '12/1'}
    fields.update(overrides)
    attrs = ' '.join(f'{k}="{v}"' for k, v in fields.items())
    return ('<x:xmpmeta xmlns:x="adobe:ns:meta/">'
            '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
            '<rdf:Description rdf:about="" xmlns:tiff="http://ns.adobe.com/tiff/1.0/" '
            f'xmlns:exif="http://ns.adobe.com/exif/1.0/" {attrs}/>'
            '</rdf:RDF></x:xmpmeta>')


def pattern(size, seed):
    """Deterministic colorful content: gradients, blocks and a colored edge."""
    from PIL import Image
    w, h = size
    image = Image.new('RGB', size)
    image.putdata([((x * 255 // max(1, w - 1) + seed * 37) % 256,
                    (y * 255 // max(1, h - 1) + seed * 71) % 256,
                    ((x // 7 + y // 5) * 23 + seed * 13) % 256)
                   for y in range(h) for x in range(w)])
    edge = max(1, w // 6)
    image.paste(((seed * 90) % 256, 120, 60), (0, 0, edge, h))
    return image


def build_corpus(folder):
    """Write the synthetic inputs; returns {name: path}."""
    from PIL import Image
    from PIL.PngImagePlugin import PngInfo
    folder.mkdir(parents=True, exist_ok=True)
    paths = {}

    def png_xmp(image, name, packet):
        info = PngInfo()
        info.add_itxt('XML:com.adobe.xmp', packet)
        image.save(folder / name, pnginfo=info)
        paths[name] = folder / name

    png_xmp(pattern((600, 400), 1), 'landscape-xmp.png', xmp_packet())
    portrait = pattern((400, 600), 2)
    exif = Image.Exif()
    exif[271], exif[272] = 'Panasonic', 'DC-S1RM2'
    sub = exif.get_ifd(0x8769)
    sub[42036] = '28-105mm F2.8 DG DN | Art 024'
    sub[34855], sub[33437], sub[33434], sub[37386] = 250, (28, 10), (1, 125), (105, 1)
    portrait.save(folder / 'portrait-exif.png', exif=exif)
    paths['portrait-exif.png'] = folder / 'portrait-exif.png'
    png_xmp(pattern((500, 500), 3), 'square-sigma.png',
            xmp_packet(**{'tiff:Make': 'SIGMA', 'tiff:Model': 'fp L'}))
    pattern((40, 32), 4).save(folder / 'tiny.png')
    paths['tiny.png'] = folder / 'tiny.png'
    pattern((16, 16), 5).save(folder / 'min16.png')
    paths['min16.png'] = folder / 'min16.png'
    # Larger than 2048 px so --share downsizes; JPEG input path.
    pattern((2400, 1600), 6).save(folder / 'large.jpg', quality=93)
    paths['large.jpg'] = folder / 'large.jpg'
    # EXIF orientation 6 with an sRGB ICC profile.
    from PIL import ImageCms
    srgb = _undated(ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes())
    rotated = Image.Exif()
    rotated[274] = 6
    pattern((300, 200), 7).save(folder / 'rotated-srgb.png', icc_profile=srgb, exif=rotated)
    paths['rotated-srgb.png'] = folder / 'rotated-srgb.png'
    # Wide-gamut RGB profile: decorative sRGB colors must convert into it.
    pattern((360, 240), 8).save(folder / 'wide-rgb.png', icc_profile=wide_rgb_profile())
    paths['wide-rgb.png'] = folder / 'wide-rgb.png'
    # Profiled grayscale with alpha (converted to sRGB, flattened on white).
    gray = Image.new('LA', (120, 80))
    gray.putdata([((x * 2) % 256, (y * 3 + x) % 256) for y in range(80) for x in range(120)])
    gray.save(folder / 'gray-alpha.png', icc_profile=gray_profile())
    paths['gray-alpha.png'] = folder / 'gray-alpha.png'
    # RGBA with partial transparency, no profile.
    rgba = Image.new('RGBA', (90, 60))
    rgba.putdata([(x * 2 % 256, 80, y * 4 % 256, (x + y) * 3 % 256)
                  for y in range(60) for x in range(90)])
    rgba.save(folder / 'rgba.png')
    paths['rgba.png'] = folder / 'rgba.png'
    # Rejected input: 16-bit PNG header.
    import zlib
    def chunk(kind, data):
        return (struct.pack('>I', len(data)) + kind + data
                + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff))
    row = b'\0' + struct.pack('>HHH', 0x1234, 0x1234, 0x1234) * 32
    (folder / 'depth16.png').write_bytes(
        b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 32, 24, 16, 2, 0, 0, 0))
        + chunk(b'IDAT', zlib.compress(row * 24)) + chunk(b'IEND', b''))
    paths['depth16.png'] = folder / 'depth16.png'
    return paths


# ----------------------------------------------------------------- cases ----

def style_flags(style):
    if style == 'D':
        return ['--right-text', 'Berlin, Germany | October 2022']
    if style == 'F':
        return ['--left-text', 'Berlin, Germany', '--right-text', 'October 2022']
    return []


def cases(font):
    """(name, input names, flags). Covers every style x every choice code."""
    base = ['landscape-xmp.png', 'portrait-exif.png', 'square-sigma.png', 'tiny.png']
    profiled = ['rotated-srgb.png', 'wide-rgb.png', 'gray-alpha.png', 'rgba.png',
                'min16.png', 'depth16.png']
    out = []
    for style in STYLES:
        for code in CODES:
            out.append((f'{style}_{code}', base,
                        ['--style', style, '--choices', code, *style_flags(style)]))
        out.append((f'{style}_profiled', profiled, ['--style', style, *style_flags(style)]))
        out.append((f'{style}_share', ['large.jpg', 'wide-rgb.png', 'portrait-exif.png'],
                    ['--style', style, '--share', *style_flags(style)]))
    for code in ('1-2-3', '2-3-2', '3-1-1'):
        out.append((f'H_share_{code}', ['large.jpg', 'portrait-exif.png', 'tiny.png'],
                    ['--style', 'H', '--choices', code, '--share']))
    # Text variants.
    viet = 'Hồ Hoàn Kiếm | Tháng 10, 2022'
    for code in ('1-1-1', '2-2-2', '3-3-3'):
        out.append((f'D_viet_{code}', base[:3], ['--style', 'D', '--choices', code,
                                                 '--right-text', viet]))
    out.append(('D_font', base[:3], ['--style', 'D', '--right-text', viet, '--font', font]))
    for name, left, right in (('blank_both', '', ''), ('blank_left', '', 'Tháng 10, 2022'),
                              ('blank_right', 'Hà Nội', ''), ('viet', 'Trong Trương | Hà Nội', viet)):
        out.append((f'F_{name}', base, ['--style', 'F', f'--left-text={left}',
                                        f'--right-text={right}']))
    out.append(('F_font', base[:2], ['--style', 'F', '--left-text', 'Hà Nội',
                                     '--right-text', 'Tháng 10', '--font', font]))
    for code in ('1-1-1', '2-2-3', '3-3-2'):
        out.append((f'E_fixed_{code}', base + ['wide-rgb.png'],
                    ['--style', 'E', '--choices', code, '--frame-color', '#ad896c']))
    out.append(('E_named', base[:2], ['--style', 'E', '--frame-color', 'navy']))
    for style in 'ABCEGH':
        for code in ('1-1-1', '2-2-2', '3-3-3'):
            out.append((f'{style}_caption_{code}', base,
                        ['--style', style, '--choices', code,
                         '--caption', 'Hà Nội — mùa thu.', '--font', font]))
    out.append(('C_font_only', base[:3], ['--style', 'C', '--font', font]))
    # Existing H labels and blur must remain byte-identical after sharing their
    # typography with A/B/G. These flags are supported by v0.11.1 too.
    for ratio in ('4:5', '1:1', '3:4', '9:16', 'original'):
        out.append((f'H_label_{ratio.replace(":", "x")}', base[:3], ['--style', 'H', '--ratio', ratio,
                    '--title', 'Praha', '--subtitle', 'Prague · Czech Republic']))
    out.append(('H_blur_label', base[:3], ['--style', 'H', '--ratio', '9:16',
                '--background', 'blur', '--title', 'Praha', '--subtitle', 'Prague']))
    out.append(('H_square_blur', base[:3], ['--style', 'H', '--ratio', '1:1', '--background', 'blur']))
    # Previews.
    for name, flags in (('plain', []), ('right', ['--right-text', 'Berlin']),
                        ('film', ['--left-text', 'Berlin', '--right-text', 'October 2022']),
                        ('film_blank_right', ['--left-text', 'Berlin', '--right-text', '']),
                        ('frame_color', ['--frame-color', '#ad896c'])):
        for image in ('landscape-xmp.png', 'portrait-exif.png', 'wide-rgb.png'):
            out.append((f'preview_{name}_{image}', [image], ['--preview', *flags]))
    # Crop and errors (messages must stay identical too).
    out.append(('crop', ['landscape-xmp.png'], ['--style', 'A', '--crop', '10', '20', '590', '380']))
    out.append(('crop_bad', ['landscape-xmp.png'], ['--style', 'A', '--crop', '0', '0', '900', '10']))
    errors = [('D_missing', ['--style', 'D']), ('D_long', ['--style', 'D', '--right-text', 'W' * 200]),
              ('F_missing', ['--style', 'F', '--left-text', 'x']),
              ('F_caption', ['--style', 'F', '--left-text=', '--right-text=', '--caption', 'x', '--font', font]),
              ('A_right', ['--style', 'A', '--right-text', 'x']),
              ('B_left', ['--style', 'B', '--left-text', 'x']),
              ('H_color', ['--style', 'H', '--frame-color', 'red']),
              ('E_bad_color', ['--style', 'E', '--frame-color', 'nope']),
              ('caption_no_font', ['--style', 'A', '--caption', 'x']),
              ('caption_long', ['--style', 'A', '--caption', 'W' * 200, '--font', font]),
              ('preview_left_only', ['--preview', '--left-text', 'x']),
              ('bad_code', ['--style', 'A', '--choices', '4-1-1'])]
    for name, flags in errors:
        out.append((f'error_{name}', ['tiny.png', 'landscape-xmp.png'], flags))
    return out


# ---------------------------------------------------------------- record ----

def _undated(profile):
    """LittleCMS stamps the creation time into bytes 24-35 of profiles it builds."""
    return profile[:24] + bytes(12) + profile[36:] if len(profile) >= 128 else profile


def normalized(data, ignore_icc_dates=False):
    """File bytes as written; with ignore_icc_dates, only ICC creation dates are zeroed.

    Revisions before v0.11.1 built their sRGB profile at run time, so outputs
    embedding it differed by the second they were made. PNG iCCP payloads are
    decompressed (zlib output would change with the date); JPEG APP2 segments
    are patched.
    """
    if not ignore_icc_dates:
        return data
    import zlib
    if data[:8] == b'\x89PNG\r\n\x1a\n':
        out, pos = bytearray(data[:8]), 8
        while pos < len(data):
            length = struct.unpack('>I', data[pos:pos + 4])[0]
            kind = data[pos + 4:pos + 8]
            body = data[pos + 8:pos + 8 + length]
            if kind == b'iCCP':
                name, _, rest = body.partition(b'\0')
                body = name + b'\0' + rest[:1] + _undated(zlib.decompress(rest[1:]))
            out += struct.pack('>I', len(body)) + kind + body
            pos += 12 + length
        return bytes(out)
    if data[:2] == b'\xff\xd8':
        out = bytearray(data)
        marker = b'\xff\xe2'
        start = 0
        while (index := out.find(marker, start)) != -1:
            if out[index + 4:index + 16] == b'ICC_PROFILE\0' and out[index + 16] == 1:
                profile = index + 18
                out[profile + 24:profile + 36] = bytes(12)
            start = index + 2
        return bytes(out)
    return data


def load_renderer(skill_dir):
    script = Path(skill_dir) / 'scripts' / 'frame_photo.py'
    sys.path.insert(0, str(script.parent))
    spec = importlib.util.spec_from_file_location('frame_photo', script)
    module = importlib.util.module_from_spec(spec)
    sys.modules['frame_photo'] = module
    spec.loader.exec_module(module)
    return module


def record(skill_dir, manifest_path, extra_flags=(), ignore_icc_dates=False):
    skill_dir = Path(skill_dir).resolve()
    renderer = load_renderer(skill_dir)
    font = str(skill_dir / 'assets' / 'fonts' / 'Inter-Regular.ttf')
    manifest = {}
    with tempfile.TemporaryDirectory(prefix='golden-') as temp:
        # Windows temp roots may use an 8.3 user-directory alias. Output paths
        # are resolved by save_verified(), so normalize the root first too.
        temp = Path(temp).resolve()
        inputs = build_corpus(temp / 'in')
        for name, images, flags in cases(font):
            out_dir = temp / 'out' / name
            argv = [str(inputs[i]) for i in images] + ['--out-dir', str(out_dir), *flags, *extra_flags]
            stdout = io.StringIO()
            entry = {}
            try:
                with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(io.StringIO()):
                    entry['exit'] = renderer.main(argv)
            except SystemExit as exit_:
                entry['exit'] = f'SystemExit({exit_.code})'
            except Exception as error:  # noqa: BLE001 - uncaught errors are part of the contract
                entry['exit'] = f'{type(error).__name__}: {error}'
            text = stdout.getvalue()
            for path, label in ((out_dir, '<out>'), (temp / 'in', '<in>'), (skill_dir, '<skill>')):
                text = text.replace(json.dumps(str(path))[1:-1], label)
            entry['stdout'] = text
            entry['files'] = {str(p.relative_to(out_dir)): hashlib.sha256(normalized(p.read_bytes(), ignore_icc_dates)).hexdigest()
                              for p in sorted(out_dir.rglob('*')) if p.is_file()} if out_dir.exists() else {}
            manifest[name] = entry
    import PIL
    payload = {'pillow': PIL.__version__, 'python': sys.version.split()[0], 'cases': manifest}
    Path(manifest_path).write_text(json.dumps(payload, indent=1, ensure_ascii=False), encoding='utf-8')
    files = sum(len(e['files']) for e in manifest.values())
    print(f'Recorded {len(manifest)} cases, {files} output files -> {manifest_path}')


def _record_subprocess(skill_dir, manifest_path, extra_flags=(), ignore_icc_dates=False):
    command = [sys.executable, __file__, 'record', str(skill_dir), str(manifest_path)]
    if extra_flags:
        command.append('--extra-flags=' + ' '.join(extra_flags))
    if ignore_icc_dates:
        command.append('--ignore-icc-dates')
    subprocess.run(command, check=True)
    return json.loads(Path(manifest_path).read_text(encoding='utf-8'))


def compare(base, keep=None, new_flags=(), ignore_icc_dates=False):
    with tempfile.TemporaryDirectory(prefix='golden-base-') as temp:
        temp = Path(temp).resolve()
        archive = subprocess.run(['git', '-C', str(ROOT), 'archive', base, 'skills/photo-framer'],
                                 check=True, capture_output=True).stdout
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            safe = {'filter': 'data'} if hasattr(tarfile, 'data_filter') else {}
            tar.extractall(temp / 'base', **safe)
        old = _record_subprocess(temp / 'base' / 'skills' / 'photo-framer', temp / 'base.json',
                                 ignore_icc_dates=ignore_icc_dates)
        new = _record_subprocess(SKILL, temp / 'new.json', new_flags, ignore_icc_dates)
        if keep:
            Path(keep).mkdir(parents=True, exist_ok=True)
            for name in ('base.json', 'new.json'):
                (Path(keep) / name).write_bytes((temp / name).read_bytes())
    differences = []
    for name in sorted(set(old['cases']) | set(new['cases'])):
        a, b = old['cases'].get(name), new['cases'].get(name)
        if a != b:
            differences.append(name)
            if a and b:
                for key in ('exit', 'stdout'):
                    if a[key] != b[key]:
                        print(f'  {name}: {key} differs')
                for file in sorted(set(a['files']) | set(b['files'])):
                    if a['files'].get(file) != b['files'].get(file):
                        print(f'  {name}: {file} differs')
            else:
                print(f'  {name}: missing on one side')
    files = sum(len(e['files']) for e in new['cases'].values())
    if differences:
        print(f'FAIL: {len(differences)} of {len(new["cases"])} cases differ from {base}.')
        return 1
    print(f'OK: {len(new["cases"])} cases, {files} output files byte-identical to {base} '
          f'(Pillow {new["pillow"]}, Python {new["python"]}).')
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)
    rec = sub.add_parser('record', help='render the corpus with one skill folder')
    rec.add_argument('skill_dir', type=Path)
    rec.add_argument('manifest', type=Path)
    rec.add_argument('--extra-flags', default='', help='flags appended to every case')
    rec.add_argument('--ignore-icc-dates', action='store_true',
                     help='zero ICC creation dates before hashing (revisions before v0.11.1)')
    cmp_ = sub.add_parser('compare', help='compare the working tree against a git revision')
    cmp_.add_argument('--base', default='HEAD', help='git revision of the reference skill (default HEAD)')
    cmp_.add_argument('--keep', type=Path, help='directory to keep both manifests for inspection')
    cmp_.add_argument('--new-flags', default='',
                      help='flags appended to every case on the working-tree side only, e.g. '
                           '"--metadata strip" to compare a new opt-out with old behaviour')
    cmp_.add_argument('--ignore-icc-dates', action='store_true',
                      help='zero ICC creation dates before hashing; needed when --base is older than '
                           'v0.11.1, which built its sRGB profile at run time')
    args = parser.parse_args(argv)
    if args.command == 'record':
        record(args.skill_dir, args.manifest, args.extra_flags.split(), args.ignore_icc_dates)
        return 0
    return compare(args.base, args.keep, args.new_flags.split(), args.ignore_icc_dates)


if __name__ == '__main__':
    raise SystemExit(main())
