#! /usr/bin/python3

# Youtube-downloader
#
# Download videos from youtube in MP4 or MP3 format with a simple GUI.
#
# © Copyright Philo Decroos
# Apache 2.0 licence

from moviepy.video.io.VideoFileClip import VideoFileClip
import os
import pytube
import re
import tkinter as tk
from tkinter import filedialog


class Page(tk.Frame):
    """Base class for a GUI page."""

    def __init__(self, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)
        self.youtube_regex = "^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)(\S+)?$"

    def show(self):
        self.lift()


class SingleUrlPage(Page):
    """Page in the GUI for downloading from a single URL."""

    def __init__(self, *args, **kwargs):
        Page.__init__(self, *args, **kwargs)
        self.target = os.path.expanduser("~/Downloads")
        self.include_video = tk.IntVar()
        self.include_video.set(0)
        self.make_widgets()

    def make_widgets(self):
        """Create the widgets that make up the page and position them."""
        self.dir_label = tk.Label(self, text="Target: " + self.target)
        self.dir_label.grid(row=0, column=0, pady=20, padx=10)

        self.dir_button = tk.Button(self, command=self.change_target, text="Choose directory")
        self.dir_button.grid(row=0, column=1)

        self.url_label = tk.Label(self, text="YouTube URL:")
        self.url_label.grid(row=1, column=0, pady=20, padx=10)

        self.url_entry = tk.Entry(self, width=40)
        self.url_entry.grid(row=1, column=1)

        self.video_checkbox = tk.Checkbutton(self, variable=self.include_video, onvalue=1, offvalue=0, text="Include video")
        self.video_checkbox.grid(row=2, column=0, pady=20, padx=10)

        self.submit_button = tk.Button(self, command=self.download, text="Download")
        self.submit_button.grid(row=2, column=1)

        self.status_label = tk.Label(self, text="")
        self.status_label.grid(row=3, columnspan=2, pady=20, padx=10)

    def download(self):
        """
        Downloads a youtube video from the url stored in url_entry.

        Stores video in target location as mp4 or converts to mp3.
        """
        url = self.url_entry.get()

        youtube_pattern = re.compile(self.youtube_regex)
        if not youtube_pattern.match(url):
            self.status_label.configure(text="URL is not a YouTube URL!", fg="red")
            return

        self.status_label.configure(text="Download in progress...", fg="green")
        self.update()

        youtube = pytube.YouTube(url)
        video = youtube.streams.first()
        path = video.download(self.target)

        if self.include_video.get() == 0:  # Convert to mp3
            videoclip = VideoFileClip(path)
            audioclip = videoclip.audio
            audioclip.write_audiofile(path[:-1] + "3")
            os.remove(path)

        self.status_label.configure(text="Download complete!", fg="green")

    def change_target(self):
        """Changes the target directory (storage location)."""
        self.target = tk.filedialog.askdirectory()
        self.dir_label.configure(text="Target: " + self.target)


class FilePage(Page):
    """Page in the GUI for downloading from a file containing URLs."""

    def __init__(self, *args, **kwargs):
        Page.__init__(self, *args, **kwargs)
        self.target = os.path.expanduser("~/Downloads")
        self.filename = "No file chosen"
        self.include_video = tk.IntVar()
        self.include_video.set(0)
        self.make_widgets()

    def make_widgets(self):
        """Create the widgets that make up the page and position them."""
        self.file_button = tk.Button(self, command=self.choose_file, text="Choose file")
        self.file_button.grid(row=0, column=0, pady=20, padx=20)

        self.file_label = tk.Label(self, text=self.filename)
        self.file_label.grid(row=0, column=1)

        self.dir_button = tk.Button(self, command=self.change_target, text="Choose target directory")
        self.dir_button.grid(row=1, column=0, pady=20, padx=20)

        self.dir_label = tk.Label(self, text=self.target)
        self.dir_label.grid(row=1, column=1, pady=20, padx=20)

        self.video_checkbox = tk.Checkbutton(self, variable=self.include_video, onvalue=1, offvalue=0, text="Include video")
        self.video_checkbox.grid(row=2, column=0, pady=20, padx=20)

        self.submit_button = tk.Button(self, command=self.download, text="Download")
        self.submit_button.grid(row=2, column=1)

        self.error_label = tk.Label(self, text="", fg="red")
        self.error_label.grid(row=3, column=0, pady=20, padx=10)

        self.status_label = tk.Label(self, text="", fg="green")
        self.status_label.grid(row=3, column=1, pady=20, padx=10)

    def choose_file(self):
        """Choose a file to use as input."""
        self.filename = filedialog.askopenfilename()
        self.file_label.configure(text=self.filename)

    def download(self):
        """
        Downloads all youtube videos from the urls listed in the given file.

        Stores videos in target location as mp4 or converts to mp3.
        """
        self.error_label.configure(text="")
        self.update()

        urls_file = open(self.filename, "r").readlines()
        if (len(urls_file) > 1000):
            self.error_label.configure(text="File is too large.")
            return

        downloaded = 0
        self.status_label.configure(text=str(downloaded) + "/" + str(len(urls_file)) + " downloaded...")
        self.update()

        for url in urls_file:
            youtube_pattern = re.compile(self.youtube_regex)
            if not youtube_pattern.match(url):
                self.error_label.configure(text="Some URLS were not valid")
                self.update()
                continue

            youtube = pytube.YouTube(url)
            video = youtube.streams.first()
            path = video.download(self.target)

            if self.include_video.get() == 0:
                videoclip = VideoFileClip(path)
                audioclip = videoclip.audio
                audioclip.write_audiofile(path[:-1] + "3")
                os.remove(path)

            downloaded += 1
            self.status_label.configure(text=str(downloaded) + "/" + str(len(urls_file)) + " downloaded...")
            self.update()

        invalid = len(urls_file) - downloaded
        if invalid == 0:
            self.status_label.configure(text="All downloads complete!")
        else:
            self.status_label.configure(text="Complete, " + str(downloaded) + "/" + str(len(urls_file)) + " downloaded.")

    def change_target(self):
        """Changes the target directory (storage location)."""
        self.target = tk.filedialog.askdirectory()
        self.dir_label.configure(text=self.target)


class YoutubeDownloader(tk.Frame):
    """Main frame for the GUI, contains the two pages and navigation buttons."""

    def __init__(self, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)

        self.winfo_toplevel().title("Youtube Downloader")

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
