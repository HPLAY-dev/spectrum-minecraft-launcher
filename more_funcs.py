import requests
import json
from mclauncher_core.download_funcs import is_library_required, get_version_list
from mclauncher_core.launcher_funcs import get_assetIndex_json
import sys
# sys.path.append('..')


from mclauncher_core.manifest_funcs import get_version_json

def get_version_size(mcversion, splited=False):
    version_json = get_version_json(mcversion)
    libraries = version_json.get('libraries', [])
    assets_size = version_json.get('assetIndex', {'totalSize': 0}).get('totalSize', 0)
    client_size = version_json.get('downloads', {}).get('client', {'size': 0}).get('size', 0)
    libraries_size = 0
    for lib in libraries:
        # if is_library_required(lib):
        lib_size = lib.get('downloads', {'artifact': {'size': 0}}).get('artifact', {'size': 0}).get('size')
        libraries_size += lib_size

    total_size = assets_size + client_size + libraries_size
    return (assets_size, client_size, libraries_size, total_size) if splited else total_size

def get_all_sizes(start_with=None, current_size=0, current_hash_ast=[], current_sha1_lib=[]):
    versions = get_version_list()
    if start_with:
        start_index = versions.index(start_with)
        versions = versions[start_index:]
    total_size = current_size
    recorded_hash_ast = current_hash_ast.copy()
    recorded_sha1_lib = current_sha1_lib.copy()
    for v in versions:
        version_json = get_version_json(v)
        assetIndex = get_assetIndex_json(version_json=version_json)
        libraries = version_json.get('libraries', [])
        assets_size = version_json.get('assetIndex', {'totalSize': 0}).get('totalSize', 0)
        client_size = version_json.get('downloads', {}).get('client', {'size': 0}).get('size', 0)
        libraries_size = 0
        for lib in libraries:
            # if is_library_required(lib):
            if 'classifiers' in lib['downloads']:
                for i in lib['downloads']['classifiers']:
                    if lib['downloads']['classifiers'][i]['sha1'] in recorded_sha1_lib:
                        continue
                    lib_size = lib.get('downloads', {'classifiers': {i: {'size': 0}}}).get('classifiers', {i: {'size': 0}}).get(i, {'size': 0}).get('size')
                    libraries_size += lib_size
                    recorded_sha1_lib.append(lib['downloads']['classifiers'][i]['sha1'])
                continue
            if lib['downloads']['artifact']['sha1'] in recorded_sha1_lib:
                continue
            lib_size = lib.get('downloads', {'artifact': {'size': 0}}).get('artifact', {'size': 0}).get('size')
            libraries_size += lib_size
            recorded_sha1_lib.append(lib['downloads']['artifact']['sha1'])
        
        assets_size = 0
        for i in assetIndex['objects']:
            if assetIndex['objects'][i]['hash'] in recorded_hash_ast:
                continue
            asset_size = assetIndex['objects'][i]['size']
            assets_size += asset_size
            recorded_hash_ast.append(assetIndex['objects'][i]['hash'])
        size = assets_size + client_size + libraries_size
        total_size += size
        print(str(v)+'\n'+str(total_size/1048576)+' MB\n')

print(get_all_sizes())