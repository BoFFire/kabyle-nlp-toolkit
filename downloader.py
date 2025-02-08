# downloader.py
import os
import requests

def get_remote_file_size(url):
    """Return the remote file size (in bytes) using a HEAD request."""
    response = requests.head(url)
    response.raise_for_status()
    return int(response.headers.get('Content-Length', 0))

def download_file(url, filename):
    """
    Download a file from URL to filename if it doesn't exist
    or its size does not match the remote file size.
    """
    remote_size = get_remote_file_size(url)
    if os.path.exists(filename):
        local_size = os.path.getsize(filename)
        if local_size == remote_size:
            print(f"{filename} already exists (size: {local_size} bytes), skipping download.")
            return
        else:
            print(f"{filename} exists but size differs (local: {local_size}, remote: {remote_size}). Re-downloading.")
    else:
        print(f"Downloading {filename} from {url} ...")
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(filename, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    print(f"Downloaded {filename}.")
