# run pip install git+https://github.com/m-bain/whisperx.git
# https://github.com/m-bain/whisperX
import os
import numpy as np
import torch
import whisperx

from spanpygui.utils.data import Audio, Text
from spanpygui.server.config import config

class WhisperX():
    def __init__(self, *args, **kwargs):
        path = os.path.join(config('files', 'model_dir'), 'faster_whisper')
        model_name = kwargs['model_name']
        self.device = kwargs['device'] if torch.cuda.is_available() else 'cpu'
        compute_type = kwargs['compute_type']
        language = kwargs['language']
        self.batch_size = kwargs['batch_size']
        self.model = whisperx.load_model(model_name, self.device, compute_type=compute_type, download_root=path, language=language)

        path = os.path.join(config('files', 'model_dir'), 'wav2vec2_asr')
        self.model_a, self.metadata = whisperx.load_align_model(language_code=language, device=self.device, model_dir=path)

    def transcribe(self, audio, batch_size=16):
        return self.model.transcribe(audio, batch_size=batch_size)
    
    def align(self, audio, segments, chars=False):
        return whisperx.align(segments, self.model_a, self.metadata, audio, self.device, return_char_alignments=chars)
    
model = None

DEFAULT = {
    'device': 'cuda',
    'batch_size': 16,
    'compute_type': 'float16',
    'model_name': 'large-v3',
    'language': 'en'
}

def transcribe_and_align(audio: Audio, return_scores=False, return_chars=False, **kwargs) -> Text:
    kwargs = DEFAULT | kwargs

    global model
    if model is None:
        model = WhisperX(**kwargs)

    # TODO more data sanitation, make mono and 16000hz
    audio = audio.data.astype(np.float32)
    transcription = model.transcribe(audio)
    alignment = model.align(audio, transcription['segments'], chars=return_chars)
    
    text = Text('words')
    scores = Text('scores')
    char = Text('chars')
    char_scores = Text('char-scores')
    saveword = []
    for segment in alignment['segments']:
        for data in segment['words']:
            if 'start' not in data: continue
            text.add_interval(data['word'], data['start'], data['end'])
            scores.add_interval(str(data['score']), data['start'], data['end'])
        if not return_chars: continue
        for data in segment['chars']:
            if 'start' not in data: continue
            char.add_interval(data['char'], data['start'], data['end'])
            char_scores.add_interval(str(data['score']), data['start'], data['end'])
    
    texts = [text]
    if return_scores: texts.append(scores)
    if return_chars: texts.append(char)
    if return_chars and return_scores: texts.append(char_scores)
    return texts