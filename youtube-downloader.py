#! /usr/bin/python3

# Youtube-downloader
#
# Download videos from youtube in MP4 or MP3 format with a simple GUI.
#
# © Copyright Philo Decroos
# Apache 2.0 licence

from moviepy.editor import *
import pytube
import re
import tkinter as tk
from tkinter import filedialog


class Page(tk.Frame):
    def __init__(self, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)
        self.youtube_regex = "^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)(\S+)?$"

    def show(self):
        self.lift()


class SingleUrlPage(Page):
    def __init__(self, *args, **kwargs):
        Page.__init__(self, *args, **kwargs)

        self.target = os.path.expanduser('~/Downloads')

        self.include_video = tk.IntVar()
        self.include_video.set(0)

        self.dirLabel = tk.Label(self, text='Target: ' + self.target)
        self.dirLabel.grid(row=0, column=0, pady=20, padx=10)

        self.dirButton = tk.Button(self, command=self.change_target, text="Choose directory")
        self.dirButton.grid(row=0, column=1)

        self.urlLabel = tk.Label(self, text="YouTube URL:")
        self.urlLabel.grid(row=1, column=0, pady=20, padx=10)

        self.urlEntry = tk.Entry(self, width=40)
        self.urlEntry.grid(row=1, column=1)

        self.videoCheckbox = tk.Checkbutton(self, variable=self.include_video, onvalue=1, offvalue=0, text="Include video")
        self.videoCheckbox.grid(row=2, column=0, pady=20, padx=10)

        self.submitButton = tk.Button(self, command=self.download, text="Download")
        self.submitButton.grid(row=2, column=1)

        self.statusLabel = tk.Label(self, text="")
        self.statusLabel.grid(row=3, columnspan=2, pady=20, padx=10)

    def download(self):
        url = self.urlEntry.get()

        youtube_pattern = re.compile(self.youtube_regex)
        if not youtube_pattern.match(url):
            self.statusLabel.configure(text='URL is not a YouTube URL!', fg="red")
            return

        self.statusLabel.configure(text='Download in progress...', fg="green")
        self.update()

        youtube = pytube.YouTube(url)
        video = youtube.streams.first()
        path = video.download(self.target)

        if self.include_video.get() == 0:
            videoclip = VideoFileClip(path)
            audioclip = videoclip.audio
            audioclip.write_audiofile(path[:-1] + '3')
            os.remove(path)

        self.statusLabel.configure(text='Download complete!', fg='green')

    def change_target(self):
        self.target = tk.filedialog.askdirectory()
        self.dirLabel.configure(text='Target: ' + self.target)


class FilePage(Page):
    def __init__(self, *args, **kwargs):
        Page.__init__(self, *args, **kwargs)

        self.target = os.path.expanduser('~/Downloads')
        self.filename = 'No file chosen'

        self.include_video = tk.IntVar()
        self.include_video.set(0)

        self.fileButton = tk.Button(self, command=self.choose_file, text="Choose file")
        self.fileButton.grid(row=0, column=0, pady=20, padx=20)

        self.fileLabel = tk.Label(self, text=self.filename)
        self.fileLabel.grid(row=0, column=1)

        self.dirButton = tk.Button(self, command=self.change_target, text="Choose target directory")
        self.dirButton.grid(row=1, column=0, pady=20, padx=20)

        self.dirLabel = tk.Label(self, text=self.target)
        self.dirLabel.grid(row=1, column=1, pady=20, padx=20)

        self.videoCheckbox = tk.Checkbutton(self, variable=self.include_video, onvalue=1, offvalue=0, text="Include video")
        self.videoCheckbox.grid(row=2, column=0, pady=20, padx=20)

        self.submitButton = tk.Button(self, command=self.download, text="Download")
        self.submitButton.grid(row=2, column=1)

        self.errorLabel = tk.Label(self, text="", fg="red")
        self.errorLabel.grid(row=3, column=0, pady=20, padx=10)

        self.statusLabel = tk.Label(self, text="", fg="green")
        self.statusLabel.grid(row=3, column=1, pady=20, padx=10)

    def choose_file(self):
        self.filename = filedialog.askopenfilename()
        self.fileLabel.configure(text=self.filename)

    def download(self):
        self.errorLabel.configure(text='')
        self.update()

        urls_file = open(self.filename, 'r').readlines()
        if (len(urls_file) > 1000):
            self.errorLabel.configure(text='File is too large.')
            return

        downloaded = 0
        self.statusLabel.configure(text=str(downloaded) + '/' + str(len(urls_file)) + ' downloaded...')
        self.update()

        for url in urls_file:
            youtube_pattern = re.compile(self.youtube_regex)
            if not youtube_pattern.match(url):
                self.errorLabel.configure(text='Some URLS were not valid')
                self.update()
                continue

            youtube = pytube.YouTube(url)
            video = youtube.streams.first()
            path = video.download(self.target)

            if self.include_video.get() == 0:
                videoclip = VideoFileClip(path)
                audioclip = videoclip.audio
                audioclip.write_audiofile(path[:-1] + '3')
                os.remove(path)

            downloaded += 1
            self.statusLabel.configure(text=str(downloaded) + '/' + str(len(urls_file)) + ' downloaded...')
            self.update()

        invalid = len(urls_file) - downloaded
        if invalid == 0:
            self.statusLabel.configure(text='All downloads complete!')
        else:
            self.statusLabel.configure(text='Complete, ' + str(downloaded) + '/' + str(len(urls_file)) + ' downloaded.')

    def change_target(self):
        self.target = tk.filedialog.askdirectory()
        self.dirLabel.configure(text=self.target)


class YoutubeDownloader(tk.Frame):
    def __init__(self, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)

        self.p1 = SingleUrlPage(self)
        self.p2 = FilePage(self)

        self.buttonframe = tk.Frame(self)
        self.container = tk.Frame(self)
        self.buttonframe.pack(side="top", fill="x", expand=False)
        self.container.pack(side="top", fill="both", expand=True)

        self.p1.place(in_=self.container, x=0, y=0, relwidth=1, relheight=1)
        self.p2.place(in_=self.container, x=0, y=0, relwidth=1, relheight=1)

        self.b1 = tk.Button(self.buttonframe, text="Single url", command=self.p1.lift)
        self.b2 = tk.Button(self.buttonframe, text="From file", command=self.p2.lift)

        self.b1.pack(side="left")
        self.b2.pack(side="left")
        self.p1.show()


if __name__ == "__main__":
    root = tk.Tk()
    downloader = YoutubeDownloader(root)
    downloader.pack(side="top", fill="both", expand=True)
    root.wm_geometry("600x300")
    root.mainloop()
