import requests, json

from mclauncher_core.launcher_funcs import get_version_manifest


def get_version_json(version, bmclapi=False) -> dict:
    """获取当前Minecraft版本的json，返回dict"""
    manifest = get_version_manifest()
    for current in manifest["versions"]:
        if current['id'] == version:
            raw = requests.get(current['url'])
            if raw.status_code != 200:
                raise Exception(f"Request Fail: {raw.status_code}\nurl: {current['url']}")
            return json.loads(raw.text)
    raise NameError("version not found")
