import requests, json

from spectrum_core.py_fallback.launcher_funcs import get_version_manifest


def get_version_json(mcversion, bmclapi=False) -> dict:
    """获取当前Minecraft版本的json，返回dict"""
    manifest = get_version_manifest()
    for current in manifest["versions"]:
        if current['id'] == mcversion:
            raw = requests.get(current['url'])
            if raw.status_code != 200:
                raise Exception(f"Request Fail: {raw.status_code}\nurl: {current['url']}")
            return json.loads(raw.text)
    raise NameError("version not found")
