#! /usr/bin/python3

import pytube
import tkinter as tk
from tkinter import filedialog
from moviepy.editor import *


class Page(tk.Frame):
    def __init__(self, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)

    def show(self):
        self.lift()


class SingleUrlPage(Page):
    def __init__(self, *args, **kwargs):
        Page.__init__(self, *args, **kwargs)

        self.target = os.path.expanduser('~/Downloads')

        self.include_video = tk.IntVar()
        self.include_video.set(0)
        self.pack(side="top", fill="both", expand=True)

        self.dirLabel = tk.Label(self, text=self.target)
        self.dirLabel.pack(side="top", fill="both", expand=True)

        self.dirButton = tk.Button(self, command=self.change_target, text="Choose directory")
        self.dirButton.pack(side="top", fill="both", expand=True)

        self.urlLabel = tk.Label(self, text="Type url:")
        self.urlLabel.pack(side="top", fill="both", expand=True)

        self.urlEntry = tk.Entry(self)
        self.urlEntry.pack(side="top", fill="both", expand=True)

        self.videoCheckbox = tk.Checkbutton(self, variable=self.include_video, onvalue=1, offvalue=0, text="Include video")
        self.videoCheckbox.pack(side="top", fill="both", expand=True)

        self.submitButton = tk.Button(self, command=self.download, text="Download")
        self.submitButton.pack(side="top", fill="both", expand=True)

    def download(self):
        url = self.urlEntry.get()
        youtube = pytube.YouTube(url)
        video = youtube.streams.first()
        path = video.download(self.target)

        if self.include_video.get() == 0:
            videoclip = VideoFileClip(path)
            audioclip = videoclip.audio
            audioclip.write_audiofile(path[:-1] + '3')
            os.remove(path)

    def change_target(self):
        self.target = tk.filedialog.askdirectory()
        self.dirLabel.configure(text=self.target)


class FilePage(Page):
    def __init__(self, *args, **kwargs):
        Page.__init__(self, *args, **kwargs)

        self.target = os.path.expanduser('~/Downloads')
        self.filename = ''

        self.include_video = tk.IntVar()
        self.include_video.set(0)
        self.pack(side="top", fill="both", expand=True)

        self.fileLabel = tk.Label(self, text=self.filename)
        self.fileLabel.pack(side="top", fill="both", expand=True)

        self.fileButton = tk.Button(self, command=self.choose_file, text="Choose file with urls")
        self.fileButton.pack(side="top", fill="both", expand=True)

        self.dirLabel = tk.Label(self, text=self.target)
        self.dirLabel.pack(side="top", fill="both", expand=True)

        self.dirButton = tk.Button(self, command=self.change_target, text="Choose target directory")
        self.dirButton.pack(side="top", fill="both", expand=True)

        self.videoCheckbox = tk.Checkbutton(self, variable=self.include_video, onvalue=1, offvalue=0, text="Include video")
        self.videoCheckbox.pack(side="top", fill="both", expand=True)

        self.submitButton = tk.Button(self, command=self.download, text="Download")
        self.submitButton.pack(side="top", fill="both", expand=True)

    def choose_file(self):
        self.filename = filedialog.askopenfilename()
        self.fileLabel.configure(text=self.filename)

    def download(self):
        with open(self.filename, 'r') as urls_file:
            for url in urls_file:
                youtube = pytube.YouTube(url)
                video = youtube.streams.first()
                path = video.download(self.target)

                if self.include_video.get() == 0:
                    videoclip = VideoFileClip(path)
                    audioclip = videoclip.audio
                    audioclip.write_audiofile(path[:-1] + '3')
                    os.remove(path)

    def change_target(self):
        self.target = tk.filedialog.askdirectory()
        self.dirLabel.configure(text=self.target)


class YoutubeDownloader(tk.Frame):
    def __init__(self, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)

        p1 = SingleUrlPage(self)
        p2 = FilePage(self)

        buttonframe = tk.Frame(self)
        container = tk.Frame(self)
        buttonframe.pack(side="top", fill="x", expand=False)
        container.pack(side="top", fill="both", expand=True)

        p1.place(in_=container, x=0, y=0, relwidth=1, relheight=1)
        p2.place(in_=container, x=0, y=0, relwidth=1, relheight=1)

        b1 = tk.Button(buttonframe, text="Single url", command=p1.lift)
        b2 = tk.Button(buttonframe, text="From file", command=p2.lift)

        b1.pack(side="left")
        b2.pack(side="left")
        p1.show()


if __name__ == "__main__":
    root = tk.Tk()
    downloader = YoutubeDownloader(root)
    downloader.pack(side="top", fill="both", expand=True)
    root.wm_geometry("400x400")
    root.mainloop()
