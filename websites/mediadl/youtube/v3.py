import platform
import subprocess
import tempfile
import os
import re
import hashlib
import json
import io
from flask import request, session, jsonify, send_file, Response
import yt_dlp
import storageapi
from urllib.parse import quote

def sanitize_filename(name):
    """
    Sanitize the video title to create a safe filename.
    Removes invalid characters for filenames.
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

def download_youtube_video(yt_url, output_path, format_type='mp4'):
    """
    Download the YouTube video or audio at the highest available quality.
    Returns the path to the downloaded file and the video title.
    """
    if format_type == 'mp3':
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
    elif format_type == 'mp4-lq':
        ydl_opts = {
            'format': (
                'bestvideo[vcodec=avc1][height<=?1080]+bestaudio[acodec=aac][ext=m4a]'
                '/bestvideo[vcodec=avc1]+bestaudio[acodec=aac]'
                '/best[ext=mp4]'
                '/best'
            ),
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'merge_output_format': 'mp4',
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'prefer_ffmpeg': False,
        }
    else:
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'merge_output_format': 'mp4',
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
        }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(yt_url, download=True)
        video_title = info_dict.get('title', 'downloaded_video')
        video_filename = ydl.prepare_filename(info_dict)
        if format_type == 'mp3':
            video_filename = os.path.splitext(video_filename)[0] + '.mp3'
        else:
            if not video_filename.endswith('.mp4'):
                video_filename = os.path.splitext(video_filename)[0] + '.mp4'
        return video_filename, video_title

def convert_to_h264_aac_stream(input_path):
    """
    Convert the input video to H.264 (video) and AAC (audio) encoding using ffmpeg.
    Stream the output directly to the response.
    """
    try:
        print("Encoding and streaming...")
        command = [
            'ffmpeg',
            '-i', input_path,
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-strict', 'experimental',  # Allows for AAC encoding
            '-b:a', '128k',  # Audio bitrate
            '-f', 'mp4',
            '-movflags', 'frag_keyframe+empty_moov+default_base_moof',
            'pipe:1'
        ]
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=10**5
        )

        def generate():
            try:
                for chunk in iter(lambda: process.stdout.read(4096), b''):
                    yield chunk
            except Exception as e:
                print(f"Exception during streaming: {e}")
                process.kill()
                raise
            finally:
                process.stdout.close()
                process.kill()
        return generate
    except Exception as e:
        print(f"Error in convert_to_h264_aac_stream: {e}")
        return None

def convert_to_h264_aac(input_path, output_path):
    """
    Convert the input video to H.264 (video) and AAC (audio) encoding using ffmpeg.
    This ensures compatibility with iOS/macOS devices.
    """
    try:
        print("Encoding...")
        subprocess.check_call([
            'ffmpeg',
            '-i', input_path,
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-strict', 'experimental',  # Allows for AAC encoding
            '-b:a', '128k',  # Audio bitrate
            '-y',  # Overwrite output files without asking
            output_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("Encoding success.")
        return output_path
    except subprocess.CalledProcessError:
        return None

def flaskMain(request, session):
    """
    Entry point for handling YouTube video download requests.
    """
    try:
        # Support both GET and POST methods
        if request.method in ['GET', 'POST']:
            # Extract parameters from args or form
            yt_url = request.args.get('yturl') or request.form.get('yturl')
            if not yt_url:
                return jsonify({"error": 1, "message": "Missing 'yturl' parameter"}), 400

            video_type = request.args.get('type') or request.form.get('type')
            if video_type:
                video_type = video_type.lower()
            else:
                video_type = 'mp4'  # Default type

            if video_type == 'mp3':
                format_type = 'mp3'
                ext = 'mp3'
            elif video_type == 'mp4-lq':
                format_type = 'mp4-lq'
                ext = 'mp4'
            elif video_type == 'mp4-hq':
                format_type = 'mp4'
                ext = 'mp4'
            else:
                # Invalid type, default to 'mp4'
                format_type = 'mp4'
                ext = 'mp4'

            # Use video URL as cache key (after hashing)
            cache_key = hashlib.sha256(yt_url.encode()).hexdigest()
            storage_path = f"{cache_key}_{video_type}.{ext}"
            metadata_path = f"{cache_key}_{video_type}_metadata.json"

            # Check if the file already exists in storage (skip caching for mp4-hq)
            if video_type != 'mp4-hq' and storageapi.has(storage_path):
                # Read the file from storageapi
                file_data = storageapi.readBytes(storage_path)
                # Read the metadata
                metadata_json = storageapi.readStr(metadata_path)
                if metadata_json:
                    metadata = json.loads(metadata_json)
                    safe_title = metadata.get('safe_title', 'downloaded_video')
                else:
                    safe_title = 'downloaded_video'
                filename = f"{safe_title}.{ext}"
                # Send the file to the client
                response = send_file(
                    io.BytesIO(file_data),
                    as_attachment=True,
                    download_name=filename,
                    mimetype='video/mp4' if ext == 'mp4' else 'audio/mpeg'
                )
                # Build Content-Disposition header
                response.headers['Content-Disposition'] = build_content_disposition(filename)
                return response

            # If not cached, proceed to download and process
            # Create a temporary directory to store the video
            with tempfile.TemporaryDirectory() as tmpdirname:
                # Download the video
                video_path, video_title = download_youtube_video(yt_url, tmpdirname, format_type)
                if not os.path.exists(video_path):
                    return jsonify({"error": 2, "message": "Failed to download the video"}), 500

                # Sanitize the video title for filename
                safe_title = sanitize_filename(video_title)
                filename = f"{safe_title}.{ext}"

                if video_type == 'mp3':
                    # Read the final file into bytes
                    with open(video_path, 'rb') as f:
                        file_data = f.read()

                    # Store the file in storageapi
                    storageapi.writeBytes(storage_path, file_data)

                    # Store metadata
                    metadata = {'safe_title': safe_title}
                    storageapi.writeStr(metadata_path, json.dumps(metadata))

                    # Send the file for download
                    response = send_file(
                        io.BytesIO(file_data),
                        as_attachment=True,
                        download_name=filename,
                        mimetype='audio/mpeg'
                    )
                    response.headers['Content-Disposition'] = build_content_disposition(filename)

                    storageapi.remove(storage_path)
                    storageapi.remove(metadata_path)

                    return response

                elif video_type == 'mp4-lq':
                    # For 'mp4-lq', we have already downloaded the video with adjusted ydl_opts
                    final_video_path = video_path

                    # Read the final file into bytes
                    with open(final_video_path, 'rb') as f:
                        file_data = f.read()

                    # Store the file in storageapi
                    storageapi.writeBytes(storage_path, file_data)

                    # Store metadata
                    metadata = {'safe_title': safe_title}
                    storageapi.writeStr(metadata_path, json.dumps(metadata))

                    # Send the file for download
                    response = send_file(
                        io.BytesIO(file_data),
                        as_attachment=True,
                        download_name=filename,
                        mimetype='video/mp4'
                    )
                    response.headers['Content-Disposition'] = build_content_disposition(filename)

                    storageapi.remove(storage_path)
                    storageapi.remove(metadata_path)

                    return response

                elif video_type == 'mp4-hq':
                    # For 'mp4-hq', stream the ffmpeg output directly
                    generate = convert_to_h264_aac_stream(video_path)
                    if not generate:
                        return jsonify({"error": 3, "message": "Failed to convert video to H.264/AAC"}), 500

                    response = Response(
                        generate(),
                        mimetype='video/mp4',
                        headers={
                            'Content-Disposition': build_content_disposition(filename)
                        },
                        direct_passthrough=True
                    )
                    return response

                else:
                    # For other types, proceed as before
                    # Convert to H.264 and AAC for better compatibility with iOS/macOS
                    converted_video_path = os.path.join(tmpdirname, f"{safe_title}_h264_aac.mp4")
                    conversion_result = convert_to_h264_aac(video_path, converted_video_path)
                    if not conversion_result or not os.path.exists(conversion_result):
                        return jsonify({"error": 3, "message": "Failed to convert video to H.264/AAC"}), 500
                    final_video_path = converted_video_path
                    filename = f"{safe_title}.{ext}"

                    # Read the final file into bytes
                    with open(final_video_path, 'rb') as f:
                        file_data = f.read()

                    # Store the file in storageapi
                    storageapi.writeBytes(storage_path, file_data)

                    # Store metadata
                    metadata = {'safe_title': safe_title}
                    storageapi.writeStr(metadata_path, json.dumps(metadata))

                    # Send the file for download
                    response = send_file(
                        io.BytesIO(file_data),
                        as_attachment=True,
                        download_name=filename,
                        mimetype='video/mp4'
                    )
                    response.headers['Content-Disposition'] = build_content_disposition(filename)

                    storageapi.remove(storage_path)
                    storageapi.remove(metadata_path)

                    return response

        else:
            return jsonify({"error": 4, "message": "Invalid request method"}), 405

    except yt_dlp.utils.DownloadError as e:
        return jsonify({"error": 5, "message": f"Download error: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": 6, "message": f"An unexpected error occurred: {str(e)}"}), 500
