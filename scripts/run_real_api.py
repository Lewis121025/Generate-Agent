import json, time, urllib.request
BASE = 'http://localhost:8000'

def request(method, path, payload=None):
    data = None
    headers = {'Accept': 'application/json'}
    if payload is not None:
        data = json.dumps(payload).encode('utf-8')
        headers['Content-Type'] = 'application/json'
    req = urllib.request.Request(f"{BASE}{path}", data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=300) as resp:
        return json.loads(resp.read().decode('utf-8'))

def run_creative():
    payload = {
        'tenant_id': 'enterprise-demo',
        'title': 'SecureSphere Cloud Threat Demo',
        'brief': '30秒视频：展示云安全态势感知与自动响应',
        'duration_seconds': 30,
        'style': 'cinematic-tech',
        'budget_limit_usd': 120.0,
    }
    project = request('POST', '/creative/projects', payload)['project']
    pid = project['id']
    print('[Creative] Created', pid, 'state=', project['state'])
    project = request('POST', f'/creative/projects/{pid}/approve-script')['project']
    history = [project['state']]
    for _ in range(40):
        if project['state'] == 'completed':
            break
        endpoint = '/approve-preview' if project['state'] == 'preview_ready' else '/advance'
        project = request('POST', f'/creative/projects/{pid}{endpoint}')['project']
        history.append(project['state'])
        print(' ->', project['state'])
        time.sleep(1)
    if project['state'] != 'completed':
        raise SystemExit('Creative workflow stuck at ' + project['state'])
    return {
        'project_id': pid,
        'state_history': history,
        'render_manifest': project['render_manifest'],
        'distribution_log': project['distribution_log'],
    }

def run_general():
    payload = {
        'tenant_id': 'enterprise-demo',
        'goal': '研究2025年北美新能源补贴政策并生成FAQ',
        'max_iterations': 4,
        'budget_limit_usd': 5.0,
    }
    session = request('POST', '/general/sessions', payload)['session']
    sid = session['id']
    print('[General] Created', sid, 'state=', session['state'])
    while session['state'] == 'active':
        session = request('POST', f'/general/sessions/{sid}/iterate')['session']
        print(' -> iteration', session['iteration'], 'state', session['state'])
        time.sleep(1)
    return {
        'session_id': sid,
        'state': session['state'],
        'spent_usd': session['spent_usd'],
        'tool_calls': session['tool_calls'],
        'messages': session['messages'],
    }

if __name__ == '__main__':
    creative_summary = run_creative()
    general_summary = run_general()
    print('\nCreative summary:', json.dumps(creative_summary, ensure_ascii=False, indent=2))
    print('\nGeneral summary:', json.dumps(general_summary, ensure_ascii=False, indent=2))
