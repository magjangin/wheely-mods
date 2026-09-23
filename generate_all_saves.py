import os
import struct

SOL_DIR = os.path.expandvars(r"%APPDATA%\com.manapotionstudios.WheelySteam\Local Store\#SharedObjects")

# Level count per chapter from GameDataVO::getMaxLevel
CHAPTER_LEVELS = {
    1: 14,
    2: 16,
    3: 12,
    4: 16,
    5: 13,
    6: 14,
    7: 15,
    8: 12,
}

def make_sol(name, level_count, has_quests=True):
    def amf3_str(s):
        b = s.encode('utf-8')
        return bytes([(len(b) << 1) | 1]) + b

    # Chapters 1-3 do not have hidden quest items; setting them to False gives 1 star per level.
    # Chapters 4-8 have questWheel and questWheely items; setting them to True gives 3 stars per level.
    quest_byte = b'\x03' if has_quests else b'\x02'

    payload = bytearray()
    # m_questWheel: Vector.<Object> of level_count booleans
    payload += amf3_str('m_questWheel') + b'\x10' + bytes([(level_count << 1) | 1]) + b'\x01\x01' + (quest_byte * level_count) + b'\x00'
    # visits: int 1
    payload += amf3_str('visits') + b'\x04\x01\x00'
    # m_levelOpened: int 99
    payload += amf3_str('m_levelOpened') + b'\x04\x63\x00'
    # m_questWheely: Vector.<Object> of level_count booleans
    payload += amf3_str('m_questWheely') + b'\x10' + bytes([(level_count << 1) | 1]) + b'\x01\x01' + (quest_byte * level_count) + b'\x00'
    # completeLastLevel: True
    payload += amf3_str('completeLastLevel') + b'\x03\x00'

    name_bytes = name.encode('utf-8')
    header_rest = b'TCSO\x00\x04\x00\x00\x00\x00' + struct.pack('>H', len(name_bytes)) + name_bytes + b'\x00\x00\x00\x03'
    full_body = header_rest + payload
    sol_data = b'\x00\xbf' + struct.pack('>I', len(full_body)) + full_body
    return sol_data

def generate_all():
    os.makedirs(SOL_DIR, exist_ok=True)
    print(f"Target SOL directory: {SOL_DIR}")

    total_stars = 0
    max_possible_stars = 0
    for chapter, levels in CHAPTER_LEVELS.items():
        has_quests = (chapter >= 4)
        name = f"wheely_{chapter}_local"
        sol_data = make_sol(name, levels, has_quests=has_quests)
        file_path = os.path.join(SOL_DIR, f"{name}.sol")
        with open(file_path, "wb") as f:
            f.write(sol_data)
        
        chapter_stars = levels * 3 if has_quests else levels
        chapter_max = levels * 3 if has_quests else levels
        total_stars += chapter_stars
        max_possible_stars += chapter_max
        print(f"Generated {name}.sol: {levels} levels, {chapter_stars}/{chapter_max} stars (size: {len(sol_data)} bytes)")

    print(f"\nAll 8 chapters generated successfully! Total stars: {total_stars} / {max_possible_stars}")

if __name__ == "__main__":
    generate_all()
