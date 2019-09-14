import json
from multiprocessing.pool import ThreadPool
import re
import shutil
import time

import pandas as pd
import requests

class AssetNotFoundError(Exception):
    """ Exception for when asset information is not found on a page. """
    pass

class Video(object):
    """ Video object that can identify and download its associated
    Wistia-hosted video file.
    
    Raises:
        AssetNotFoundError: if a video with the associated parameters
            is not found in the queried asset list.
    """
    baseaddr = 'http://fast.wistia.net/embed/iframe/'

    def __init__(self, vid_name=None, vid_id=None, resolution='1080p', container='mp4'):
        self.srcpage = Video.baseaddr + vid_id
        self.vid_name = vid_name if isinstance(vid_name, str) else None
        self.assets = None
        self.vidurl = None
        self.resolution = resolution if resolution in {'224p','360p','720p','1080p','4k'} else '1080p'
        self.container = container if container in {'mp4',} else 'mp4'
    
    def get_assets(self):
        """ Parse video blob list from assets source.

        Raises:
            AssetNotFoundError : if a video with the associated parameters
            is not found in the queried asset list.
        
        Returns:
            DataFrame : pandas dataframe containing asset (video) information
        """
        findstr = r'W\.iframeInit\({"assets":(\[.*\])'
        try:
            page = str(requests.get(self.srcpage).content, 'utf-8')
            asset_search = re.search(findstr, page)
            if asset_search:
                assets = asset_search.group(1)
                try:
                    assets = json.loads(assets)
                except ValueError:
                    print("Error loading JSON string")
                self.assets = pd.DataFrame(assets)
                return self.assets
            else:
                raise AssetNotFoundError
        except:
            print("Failed to get asset information from page.\nCheck video ID.")
    
    def get_vidurl(self):
        """ Get the appropriate video URL.
        
        Returns:
            str : the video URL
        """
        if self.assets is None:
            self.get_assets()
            
        df = self.assets
        des = df.loc[(df['container']==self.container) & (df['display_name']==self.resolution), 'url']
        if des.shape[0] == 1:
            self.vidurl = des.iloc[0].replace('.bin',f'.{self.container}')
        return self.vidurl

    def download(self):
        """ Download the video.
        
        Returns:
            str : the video URL that was downloaded
        """
        # If we don't know the video url yet, run that step.
        if self.vidurl is None:
            self.get_vidurl()
        
        # If there's no video name provided, use the original video url
        if self.vid_name is None:
            path = self.vidurl.rpartition('/')[2]
        else:
            path = self.vid_name + f'.{self.container}'
        
        # Download the video stream into a binary file
        try:
            r = requests.get(self.vidurl, stream=True)
        except:
            print(f"Error downloading {self.vid_name}")
            return None
        if r.status_code == 200:
            with open(path, 'wb') as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)
        return self.vidurl

def download_vid(item):
    """Download a video based on the name and id provided.
    
    Arguments:
        item : Tuple(str,str) : The video name (desired base filename) and
            video id (used for downloading) associted with a given video.
    """
    vid_name, vid_id = item
    vid = Video(vid_name, vid_id, resolution='224p')
    vid.download()

if __name__ == '__main__':
    vid_ids = pd.read_csv('vid_ids.csv',comment='#', header=0)
    ids = [tuple(v) for v in vid_ids[['Video_Title','vid_id']].values]
    start = time.time()
    results = ThreadPool(14).imap_unordered(download_vid, ids)
    for url in results:
        print(url)
    end = time.time()
    print(f"Total time = {end-start:.02f} seconds")