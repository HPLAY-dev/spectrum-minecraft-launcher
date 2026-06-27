from urllib.parse import urlparse, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import webbrowser

# OAuthéç˝Ž
oauth_base_url = 'https://login.microsoftonline.com/consumers/oauth2/v2.0/authorize'
client_id = "7000942a-0525-4e21-a817-faf950ab6bc4"
redirect_uri = "http://localhost:8080/callback"  # ćŹĺ°çĺŹĺ°ĺ

class OAuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        # ĺŞĺ¤çĺč°čˇŻĺž?
        print('A GET has been processed')
        if self.path.startswith('/callback'):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            # č§ŁććĽčŻ˘ĺć°
            query = urlparse(self.path).query
            params = parse_qs(query)
            
            if 'code' in params:
                print(params['code'][0])
                auth_code = params['code'][0]
                self.wfile.write(b'<h1>Authentication Successful!</h1><p>You can close this window.</p>')
                print(f"Authorization code received: {auth_code}")
            elif 'error' in params:
                error = params['error'][0]
                error_desc = params.get('error_description', [''])[0]
                self.wfile.write(f'<h1>Error: {error}</h1><p>{error_desc}</p>'.encode())
                print(f"Authentication error: {error} - {error_desc}")
            else:
                print('<h1>No code or error received</h1>')
                self.wfile.write(b'<h1>No code or error received</h1>')
        
        else:
            print('A wrong request has been GETed on localhost:8080')
            self.send_response(404)
            self.end_headers()

def start_server():
    """ĺŻĺ¨HTTPćĺĄĺ?""
    server = HTTPServer(('localhost', 8080), OAuthHandler)
    print("Starting HTTP server on http://localhost:8080")
    
    # ĺ¨ĺĺ°çşżç¨ä¸­čżčĄćĺĄĺ?
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    
    return server, OAuthHandler

def send_auth_request():
    """ĺéOAuthčŽ¤čŻčŻˇćą"""
    params = {
        'client_id': client_id,
        'response_type': 'code',
        'redirect_uri': redirect_uri,
        'scope': 'XboxLive.signin XboxLive.offline_access',
        'response_mode': 'query'
    }
    # https://login.microsoftonline.com/consumers/oauth2/v2.0/authorize?client_id=7000942a-0525-4e21-a817-faf950ab6bc4&response_type=code&redirect_uri=http://localhost:8080/callback&scope=XboxLive.signin%20offline_access&response_mode=query
    auth_url = oauth_base_url + '?' + '&'.join([f"{k}={v}" for k, v in params.items()])
    
    print(f"Opening browser for authentication: {auth_url}")
    webbrowser.open(auth_url)

def get_auth_code(timeout=120):
    """čˇĺććç ďźéťĺĄç´ĺ°ćśĺ°ćčśćśďź"""
    server, handler = start_server()
    send_auth_request()
    
    print("Waiting for authentication... (timeout: 120 seconds)")
    
    # ç­ĺžććç ćčśćś
    import time
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            auth_code
        except NameError:
            pass
        except Exception as e:
            print(e)
        else:
            print('Auth Code Received: '+auth_code)
            return auth_code
        time.sleep(0.1)

    server.shutdown()
    raise TimeoutError("Authentication timeout")

# ä˝żç¨ç¤şäž
if __name__ == "__main__":
    auth_code = get_auth_code()
#         print(f"Success! Authorization code: {auth_code}")
        
#         # čżéä˝ ĺŻäťĽçť§çť­ç¨ććç äş¤ć˘access token
#         token_url = 'https://login.microsoftonline.com/consumers/oauth2/v2.0/token'
#         token_data = {
#             'client_id': client_id,
#             'code': auth_code,
#             'redirect_uri': redirect_uri,
#             'grant_type': 'authorization_code',
#             'scope': 'XboxLive.signin offline_access'
#         }
#         response = requests.post(token_url, data=token_data)
#         print("Token response:", response.json())
        
#     except TimeoutError as e:
#         print(e)
#     except KeyboardInterrupt:
#         print("\nAuthentication cancelled by user")