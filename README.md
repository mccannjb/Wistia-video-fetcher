# Wistia-video-fetcher
Python script to download Wistia-hosted videos.

Method
------
To download videos...
- right-click the video you're watching and select "Copy link and thumbnail"
- paste the copied text into a text editor
- find the video code (eg. 'wvideo=a1b2c3d4e5') and copy the code portion
- insert the video name (custom) and copied video code for each video you wish to download into `vid_ids.csv`
- set the desired resolution in the download.py script
- run download.py
    Downloaded files will be saved into the current directory.
