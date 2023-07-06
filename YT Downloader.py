"""
author: Yichen Zhang
"""
import os
import subprocess
import ctypes
import re
import threading
#pip install ffmpeg-python
import ffmpeg
#pip install pytube
from pytube import YouTube
import tkinter as tk
from tkinter import filedialog
from tkinter.ttk import Progressbar
#pip install humanize
import humanize

def exist1080p(streams):
    return len(streams.filter(res="1080p"))>0

def getBestMP4StreamV(streams):
    return streams.filter(mime_type="video/mp4").order_by("resolution")[-1]

def getBestMP4StreamA(streams):
    return streams.filter(mime_type="audio/mp4").order_by("abr")[-1]

def getBestMP4StreamP(streams):
    return streams.get_highest_resolution()

def VAMerge(Vfilename, Afilename, FinalName):
    v = ffmpeg.input(path+Vfilename).video
    a = ffmpeg.input(path+Afilename).audio
    ffmpeg.output(v,a,path+FinalName,codec="copy").run()
    os.remove(path+Vfilename)
    os.remove(path+Afilename)

def hideFile(filename):
    subprocess.run('attrib +h "' + filename + '"')

reserved = ["con","prn","aux","nul","com0","com1","com2","com3","com4","com5",
            "com6","com7","com8","com9","lpt0","lpt1","lpt2","lpt3","lpt4",
            "lpt5","lpt6","lpt7","lpt8","lpt9"]
def uniqueValidFilename(name, extension):
    name = re.sub(r"[\\/:*\"<>|]", "", name)
    if name.lower() not in reserved and not os.path.exists(path+name+extension):
        return name+extension
    i = 2
    while os.path.exists(path+name+' ('+str(i)+')'+extension):
        i += 1
    return name+' ('+str(i)+')'+extension

def resetProgressbar():
    prog_bar["value"] = 0
    prog_bar.update()

def updateProgressMessage(total_bytes, percentage):
    message = "{:00.2f}% downloaded, ".format(percentage)+humanize.naturalsize(total_bytes,gnu=True,format='%.2f')
    if total_bytes>=1024:
        message += "B"
    message += " total"
    progress_msg.config(text=message)

def updateProgressbar(s, chunk, bytes_remaining):
    percentage = (1-bytes_remaining/s.filesize)*100
    updateProgressMessage(s.filesize, percentage)
    prog_bar["value"] = percentage
    prog_bar.update()

def downloadDASH(yt):
    download_msg.config(text="Downloading Video Stream...")
    vstr = getBestMP4StreamV(yt.streams)
    updateProgressMessage(vstr.filesize, 0)
    vname = uniqueValidFilename("[VIDEO ONLY]"+yt.title, ".mp4")
    vstr.download(output_path=path, filename=vname)
    hideFile(path+vname)
    
    download_msg.config(text="Downloading Audio Stream...")
    astr = getBestMP4StreamA(yt.streams)
    updateProgressMessage(astr.filesize, 0)
    resetProgressbar()
    aname = uniqueValidFilename("[AUDIO ONLY]"+yt.title, ".aac")
    astr.download(output_path=path, filename=aname)
    hideFile(path+aname)
    
    download_msg.config(text="Merging Video and Audio...")
    progress_msg.config(text="")
    resetProgressbar()
    fname = uniqueValidFilename(yt.title, ".mp4")
    VAMerge(vname, aname, fname)

def downloadProgressive(yt):
    download_msg.config(text="Downloading Video...")
    s = getBestMP4StreamP(yt.streams)
    updateProgressMessage(s.filesize, 0)
    name = uniqueValidFilename(yt.title, ".mp4")
    s.download(output_path=path, filename=name)

def downloadAudioOnly(yt):
    download_msg.config(text="Downloading Audio...")
    s = getBestMP4StreamA(yt.streams)
    updateProgressMessage(s.filesize, 0)
    name = uniqueValidFilename(yt.title, ".mp3")
    s.download(output_path=path, filename=name)

path = ''
def select_path():
    if working:
        return
    global path
    path_tmp = filedialog.askdirectory()
    if not path_tmp=='':
        path = path_tmp
    if path=='':
        return
    if not path[-1]=='/':
        path += '/'
    path_label.config(text="Selected Folder: "+path, font=('Arial', 11))

def downloadInit():
    download_msg.config(text="Analyzing Link...")
    progress_msg.config(text="")
    resetProgressbar()
    try:
        yt = YouTube(link_field.get(), on_progress_callback=updateProgressbar)
    except:
        tk.messagebox.showinfo("Invalid Link", "Link is invalid")
        download_msg.config(text="")
        return None
    if path=='':
        tk.messagebox.showinfo("Invalid Path", "Download folder is not specified")
        download_msg.config(text="")
        return None
    if not os.path.exists(path):
        tk.messagebox.showinfo("Invalid Path", "Download folder does not exist")
        download_msg.config(text="")
        return None
    screen.title("Downloading: "+yt.title)
    download_msg.config(text="Downloading: "+yt.title)
    return yt

def downloadSuccess(title):
    download_msg.config(text="Download Complete: "+title)
    progress_msg.config(text="")
    screen.title("YouTube Downloader")
    prog_bar["value"] = 100
    prog_bar.update()

def downloadFail():
    tk.messagebox.showinfo("Download Failed", "An error occurred")
    screen.title("YouTube Downloader")
    download_msg.config(text="Download Failed")
    progress_msg.config(text="")

def downloadVideoThread():
    global working
    try:
        yt = downloadInit()
        if yt==None:
            working = False
            return
        if exist1080p(yt.streams):
            downloadDASH(yt)
        else:
            downloadProgressive(yt)
        downloadSuccess(yt.title)
    except:
        downloadFail()
    working = False

def downloadAudioThread():
    global working
    try:
        yt = downloadInit()
        if yt==None:
            working = False
            return
        downloadAudioOnly(yt)
        downloadSuccess(yt.title)
    except:
        downloadFail()
    working = False

working = False
def downloadVideoButton():
    global working
    if working:
        return
    working = True
    threading.Thread(target=downloadVideoThread).start()

def downloadAudioButton():
    global working
    if working:
        return
    working = True
    threading.Thread(target=downloadAudioThread).start()

if __name__ == "__main__":
    screen = tk.Tk()
    screen.title("YouTube Downloader")
    screen.tk.call('tk', 'scaling', 2)
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
    
    canvas = tk.Canvas(screen, width=800, height=480)
    canvas.pack()
    
    link_label = tk.Label(screen, text="Enter Download Link: ", font=('Arial', 15))
    canvas.create_window(400, 60, window=link_label)
    
    link_field = tk.Entry(screen, width=55, font=('Arial', 12) )
    canvas.create_window(400, 120, window=link_field)
    
    path_label = tk.Label(screen, text="Select Download Folder", font=('Arial', 15))
    canvas.create_window(400, 180, window=path_label)
    
    select_btn = tk.Button(screen, text="Select Folder", font=('Arial', 14), command=select_path)
    canvas.create_window(400, 240, window=select_btn)
    
    video_btn = tk.Button(screen, text="Download Video", font=('Arial', 14), command=downloadVideoButton)
    canvas.create_window(230, 320, window=video_btn)
    
    audio_btn = tk.Button(screen, text="Download Audio Only", font=('Arial', 14), command=downloadAudioButton)
    canvas.create_window(580, 320, window=audio_btn)
    
    progress_msg = tk.Label(screen, text="", font=('Arial', 9))
    canvas.create_window(260, 390, window=progress_msg, anchor=tk.W)
    
    download_msg = tk.Label(screen, text="", font=('Arial', 9))
    canvas.create_window(22.5, 390, window=download_msg, anchor=tk.W)
    
    prog_bar = Progressbar(screen, length=750, mode='determinate')
    canvas.create_window(400, 425, window=prog_bar)
    
    screen.mainloop()
    