import ffmpeg
from queue import Queue
import sys
from threading import Thread


def reader(pipe, queue):
    try:
        with pipe:
            for line in iter(pipe.readline, b''):
                queue.put((pipe, line))
    finally:
        queue.put(None)


def compress_video(source_path, destination_path, progress_bar):
    error = ""

    try:
        sepia = (
            ffmpeg
            .input(source_path)
            .output(destination_path, vcodec="libx265", crf=24, preset="fast",
                    acodec="aac", audio_bitrate="128k",
                    loglevel="quiet")
            .global_args('-progress', 'pipe:1')
            .overwrite_output()
            .run_async(pipe_stdout=True, pipe_stderr=True)
        )
        q = Queue()
        Thread(target=reader, args=[sepia.stdout, q]).start()
        for source, line in iter(q.get, None):
            line = line.decode()
            if source == sepia.stderr:
                error += "\n" + line
            else:
                line = line.rstrip()
                parts = line.split('=')
                key = parts[0] if len(parts) > 0 else None
                value = parts[1] if len(parts) > 1 else None
                if key == 'out_time_ms':
                    time = max(round(float(value) / 1000000., 2), 0)
                    progress_bar.update(time - progress_bar.n)
                elif key == 'progress' and value == 'end':
                    progress_bar.update(progress_bar.total - progress_bar.n)

    except ffmpeg.Error:
        print(error, file=sys.stderr)
        sys.exit(1)
