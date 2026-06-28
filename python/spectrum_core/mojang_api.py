import requests


def get_skin_and_cape(uuid=str):
    """
    Get skin and cape texture from mojang server.
    Return:
    {
        "skin_url": str,
        "cape_url": str,
        "slim": bool
    }
    """
    url = f"https://sessionserver.mojang.com/session/minecraft/profile/{uuid}"
    response = requests.get(url)
    return_dict = {"skin_url": None, "cape_url": None, "slim": False}
    if response.status_code == 200:
        data = response.json()
        textures = data.get("properties", []).get("value", []).get("textures", {})
    
    for texture in textures:
        if texture.get("type") == "SKIN":
            skin_url = texture.get("url")
            return_dict['skin_url'] = skin_url
            return_dict['slim'] = texture.get("metadata", {}).get("model") == "slim"

        elif texture.get("type") == "CAPE":
            cape_url = texture.get("url")
            return_dict['cape_url'] = cape_url

    return return_dict