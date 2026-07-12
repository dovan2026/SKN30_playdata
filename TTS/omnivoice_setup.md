# OmniVoice TTS, 검증된 셋업

[k2-fsa/OmniVoice](https://github.com/k2-fsa/OmniVoice) 기반. 


---

## Step 0. 환경 점검

| 항목 | 권장 | 확인 명령 |
|---|---|---|
| Python | 3.10 | `python --version` |
| GPU (NVIDIA) | 12GB VRAM 권장 (없으면 CPU, 느림) | `nvidia-smi` |
| CUDA | 12.8 | `nvidia-smi` 우상단 |
| 디스크 | 5GB 여유 (모델 캐시) | - |
| git | 필수 | `git --version` |
| uv | 필수 | `uv --version` (없으면 <https://docs.astral.sh/uv/>) |

## Step 1. 소스 clone

```powershell
git clone https://github.com/k2-fsa/OmniVoice.git
```

## Step 2. **OmniVoice 전용 가상환경** (중요)

> ⚠️ 다른 단원(YOLO 등) 과 같은 `.venv` 를 쓰면 **torch 버전 충돌** 로 실패합니다. 이 폴더 안에 별도 venv 를 만드세요.

```powershell
uv venv --python 3.10 .venv
```

활성화는 안 해도 됩니다. 아래 명령들이 `--python .venv/Scripts/python.exe` 로 명시 호출.

## Step 3. PyTorch 트리오 설치 (CUDA 12.8)

세 패키지를 **반드시 같은 명령에서, 같은 인덱스로** 설치. 분리 설치하면 mismatch 가 일어납니다.

```powershell
uv pip install --python .venv/Scripts/python.exe `
    torch==2.8.0 torchvision==0.23.0 torchaudio==2.8.0 `
    --index-url https://download.pytorch.org/whl/cu128
```

CPU 만 쓸 경우 (속도 매우 느림):
```powershell
uv pip install --python .venv/Scripts/python.exe `
    torch==2.8.0 torchvision==0.23.0 torchaudio==2.8.0
```

## Step 4. OmniVoice 설치 + 오디오 라이브러리

```powershell
uv pip install --python .venv/Scripts/python.exe `
    -e ./OmniVoice ipykernel soundfile sounddevice
```

## Step 5. Jupyter 커널 등록

이 폴더의 `.venv` 를 Jupyter 가 인식하도록 커널 등록.

```powershell
.venv\Scripts\python.exe -m ipykernel install --user `
    --name omnivoice --display-name "Python (OmniVoice)"
```

이후 노트북 열고 **우측 상단 커널 선택에서 "Python (OmniVoice)" 고르기**.

## Step 6. 검증 (import 확인)

새 노트북 셀 또는 PowerShell 에서:

```python
import sys, torch
print("Python:", sys.executable)
print("CUDA  :", torch.cuda.is_available())

from omnivoice import OmniVoice
print("OK")
```

`CUDA: True` + `OK` 가 보이면 셋업 완료. 첫 모델 로드 (`from_pretrained`) 는 가중치 다운로드 때문에 몇 분 소요.

---
