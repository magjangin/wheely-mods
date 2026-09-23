import os
import shutil
import zlib
import struct

GAME_DIR = r"H:\steam\steamapps\common\Wheely"
RES_DIR = os.path.join(GAME_DIR, "res")

class ABCParser:
    def __init__(self, data):
        self.data = data
        self.pos = 4
    def read_u30(self):
        res, shift = 0, 0
        while True:
            b = self.data[self.pos]
            self.pos += 1
            res |= (b & 0x7f) << shift
            if not (b & 0x80): break
            shift += 7
        return res
    def read_u8(self):
        b = self.data[self.pos]; self.pos += 1; return b
    def read_u16(self):
        r = struct.unpack('<H', self.data[self.pos:self.pos+2])[0]; self.pos += 2; return r

def parse_swf(swf_bytes):
    sig = swf_bytes[:3]
    ver = swf_bytes[3:4]
    decl_len = struct.unpack('<I', swf_bytes[4:8])[0]
    if sig == b'CWS':
        body = zlib.decompress(swf_bytes[8:])
    elif sig == b'FWS':
        body = swf_bytes[8:]
    else:
        raise ValueError(f"Unknown SWF signature: {sig}")

    nbits = body[0] >> 3
    pos = ((5 + nbits * 4 + 7) // 8) + 4
    abc_tag_offset = None
    abc = None
    while pos < len(body):
        hdr_t = struct.unpack('<H', body[pos:pos+2])[0]; pos += 2
        t = hdr_t >> 6; l = hdr_t & 0x3f
        if l == 0x3f: l = struct.unpack('<I', body[pos:pos+4])[0]; pos += 4
        if t in (82, 72): # DoABC
            apos = pos + 4
            while body[apos] != 0: apos += 1
            apos += 1
            abc = body[apos:pos+l]
            abc_tag_offset = apos
            break
        pos += l

    p = ABCParser(abc)
    # Skip cpool
    n_int = p.read_u30()
    for _ in range(1, n_int): p.read_u30()
    n_uint = p.read_u30()
    for _ in range(1, n_uint): p.read_u30()
    n_double = p.read_u30()
    if n_double > 0: p.pos += (n_double - 1) * 8
    n_str = p.read_u30()
    for _ in range(1, n_str):
        slen = p.read_u30(); p.pos += slen
    n_ns = p.read_u30()
    for _ in range(1, n_ns):
        p.read_u8(); p.read_u30()
    n_ns_set = p.read_u30()
    for _ in range(1, n_ns_set):
        count = p.read_u30()
        for _ in range(count): p.read_u30()
    n_multi = p.read_u30()
    for _ in range(1, n_multi):
        kind = p.read_u8()
        if kind in (0x07, 0x0D): p.read_u30(); p.read_u30()
        elif kind in (0x0F, 0x10): p.read_u30()
        elif kind in (0x11, 0x12): pass
        elif kind in (0x09, 0x0E): p.read_u30(); p.read_u30()
        elif kind in (0x1B, 0x1C): p.read_u30()
        elif kind == 0x1D:
            p.read_u30(); count = p.read_u30()
            for _ in range(count): p.read_u30()

    n_methods = p.read_u30()
    for _ in range(n_methods):
        pc = p.read_u30(); p.read_u30()
        for _ in range(pc): p.read_u30()
        p.read_u30(); flg = p.read_u8()
        if flg & 0x08:
            oc = p.read_u30()
            for _ in range(oc): p.read_u30(); p.read_u8()
        if flg & 0x80:
            for _ in range(pc): p.read_u30()

    n_meta = p.read_u30()
    for _ in range(n_meta):
        p.read_u30(); ic = p.read_u30()
        for _ in range(ic): p.read_u30(); p.read_u30()

    def read_traits():
        tc = p.read_u30()
        for _ in range(tc):
            p.read_u30(); tk = p.read_u8(); kt = tk & 0x0F
            if kt in (0, 6):
                p.read_u30(); p.read_u30(); vi = p.read_u30()
                if vi != 0: p.read_u8()
            elif kt in (1, 2, 3): p.read_u30(); p.read_u30()
            elif kt in (4, 5): p.read_u30(); p.read_u30()
            if (tk >> 4) & 0x04:
                mc = p.read_u30()
                for _ in range(mc): p.read_u30()

    n_inst = p.read_u30()
    for _ in range(n_inst):
        p.read_u30(); p.read_u30(); flg = p.read_u8()
        if flg & 0x08: p.read_u30()
        ic = p.read_u30()
        for _ in range(ic): p.read_u30()
        p.read_u30(); read_traits()
    for _ in range(n_inst):
        p.read_u30(); read_traits()
    n_scripts = p.read_u30()
    for _ in range(n_scripts):
        p.read_u30(); read_traits()

    n_bodies = p.read_u30()
    bodies = {}
    for _ in range(n_bodies):
        mid = p.read_u30(); p.read_u30(); p.read_u30(); p.read_u30(); p.read_u30()
        clen = p.read_u30()
        cstart = p.pos
        p.pos += clen
        exc = p.read_u30()
        for _ in range(exc): p.read_u30(); p.read_u30(); p.read_u30(); p.read_u30(); p.read_u30()
        read_traits()
        bodies[mid] = {'body_offset': abc_tag_offset + cstart, 'len': clen}

    return bytearray(body), bodies, sig, ver, decl_len

def patch_file(file_path, patches):
    bak_path = file_path + ".bak"
    if not os.path.exists(bak_path):
        print(f"Creating backup: {bak_path}")
        shutil.copy2(file_path, bak_path)
    else:
        print(f"Backup already exists: {bak_path}")

    # Always read from backup if available, to allow re-patching cleanly
    with open(bak_path, "rb") as f:
        swf_bytes = f.read()

    body, bodies, sig, ver, decl_len = parse_swf(swf_bytes)

    for mid, replacement_generator in patches.items():
        if mid not in bodies:
            raise KeyError(f"Method ID {mid} not found in {file_path}")
        info = bodies[mid]
        offset = info['body_offset']
        orig_len = info['len']
        new_code = replacement_generator(orig_len)
        if len(new_code) != orig_len:
            raise ValueError(f"Method {mid} code length mismatch: orig={orig_len}, new={len(new_code)}")
        body[offset:offset+orig_len] = new_code
        print(f"  Patched Method {mid} at offset {offset} (len {orig_len})")

    # Compress and save
    if sig == b'CWS':
        compressed_body = zlib.compress(bytes(body), level=9)
        new_swf = b'CWS' + ver + struct.pack('<I', len(body) + 8) + compressed_body
    else:
        new_swf = b'FWS' + ver + struct.pack('<I', len(body) + 8) + bytes(body)

    with open(file_path, "wb") as f:
        f.write(new_swf)
    print(f"Successfully saved patched file: {file_path} (new size: {len(new_swf)} bytes)")

def make_return_const_int(val):
    def gen(orig_len):
        # 0xd0 = getlocal_0, 0x30 = pushscope, 0x24 = pushbyte <val>, 0x48 = returnvalue, 0x02 = nop
        code = bytes([0xd0, 0x30, 0x24, val & 0xff, 0x48])
        assert len(code) <= orig_len
        return code + b'\x02' * (orig_len - len(code))
    return gen

def make_return_true():
    def gen(orig_len):
        # 0xd0 = getlocal_0, 0x30 = pushscope, 0x26 = pushtrue, 0x48 = returnvalue, 0x02 = nop
        code = bytes([0xd0, 0x30, 0x26, 0x48])
        assert len(code) <= orig_len
        return code + b'\x02' * (orig_len - len(code))
    return gen

def make_return_void():
    def gen(orig_len):
        # 0xd0 = getlocal_0, 0x30 = pushscope, 0x47 = returnvoid, 0x02 = nop
        code = bytes([0xd0, 0x30, 0x47])
        assert len(code) <= orig_len
        return code + b'\x02' * (orig_len - len(code))
    return gen

def make_patch_method_0_windowed():
    def gen(orig_len):
        # orig: d0 30 5e c0 06 26 96 68 c0 06 5e c1 06 26 68 c1 06 47
        # patch 26 (pushtrue) to 27 (pushfalse) for START_FULL_SCREEN
        code = bytes.fromhex("d0305ec006269668c0065ec1062768c10647")
        assert len(code) == orig_len
        return code
    return gen

def make_patch_method_2_windowed():
    def gen(orig_len):
        orig = bytes.fromhex("d03060990a2400619a0a60c106120c000060990a609b0a669c0a619d0a5d8703600266d307d0663e4f870302d0600266d407d0663f4f860302d05d03d04a0301683d47")
        assert len(orig) == orig_len
        # Replace the 11-byte fullscreen setter (60990a609b0a669c0a619d0a) with nops (0x02)
        target = bytes.fromhex("60990a609b0a669c0a619d0a")
        assert target in orig
        return orig.replace(target, b'\x02' * len(target))
    return gen

def patch_application_xml():
    xml_path = os.path.join(GAME_DIR, "META-INF", "AIR", "application.xml")
    bak_path = xml_path + ".bak"
    if not os.path.exists(bak_path):
        print(f"Creating backup: {bak_path}")
        shutil.copy2(xml_path, bak_path)
    
    with open(xml_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Configure 1280x720 windowed mode fixed
    import re
    window_pattern = r"<initialWindow>[\s\S]*?</initialWindow>"
    new_window = (
        "  <initialWindow>\n"
        "    <title>Wheely</title>\n"
        "    <content>WheelyAll.bin</content>\n"
        "    <systemChrome>standard</systemChrome>\n"
        "    <transparent>false</transparent>\n"
        "    <visible>true</visible>\n"
        "    <minimizable>true</minimizable>\n"
        "    <maximizable>false</maximizable>\n"
        "    <resizable>false</resizable>\n"
        "    <width>1280</width>\n"
        "    <height>720</height>\n"
        "    <minSize>1280 720</minSize>\n"
        "    <maxSize>1280 720</maxSize>\n"
        "    <requestedDisplayResolution>high</requestedDisplayResolution>\n"
        "    <renderMode>direct</renderMode>\n"
        "  </initialWindow>"
    )
    patched_content = re.sub(window_pattern, new_window, content)
    with open(xml_path, "w", encoding="utf-8") as f:
        f.write(patched_content)
    print(f"  Configured 1280x720 windowed mode in {xml_path}")

def run_all_patches():
    print("=== Wheely All-Stages Unlock & 1280x720 Windowed Patcher ===")

    # 1. Main Game Launcher & Chapter Selector + Windowed Mode
    wheely_all_bin = os.path.join(GAME_DIR, "WheelyAll.bin")
    print(f"\n[1/10] Patching {wheely_all_bin}...")
    patch_file(wheely_all_bin, {
        0: make_patch_method_0_windowed(),  # START_FULL_SCREEN = false
        2: make_patch_method_2_windowed(),  # Nop out fullscreen setting in init()
        417: make_return_void(),            # setFullScreen() = returnvoid (런타임 전체화면 전환 무력화)
        692: make_return_const_int(0),      # minStarsToOpen = 0 (모든 챕터 필요 별 0개)
        699: make_return_true(),            # isOpened = true (모든 챕터 항상 열림)
        698: make_return_const_int(99),     # levelOpened = 99 (모든 레벨 열림)
    })

    # 2. Application descriptor for 1280x720 windowed mode
    print("\n[2/10] Patching application.xml...")
    patch_application_xml()

    # 2. Episodes 1 ~ 3: isLevelCompleted returns true
    ep1_file = os.path.join(RES_DIR, "Wheely_1.res")
    print(f"\n[2/9] Patching {ep1_file}...")
    patch_file(ep1_file, {
        260: make_return_true(), # isLevelCompleted = true
    })

    ep2_file = os.path.join(RES_DIR, "Wheely_2.res")
    print(f"\n[3/9] Patching {ep2_file}...")
    patch_file(ep2_file, {
        259: make_return_true(), # isLevelCompleted = true
    })

    ep3_file = os.path.join(RES_DIR, "Wheely_3.res")
    print(f"\n[4/9] Patching {ep3_file}...")
    patch_file(ep3_file, {
        239: make_return_true(), # isLevelCompleted = true
    })

    # 3. Episodes 4 ~ 8: GetLevelOpened returns 99
    ep4_file = os.path.join(RES_DIR, "Wheely_4.res")
    print(f"\n[5/9] Patching {ep4_file}...")
    patch_file(ep4_file, {
        3446: make_return_const_int(99), # GetLevelOpened = 99
    })

    ep5_file = os.path.join(RES_DIR, "Wheely_5.res")
    print(f"\n[6/9] Patching {ep5_file}...")
    patch_file(ep5_file, {
        3056: make_return_const_int(99), # GetLevelOpened = 99
    })

    ep6_file = os.path.join(RES_DIR, "Wheely_6.res")
    print(f"\n[7/9] Patching {ep6_file}...")
    patch_file(ep6_file, {
        3685: make_return_const_int(99), # GetLevelOpened = 99
    })

    ep7_file = os.path.join(RES_DIR, "Wheely_7.res")
    print(f"\n[8/9] Patching {ep7_file}...")
    patch_file(ep7_file, {
        3902: make_return_const_int(99), # GetLevelOpened = 99
    })

    ep8_file = os.path.join(RES_DIR, "Wheely_8.res")
    print(f"\n[9/9] Patching {ep8_file}...")
    patch_file(ep8_file, {
        3069: make_return_const_int(99), # GetLevelOpened = 99
    })

    print("\n[ALL DONE] All 8 chapters and all stages are successfully unlocked!")

if __name__ == "__main__":
    run_all_patches()
