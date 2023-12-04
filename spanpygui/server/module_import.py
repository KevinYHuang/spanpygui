import subprocess
import sys
try:
    import torch, torchaudio, torchvision
except:
    try:
        subprocess.run([sys.executable, "-m", "pip", "show", "light-the-torch"], check=True, stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        subprocess.run([sys.executable, "-m", "pip", "install", "light-the-torch"])
    process = subprocess.Popen(["ltt", "install", "torch", "torchaudio", "torchvision"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in process.stdout: print(line, end='')
    process.wait()
    import torch
    print(torch.cuda.is_available())
if torchaudio.get_audio_backend() is None:
    print("No audio backend found. Installing the appropriate backend.")
    subprocess.run([sys.executable, "-m", "pip", "install", "soundfile" if sys.platform == "win32" else "sox"])