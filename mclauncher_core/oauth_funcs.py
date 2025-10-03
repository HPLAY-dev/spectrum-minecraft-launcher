import requests, json
import mclauncher_core.oauth_server as oauth

# OAuth
client_id = "7000942a-0525-4e21-a817-faf950ab6bc4"


def code_to_token(auth_code: str, redirect_uri=oauth.redirect_uri):
    token_url = 'https://login.microsoftonline.com/consumers/oauth2/v2.0/token'
    token_data = {
        'client_id': client_id,
        'code': auth_code,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code',
        'scope': 'XboxLive.signin offline_access'
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json'
    }
    response = requests.post(token_url, data=token_data, headers=headers)
    return response.json()


def refresh_token(refresh_token: str):
    url = 'https://login.microsoftonline.com/consumers/oauth2/v2.0/token'
    token_data = {
        {"client_id", client_id},
        {"scope", "XboxLive.signin XboxLive.offline_access"},
        {"refresh_token", refresh_token},
        {"grant_type", "refresh_token"}
    }
    response = requests.post(url, data=token_data)
    return response.json()


def access_token_to_xbl(access_token: str):
    url = 'https://user.auth.xboxlive.com/user/authenticate'
    data = {
        "Properties": {
            "AuthMethod": "RPS",
            "SiteName": "user.auth.xboxlive.com",
            "RpsTicket": f"d={access_token}"  # 确保有 d= 前缀
        },
        "RelyingParty": "http://auth.xboxlive.com",  # 使用 http 而不是 https
        "TokenType": "JWT"
    }
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    # 添加详细的调试信息
    print(f"Making XBL request with access token: {access_token[:50]}...")

    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)

        print(f"XBL Response Status: {response.status_code}")
        print(f"XBL Response Headers: {dict(response.headers)}")

        if response.status_code != 200:
            print(f"XBL Error Response: {response.text}")
            raise Exception(f"XBL auth failed: {response.status_code}")

        response_data = response.json()

        if "Token" not in response_data:
            print("Error: Token not found in response:", response_data)
            raise KeyError('Failed to get XBL token')

        result = {
            "token": response_data["Token"],
            'uhs': response_data["DisplayClaims"]["xui"][0]['uhs']
        }
        print("XBL Auth Success")
        return result

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        raise
    except json.JSONDecodeError as e:
        print(f"JSON decode failed: {e}")
        print(f"Response content: {response.text}")
        raise

    # response = requests.post(url, json=data, headers=headers)
    # response_data = response.json()
    # 1
    # 1
    # if "Token" not in response_data:
    #     print("Error response:", response_data)
    #     raise KeyError('Failed to get XBL token')

    # returns = {
    #     "token": response_data["Token"],
    #     'uhs': response_data["DisplayClaims"]["xui"][0]['uhs']
    # }
    # print(returns)
    # return returns


def xbl_to_xsts(xbl_return: dict):
    url = 'https://xsts.auth.xboxlive.com/xsts/authorize'
    xbl = xbl_return['token']
    data = {
        "Properties": {
            "SandboxId": "RETAIL",
            "UserTokens": [
                xbl
            ]
        },
        "RelyingParty": "rp://api.minecraftservices.com/",
        "TokenType": "JWT"
    }
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    # 发送请求并获取响应
    response = requests.post(url, json=data, headers=headers)

    # 检查状态码
    if response.status_code != 200:
        print(f"XSTS Error: {response.status_code}")
        print(f"Response: {response.text}")
        raise Exception(f"XSTS auth failed: {response.status_code}")

    # 解析JSON响应
    response_data = response.json()

    # 创建返回字典
    returns = {}
    returns['uhs'] = response_data['DisplayClaims']['xui'][0]['uhs']
    returns['xsts_token'] = response_data['Token']

    return returns


def xsts_to_mc_token(xsts_return: dict):
    url = 'https://api.minecraftservices.com/authentication/login_with_xbox'
    uhs = xsts_return['uhs']
    xsts_token = xsts_return['xsts_token']
    data = {
        "identityToken": f"XBL3.0 x={uhs};{xsts_token}"
    }

    # 添加调试信息
    print(f"Making Minecraft auth request with XSTS token")
    print(f"Identity token: XBL3.0 x={uhs};{xsts_token[:50]}...")

    try:
        response = requests.post(url, json=data)

        print(f"Minecraft Auth Status: {response.status_code}")
        print(f"Minecraft Auth Response: {response.text}")

        if response.status_code != 200:
            print(f"Minecraft auth failed with status: {response.status_code}")
            raise Exception(f"Minecraft auth failed: {response.status_code}")

        response_data = response.json()

        # 检查access_token是否存在
        if 'access_token' not in response_data:
            print(f"Access token not found in response: {response_data}")
            # 检查是否有错误信息
            if 'error' in response_data:
                print(f"Error: {response_data.get('error')}")
                print(f"Error description: {response_data.get('error_description', 'No description')}")
            raise KeyError('access_token not found in Minecraft auth response')

        access_token = response_data['access_token']
        print(f"Successfully obtained Minecraft access token")
        return access_token

    except requests.exceptions.RequestException as e:
        print(f"Minecraft auth request failed: {e}")
        raise
    except json.JSONDecodeError as e:
        print(f"Failed to parse Minecraft auth response: {e}")
        print(f"Raw response: {response.text}")
        raise


def get_mc_token(custom_auth_code=None):
    print('Getting auth_code')
    if custom_auth_code == None:
        auth_code = oauth.get_auth_code()
    else:
        auth_code = custom_auth_code
    print('Getting access_token')
    access_token = code_to_token(auth_code)['access_token']
    print('Getting xbl')
    xbl = access_token_to_xbl(access_token)
    print('Getting xsts')
    xsts = xbl_to_xsts(xbl)
    print('Getting mc_token')
    mc_token = xsts_to_mc_token(xsts)
    print('Finish')
    return mc_token


def is_owned(mc_token, with_profile_data=False):
    headers = {
        'Authorization': f'Bearer {mc_token}',
        'Accept': 'application/json'
    }

    # 检查Minecraft权限
    entitlements_url = "https://api.minecraftservices.com/entitlements/mcstore"
    try:
        entitlements_response = requests.get(entitlements_url, headers=headers)
        entitlements_response.raise_for_status()
        entitlements_data = entitlements_response.json()

        # 获取物品列表
        items = entitlements_data.get('items', [])

        # 获取用户资料
        profile_url = "https://api.minecraftservices.com/minecraft/profile"
        profile_response = requests.get(profile_url, headers=headers)
        profile_data = profile_response.json() if profile_response.status_code == 200 else {}

        # 检查是否拥有Minecraft
        # 条件：有权限物品 且 个人资料不包含NOT_FOUND错误
        has_minecraft = (len(items) > 0 and
                         profile_response.status_code == 200 and
                         'error' not in profile_data)
        if with_profile_data:
            return [has_minecraft, profile_data]
        else:
            return has_minecraft

    except:
        return False


def get_mslogin_uuid_name(access_token: str):
    data = is_owned(access_token, True)
    if data[0]:
        # 提取用户信息
        uuid = data[1].get('id', '')
        name = data[1].get('name', '')
        print(f"uuid={uuid}")
        print(f"name={name}")

        return [uuid, name]
    else:
        raise Exception('No Minecraft license found or profile not available')
        if profile_response.status_code != 200:
            raise Exception(f"Profile API error: {profile_response.status_code} - {profile_response.text}")
