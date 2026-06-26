#!/usr/bin/env python3
"""微信模板消息推送工具。复用 proxy.js 中的测试号配置。"""
import urllib.request, json, ssl, time
ssl._create_default_https_context = ssl._create_unverified_context

WX_APPID = 'wx12638a290906c4f8'
WX_SECRET = '7d279ce476833e772ade01f78b1d5545'
WX_OPENID = 'oRCv22_Olctg1XCsnbkcMf13g0J0'
WX_TMPL = '86N8AMxv4LofYGEMApnE2RjNuqQ3ZmO82rjiRovbkLE'

_token = None
_token_exp = 0


def _get_token():
    global _token, _token_exp
    if _token and time.time() < _token_exp:
        return _token
    url = f'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={WX_APPID}&secret={WX_SECRET}'
    try:
        req = urllib.request.Request(url, method='GET')
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read())
        _token = data.get('access_token')
        _token_exp = time.time() + data.get('expires_in', 7200) - 300
        return _token
    except Exception as e:
        print(f'[WX] Token error: {e}')
        return None


def push(title, content, remark=''):
    """推一条微信模板消息。"""
    token = _get_token()
    if not token:
        print('[WX] No token, skip push')
        return False

    time_str = time.strftime('%H:%M', time.localtime())
    body = {
        'touser': WX_OPENID,
        'template_id': WX_TMPL,
        'data': {
            'first': {'value': title, 'color': '#1a1a1a'},
            'keyword1': {'value': content, 'color': '#333'},
            'keyword2': {'value': time_str, 'color': '#999'},
            'keyword3': {'value': remark, 'color': '#666'},
            'remark': {'value': '', 'color': '#666'}
        }
    }
    try:
        url = f'https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={token}'
        req = urllib.request.Request(url, data=json.dumps(body).encode('utf-8'),
                                     headers={'Content-Type': 'application/json'}, method='POST')
        resp = urllib.request.urlopen(req, timeout=10)
        result = json.loads(resp.read())
        ok = result.get('errcode') == 0
        print(f'[WX] Push {"OK" if ok else "FAIL"}: {result}')
        return ok
    except Exception as e:
        print(f'[WX] Push error: {e}')
        return False


if __name__ == '__main__':
    push('🧪 测试消息', '这是来自早报系统的测试推送', '如果收到，说明配置正确')
