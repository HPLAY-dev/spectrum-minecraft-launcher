import requests


def download_javawrapper() -> None:
    # url = 'https://github.com/00ll00/java_launch_wrapper/releases/download/v1.4.4/java_launch_wrapper-1.4.4.jar'
    url = 'https://gitlab.com/HPLAY-dev/javawrapper-binary/-/raw/main/JavaWrapper.jar?inline=false'
    obj = requests.get(url)
    if obj.status_code != 200:
        raise Exception('Connection error while downloading javawrapper')
    else:
        with open('JavaWrapper.jar', 'wb') as f:
            f.write(obj.content)