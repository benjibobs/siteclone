# siteclone
A python script to clone a webpage. It's that simple.

# Setup:

`git clone https://github.com/benjibobs/siteclone.git`

`pip install -r requirements.txt`

# Usage:

`python3 clone.py <url> <directory>`

The url argument is optional, the script will ask for a url if one is not provided.

The directory is optional, the script will ask for a directory name where to clone the site if one is not provided.

Relative paths containing with '../' are replaced with 'dotdot/' to prevent directory traversal/sandbox escape/whatever you want to classify it as :)
