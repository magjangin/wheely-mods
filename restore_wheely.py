import os
import shutil

GAME_DIR = r"H:\steam\steamapps\common\Wheely"
RES_DIR = os.path.join(GAME_DIR, "res")

def restore():
    print("=== Wheely Backup Restorer ===")
    files = [
        os.path.join(GAME_DIR, "WheelyAll.bin"),
        os.path.join(GAME_DIR, "META-INF", "AIR", "application.xml"),
    ]
    for i in range(1, 9):
        files.append(os.path.join(RES_DIR, f"Wheely_{i}.res"))

    restored_count = 0
    for target in files:
        bak = target + ".bak"
        if os.path.exists(bak):
            shutil.copy2(bak, target)
            print(f"Restored: {target} from {bak}")
            restored_count += 1
        else:
            print(f"Warning: Backup not found for {target}")

    print(f"\n[DONE] Restored {restored_count}/{len(files)} files to original state.")

if __name__ == "__main__":
    restore()
