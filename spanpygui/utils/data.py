from moviepy.editor import VideoFileClip, AudioFileClip
import numpy as np
from scipy import io, signal
from scipy.sparse import csr_matrix
from pathlib import Path
import textgrid
import cv2


from spanpygui.server.config import config

from spanpygui.utils.render import render_image, render_segments, render_weighted

class Data:
    def __init__(self, name, data=None):
        self.data = data
        self.name: str = name
        self.active = True
    
    def __len__(self): 
        return len(self.data)
    
    def __getitem__(self, index):
        return self.data[index]

    def set_name(self, name): 
        self.name = name


class Frames(Data):
    def __init__(self, name, data=None, prerender=False):
        super().__init__(name, data)
        self.fps = config('render', 'default_fps', default=24)
        self.offset = 0
        self.prerender = [] if prerender else None
        if data is not None: self.set_data(data)

    def set_data(self, data):
        self.data = data
        self.prerender = [None] * len(data)

    def resize(self, shape):
        for i in range(len(self)):
            self.data[i] = cv2.resize(self.data[i], shape)

    def set_fps(self, fps):
        self.fps = fps

    def render(self, canvas, i):
        if self.prerender is None:
            canvas[:,:,:] = render_image(canvas, self.data[i])
        if self.prerender[i] is None:
            self.prerender[i] = render_image(canvas, self.data[i])
        canvas[:,:,:] = self.prerender[i]
        return canvas


class Audio(Data):
    def __init__(self, name, data=None, fs:int=config('audio', 'sample_rate', default=48000)):
        super().__init__(name, data)
        self.data = np.zeros(0) if data is None else data
        self.offset = 0
        self.fs = fs

    def __len__(self):
        return self.data.shape[0]


DEFAULT_PLOT_ARGS = {
    'marker':'o', 
    'color':(255,0,0),
    'thickness': 2,
    'marker_size': 8,
}
class Segments(Data):
    def __init__(self, name, data=None, plot_args={}, bounds=(0,84,84,0), prerender=False):
        super().__init__(name, data)
        self.data = {} if data is None else data
        self.bounds = bounds
        self.plot_args = DEFAULT_PLOT_ARGS | plot_args
        self.prerender = {} if prerender else None

    def render(self, canvas, i):
        if self.prerender is None:
            transformed_data = self.data[i] - np.array((self.bounds[0],self.bounds[3]))[None,:]
            transformed_data = transformed_data * np.array((canvas.shape[1]/(self.bounds[1]-self.bounds[0]),canvas.shape[0]/(self.bounds[2]-self.bounds[3])))[None,:]
            rendered = render_segments(canvas, transformed_data, output_alpha=True, **self.plot_args)
            canvas[:,:,:] = render_weighted(canvas, rendered)
            return canvas
        
        if i not in self.prerender:
            # This is broken as you cannot have 3d sparse matrices. Fix later, but low priority
            transformed_data = self.data[i] - np.array((self.bounds[0],self.bounds[3]))[None,:]
            transformed_data = transformed_data * np.array((canvas.shape[1]/(self.bounds[1]-self.bounds[0]),canvas.shape[0]/(self.bounds[2]-self.bounds[3])))[None,:]
            self.prerender[i] = csr_matrix(render_segments(canvas, transformed_data, output_alpha=True, **self.plot_args), dtype=np.uint8)
        canvas[:,:,:] = render_weighted(canvas, self.prerender[i].toarray())
        return canvas
    

class Track(Data):
    def __init__(self, name, data=None):
        super().__init__(name, data)
        self.data = {} if data is None else data


class Text(Data):
    class Point:
        def __init__(self, time, label):
            self.time = time
            self.label = label

    class Interval:
        def __init__(self, start, stop, label):
            self.start = start
            self.stop = stop
            self.label = label

    def __init__(self, name, data=None, point=False):
        super().__init__(name, data)
        self.data: list[Text.Point|Text.Interval] = [] if data is None else data
        self.is_point = point

    def __len__(self):
        return len(self.data)

    def __iter__(self):
        return iter(self.data)

    def __getitem__(self, ind):
        return self.data[ind]
    
    def add_interval(self, label, start, end):
        assert not self.is_point, "Attempted adding interval to poitn tier"
        # TODO overlap check
        self.data.append(Text.Interval(start, end, label))
    
    def add_point(self, label, time):
        assert self.is_point, "Attempted adding point to interval tier"
        # TODO overlap check
        self.data.append(Text.Point(time, label))



# =====[ LOADING FUNCTIONS ] =====

def load_video(file, mono=True, fs=None):
    name = Path(file).stem
    if fs is None: fs = config('audio', 'sample_rate', default=48000)
    clip = VideoFileClip(file, audio_fps=fs)
    frames = Frames(name, [f for f in clip.iter_frames()])
    frames.set_fps(clip.fps)

    audio = None
    if clip.audio:
        audio = clip.audio.to_soundarray()
        if mono: audio = np.mean(audio, axis=1)
        audio = Audio(name, audio, fs)
    
    clip.close()
    return frames, audio, clip.fps

def load_audio(file, mono=True, fs=None):
    name = Path(file).stem
    if fs is None: fs = config('audio', 'sample_rate', default=48000)
    sr, audio = io.wavfile.read(file)
    audio = audio / np.iinfo(np.int16).max
    if mono and len(audio.shape)>1: audio = np.mean(audio, axis=1)
    audio = signal.resample(audio, int(audio.shape[0] / sr * fs))
    return Audio(name, audio, fs)


def load_segments(file, format='span2009', size=84):
    if format == 'span2009':
        names = [
            'epiglottis', 'tongue', 'mandible', 'lower_lip', 'chin', 'neck',
            'arytenoid', 'pharynx', 'back', 'trachea',
            'hard_palate', 'velum', 'nasal_cavity', 'nose', 'upper_lip'
        ]
        segments = [{} for _ in names]
        mat = io.loadmat(file)
        for trackdata in mat['trackdata'][0]:
            try:
                contours = trackdata['contours'][0,0]
                frameNo = trackdata['frameNo'][0,0][0,0] - 1

                segment = contours['segment'][0,0][0]
                j = 0
                for s in segment[:-1]:
                    v = s['v'][0,0]
                    i = s['i'][0,0].flatten()
                    points_dict = {}
                    for index, point in zip(i, v):
                        if index not in points_dict: points_dict[index] = []
                        corrected_point = np.zeros(2)
                        corrected_point[0] = point[0] + size // 2
                        corrected_point[1] = -point[1] + size // 2 - 1
                        points_dict[index].append(corrected_point)
                    for index in sorted(points_dict.keys()):
                        segments[j][frameNo] = np.array(points_dict[index])
                        j += 1
            except:
                print('ah')
                pass
        return [Segments(n, s) for n, s in zip(names, segments)]
    else:
        raise # unsupported segmentation format

def load_textgrid(file):
    grid = textgrid.TextGrid.fromFile(file)
    tiers = []
    for tier in grid:
        is_point = isinstance(tier, textgrid.PointTier)
        tier_data = []
        for item in tier:
            if is_point:
                tier_data.append(Text.Point(item.time, item.mark))
            else:
                tier_data.append(Text.Interval(item.minTime, item.maxTime, item.mark))
        tiers.append(Text(tier.name, tier_data, is_point))
    return tiers


# =====[ WRITING FUNCTIONS ]=====

def write_audio(file: str, audio: Audio):
    ext = file[-3:]
    if ext == 'wav':
        io.wavfile.write(file, audio.fs, audio.data)
    else:
        raise

def write_textgrid(file: str, texts: list[Text]):
    grid = textgrid.TextGrid()
    for text in texts:
        if text.is_point:
            tier = textgrid.PointTier(text.name)
            for point in text: tier.add(point.time, point.label)
            tier.maxTime = max([p.time for p in text])
        else:
            tier = textgrid.IntervalTier(text.name)
            for interval in text: tier.add(interval.start, interval.stop, interval.label)
        grid.append(tier)
    grid.write(file)