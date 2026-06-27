import os
import json
import requests


releaseType = 'production'
api_base = 'https://releases.r2.labymod.net/api/v1/'
manifest_url = 'manifest/${channel}/latest.json'
channel_url = 'channels.json'
libraries_url = 'libraries/{releaseType}.json'
download_neo_url = 'download/labymod4/${releaseType}/${commitReference}.jar'
# https://releases.r2.labymod.net/api/v1/libraries/production.json

def downloadFile(url, path):
    print(f'\tDownloading\n\t--{url}\n\t--{path}')
    os.makedirs(parent(path), exist_ok=True)
    response = requests.get(url)
    with open(path, 'wb') as file:
        file.write(response.content)

def parent(path):
    return '/'.join(path.split('/')[:-1])

def getUrl(path):
    return api_base + path

def getManifestNeo(releaseType, token=None, manifest_url=manifest_url):
    manifest_url = manifest_url.replace('${channel}', releaseType)
    manifest = requests.get(getUrl(manifest_url)).json()
    return manifest

def getLibraryApi(releaseType, token=None, libraries_url=libraries_url):
    libraryApi = requests.get(getUrl(libraries_url).replace('{releaseType}', releaseType)).json()
    return libraryApi

def downloadJar(releaseType, commitReference, path, token=None, download_neo_url=download_neo_url):
    # path = f'{minecraftDirectory}/net/labymod/LabyMod/{version}' + 'LabyMod-{version}.jar'removed
    url = getUrl(download_neo_url).replace('${releaseType}', releaseType).replace('${commitReference}', commitReference)
    downloadFile(url, path)
    # check with sha1 from manifest['sha1'] todo

def installJava17(profileId, libraries, labyModVersion, labyModVersionType, commitReference, customManifestUrl, releaseType, sha1):
    version = requests.get(customManifestUrl).json()
    version['id'] = profileId
    version['libraries'].append({
        'name': "net.labymod:LabyMod:4",
        'url': f'https://releases.r2.labymod.net/api/v1/download/labymod4/{releaseType}/{commitReference}.jar',
        'sha1': sha1
    })
    version['libraries'].extend(libraries)

    # labyModData
    labyModData = {
        'channelType': releaseType,
        'version': labyModVersion,
        'versionType': labyModVersionType,
        'commitReference': commitReference
    }
    version['labymod_data'] = labyModData
    return version

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
    # version should be 4...
    print('Get Manifest')
    manifest = getManifestNeo(releaseType=releaseType)
    print('Get LibraryAPI')
    commitReference = manifest['commitReference']
    libraryApi = getLibraryApi("production")

    # Download Libraries
    for lib in libraryApi['libraries']:
        # Get Informations
        minecraftVersion = lib['minecraftVersion']
        if not lib['url'].startswith('https://releases.r2.labymod.net/'):
            raise Exception('Unsupported library url: ' + json.dumps(lib))
        path = lib['url'].removeprefix('https://releases.r2.labymod.net/')

        # Download
        print('LIB:'+lib['url']+'\t'+f'{minecraftDirectory}/{path}')
        path = f'{minecraftDirectory}/{path}'
        if not os.path.exists(path):
            downloadFile(lib['url'], path)
        # Check sha1 todo

    # Download LabyMod Jar
    print('Downloading LabyMod Jar')
    path = f'{minecraftDirectory}/libraries/net/labymod/LabyMod/{version}/LabyMod-{version}.jar'
    if not os.path.exists(path):
        downloadJar("production", commitReference, path)
    
    # Download Shader & misc
    def download_misc(name, minecraftDirectory, instance_name, manifest, commitReference, releaseType):
        path = f'{minecraftDirectory}/versions/{instance_name}/labymod-neo/assets/{name}.jar'
        url = f'{api_base}download/assets/labymod4/{releaseType}/{commitReference}/{name}/{manifest["assets"][name]}.jar'
        if not os.path.exists(path):
            downloadFile(url, path)
    
    # Get Misc Things to download
    miscs = []
    for k, v in manifest['assets'].items():
        miscs.append(k)

    for name in miscs:
        print('Downloading '+name)
        download_misc(name, minecraftDirectory, instance_name, manifest, commitReference, releaseType)
    
    # Finally, Download version
    # select the version
    print('Retrieving Version JSON')
    for i in manifest['minecraftVersions']:
        if i['version'] == mcversion:
            ver = i
            break
    isJava17Era = "customManifestUrl" in ver
    profileId = "LabyMod-4-" + commitReference
    libraries = libraryApi['libraries']
    labyModVersion = manifest['labyModVersion']
    labyModVersionType = ver['type']
    if isJava17Era:
        manifest = installJava17(profileId, libraries, labyModVersion, labyModVersionType, commitReference, ver['customManifestUrl'], releaseType, sha1=manifest['sha1'])
    else:
        manifest = installLegacy(profileId, libraries, labyModVersion, labyModVersionType, commitReference, mcversion)
    
    os.makedirs(f'{minecraftDirectory}/versions/{instance_name}', exist_ok=True)
    with open(minecraftDirectory+f'/versions/{instance_name}/{instance_name}.json', 'w') as f:
        f.write(json.dumps(manifest))
    print('LabyMod FINISH')