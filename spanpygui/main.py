import time
from spanpygui.server.app import run
from spanpygui.server.runtime import new_session

if __name__ == "__main__":
    s = new_session('test')
    s.import_video('example/rainbow.mp4')
    s.import_segments('example/rainbow.mat')
    run()