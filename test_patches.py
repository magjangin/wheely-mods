import os
import zlib
import struct

GAME_DIR = r"H:\steam\steamapps\common\Wheely"
RES_DIR = os.path.join(GAME_DIR, "res")

def test_file(file_path, expected_patterns):
    print(f"Testing {os.path.basename(file_path)}...")
    with open(file_path, "rb") as f:
        data = f.read()

    assert data[:3] == b'CWS', f"Invalid signature: {data[:3]}"
    decomp = zlib.decompress(data[8:])
    assert len(decomp) + 8 == struct.unpack('<I', data[4:8])[0]

    for offset, expected_prefix in expected_patterns:
        actual = decomp[offset:offset+len(expected_prefix)]
        assert actual == expected_prefix, f"Mismatch at offset {offset}: expected {expected_prefix.hex()}, got {actual.hex()}"
        print(f"  Verified offset {offset}: {actual.hex()} OK")

def run_tests():
    # 1. WheelyAll.bin
    test_file(os.path.join(GAME_DIR, "WheelyAll.bin"), [
        (24789124, bytes.fromhex("d0305ec006269668c0065ec1062768c10647")), # Method 0: START_FULL_SCREEN = false (27)
        (24789211, bytes([0x02] * 11)),                                     # Method 2: fullscreen setter nopped out
        (24807870, bytes([0xd0, 0x30, 0x47])),                              # Method 417: setFullScreen = returnvoid
        (24830819, bytes([0xd0, 0x30, 0x24, 0x00, 0x48])),                 # minStarsToOpen = 0
        (24831139, bytes([0xd0, 0x30, 0x26, 0x48])),                       # isOpened = true
        (24831120, bytes([0xd0, 0x30, 0x24, 0x63, 0x48])),                 # levelOpened = 99
    ])

    # 1.1 application.xml Windowed settings
    print("Testing application.xml...")
    with open(os.path.join(GAME_DIR, "META-INF", "AIR", "application.xml"), "r", encoding="utf-8") as f:
        xml_text = f.read()
    assert "<width>1280</width>" in xml_text, "Missing width 1280 in application.xml"
    assert "<height>720</height>" in xml_text, "Missing height 720 in application.xml"
    assert "<minSize>1280 720</minSize>" in xml_text, "Missing minSize 1280 720 in application.xml"
    assert "<maxSize>1280 720</maxSize>" in xml_text, "Missing maxSize 1280 720 in application.xml"
    assert "<resizable>false</resizable>" in xml_text, "Missing resizable false in application.xml"
    print("  Verified application.xml 1280x720 windowed mode OK")

    # 2. Wheely_1 to 3
    test_file(os.path.join(RES_DIR, "Wheely_1.res"), [
        (5544330, bytes([0xd0, 0x30, 0x26, 0x48])), # isLevelCompleted = true
    ])
    test_file(os.path.join(RES_DIR, "Wheely_2.res"), [
        (8601009, bytes([0xd0, 0x30, 0x26, 0x48])), # isLevelCompleted = true
    ])
    test_file(os.path.join(RES_DIR, "Wheely_3.res"), [
        (11173890, bytes([0xd0, 0x30, 0x26, 0x48])), # isLevelCompleted = true
    ])

    # 3. Wheely_4 to 8
    test_file(os.path.join(RES_DIR, "Wheely_4.res"), [
        (13982564, bytes([0xd0, 0x30, 0x24, 0x63, 0x48])), # GetLevelOpened = 99
    ])
    test_file(os.path.join(RES_DIR, "Wheely_5.res"), [
        (15756496, bytes([0xd0, 0x30, 0x24, 0x63, 0x48])), # GetLevelOpened = 99
    ])
    test_file(os.path.join(RES_DIR, "Wheely_6.res"), [
        (18725258, bytes([0xd0, 0x30, 0x24, 0x63, 0x48])), # GetLevelOpened = 99
    ])
    test_file(os.path.join(RES_DIR, "Wheely_7.res"), [
        (13880692, bytes([0xd0, 0x30, 0x24, 0x63, 0x48])), # GetLevelOpened = 99
    ])
    test_file(os.path.join(RES_DIR, "Wheely_8.res"), [
        (9771021, bytes([0xd0, 0x30, 0x24, 0x63, 0x48])), # GetLevelOpened = 99
    ])

    print("\n[SUCCESS] All verification tests passed successfully!")

if __name__ == "__main__":
    run_tests()
