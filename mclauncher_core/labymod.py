import os
import json
import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

releaseType = 'production'
api_base = 'https://releases.r2.labymod.net/api/v1/'
manifest_url = 'manifest/${channel}/latest.json'
channel_url = 'channels.json'
libraries_url = 'libraries/{releaseType}.json'
download_neo_url = 'download/labymod4/${releaseType}/${commitReference}.jar'
# https://releases.r2.labymod.net/api/v1/libraries/production.json

_DEFAULT_TIMEOUT = (30, 300)
_RETRYABLE = (
    requests.exceptions.SSLError,
    requests.exceptions.ConnectionError,
    requests.exceptions.ChunkedEncodingError,
    requests.exceptions.Timeout,
)


def _make_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def _http_get_json(url: str) -> dict:
    session = _make_session()
    last_err = None
    for attempt in range(1, 6):
        try:
            resp = session.get(url, timeout=_DEFAULT_TIMEOUT)
            resp.raise_for_status()
            return resp.json()
        except _RETRYABLE as e:
            last_err = e
            if attempt < 5:
                wait = min(2 ** attempt, 30)
                print(f'Retry {attempt}/5 after {wait}s: {e}')
                time.sleep(wait)
                continue
            raise
    raise last_err  # pragma: no cover


def downloadFile(url, path, retries=5):
    path = os.path.normpath(path)
    print(f'\tDownloading\n\t--{url}\n\t--{path}')
    os.makedirs(parent(path), exist_ok=True)
    session = _make_session()
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            with session.get(url, timeout=_DEFAULT_TIMEOUT, stream=True) as response:
                response.raise_for_status()
                tmp_path = path + '.part'
                with open(tmp_path, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=65536):
                        if chunk:
                            file.write(chunk)
                os.replace(tmp_path, path)
            return
        except _RETRYABLE as e:
            last_err = e
            for suffix in (path + '.part', path):
                if os.path.exists(suffix):
                    try:
                        os.remove(suffix)
                    except OSError:
                        pass
            if attempt < retries:
                wait = min(2 ** attempt, 30)
                print(f'\tRetry {attempt}/{retries} after {wait}s: {e}')
                time.sleep(wait)
                continue
            raise
    if last_err:
        raise last_err

def parent(path):
    return os.path.dirname(os.path.normpath(path.replace('/', os.sep)))


def _join_mc_dir(minecraft_directory, *parts):
    return os.path.normpath(os.path.join(minecraft_directory, *parts))


def _filter_libraries(libraries, mcversion):
    """仅保留与目标 MC 版本相关的 LabyMod 库。"""
    matched = []
    for lib in libraries:
        lib_mc = lib.get('minecraftVersion')
        if lib_mc is None or lib_mc == 'all' or lib_mc == mcversion:
            matched.append(lib)
    return matched


def _api_library_to_minecraft(lib):
    """将 LabyMod API 库条目转为 version.json 可用的 library 结构。"""
    url = lib['url']
    rel = url.removeprefix('https://releases.r2.labymod.net/')
    entry = {'name': lib['name']}
    if lib.get('sha1'):
        entry['downloads'] = {
            'artifact': {
                'path': rel,
                'sha1': lib['sha1'],
                'size': lib.get('size', 0),
                'url': url,
            }
        }
    return entry

def getUrl(path):
    return api_base + path

def getManifestNeo(releaseType, token=None, manifest_url=manifest_url):
    manifest_url = manifest_url.replace('${channel}', releaseType)
    return _http_get_json(getUrl(manifest_url))

def getLibraryApi(releaseType, token=None, libraries_url=libraries_url):
    return _http_get_json(getUrl(libraries_url).replace('{releaseType}', releaseType))

def downloadJar(releaseType, commitReference, path, token=None, download_neo_url=download_neo_url):
    # path = f'{minecraftDirectory}/net/labymod/LabyMod/{version}' + 'LabyMod-{version}.jar'removed
    url = getUrl(download_neo_url).replace('${releaseType}', releaseType).replace('${commitReference}', commitReference)
    downloadFile(url, path)
    # check with sha1 from manifest['sha1'] todo

def installJava17(profileId, libraries, labyModVersion, labyModVersionType, commitReference, customManifestUrl, releaseType, sha1):
    version = _http_get_json(customManifestUrl)
    version['id'] = profileId
    lm_url = f'https://releases.r2.labymod.net/api/v1/download/labymod4/{releaseType}/{commitReference}.jar'
    version['libraries'].append({
        'name': 'net.labymod:LabyMod:4',
        'downloads': {
            'artifact': {
                'path': 'libraries/net/labymod/LabyMod/4/LabyMod-4.jar',
                'sha1': sha1,
                'url': lm_url,
            }
        },
    })
    version['libraries'].extend(_api_library_to_minecraft(lib) for lib in libraries)

    # labyModData
    labyModData = {
        'channelType': releaseType,
        'version': labyModVersion,
        'versionType': labyModVersionType,
        'commitReference': commitReference,
        'minecraftVersion': None,  # 由 download() 填入
    }
    version['labymod_data'] = labyModData
    return version


def sync_libraries(minecraftDirectory, mcversion):
    """补全缺失的 LabyMod 依赖库（含 launchwrapper），可重复调用。"""
    minecraftDirectory = os.path.abspath(os.path.expanduser(minecraftDirectory))
    libraryApi = getLibraryApi("production")
    libraries = _filter_libraries(libraryApi['libraries'], mcversion)
    for lib in libraries:
        if not lib['url'].startswith('https://releases.r2.labymod.net/'):
            continue
        rel_path = lib['url'].removeprefix('https://releases.r2.labymod.net/')
        path = _join_mc_dir(minecraftDirectory, rel_path)
        if not os.path.exists(path):
            print('SYNC LIB:' + lib['url'])
            downloadFile(lib['url'], path)

def installLegacy(*kargs, **kwargs):
    raise NotImplementedError()

# API start
def get_versions():
    versions = []
    manifest = getManifestNeo(releaseType=releaseType)
    for i in manifest['minecraftVersions']:
        versions.append(i['version'])
    return versions
    

def download(minecraftDirectory, version, mcversion: str, instance_name):
    minecraftDirectory = os.path.abspath(os.path.expanduser(minecraftDirectory))
    if not os.path.isdir(minecraftDirectory):
        os.makedirs(minecraftDirectory, exist_ok=True)

    print('Get Manifest')
    manifest = getManifestNeo(releaseType=releaseType)
    print('Get LibraryAPI')
    commitReference = manifest['commitReference']
    libraryApi = getLibraryApi("production")

    ver = None
    for i in manifest['minecraftVersions']:
        if i['version'] == mcversion:
            ver = i
            break
    if ver is None:
        raise ValueError(f'LabyMod 不支持 Minecraft 版本: {mcversion}')

    libraries = _filter_libraries(libraryApi['libraries'], mcversion)

    # Download Libraries (仅当前 MC 版本)
    for lib in libraries:
        if not lib['url'].startswith('https://releases.r2.labymod.net/'):
            raise Exception('Unsupported library url: ' + json.dumps(lib))
        rel_path = lib['url'].removeprefix('https://releases.r2.labymod.net/')
        path = _join_mc_dir(minecraftDirectory, rel_path)
        print('LIB:' + lib['url'] + '\t' + path)
        if not os.path.exists(path):
            downloadFile(lib['url'], path)

    # Download LabyMod Jar
    print('Downloading LabyMod Jar')
    path = _join_mc_dir(
        minecraftDirectory,
        'libraries', 'net', 'labymod', 'LabyMod', str(version),
        f'LabyMod-{version}.jar',
    )
    if not os.path.exists(path):
        downloadJar("production", commitReference, path)

    # Download Shader & misc
    def download_misc(name, manifest, commitReference, releaseType):
        asset_path = _join_mc_dir(
            minecraftDirectory,
            'versions', instance_name, 'labymod-neo', 'assets', f'{name}.jar',
        )
        url = (
            f'{api_base}download/assets/labymod4/{releaseType}/'
            f'{commitReference}/{name}/{manifest["assets"][name]}.jar'
        )
        if not os.path.exists(asset_path):
            downloadFile(url, asset_path)

    for name in manifest['assets']:
        print('Downloading ' + name)
        download_misc(name, manifest, commitReference, releaseType)

    # Build version JSON
    print('Retrieving Version JSON')
    isJava17Era = "customManifestUrl" in ver
    profileId = "LabyMod-4-" + commitReference
    labyModVersion = manifest['labyModVersion']
    labyModVersionType = ver['type']
    if isJava17Era:
        version_json = installJava17(
            profileId, libraries, labyModVersion, labyModVersionType,
            commitReference, ver['customManifestUrl'], releaseType,
            sha1=manifest['sha1'],
        )
        version_json['labymod_data']['minecraftVersion'] = mcversion
    else:
        manifest = installLegacy(
            profileId, libraries, labyModVersion, labyModVersionType,
            commitReference, mcversion,
        )
        version_json = manifest

    instance_dir = _join_mc_dir(minecraftDirectory, 'versions', instance_name)
    os.makedirs(instance_dir, exist_ok=True)
    json_path = _join_mc_dir(instance_dir, f'{instance_name}.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(version_json))
    print('LabyMod FINISH')