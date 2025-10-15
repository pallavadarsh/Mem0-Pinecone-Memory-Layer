import os
import requests
import streamlit as st

API = os.getenv('API', 'http://54.226.120.93:8001')

st.set_page_config(page_title='Chat + Memory (Mem0 / Pinecone)', layout='wide', page_icon='💾')

# ---- Approximate Material UI look with CSS ----
MUI_CSS = '''
<style>
:root {
  --mui-primary: #1976d2;
  --mui-blue-50:#e3f2fd; --mui-blue-800:#1565c0;
  --mui-deeppurple-50:#ede7f6; --mui-deeppurple-800:#4527a0;
  --mui-orange-50:#fff3e0; --mui-orange-900:#e65100;
  --mui-pink-50:#fce4ec; --mui-pink-800:#ad1457;
  --mui-teal-50:#e0f2f1; --mui-teal-900:#004d40;
  --mui-green-50:#e8f5e9; --mui-green-900:#1b5e20;
  --mui-grey-50:#fafafa; --mui-grey-100:#f5f5f5; --mui-grey-800:#424242;
  --mui-indigo-50:#e8eaf6; --mui-indigo-800:#283593;
}
.block-container { padding-top: 1rem; }
.mui-card {
  border: 1px solid #eee; border-radius: 12px; background: #fff; padding: 14px; margin-bottom: 18px;
  box-shadow: 0 0 0 rgba(0,0,0,0);
}
.mui-card h3 { margin: 0 0 6px 0; font-weight: 700; font-size: 1rem; }
.mui-sub { margin: 0 0 12px 0; color: #666; font-size: 0.86rem; }
.mui-chip {
  display: inline-block; padding: 4px 8px; border-radius: 999px; font-size: 12px; font-weight: 600; color: #111;
}
.mui-row { display: grid; grid-template-columns: 160px 1fr; gap: 8px; margin: 6px 0; }
.mui-k { color: #666; font-size: 12px; }
.mui-v { white-space: pre-wrap; font-size: 0.95rem; }
.msg { display:flex; gap: 10px; align-items:flex-start; margin-bottom: 10px; }
.msg .bub {
  padding: 10px 12px; border-radius: 8px; border: 1px solid #eee; background: #fff;
}
.msg.user .avatar { background:#111; color:#fff; }
.msg.assistant .avatar { background:#1565c0; color:#fff; }
.avatar {
  width:28px; height:28px; display:flex; align-items:center; justify-content:center; border-radius:50%;
  font-weight:700;
}
.score-wrap { display:flex; align-items:center; gap:8px; min-width:140px; }
.score-bar { width:100px; height:8px; background:#eee; border-radius:6px; position:relative; overflow:hidden; }
.score-fill { position:absolute; left:0; top:0; bottom:0; background: var(--mui-primary); }
.score-num { font-size: 12px; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Courier New', monospace; width:44px; text-align:right; }
</style>
'''
st.markdown(MUI_CSS, unsafe_allow_html=True)

TYPE_STYLE = {
  'factual':   {'bg':'var(--mui-blue-50)',       'fg':'var(--mui-blue-800)'},
  'semantic':  {'bg':'var(--mui-deeppurple-50)', 'fg':'var(--mui-deeppurple-800)'},
  'episodic':  {'bg':'var(--mui-orange-50)',     'fg':'var(--mui-orange-900)'},
  'preference':{'bg':'var(--mui-pink-50)',       'fg':'var(--mui-pink-800)'},
  'task_state':{'bg':'var(--mui-teal-50)',       'fg':'var(--mui-teal-900)'},
  'procedure': {'bg':'var(--mui-indigo-50)',     'fg':'var(--mui-indigo-800)'},
  'ltm':       {'bg':'var(--mui-green-50)',      'fg':'var(--mui-green-900)'},
  'stm':       {'bg':'var(--mui-grey-100)',      'fg':'var(--mui-grey-800)'},
  'default':   {'bg':'var(--mui-grey-50)',       'fg':'var(--mui-grey-800)'}
}

def type_chip(t: str|None):
    key = (t or 'default').lower()
    stl = TYPE_STYLE.get(key, TYPE_STYLE['default'])
    return f'<span class="mui-chip" style="background:{stl["bg"]};color:{stl["fg"]}">{t or "—"}</span>'

def score_bar(score):
    try:
        s = float(score)
    except (TypeError, ValueError):
        return '<span style="color:#666;font-size:12px">—</span>'
    pct = max(0, min(1, s)) * 100.0
    return f'''<div class="score-wrap">
        <div class="score-bar"><span class="score-fill" style="width:{pct:.0f}%"></span></div>
        <div class="score-num">{s:.3f}</div>
    </div>'''

if 'chat_log' not in st.session_state: st.session_state.chat_log = []
if 'retrieval_results' not in st.session_state: st.session_state.retrieval_results = []

left, right = st.columns([0.6, 0.4])
with left:
    st.markdown('## Chat + Memory **Mem0** / Pinecone')
with right:
    st.caption('Streamlit UI — mirrors the React/MUI demo')

c1, c2, c3 = st.columns([0.18, 0.62, 0.20])
with c1:
    user_id = st.text_input('User ID', value='adarsh')
with c2:
    message = st.text_input('Type a message', value='', placeholder='Type a message…')
with c3:
    send = st.button('Send', use_container_width=True, type='primary')

err_box = st.empty()

def fetch_chat(uid, msg):
    url = f'{API}/chat'
    try:
        r = requests.post(url, json={'user_id': uid, 'message': msg, 'type':'auto'},verify=False, timeout=60)
        if r.status_code >= 400:
            return None, f'{r.status_code}: {r.text}'
        return r.json(), None
    except Exception as e:
        return None, str(e)

def fetch_retrieve(uid, q, top_k=8):
    try:
        url = f'{API}/memory/retrieve'
        r = requests.get(url, params={'user_id': uid, 'q': q, 'top_k': top_k}, timeout=60)
        if r.status_code >= 400:
            return None, f'{r.status_code}: {r.text}'
        return r.json(), None
    except Exception as e:
        return None, str(e)

if send and message.strip():
    data, err = fetch_chat(user_id, message.strip())
    if err:
        err_box.error(err)
    else:
        st.session_state.chat_log.append({'role': 'user', 'content': message.strip()})
        st.session_state.chat_log.append({'role': 'assistant', 'content': data.get('reply',''), 'raw': data})

lc, rc = st.columns([0.58, 0.42])

with lc:
    st.markdown('<div class="mui-card"><h3>Conversation</h3><div class="mui-sub">Your messages and the assistant reply</div>', unsafe_allow_html=True)
    if not st.session_state.chat_log:
        st.info('Start chatting! Retrieved memories, policy decisions, and stored summaries will appear on the right.')
    else:
        for m in st.session_state.chat_log:
            role = m['role']
            content = m['content']
            cls = 'user' if role == 'user' else 'assistant'
            avatar = 'U' if role == 'user' else 'A'
            st.markdown(f'''<div class="msg {cls}">
              <div class="avatar">{avatar}</div>
              <div class="bub">{content}</div>
            </div>''', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with rc:
    last = None
    for m in reversed(st.session_state.chat_log):
        if m['role'] == 'assistant':
            last = m.get('raw') or {}
            break

    st.markdown('<div class="mui-card"><h3>Retrieved Memories (last turn)</h3><div class="mui-sub">Type & similarity score</div>', unsafe_allow_html=True)
    items = (last or {}).get('retrieved') or []
    if not items:
        st.info('No retrieved memories for this turn.')
    else:
        for r in items:
            tchip = type_chip(r.get('type'))
            sbar = score_bar(r.get('score'))
            st.markdown(f'''
            <div style="border:1px solid #eaeaea;border-radius:8px;padding:10px;background:#fafafa;margin-bottom:8px;">
              <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
                <div>{tchip}</div>
                <div>{sbar}</div>
              </div>
              <div style="white-space:pre-wrap;">{r.get('text','')}</div>
            </div>''', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="mui-card"><h3>Stored Result & Summary</h3><div class="mui-sub">What got stored this turn</div>', unsafe_allow_html=True)
    stored = (last or {}).get('stored')
    summary = (last or {}).get('summary')
    if not stored and not summary:
        st.info('Skipped storing this turn.')
    else:
        if stored:
            st.markdown(f"""
            <div style='border:1px solid #eaeaea;border-radius:8px;padding:10px;margin-bottom:8px;'>
              <div class='mui-row'><div class='mui-k'>Stored ID</div><div class='mui-v'><code>{stored.get('id','—')}</code></div></div>
              <div class='mui-row'><div class='mui-k'>Type</div><div class='mui-v'>{type_chip(((stored.get('metadata') or {}).get('type')))}</div></div>
              <div class='mui-row'><div class='mui-k'>Text</div><div class='mui-v'>{(stored.get('metadata') or {}).get('text','—')}</div></div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown(f"""
        <div style='border:1px solid #eaeaea;border-radius:8px;padding:10px;'>
          <div class='mui-k' style='margin-bottom:6px;'>Summary (Q/A)</div>
          <div class='mui-v'>{summary or '—'}</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="mui-card"><h3>Policy Trace</h3><div class="mui-sub">Classifier, rationale, scores, dedup</div>', unsafe_allow_html=True)
    policy = (last or {}).get('policy')
    if not policy:
        st.info('No policy data.')
    else:
        dedup_scores = ', '.join([f"{s:.3f}" if isinstance(s,(int,float)) else str(s) for s in (policy.get('dedup_top_scores') or [])]) or '—'
        rows = [
            ('Rationale', policy.get('rationale')),
            ('Specificity', policy.get('specificity')),
            ('Longevity', policy.get('longevity')),
            ('Score', policy.get('score')),
            ('Decision', policy.get('decision')),
            ('Dedup top scores', dedup_scores),
        ]
        tchip = type_chip(policy.get('classified_type'))
        st.markdown('<div style="border:1px solid #eaeaea;border-radius:8px;padding:10px;">', unsafe_allow_html=True)
        st.markdown(f'<div class="mui-row"><div class="mui-k">Classified type</div><div class="mui-v">{tchip}</div></div>', unsafe_allow_html=True)
        for k, v in rows:
            st.markdown(f'<div class="mui-row"><div class="mui-k">{k}</div><div class="mui-v">{v if v is not None else "—"}</div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="mui-card"><h3>Search Memory</h3><div class="mui-sub">Query the store directly</div>', unsafe_allow_html=True)
qcol1, qcol2 = st.columns([0.8, 0.2])
with qcol1:
    retrieval_query = st.text_input('Search query', value='endpoint', label_visibility='collapsed', key='search_input')
with qcol2:
    if st.button('Retrieve', use_container_width=True):
        data, err = fetch_retrieve(user_id, retrieval_query, 8)
        if err:
            err_box.error(err)
        else:
            st.session_state.retrieval_results = data.get('results') or []

items = st.session_state.retrieval_results
if not items:
    st.info('No results')
else:
    for r in items:
        tchip = type_chip(r.get('type'))
        sbar = score_bar(r.get('score'))
        st.markdown(f'''
        <div style="border:1px solid #eaeaea;border-radius:8px;padding:10px;background:#fafafa;margin-bottom:8px;">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
            <div>{tchip}</div>
            <div>{sbar}</div>
          </div>
          <div style="white-space:pre-wrap;">{r.get('text','')}</div>
        </div>''', unsafe_allow_html=True)