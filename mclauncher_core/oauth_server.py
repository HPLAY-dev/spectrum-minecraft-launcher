from urllib.parse import urlparse, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import webbrowser

# OAuth配置
oauth_base_url = 'https://login.microsoftonline.com/consumers/oauth2/v2.0/authorize'
client_id = "7000942a-0525-4e21-a817-faf950ab6bc4"
redirect_uri = "http://localhost:8080/callback"  # 本地监听地址

class OAuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        # 只处理回调路径
        print('A GET has been processed')
        if self.path.startswith('/callback'):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            # 解析查询参数
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
    """启动HTTP服务器"""
    server = HTTPServer(('localhost', 8080), OAuthHandler)
    print("Starting HTTP server on http://localhost:8080")
    
    # 在后台线程中运行服务器
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    
    return server, OAuthHandler

def send_auth_request():
    """发送OAuth认证请求"""
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
    """获取授权码（阻塞直到收到或超时）"""
    server, handler = start_server()
    send_auth_request()
    
    print("Waiting for authentication... (timeout: 120 seconds)")
    
    # 等待授权码或超时
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

# 使用示例
if __name__ == "__main__":
    auth_code = get_auth_code()
#         print(f"Success! Authorization code: {auth_code}")
        
#         # 这里你可以继续用授权码交换access token
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