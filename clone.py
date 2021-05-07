import sys
import os
import ssl
import re
import socks
import socket
import string
from urllib.request import Request, urlopen
from urllib.parse import quote, urlparse


def get(url):
    IP_ADDR = '127.0.0.1'
    PORT = 9050

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    request = Request(url)
    socks.set_default_proxy(socks.SOCKS5, IP_ADDR, PORT)
    socket.socket = socks.socksocket

    return  urlopen(request, context=ctx)

def extractUrl(url):
    url_parse = urlparse(url)

    return url_parse[0] + "://" + url_parse[1] + url_parse[2]

#  build the path by removing extra // and resolving relative path
#  ex: abc//def = abc/def
#  and abc/def/../ghi = abc/ghi
def resolvePath(path):
    temp_path = re.sub("\/\.\/|\/+", "/", "/".join(path))

    while True:
        path = temp_path
        temp_path = re.sub("(^|\/)(?!\.?\.\/)([^\/]+)\/\.\.\/*", "/", temp_path)

        if path == temp_path:
            break


    #  check if the path containes http or https protocol, if yes, then replace the 
    #  "/" removed from the pretocol while resolving it
    prefix = re.match("http:\/|https:\/", temp_path)

    if prefix:
        prefix = prefix.group(0)
        temp_path = temp_path.replace(prefix, prefix + "/")

    return temp_path


def resources(content, reg):
    items = []
    regex = reg + "([^=\"'(\s]+)" + str("(" + "|".join(dataTypesToDownload) + ")").replace(".", "\.") + "([^\"')>\s]*)"

    for match in re.findall(regex, content):

        if((match[2] and match[2].startswith("?")) or match[2] == ''): 
           items.append(''.join(match))

    return items


def replace(from_dir, content, reg = ""):
    for resource in resources(content, reg):
        
        if download(from_dir, resource):
            path = downloadedFiles[-1].replace(base_path, "")
            content = content.replace(resource, resolvePath(["/", path]))

    return content


def write(dContent, download_path):
    item_path = download_path.split("/")[:-1]
    
    trail = "./"

    for folder in item_path:
        trail += folder + "/"
        try:
            os.mkdir(trail)
        except OSError:
            pass	
    
    download = open(download_path, "wb")

    for chunk in dContent:
        download.write(chunk)

    download.close()


def download(from_dir, item):
    global downloadedFiles

    external = False
    prefix = ""

    while item.startswith("/"):
        item = item[1:]

    if item.startswith("."):
        item = resolvePath([from_dir, item])

    if item.startswith(url):
        item = item.replace(url, "")

    if item.startswith(domain):
        item = item.replace(domain, "")

    if item.startswith(("http://", "https://")):
        external = True
        prefix = re.match("http:\/\/|https:\/\/", item).group(0)
        item = re.sub("http:\/\/|https:\/\/", "", item)

    download_path = resolvePath([base_path, urlparse(item)[2]])

    #  If the element is already downloaded make downloaded flag true  and move to the 
    #  end of the list so that the content can be overwritten with the correct path
    if download_path in downloadedFiles:
        index = downloadedFiles.index(download_path)
        downloadedFiles.append(downloadedFiles.pop(index))
        downloadUrls.append(downloadUrls.pop(index))
        return True

    if external:
        d_url = resolvePath([prefix, item])

    else:
        d_url = resolvePath([url, item])

    print("Downloading {} to {}".format(d_url, download_path))

    try:
        dContent = get(quote(d_url, safe=string.printable))
        write(dContent, download_path)
        downloadedFiles.append(download_path)
        downloadUrls.append(d_url)
        print("Downloaded!")
        return True

    except Exception as e:
        print("An error occured: " + str(e.reason))
        return False


downloadedFiles = []
downloadUrls = []
dataTypesToDownload = [".svg", ".jpg", ".jpeg", ".png", ".gif", ".ico", ".css", ".js", ".html", ".php", ".json", ".ttf", ".otf", ".woff2", ".woff", ".eot", ".mp4"]
textFiles = ["css", "js", "html", "php", "json"]

if len(sys.argv) == 1:
    url = input("URL of site to clone: ")
else:
    if sys.argv[1] == "-h":
        print("Usage: {} [url] [directory]".format(sys.argv[0]))
        exit()
    url = sys.argv[1]

if len(sys.argv) <= 2:
    base_path = input("Directory to clone into: ")
else:
    base_path = sys.argv[2]

if "http://" not in url and "https://" not in url:
    url = "http://" + url


frag = url.replace(extractUrl(url), "")
url = extractUrl(url)
domain = urlparse(url)[1]

response = get(url + frag)
content = replace(base_path, response.read().decode('utf-8'))

path = resolvePath([base_path, "index.html"])
file = open(path, "w")
file.write(content)
file.close()


downloadedFiles.append(path)
downloadUrls.append(url)

print('Scanning for CSS based url(x) references...')

for subdir, dirs, files in os.walk(base_path):
    for file in files:
            
        if file == ".DS_Store" or file.split(".")[-1] not in textFiles:
            continue

        file = os.path.join(subdir, file)
        f = open(file, 'r+')
        
        print("Scanning  File " + f.name)

        d_url = urlparse(downloadUrls[downloadedFiles.index(file)])
        from_dir = d_url[0] + "://" + d_url[1] + "/".join(d_url[2].split("/")[:-1]) 
        content = replace(from_dir, f.read(), "url\s*\(['\"]*")

        f.seek(0)
        f.truncate()
        f.write(content)
        f.close()


print("Cloned " + url + " !")
