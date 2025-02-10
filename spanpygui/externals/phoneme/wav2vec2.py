# pip install phonemizer
from phonemizer.backend.espeak.wrapper import EspeakWrapper
EspeakWrapper.set_library('C:\Program Files\eSpeak NG\libespeak-ng.dll')

import os
import torch

from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC
from spanpygui.server.config import config
from spanpygui import Audio, Text

class Wav2Vec2XLSRPhoneme():
    def __init__(self, *args, **kwargs):
        self.properties = {
            'model_name': 'facebook/wav2vec2-xlsr-53-espeak-cv-ft',
            'cuda': True
        } | kwargs
        self._get_model()
        
    def _get_model(self):
        path = os.path.join(config('files', 'model_dir'), 'wav2vec2phoneme')
        file = self.properties['model_name']
        if not os.path.exists(path):
            os.makedirs(path)
        self.processor = Wav2Vec2Processor.from_pretrained(file, cache_dir=path)
        self.model = Wav2Vec2ForCTC.from_pretrained(file).to('cuda' if self.properties['cuda'] and torch.cuda.is_available() else 'cpu')

        # send a "dummy message to warm it up"
        self.transcribe(torch.Tensor([0] * (1*512)))

    def transcribe(self, audio, sr=None):
        input_values = self.processor(audio, return_tensors="pt").input_values
        with torch.no_grad():
            logits = self.model(input_values.to(self.model.device)).logits
        predicted_ids = torch.argmax(logits.cpu(), dim=-1)
        return self.processor.batch_decode(predicted_ids)
    
model = Wav2Vec2XLSRPhoneme()

def transcribe_phonemes(audio:Audio, start=0, end=None) -> Text:
    start = int(start * audio.fs)
    end = len(audio.data) if end is None else int(end * audio.fs)

    transcription = model.transcribe(torch.tensor(audio.data[start:end]))
    text = Text(audio.name)
    text.add_interval(transcription[0], 0, len(audio.data)/audio.fs)
    return text


if __name__ == "__main__":
    from spanpygui import load_audio
    audio = load_audio('example/rainbow.wav')
    transcript = transcribe_phonemes(audio)
    print(transcript[0].label)
    #print(convert_alphabet(transcript, 'ipa', 'arpabet')[0].label)