# run pip install openai-whisper
# also consider distilwhisper https://www.reddit.com/r/MachineLearning/comments/17vqtcb/p_distilwhisper_a_distilled_variant_of_whisper/
import whisper
from whisper.tokenizer import get_tokenizer
import os
import numpy as np
import torch

from spanpygui.utils.data import Audio, Text
from spanpygui.server.config import config

class Whisper():
    def __init__(self, *args, **kwargs):
        self.properties = {
            'model_name': 'large-v3',
            'cuda': True
        } | kwargs
        self._get_model()
        
    def _get_model(self):
        path = os.path.join(config('files', 'model_dir'), 'whisper')
        file = self.properties['model_name']
        if not os.path.exists(path):
            os.makedirs(path)
        if not os.path.exists(os.path.join(path, file+'.pt')):
            self.model = whisper.load_model(file, download_root=path)
        else:
            self.model = whisper.load_model(os.path.join(path, file + '.pt'))

        tokenizer = get_tokenizer(multilingual=self.model.is_multilingual())  # use multilingual=True if using multilingual model
        self.number_tokens = [
            i 
            for i in range(tokenizer.eot)
            if all(c in "0123456789" for c in tokenizer.decode([i]).removeprefix(" "))
        ]

        # send a "dummy message to warm it up"
        self.model.transcribe(np.array([0] * (1*512), dtype=np.float32), fp16=(self.properties['cuda'] and torch.cuda.is_available()))

    def transcribe(self, audio, suppress_numbers=True):
        return self.model.transcribe(audio, 
                                     suppress_tokens=([-1]+self.number_tokens) if suppress_numbers else [], 
                                     fp16=(self.properties['cuda'] and torch.cuda.is_available())
                                     )['text'].strip()
    
model = Whisper()

def transcribe(audio: Audio) -> Text:
    # TODO more data sanitation, make mono and 16000hz
    transcription = model.transcribe(audio.data.astype(np.float32))
    text = Text(audio.name)
    text.add_interval(transcription, 0, len(audio.data)/audio.fs)
    return text