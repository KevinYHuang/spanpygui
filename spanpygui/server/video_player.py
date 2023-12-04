import time
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import threading
from bisect import bisect_left

from spanpygui.server.config import config

class VideoPlayer:
    def __init__(self):
        self.fps = 83.28
        self.curr_time = 0
        self.last_time = None
        
        self.renderer = VideoRenderer()
        self.renderer.start()

    def set_fps(self, fps):
        self.fps = fps

    def get_num_video_frames(self):
        return len(self.renderer)

    def get_duration(self):
        return len(self.renderer)/self.fps

    def get_curr_time(self):
        return self.curr_time
    
    def set_curr_time(self, t):
        self.curr_time = t
    
    def get_curr_frame_num(self):
        return int(self.curr_time*self.fps)
    
    def set_num_frames(self, num):
        self.renderer.set_num_frames(num)

    def set_render_callback(self, cb):
        self.renderer.set_render_callback(cb)

    def start_render_frames(self, indices):
        self.renderer.render_frames(indices)
        if not self.renderer.is_running(): self.renderer.start()

    def get_curr_frame(self):
        if self.last_time is not None:
            now = time.time()
            if self.curr_time + now - self.last_time >= len(self.renderer)/self.fps:
                self.curr_time = len(self.renderer)/self.fps
                self.last_time = None
            else:
                self.curr_time += now - self.last_time
                self.last_time = now
        return self.renderer[int(self.curr_time*self.fps)]

    def play(self):
        if self.curr_time >= len(self.renderer)/self.fps: self.curr_time = 0
        self.last_time = time.time()

    def pause(self):
        print('pausing')
        self.last_time = None

    def is_playing(self):
        return self.last_time is not None


class VideoRenderer:
    def __init__(self, render_callback=None):
        self.frames: list[np.ndarray] = []
        self.render_callback = render_callback
        self.queue: list[int] = []
        self.ref_index = 0 # Where to prioritize renderring from

        self.width = config('render', 'width', default=512)
        self.height = config('render', 'height', default=512)
        self.workers = config('render', 'workers', default=8)
        self.executor = ThreadPoolExecutor(max_workers=self.workers)
        self.queue_lock = threading.Lock()
        self.running = False

    def __len__(self):
        return len(self.frames)
    
    def __getitem__(self, ind):
        return self.frames[ind]

    def set_render_callback(self, cb):
        self.render_callback = cb

    def set_num_frames(self, num):
        diff = num - len(self.frames)
        if diff > 0:
            self.frames += [np.zeros((self.width,self.height,3), dtype=np.uint8) for _ in range(diff)]
        elif diff < 0:
            self.frames = self.frames[:diff]

    def set_ref(self, ref):
        self.ref_index = ref

    def render_frames(self, indices):
        # add the indices to the list and reorder the list to render ref first then anything sequentially afterwards wrapping around
        if max(indices)+1 > len(self.frames): self.set_num_frames(max(indices)+1)
        with self.queue_lock:
            self.queue += list(indices)
            self.queue = sorted(set(self.queue))
            split = bisect_left(self.queue, self.ref_index)
            self.queue = self.queue[split:] + self.queue[:split]

    def start(self):
        self.running = True
        for _ in range(self.workers):
            self.executor.submit(self.worker)
    
    def stop(self):
        self.running = False
        self.queue = []
        self.executor.shutdown(wait=False)

    def is_running(self):
        return self.running

    def worker(self):
        tries = 0
        while self.running:
            i = self.get_next_frame()
            if i is None:
                if tries > 3: self.stop()
                tries += 1
                time.sleep(1+np.random.rand())
            else:
                self.frames[i] = self.render_callback(i)

    def get_next_frame(self):
        with self.queue_lock:
            if len(self.queue) == 0: return None
            return self.queue.pop(0)
