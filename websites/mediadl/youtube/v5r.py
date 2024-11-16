import os
import threading

import websites.mediadl.youtube.v5backend_datacenter as Backend

from flask import request, session, jsonify, send_file, Response

def asyncTask(task, cacheID):
    threading.Thread(target=task).start()
    return jsonify({"message": "Conversion started", "progress": f"/mediadl/youtube/v5d?id={cacheID}"}), 202

def flaskMain(request, session):
    """
    Entry point for handling YouTube video download requests.


    Parameters:
    - url: YouTube video URL
    - type: File type: audio or video or audiovideo (default: audiovideo)
    - remux: Convert from dash to isom (default: false)
    - qt: Convert to QuickTime compatible format (default: false)
    """
    try:
        # Support both GET and POST methods
        if request.method in ['GET', 'POST']:
            # Extract parameters from args or form
            yt_url = request.args.get('url') or request.form.get('url')
            if not yt_url:
                return jsonify({"error": 1, "message": "Missing 'url' parameter"}), 400

            video_audio = request.args.get('type') or request.form.get('type') or "audiovideo"
            remux = request.args.get('remux') or request.form.get('remux') or "false"
            qt = request.args.get('qt') or request.form.get('qt') or "false"

            # Convert string to boolean
            remux = remux.lower() == "true"
            qt = qt.lower() == "true"

            cacheLocation = Backend.getTemporaryFileLocation()
            cid = os.path.basename(cacheLocation)
            progressfile = f"{cacheLocation}/_progress"
            downloadfile = f"{cacheLocation}/_download"
            # Download the video
            if video_audio == "audio":            
                def task():        
                    try:
                        with open(progressfile, "w") as f:
                            f.write("0:Downloading")
                        downloadPath = Backend.downloadAudio(yt_url, downloadTo=cacheLocation)
                        with open(downloadfile, "w") as f:
                            f.write(downloadPath)
                        with open(progressfile, "w") as f:
                            f.write("100.00:END")
                    except Exception as e:
                        with open(progressfile, "w") as f:
                            f.write("0:Error")
                        raise e
                return asyncTask(task, cid)
                    

            elif video_audio == "video":
                if qt:
                    def task():
                        try:
                            with open(progressfile, "w") as f:
                                f.write("0:Downloading")
                            downloaded = Backend.downloadVideo(yt_url, remux=remux, downloadTo=cacheLocation)
                            downloadPath = Backend.convertToQuickTimeCompatible(downloaded, progressPercentFile=progressfile)
                            with open(downloadfile, "w") as f:
                                f.write(downloadPath)
                        except Exception as e:
                            with open(progressfile, "w") as f:
                                f.write("0:Error")
                            raise e
                    return asyncTask(task, cid)
                else:
                    def task():
                        try:
                            with open(progressfile, "w") as f:
                                f.write("0:Downloading")
                            downloadPath = Backend.downloadVideo(yt_url, remux=remux, downloadTo=cacheLocation)
                            with open(downloadfile, "w") as f:
                                f.write(downloadPath)
                            with open(progressfile, "w") as f:
                                f.write("100.00:END")
                        except Exception as e:
                            with open(progressfile, "w") as f:
                                f.write("0:Error")
                            raise e
                    
                    return asyncTask(task, cid)

            elif video_audio == "audiovideo":
                if qt:
                    # Threading for async conversion
                    def task():
                        try:
                            with open(progressfile, "w") as f:
                                f.write("0:Downloading")
                            downloaded = Backend.downloadAudioVideo(yt_url, remux=remux, downloadTo=cacheLocation)
                            downloadPath = Backend.convertToQuickTimeCompatible(downloaded, progressPercentFile=progressfile)
                            with open(downloadfile, "w") as f:
                                f.write(downloadPath)
                        except Exception as e:
                            with open(progressfile, "w") as f:
                                f.write("0:Error")
                            raise e
                    return asyncTask(task, cid)
                else:
                    def task():
                        try:
                            with open(progressfile, "w") as f:
                                f.write("0:Downloading")
                            downloadPath = Backend.downloadAudioVideo(yt_url, downloadTo=cacheLocation, remux=remux)
                            with open(downloadfile, "w") as f:
                                f.write(downloadPath)
                            with open(progressfile, "w") as f:
                                f.write("100.00:END")
                        except Exception as e:
                            with open(progressfile, "w") as f:
                                f.write("0:Error")
                            raise e
                    return asyncTask(task, cid)

        else:
            return jsonify({"error": 4, "message": "Invalid request method"}), 405

    except Exception as e:
        return jsonify({"error": 6, "message": f"An unexpected error occurred: {str(e)}"}), 500
