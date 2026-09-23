# 🚗 Wheely QoL Mods & Save Toolkit

[![Game](https://img.shields.io/badge/Game-Wheely%20(Steam)-red.svg)](#)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](#)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)](#)
[![Adobe AIR](https://img.shields.io/badge/Runtime-Adobe%20AIR%20%2F%20AVM2-orange.svg)](#)

Steam 버전 **Wheely (1~8편 통합 에디션)**의 편의성을 개선하고 모든 콘텐츠를 즉시 즐길 수 있도록 돕는 올인원 모딩 툴킷입니다.

외부 디컴파일러 설치 없이 순수 파이썬(ActionScript 3 바이트코드 및 Local Shared Object 파서)으로 구동되며, **전 챕터/스테이지 즉시 해금**, **1280×720 창모드 강제 전환**, **올 3스타(All 3-Star) 완벽 세이브 주입**을 원클릭으로 처리합니다.

---

## 📑 목차 (Table of Contents)

- [주요 기능 (Features)](#-주요-기능-features)
- [프로젝트 구성 (File Structure)](#-프로젝트-구성-file-structure)
- [기술적 원리 (Technical Overview)](#-기술적-원리-technical-overview)
- [설치 및 사용법 (Quick Start)](#-설치-및-사용법-quick-start)
  - [사전 준비](#사전-준비)
  - [1. 바이너리 패치 (올해금 + 창모드)](#1-바이너리-패치-올해금--창모드)
  - [2. 올 3스타 세이브 파일 주입](#2-올-3스타-세이브-파일-주입)
  - [3. 패치 무결성 검증 (선택 사항)](#3-패치-무결성-검증-선택-사항)
  - [4. 원본 복원 (언패치)](#4-원본-복원-언패치)
- [주의 사항 (Notes)](#-주의-사항-notes)

---

## ✨ 주요 기능 (Features)

### 1. 🔓 전 챕터 및 전 스테이지 즉시 해금 (All Stages & Chapters Unlock)
- **런처 조작 (`WheelyAll.bin`)**: 챕터 오픈에 필요한 별 개수 요구 조건을 0개(`minStarsToOpen = 0`), 챕터 오픈 상태를 항상 참(`isOpened = true`), 오픈 레벨을 99(`levelOpened = 99`)로 강제합니다.
- **에피소드 1~3 (`Wheely_1~3.res`)**: 모든 레벨을 클리어 완료 상태(`isLevelCompleted = true`)로 패치합니다.
- **에피소드 4~8 (`Wheely_4~8.res`)**: 오픈 레벨 조회 함수(`GetLevelOpened`)가 항상 99를 반환하여 원하는 스테이지를 자유롭게 진입할 수 있습니다.

### 2. 🖥️ 1280×720 고정 창모드 지원 (Fixed Windowed Mode)
- 기본 강제 전체화면 옵션(`START_FULL_SCREEN`)을 `false`로 치환합니다.
- 런타임 전체화면 전환 루틴(`setFullScreen`)을 `returnvoid` 처리하고, 초기화 내 세터 코드를 `NOP(0x02)` 처리합니다.
- Adobe AIR 매니페스트(`application.xml`)를 자동 수정하여 1280×720 크기의 깔끔한 고정 창모드로 실행되도록 보장합니다.

### 3. ⭐ 전 챕터 올 3스타 세이브 생성기 (All 3-Star Save Generator)
- Flash Local Shared Object(`.sol`) 및 AMF3 바이너리를 직접 생성하여 게임 내 저장 경로(`%APPDATA%`)에 주입합니다.
- 1~8편의 모든 히든 퀘스트 아이템(타이어, 미니 휠리 등) 획득 플래그를 활성화하여 전 레벨 3스타를 달성시킵니다.

### 4. 🛡️ 자동 백업 & 원클릭 복원
- 패치 적용 전 원본 파일의 `.bak` 백업을 자동으로 생성합니다.
- 언제든 `restore_wheely.py`를 실행하여 순정(Vanilla) 상태로 되돌릴 수 있습니다.

---

## 📂 프로젝트 구성 (File Structure)

```text
wheely-mods/
├── patch_wheely.py       # 바이너리 바이트코드 패치 및 창모드 설정 스크립트
├── generate_all_saves.py # 올 3스타 .sol 세이브 자동 생성/주입 스크립트
├── restore_wheely.py     # .bak 백업 기반 원본 파일 복구 스크립트
├── test_patches.py       # 패치 적용 여부 및 오프셋 무결성 검증 테스트
├── .gitignore            # Git 제외 목록 (캐시, 백업 파일 등)
└── README.md             # 프로젝트 안내 문서
```

---

## 🔬 기술적 원리 (Technical Overview)

| 파일 | 메서드 ID / 대상 | 주입 바이트코드 (AVM2) | 동작 설명 |
| :--- | :--- | :--- | :--- |
| `WheelyAll.bin` | 0 | `... 27 ...` | `START_FULL_SCREEN`을 `pushfalse`로 수정 |
| `WheelyAll.bin` | 2 | `0x02` * 11 | Fullscreen Setter 바이트를 NOP 패딩 |
| `WheelyAll.bin` | 417 | `d0 30 47` + NOP | `setFullScreen()` 즉시 리턴 (`returnvoid`) |
| `WheelyAll.bin` | 692 | `d0 30 24 00 48` + NOP | `minStarsToOpen = 0` (별 요구량 0개) |
| `WheelyAll.bin` | 699 | `d0 30 26 48` + NOP | `isOpened = true` (챕터 항상 오픈) |
| `WheelyAll.bin` | 698 | `d0 30 24 63 48` + NOP | `levelOpened = 99` (모든 레벨 오픈) |
| `Wheely_1~3.res` | 가변 | `d0 30 26 48` + NOP | `isLevelCompleted = true` |
| `Wheely_4~8.res` | 가변 | `d0 30 24 63 48` + NOP | `GetLevelOpened = 99` |

- **SWF/CWS 파싱**: SWF의 zlib 헤더(`CWS`)를 풀고 `DoABC` 태그 내 ActionScript 바이트코드 풀을 파싱하여 타겟 메서드의 바디 오프셋을 동적으로 계산합니다.
- **바이트코드 인라인 치환**: AVM2 명령어를 기존 바디 길이와 정확히 일치하도록 치환하며, 남는 공간은 `0x02 (NOP)`로 안전하게 패딩합니다.
- **AMF3 직렬화**: Flash `.sol` 파일의 `TCSO` 헤더와 AMF3 벡터 불리언 포맷을 바이너리로 직접 조립하여 세이브를 생성합니다.

---

## 🚀 설치 및 사용법 (Quick Start)

### 사전 준비
- **Python 3.8 이상** 설치
- 기본 설정 경로: `H:\steam\steamapps\common\Wheely`  
  *(게임이 다른 드라이브/폴더에 설치되어 있다면, 각 `.py` 파일 상단의 `GAME_DIR` 경로를 본인의 설치 경로에 맞게 변경해 주세요.)*

### 1. 바이너리 패치 (올해금 + 창모드)
게임이 종료된 상태에서 아래 명령어를 실행합니다.
```bash
python patch_wheely.py
```
- 모든 대상 파일의 백업(`.bak`)이 자동 생성된 뒤 패치가 완료됩니다.

### 2. 올 3스타 세이브 파일 주입
전 챕터 모든 스테이지를 3스타로 등록하고 싶다면 실행합니다.
```bash
python generate_all_saves.py
```
- `%APPDATA%\com.manapotionstudios.WheelySteam\Local Store\#SharedObjects` 경로에 챕터 1~8편의 세이브가 즉시 생성됩니다.

### 3. 패치 무결성 검증 (선택 사항)
패치가 규격대로 안전하게 변경되었는지 검증합니다.
```bash
python test_patches.py
```

### 4. 원본 복원 (언패치)
게임을 설치 초기 순정 상태로 되돌리고 싶다면 실행합니다.
```bash
python restore_wheely.py
```

---

## ⚠️ 주의 사항 (Notes)
- 패치 스크립트 실행 전 게임을 반드시 종료해 주세요.
- 최초 실행 시 각 파일의 백업본(`.bak`)이 생성되므로 언제든 원상 복구가 가능합니다.
- Steam 게임 무결성 검사를 수행할 경우 모든 패치가 순정 파일로 덮어씌워질 수 있습니다.
