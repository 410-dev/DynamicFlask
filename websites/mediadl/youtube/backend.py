# def download_video(url):
#     from pytube import YouTube
#     import os
#     import re
#
#     # Import ffmpeg only if needed
#     def combine_video_audio(video_path, audio_path, output_path):
#         import ffmpeg
#         video_stream = ffmpeg.input(video_path)
#         audio_stream = ffmpeg.input(audio_path)
#         ffmpeg.output(video_stream, audio_stream, output_path, vcodec='copy', acodec='copy').run(overwrite_output=True)
#         os.remove(video_path)
#         os.remove(audio_path)
#
#     yt = YouTube(url)
#     print(f"Title: {yt}")
#     # Sanitize the title to create a valid filename
#     filename = re.sub(r'[<>:"/\\|?*]', '', "test") + ".mp4"
#
#     # Try to get the highest resolution progressive stream
#     stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
#     if stream:
#         print(f"Downloading progressive stream at {stream.resolution}")
#         stream.download(filename=filename)
#         print(f"Downloaded: {filename}")
#     else:
#         print("No progressive stream available at high resolution.")
#         # Download video and audio separately
#         video_stream = yt.streams.filter(adaptive=True, file_extension='mp4', only_video=True).order_by('resolution').desc().first()
#         audio_stream = yt.streams.filter(adaptive=True, file_extension='mp4', only_audio=True).order_by('abr').desc().first()
#
#         if not video_stream or not audio_stream:
#             print("Error: Cannot find suitable video or audio streams.")
#             return
#
#         print(f"Downloading video stream at {video_stream.resolution}")
#         video_path = video_stream.download(filename='temp_video.mp4')
#         print(f"Downloading audio stream at {audio_stream.abr}")
#         audio_path = audio_stream.download(filename='temp_audio.mp4')
#
#         # Combine video and audio using ffmpeg
#         print("Combining video and audio streams...")
#         combine_video_audio(video_path, audio_path, filename)
#         print(f"Downloaded and combined video: {filename}")
#
# download_video("https://www.youtube.com/shorts/TRwtUB0rT0E")

import os
from pytubefix import YouTube
from moviepy.editor import VideoFileClip, AudioFileClip
import streamlit as st


def download_video(url, save_dir, progress_callback=None):
    # Create a YouTube object from the URL
    yt = YouTube(url)

    # Find the highest resolution video stream without audio
    video_stream = yt.streams.filter(progressive=False, file_extension='mp4', only_video=True).order_by(
        'resolution').desc().first()

    # Download the video stream to a temporary file
    video_temp_path = os.path.join(save_dir, 'temp_video.mp4')
    video_stream.download(output_path=save_dir, filename='temp_video.mp4')

    # Find the highest quality audio stream
    audio_stream = yt.streams.filter(only_audio=True, file_extension='mp4').order_by('abr').desc().first()

    # Download the audio stream to a temporary file
    audio_temp_path = os.path.join(save_dir, 'temp_audio.mp3')
    audio_stream.download(output_path=save_dir, filename='temp_audio.mp3')

    # Load the downloaded video and audio files into moviepy clips
    video_clip = VideoFileClip(video_temp_path)
    audio_clip = AudioFileClip(audio_temp_path)

    # Combine the audio clip with the video clip
    final_clip = video_clip.set_audio(audio_clip)

    # Save the final clip as an MP4 file
    final_video_path = os.path.join(save_dir, 'final_video.mp4')
    final_clip.write_videofile(final_video_path, codec='libx264', audio_codec='aac')

    # Close the clips to release resources
    video_clip.close()
    audio_clip.close()
    final_clip.close()

    # Delete the temporary files
    os.remove(video_temp_path)
    os.remove(audio_temp_path)

    return final_video_path


def main():
    # st.title("YouTube Video Downloader")
    #
    # url = st.text_input("Enter YouTube Video URL:")
    # save_dir = st.text_input("Enter Directory to Save Video:")
    #
    # if st.button("Download"):
    #     if url and save_dir:
    #         with st.spinner("Downloading..."):
    #             downloaded_video_path = download_video(url, save_dir)
    #             if downloaded_video_path:
    #                 st.success(f"Downloaded video saved at: {downloaded_video_path}")
    #             else:
    #                 st.error("Failed to download video.")
    #     else:
    #         st.error("Please provide both URL and save directory.")

    url = "https://www.youtube.com/shorts/TRwtUB0rT0E"
    save_dir = "./"
    downloaded_video_path = download_video(url, save_dir)
    print(f"Downloaded video saved at: {downloaded_video_path}")


if __name__ == "__main__":
    main()
