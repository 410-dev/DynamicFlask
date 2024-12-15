import re
import random
import ffmpeg
import threading
import os
import shlex
import datetime
import platform
import subprocess

import storageapi

from urllib.parse import quote
from pytubefix import YouTube

allowHwAccel_CUDA = False
allowHwAccel_AppleSilicon = False

def sanitize_filename(name):
    """
    Sanitize the video title to create a safe filename.
    Removes invalid characters for filenames.
    Also include sharp, ampersand, and percent characters
    """
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    return name.strip()

def build_content_disposition(filename):
    ascii_filename = filename.encode('ascii', 'ignore').decode('ascii')
    if ascii_filename != filename:
        # Filename contains non-ASCII characters
        # Use both 'filename' and 'filename*' parameters
        disposition = f"attachment; filename=\"{ascii_filename}\"; filename*=UTF-8''{quote(filename)}"
    else:
        # Filename is ASCII
        disposition = f"attachment; filename=\"{filename}\""
    return disposition


def getTemporaryFileLocation(fixedRandom: str = None, updateAccessTime: bool = True, createIfNotExist: bool = True) -> str:
    if not fixedRandom:
        random_string = ''.join(random.choices('0123456789', k=6))
        path = storageapi.cacheDir(random_string)
    else:
        path = storageapi.cacheDir(fixedRandom)

    if not updateAccessTime:
        with open(f"{path}/_access", "w") as f:
            f.write(str(datetime.datetime.now()))

    return path

def download(youtubeURL: str, downloadTo: str, extension: str, saveExtension: str, orderby: str, desc: bool) -> str:
    print(f"[INFO] [Download] Downloading video from YouTube: {youtubeURL}")
    # proxy = {
    #     "http": "http://100.110.150.103:3128",
    #     "https": "http://100.110.150.103:3128"
    # }
    # yt = YouTube(youtubeURL, proxies=proxy)
    yt = YouTube(youtubeURL)
    print(f"1: {yt}")
    if extension is not None:
        yt = yt.streams.filter(file_extension=extension)
    else:
        yt = yt.streams
    print(f"2: {yt}")
    if orderby is not None:
        yt = yt.order_by(orderby)
    print(f"3: {yt}")
    if desc:
        yt = yt.desc()
    else:
        yt = yt.asc()
    print(f"4: {yt}")
    yt = yt.first()
    print(f"5: {yt}")
    print("[INFO] [Download] Download start!")
    downloaded: str = yt.download(downloadTo, filename=f"{sanitize_filename(yt.title)}.{saveExtension}")
    print(f"[INFO] [Download] Downloaded to: {downloaded}")
    return downloaded

def downloadVideo(youtubeURL: str, extension: str = "mp4", downloadTo: str = None, remux: bool = False, ) -> str:
    if downloadTo is None:
        downloadTo = getTemporaryFileLocation()
    result = download(youtubeURL, downloadTo, "mp4", extension, 'resolution', True)
    if remux:
        return remuxVideo(result)
    return result

def downloadAudio(youtubeURL: str, extension: str = "m4a", downloadTo: str = None) -> str:
    if downloadTo is None:
        downloadTo = getTemporaryFileLocation()
    return download(youtubeURL, downloadTo, "mp4", extension, 'abr', True)

def remuxVideo(filePath: str, output: str = None) -> str:
    print(f"[INFO] [Remux] Remuxing video: {filePath} -> {output}")
    if output is None:
        output = f"{filePath}_remuxed.mp4"
        print(f"[INFO] [Remux] Output automatically reassigned to: {output}")
    try:
        # Remux with QuickTime-compatible settings
        print(f"[INFO] [Remux] Remuxing video to QuickTime-compatible format...")
        ffmpeg.input(filePath).output(
            output,
            c='copy',
            movflags='faststart',
            f='mp4'  # Explicitly set MP4 container
        ).run(overwrite_output=True)
        print(f"[INFO] [Remux] Remuxed video saved to: {output}")
        return output
    except ffmpeg.Error as e:
        print(f"Error during remuxing: {e}")
        return None

def convertToQuickTimeCompatible(
    filePath: str,
    output: str = None,
    codec: str = "h264",
    appleSilicon: bool = allowHwAccel_AppleSilicon,
    cuda: bool = allowHwAccel_CUDA,
    progressPercentFile: str = None,
) -> str:

    if output is None:
        output = f"{filePath}_qt_compatible.mp4"

    if platform.system() == "Windows":
        progressPercentFileQuote = progressPercentFile
        outputFileQuote = output
        filePathQuote = filePath
    else:
        progressPercentFileQuote = shlex.quote(progressPercentFile)
        outputFileQuote = shlex.quote(output)
        filePathQuote = shlex.quote(filePath)

    print(f"[INFO] [Convert] Converting video to QuickTime-compatible format: {filePath} -> {output}")

    # Determine video codec based on user choice and hardware acceleration
    if appleSilicon:
        if codec == "h265":
            video_codec = "hevc_videotoolbox"
        elif codec == "h264":
            video_codec = "h264_videotoolbox"
        else:
            raise ValueError("Invalid codec for Apple Silicon. Choose 'h264' or 'h265'.")
        print(f"[INFO] [Convert] Using hardware acceleration for Apple Silicon: {video_codec}")
    elif cuda:
        if codec == "h265":
            video_codec = "hevc_nvenc"
        elif codec == "h264":
            video_codec = "h264_nvenc"
        else:
            raise ValueError("Invalid codec for CUDA. Choose 'h264' or 'h265'.")
        print(f"[INFO] [Convert] Using hardware acceleration for CUDA: {video_codec}")
    else:
        # Fallback to software encoding
        if codec == "h265":
            video_codec = "libx265"
        elif codec == "h264":
            video_codec = "libx264"
        else:
            raise ValueError("Invalid codec. Choose 'h264' or 'h265'.")
        print(f"[INFO] [Convert] Using software encoding: {video_codec}")

    def get_video_duration(filePath: str) -> float:
        try:
            probe = ffmpeg.probe(filePath)
            video_stream = next(
                stream for stream in probe["streams"] if stream["codec_type"] == "video"
            )
            duration = float(video_stream["duration"])
            return duration
        except Exception as e:
            print(f"Error retrieving video duration: {e}")
            return None

    def parse_progress(stderr, totalDuration):
        """
        Parses FFmpeg progress from stderr and writes it to a progress file.
        """
        try:
            duration = None
            for line in stderr:
                if progressPercentFile:
                    print(line)
                    # Extract the duration
                    if "Duration:" in line:
                        time_str = line.split("Duration:")[1].split(",")[0].strip()
                        hours, minutes, seconds = map(float, time_str.split(":"))
                        duration = hours * 3600 + minutes * 60 + seconds
                        print(f"EXTRACTED DURATION: {duration}")

                    # Track progress
                    if "out_time=" in line:
                        if "N/A" in line:
                            continue
                        time_str = line.split("out_time=")[1].split(" ")[0].strip()
                        hours, minutes, seconds = map(float, time_str.split(":"))
                        elapsed = hours * 3600 + minutes * 60 + seconds
                        with open(progressPercentFile, "w") as f:
                            print(f"Progress: {elapsed:.2f}sec / {totalDuration:.2f}sec ({elapsed/totalDuration*100:.2f}%)")
                            f.write(f"{elapsed/totalDuration*100}:CONTINUE")

                    if "progress=end" in line:
                        with open(progressPercentFile, "w") as f:
                            print("END CONFIRM - Progress: 100.00%")
                            f.write("100.00:END")
        except Exception as e:
            print(f"Error parsing progress: {e}")
            if progressPercentFile:
                with open(progressPercentFile, "w") as f:
                    f.write(f"0:Error:{str(e)}")

    try:
        # Build FFmpeg command
        print(f"[INFO] [Convert] Building FFmpeg command...")
        ffmpeg_cmd = (
            ffmpeg.input(filePathQuote)
            .output(
                outputFileQuote,
                vcodec=video_codec,
                acodec="aac",
                movflags="faststart",
                preset="medium" if not (appleSilicon or cuda) else None,
                crf=23 if not (appleSilicon or cuda) else None,
            )
        )

        # Run FFmpeg with real-time progress monitoring, allow overwriting the output
        process = (
            ffmpeg_cmd.global_args("-progress", "pipe:1", "-nostats", "-y")
            .compile()
        )

        if progressPercentFile:
            # Run the process in a thread to parse progress
            print("Running FFmpeg with progress monitoring...")
            # escaped_process = [shlex.quote(arg) for arg in process]
            escaped_process = process
            print(f"ARGS: {' '.join(escaped_process)}")
            stderr_thread = threading.Thread(
                target=parse_progress,
                args=(os.popen(" ".join(escaped_process)), get_video_duration(filePath)),
            )
            stderr_thread.start()
            stderr_thread.join()

        # Execute FFmpeg
        if not progressPercentFile:
            ffmpeg_cmd.run(overwrite_output=True)
        # ffmpeg_cmd.run(overwrite_output=True)
        return output
    #
    except Exception as e:
        print(f"Error during conversion: {e}")
        if progressPercentFile:
            with open(progressPercentFile, "w") as f:
                f.write(f"0:Error:{str(e)}")
        return None


def combineAudioVideo(audioPath: str, remuxedVideoPath: str, outputPath: str) -> str:
    video_input = ffmpeg.input(remuxedVideoPath)  # Video input
    audio_input = ffmpeg.input(audioPath)        # Audio input

    # Combine the inputs and set the output
    print("Combining video and audio streams...")
    print(f"Video: {remuxedVideoPath} -> {video_input}")
    print(f"Audio: {audioPath} -> {audio_input}")
    print(f"Output: {outputPath}")
    (
        ffmpeg.output(
                video_input,
                audio_input,
                outputPath,
                vcodec="copy",  # Copy video codec (no re-encoding)
                acodec="copy",  # Copy audio codec (no re-encoding)
                **{"map": "0:v:0", "map:a": "1:a:0?"}  # Map video and audio streams
        ).run(overwrite_output=True)
    )
    return outputPath


def downloadAudioVideo(youtubeURL: str, audioExtension: str = "m4a", videoExtension: str = "mp4", downloadTo: str = None, remux: bool = True) -> str:
    if downloadTo is None:
        downloadTo = getTemporaryFileLocation()

    audio = downloadAudio(youtubeURL, audioExtension, downloadTo)
    video = downloadVideo(youtubeURL, videoExtension, downloadTo)
    if remux:
        vrmxd = remuxVideo(video)
    else:
        vrmxd = video
        video = f"{video}_no-remuxed.mp4"
    combineAudioVideo(audio, vrmxd, video)
    return video


def testentry():
    print(os.path.basename(getTemporaryFileLocation()))

