#! /usr/bin/python3

# Youtube-downloader
#
# Download videos from youtube in MP4 or MP3 format with a simple GUI.
# Input sources can be single Youtube URLs, files containing multiple URLS
# or Spotify Playlists.
#
# Copyright Philo Decroos
# Apache 2.0 licence

from moviepy.video.io.VideoFileClip import VideoFileClip
from spotipy.oauth2 import SpotifyClientCredentials
from tkinter import filedialog
from urllib.parse import unquote
from youtube_api import YouTubeDataAPI
import asyncio
import magic
import os
import pytube
import re
import spotipy
import tkinter as tk


class Page(tk.Frame):
    """Base class for a GUI page. Contains methods that all pages need."""

    def __init__(self, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)
        self.youtube_regex = re.compile(r"^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)(\S+)?$")

    def show(self):
        self.lift()

    def convert_to_mp3(self, video_path):
        """Convert an mp4 video to an mp3 audio file."""
        if magic.from_file(video_path) != 'video/mp4':
            return

        videoclip = VideoFileClip(video_path)
        audioclip = videoclip.audio
        audioclip.write_audiofile(video_path[:-1] + "3")
        videoclip.close()
        os.remove(video_path)

    def clip_string(self, string):
        """Clip long strings (file paths for example) so they don't mess up the GUI."""
        return (string[:35] + '...') if len(string) > 35 else string


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
        self.dir_label = tk.Label(self, text=self.clip_string("Target: " + self.target))
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

        if not self.youtube_regex.match(url):
            self.status_label.configure(text="URL is not a YouTube URL!", fg="red")
            return

        self.status_label.configure(text="Download in progress...", fg="green")
        self.update()

        youtube = pytube.YouTube(url)
        video = youtube.streams.first()

        if video is None:
            self.status_label.configure(text="Sorry, this video is not \navailable for download.", fg="red")
            return

        path = video.download(self.target)
        if self.include_video.get() == 0:
            self.convert_to_mp3(path)

        self.status_label.configure(text="Download complete!", fg="green")

    def change_target(self):
        """Changes the target directory (storage location)."""
        self.target = tk.filedialog.askdirectory()
        self.dir_label.configure(text=self.clip_string("Target: " + self.target))


class FilePage(Page):
    """Page in the GUI for downloading from a file containing Youtube URLs."""

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

        self.file_label = tk.Label(self, text=self.clip_string(self.filename))
        self.file_label.grid(row=0, column=1)

        self.dir_button = tk.Button(self, command=self.change_target, text="Choose target directory")
        self.dir_button.grid(row=1, column=0, pady=20, padx=20)

        self.dir_label = tk.Label(self, text=self.clip_string(self.target))
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
        self.file_label.configure(text=self.clip_string(self.filename))

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
        invalid = 0
        not_available = 0
        self.status_label.configure(text=f"{downloaded}/{len(urls_file)} downloaded...")
        self.update()

        for url in urls_file:
            if not self.youtube_regex.match(url):
                invalid += 1
                continue

            youtube = pytube.YouTube(url)
            video = youtube.streams.first()
            if video is None:
                not_available += 1
                continue

            path = video.download(self.target)
            if self.include_video.get() == 0:
                self.convert_to_mp3(path)

            downloaded += 1
            self.status_label.configure(text=f"{downloaded}/{len(urls_file)} downloaded...")
            self.update()

        if invalid == 0 and not_available == 0:
            self.status_label.configure(text="All downloads complete!")
        else:
            self.status_label.configure(text=f"Complete, {downloaded}/{len(urls_file)} downloaded.")
            self.error_label.configure(text=f"{invalid} URL's were invalid, \n{not_available} videos were not available \nfor download.")

    def change_target(self):
        """Changes the target directory (storage location)."""
        self.target = tk.filedialog.askdirectory()
        self.dir_label.configure(text=self.clip_string(self.target))


class SpotifyPage(Page):
    """Page in the GUI for downloading from a Spotify playlist."""

    def __init__(self, *args, **kwargs):
        Page.__init__(self, *args, **kwargs)
        self.spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials())
        self.target = os.path.expanduser("~/Downloads")
        self.include_video = tk.IntVar()
        self.include_video.set(0)
        self.playlist = {}
        self.make_widgets()

    def make_widgets(self):
        """Create the widgets that make up the page and position them."""
        self.disclaimer = tk.Label(
            self,
            text="Note: this tool downloads the songs from Youtube.\n" +
                 "This will not work for every song and downloads can\n" +
                 "be different from the Spotify songs."
        )
        self.disclaimer.grid(row=0, columnspan=2)

        self.search_label = tk.Label(self, text="Search Spotify playlist:")
        self.search_label.grid(row=1, column=0, pady=20, padx=10)

        self.search_entry = tk.Entry(self, width=40)
        self.search_entry.grid(row=1, column=1)

        self.search_button = tk.Button(self, command=self.search_playlist, text="Search")
        self.search_button.grid(row=2, column=0, pady=20, padx=20)

        self.current_playlist = tk.Label(self, text="No playlist found")
        self.current_playlist.grid(row=2, column=1)

        self.dir_button = tk.Button(self, command=self.change_target, text="Choose target directory")
        self.dir_button.grid(row=3, column=0, pady=20, padx=20)

        self.dir_label = tk.Label(self, text=self.clip_string(self.target))
        self.dir_label.grid(row=3, column=1, pady=20, padx=20)

        self.video_checkbox = tk.Checkbutton(self, variable=self.include_video, onvalue=1, offvalue=0, text="Include video")
        self.video_checkbox.grid(row=4, column=0, pady=20, padx=20)

        self.submit_button = tk.Button(self, command=self.download, text="Download")
        self.submit_button.grid(row=4, column=1)

        self.error_label = tk.Label(self, text="", fg="red")
        self.error_label.grid(row=5, column=0, pady=20, padx=10)

        self.status_label = tk.Label(self, text="", fg="green")
        self.status_label.grid(row=5, column=1, pady=20, padx=10)

    def search_playlist(self):
        """Search for a Spotify playlist and display the name of the first match."""
        term = self.search_entry.get()
        if (term == ''):
            self.current_playlist.configure(text='No playlist found')
            self.playlist = {}
            return

        result = self.spotify.search(q=term, type='playlist', limit=1)

        if len(result['playlists']['items']) == 0:
            self.current_playlist.configure(text='No playlist found')
            self.playlist = {}
            return

        self.playlist = result['playlists']['items'][0]
        self.current_playlist.configure(text=self.clip_string(self.playlist['owner']['display_name'] + ' - ' + self.playlist['name']))

    def get_tracks(self, offset):
        """
        Get the next 100 tracks from the selected
        playlist, starting from the offset.
        """
        if self.playlist == {}:
            return

        return self.spotify.playlist_items(
            self.playlist['id'],
            fields=('items(track(name,artists(name))),next'),
            limit=100,
            offset=offset,
            additional_types=('track',)
        )

    def is_valid(self):
        """Check for possible errors before starting the download."""
        if self.playlist == {}:
            self.error_label.configure(text="Please search a playlist first.")
            self.update()
            return False

        length = self.playlist['tracks']['total']
        if (length > 1000):
            self.error_label.configure(text="The playlist cannot be \nlonger than 1000 songs.")
            self.update()
            return False

        return True

    def download(self):
        """
        Tries to find all songs from the selected Spotify
        playlist on Youtube and downloads them.

        Stores videos in target location as mp4 or converts to mp3.
        """
        if not self.is_valid():
            return

        self.error_label.configure(text="")
        self.update()

        length = self.playlist['tracks']['total']

        offset = 0  # Spotify API is paginated, so we remember the offset
        tracks = self.get_tracks(offset)

        downloaded = 0
        not_found = 0
        self.status_label.configure(text=f"{downloaded}/{length} downloaded...")
        self.update()

        while True:  # Loop over pages of Spotify API
            for track in tracks['items']:
                yt = YouTubeDataAPI(os.environ.get('YOUTUBE_API_KEY'))
                artist = track['track']['artists'][0]['name']
                track_name = track['track']['name']
                searches = yt.search(q=f'{artist} {track_name}', max_results=5)
                video = None
                for result in searches:  # Look for first downloadable video in top 5 results
                    video_title = unquote(result['video_title'].lower())  # Decode URL encoding
                    if track_name.lower() not in video_title and not any(map(video_title.__contains__, ['ft', 'feat'])):
                        continue  # Try to filter irrelevant search results

                    video_id = result['video_id']
                    youtube = pytube.YouTube(f'https://www.youtube.com/watch?v={video_id}')
                    video = youtube.streams.first()
                    if video:
                        break

                if video is None:
                    not_found += 1
                    continue

                path = video.download(self.target)
                if self.include_video.get() == 0:
                    self.convert_to_mp3(path)

                downloaded += 1
                self.status_label.configure(text=f"{downloaded}/{length} downloaded...")
                self.update()

            offset += 100  # Increase offset and retrieve next page if it exists
            if offset < length and tracks['next']:
                tracks = self.get_tracks(offset)
            else:
                break

        if not_found == 0:
            self.status_label.configure(text="All downloads complete!")
        else:
            self.status_label.configure(text=f"Complete, {downloaded}/{length} downloaded.")

    def change_target(self):
        """Changes the target directory (storage location)."""
        self.target = tk.filedialog.askdirectory()
        self.dir_label.configure(text=self.clip_string(self.target))


class YoutubeDownloader(tk.Frame):
    """Main frame for the GUI, contains the two pages and navigation buttons."""

    def __init__(self, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)

        self.winfo_toplevel().title("Youtube Downloader")

        self.p1 = SingleUrlPage(self)
        self.p2 = FilePage(self)
        self.p3 = SpotifyPage(self)

        self.buttonframe = tk.Frame(self)
        self.container = tk.Frame(self)
        self.buttonframe.pack(side="top", fill="x", expand=False)
        self.container.pack(side="top", fill="both", expand=True)

        self.p1.place(in_=self.container, x=0, y=0, relwidth=1, relheight=1)
        self.p2.place(in_=self.container, x=0, y=0, relwidth=1, relheight=1)
        self.p3.place(in_=self.container, x=0, y=0, relwidth=1, relheight=1)

        self.b1 = tk.Button(self.buttonframe, text="Single url", command=self.p1.lift)
        self.b2 = tk.Button(self.buttonframe, text="From file", command=self.p2.lift)
        self.b3 = tk.Button(self.buttonframe, text="From Spotify", command=self.p3.lift)

        self.b1.pack(side="left")
        self.b2.pack(side="left")
        self.b3.pack(side="left")
        self.p1.show()


if __name__ == "__main__":
    root = tk.Tk()
    downloader = YoutubeDownloader(root)
    downloader.pack(side="top", fill="both", expand=True)
    root.wm_geometry("650x450")
    root.mainloop()
