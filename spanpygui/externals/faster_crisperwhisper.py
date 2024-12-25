# run pip install ?
# https://github.com/nyrahealth/CrisperWhisper
import os
import numpy as np
import torch
from faster_whisper import WhisperModel

from spanpygui.utils.data import Audio, Text
from spanpygui.server.config import config

class FasterCrisperWhisper():
    def __init__(self, *args, **kwargs):
        path = os.path.join(config('files', 'model_dir'), 'faster_crisperwhisper')
        model_name = kwargs['model_name']
        self.device = kwargs['device'] if torch.cuda.is_available() else 'cpu'
        compute_type = kwargs['compute_type']
        self.language = kwargs['language']
        self.model = WhisperModel(model_name, device=self.device, compute_type=compute_type, download_root=path)

    def transcribe_and_align(self, audio):
        segments, _ = self.model.transcribe(audio, beam_size=1, language=self.language, word_timestamps=True)
        transcripts = []
        for segment in segments: transcripts += segment.words
        return transcripts
    
model = None

DEFAULT = {
    'device': 'cuda',
    'compute_type': 'float16',
    'model_name': 'nyrahealth/faster_CrisperWhisper',
    'language': 'en'
}

def transcribe_and_align(audio: Audio, return_scores=True, norm_audio=True, **kwargs) -> Text:
    kwargs = DEFAULT | kwargs

    global model
    if model is None:
        model = FasterCrisperWhisper(**kwargs)

    # TODO more data sanitation, make mono and 16000hz
    audio = audio.data.astype(np.float16)
    if norm_audio: audio = audio / max(audio)
    alignment = model.transcribe_and_align(audio)

    text = Text('words')
    scores = Text('scores')
    for s in alignment:
        if s.end <= s.start:
            continue # TODO resolve in better way
        text.add_interval(s.word, s.start, s.end)
        scores.add_interval(f'{s.probability*100:0.2f}', s.start, s.end)
    
    texts = [text]
    if return_scores: texts.append(scores)
    return texts