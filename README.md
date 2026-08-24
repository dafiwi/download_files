# Download Files

This Python script downloads all files (including subdirectories and their files) from a web server.
It supports HTTP Basic Authentication. 
The script was tested successfully with Linux and an Apache Server.

## ⚠️ Important Disclaimer

**USE AT YOUR OWN RISK!**

This Python script is provided "as is" without any warranties or guarantees.

- The author is **not responsible** for any data loss, file corruption, or other damages caused by using this script.
- The script will not work if the web server URL is not correct.

By using this script, you agree to assume all risks and indemnify the author from any claims.

## Notes

Start the script (see Requirements) and enter or paste the URL to the web server or cloud storage where you want to download your files from.
If the web server needs Basic HTTP Authentication you have to enter the correct username and password.
Then you have to enter the name of the target directory inside your Downloads directory.

If the download is not possible you will get a status message like "other" (other authentication method) or "forbidden".

## Tech Stack
- Python 3.10+
- Libraries: bs4, getpass, pathlib, requests, time, urllib.parse

## Installation
### Requirements
- Python 3.10 or higher.

git clone https://github.com/dafiwi/download_files.git

cd path/to/script-directory

pip install -r requirements.txt

chmod +x download_files.py
./download_files.py

OR

python3 download_files.py

OR

python download_files.py

## License
This project is licensed under the MIT License. See [LICENSE](LICENSE). Copyright (c) dafiwi/2026 (https://github.com/dafiwi/download_files).