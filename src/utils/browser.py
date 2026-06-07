import os
import webbrowser

def open_url(url: str) -> None:
    old_ld_path = os.environ.get("LD_LIBRARY_PATH")
    
    if "LD_LIBRARY_PATH_ORIG" in os.environ:
        os.environ["LD_LIBRARY_PATH"] = os.environ["LD_LIBRARY_PATH_ORIG"]
    else:
        os.environ.pop("LD_LIBRARY_PATH", None)
    
    try:
        webbrowser.open(url)
    finally:
        if old_ld_path is not None:
            os.environ["LD_LIBRARY_PATH"] = old_ld_path