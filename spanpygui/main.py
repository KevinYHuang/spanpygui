import time
from spanpygui.server.app import run
from spanpygui.server.runtime import new_session

if __name__ == "__main__":
    s = new_session('test')
    s.import_video('E:/datasets/75spks/segmentation/F_18_Sacramento_sub047/avi_withaudio/usc_vtsf_F_18_Sacramento_rt_bVt_r1_withaudio.avi')
    s.import_segments('E:/datasets/75spks/segmentation/F_18_Sacramento_sub047/tracks/usc_vtsf_F_18_Sacramento_rt_bVt_r1_track.mat')
    run()