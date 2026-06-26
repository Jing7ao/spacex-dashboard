#!/usr/bin/env python3
"""PushPlus 推送工具 —— 支持长文本Markdown，突破微信模板消息长度限制"""
import urllib.request, json, ssl, time
ssl._create_default_https_context = ssl._create_unverified_context

PUSHPLUS_TOKEN = 'd76fe013c04f4f3cae022e47e8aebe12'


def push(title, content, template='markdown'):
    """推送到微信。title=标题，content=Markdown正文。"""
    body = {
        'token': PUSHPLUS_TOKEN,
        'title': title,
        'content': content,
        'template': template,
    }
    try:
        url = 'http://www.pushplus.plus/send'
        req = urllib.request.Request(url, data=json.dumps(body).encode('utf-8'),
                                     headers={'Content-Type': 'application/json'}, method='POST')
        resp = urllib.request.urlopen(req, timeout=10)
        result = json.loads(resp.read())
        ok = result.get('code') == 200
        print(f'[PushPlus] {"OK" if ok else "FAIL"}: {result.get("msg","?")}')
        return ok
    except Exception as e:
        print(f'[PushPlus] Error: {e}')
        return False


if __name__ == '__main__':
    push('🧪 测试',
         '## 测试推送\n\n> 如果收到这条消息，说明 PushPlus 配置成功 ✅\n\n'
         '从现在开始，早报和晚报将正常推送，不受微信模板消息长度限制。\n\n'
         '---\n\n*系统已就绪*')
