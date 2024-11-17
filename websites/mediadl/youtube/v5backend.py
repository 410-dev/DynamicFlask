import re
import random
import ffmpeg
import threading
import os
import shlex
import datetime
import platform

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

def download(youtubeURL: str, downloadTo: str, extension: str, orderby: str, desc: bool) -> str:
    yt = YouTube(youtubeURL)
    if extension is not None:
        yt = yt.streams.filter(file_extension=extension)
    else:
        yt = yt.streams
    if orderby is not None:
        yt = yt.order_by(orderby)
    if desc:
        yt = yt.desc()
    else:
        yt = yt.asc()
    yt = yt.first()
    downloaded: str = yt.download(downloadTo, filename=sanitize_filename(yt.title))
    return downloaded

def downloadVideo(youtubeURL: str, extension: str = "mp4", downloadTo: str = None) -> str:
    if downloadTo is None:
        downloadTo = getTemporaryFileLocation()
    return download(youtubeURL, downloadTo, extension, 'resolution', True)

def downloadAudio(youtubeURL: str, extension: str = "mp4", downloadTo: str = None) -> str:
    if downloadTo is None:
        downloadTo = getTemporaryFileLocation()
    return download(youtubeURL, downloadTo, extension, 'abr', True)

def remuxVideo(filePath: str, output: str = None) -> str:
    if output is None:
        output = f"{filePath}_remuxed.mp4"
    try:
        # Remux with QuickTime-compatible settings
        ffmpeg.input(filePath).output(
            output,
            c='copy',
            movflags='faststart',
            f='mp4'  # Explicitly set MP4 container
        ).run(overwrite_output=True)
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

    # Determine video codec based on user choice and hardware acceleration
    if appleSilicon:
        if codec == "h265":
            video_codec = "hevc_videotoolbox"
        elif codec == "h264":
            video_codec = "h264_videotoolbox"
        else:
            raise ValueError("Invalid codec for Apple Silicon. Choose 'h264' or 'h265'.")
    elif cuda:
        if codec == "h265":
            video_codec = "hevc_nvenc"
        elif codec == "h264":
            video_codec = "h264_nvenc"
        else:
            raise ValueError("Invalid codec for CUDA. Choose 'h264' or 'h265'.")
    else:
        # Fallback to software encoding
        if codec == "h265":
            video_codec = "libx265"
        elif codec == "h264":
            video_codec = "libx264"
        else:
            raise ValueError("Invalid codec. Choose 'h264' or 'h265'.")
        
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
                

    try:
        # Build FFmpeg command
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
            stderr_thread = threading.Thread(
                target=parse_progress,
                args=(os.popen(" ".join(process)), get_video_duration(filePath)),
            )
            stderr_thread.start()
            stderr_thread.join()

        # Execute FFmpeg
        if not progressPercentFile:
            ffmpeg_cmd.run(overwrite_output=True)
        # ffmpeg_cmd.run(overwrite_output=True)
        return output

    except ffmpeg.Error as e:
        print(f"Error during conversion: {e}")
        if progressPercentFile:
            with open(progressPercentFile, "w") as f:
                f.write("Error")
        return None


def combineAudioVideo(audioPath: str, remuxedVideoPath: str, outputPath: str) -> str:
    video_input = ffmpeg.input(remuxedVideoPath)  # Video input
    audio_input = ffmpeg.input(audioPath)        # Audio input

    # Combine the inputs and set the output
    (
        ffmpeg.output(
                video_input,
                audio_input,
                outputPath,
                vcodec="copy",  # Copy video codec (no re-encoding)
                acodec="copy",  # Copy audio codec (no re-encoding)
                **{"map": "0:v:0", "map:a": "1:a:0"}
        ).run(overwrite_output=True)
    )
    return outputPath


def downloadAudioVideo(youtubeURL: str, audioExtension: str = "mp4", videoExtension: str = "mp4", downloadTo: str = None, remux: bool = True) -> str:
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

