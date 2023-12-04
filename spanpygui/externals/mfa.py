import os
import subprocess
import tempfile
from scipy.io.wavfile import write
import shutil

from spanpygui.utils.data import Audio, Text, write_audio, load_textgrid

def mfa(audio: Audio, text: Text, dict='english_us_arpa', model='english_us_arpa', conda_env='aligner'):
    # Create temporary files to process
    temp_dir = tempfile.mkdtemp()
    temp_name = 'temp'

    wav_path = os.path.join(temp_dir, f'{temp_name}.wav')
    write_audio(wav_path, audio)

    text_path = os.path.join(temp_dir, f'{temp_name}.txt')
    with open(text_path, 'w') as text_file:
        text_file.write(' '.join([a.label for a in text]))
        
    # Run mfa
    mfa_command = f'conda run -n {conda_env} mfa align {temp_dir} {dict} {model} {temp_dir}'
    subprocess.run(mfa_command, shell=True)

    # Parse output and clean up
    alignments = None
    out_path = os.path.join(temp_dir, f'{temp_name}.TextGrid')
    if os.path.exists(out_path):
        alignments = load_textgrid(out_path)

    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

    return alignments