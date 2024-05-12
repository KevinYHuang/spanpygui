import os
from PIL import Image
import numpy as np
import pickle

from spanpygui.server.utils import increment_name
from spanpygui.server.config import config
from spanpygui.server.video_player import VideoPlayer

from spanpygui.utils.data import Frames, Audio, Segments, Track, Text, load_video, load_segments, load_textgrid

class Session:

    def __init__(self, name='Untitled'):
        if (os.path.exists(name) and name.endswith('.span')) or os.path.exists(f'{name}.span'):
            self.load(name)
        else:
            self.frames: dict[str,Frames] = {}
            self.audios: dict[str,Audio] = {}
            self.segments: dict[str,Segments] = {}
            self.tracks: dict[str,Track] = {}
            self.texts: dict[str,Text] = {}
            self.name = name

        self.load = self._load
        self.fps = 83.28
        self.player = VideoPlayer()
        self.player.set_render_callback(self.render_frame)

    def save(self, directory):
        with open(os.path.join(directory, f'{self.name}.span'), 'wb') as f:
            pickle.dump({
                'frames': self.frames,
                'audios': self.audios,
                'segments': self.segments,
                'tracks': self.tracks,
                'texts': self.texts,
            }, f)
            
    def _load(self, path):
        with open(path, 'rb') as f:
            data = pickle.load(f)
            self.frames = data['frames']
            self.audios = data['audios']
            self.segments = data['segments']
            self.tracks = data['tracks']
            self.texts = data['texts']
            self.name = os.path.splitext(os.path.basename(path))[0]

    @staticmethod
    def load(path):
        s = Session(os.path.splitext(os.path.basename(path))[0])
        s._load(path)
        return s

    def play(self):
        self.player.play()
    def pause(self):
        self.player.pause()
    def is_playing(self):
        return self.player.is_playing()
    def get_curr_time(self):
        return self.player.get_curr_time()
    def set_curr_time(self, time):
        return self.player.set_curr_time(time)
    def get_curr_frame_num(self):
        return self.player.get_curr_frame_num()
    def get_duration(self):
        return self.player.get_duration()


    def import_video(self, file, render=True, **kwargs):
        frames, audio, fps = load_video(file, **kwargs)
        if len(self.frames) == 0:
            self.fps = fps
            self.player.set_fps(self.fps)
            self.player.set_num_frames(len(frames))
        
        name = increment_name(frames.name, self.frames)
        if audio is not None: name = increment_name(frames.name, self.audios)
        
        frames.set_name(name)
        self.frames[frames.name] = frames
        if audio is not None: 
            audio.set_name(name)
            self.audios[audio.name] = audio

        if render:
            self.player.start_render_frames(np.arange(len(frames)))
        return frames.name, audio.name if audio else None


    def import_segments(self, file, render=True, **kwargs):
        indices = []
        segments = load_segments(file, **kwargs)
        for s in segments:
            s.set_name(increment_name(s.name, self.segments))
            self.segments[s.name] = s
            indices += list(s.data.keys())

        if render:
            self.player.start_render_frames(indices)


    def import_text(self, file: str, **kwargs):
        if file.endswith('.TextGrid'):
            self.texts += load_textgrid(file, **kwargs)
        else:
            raise


    def render_frame(self, i):
        width = config('render', 'width')
        height = config('render', 'height')
        canvas = np.zeros((height, width, 3), dtype=np.uint8)

        # Render frames
        for f in self.frames.values():
            if not f.active: continue
            f.render(canvas, i)

        # Render segments
        for s in self.segments.values():
            if not s.active: continue
            s.render(canvas, i)

        return canvas