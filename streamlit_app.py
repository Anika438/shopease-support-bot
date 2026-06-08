import streamlit as st
import requests

st.set_page_config(page_title='ShopEase Support', page_icon='🛍️')
with st.sidebar:
  st.title('ShopEase Customer Support')
  st.markdown("Hello, I am Chuggy, your virtual assistant for ShopEase. I can help you with your orders, returns, product information, and more. Just ask me anything related to ShopEase, and I'll do my best to assist you!")
  if st.button('Clear chat history'):
    response = requests.delete(f"http://localhost:8000/history/{st.session_state.session_id}")
    st.session_state['messages'] = []
    st.rerun()

# Get session_id from URL, or generate a new one
params = st.query_params

if 'session_id' not in st.session_state:
    if 'session' in params:
        # returning user — reuse existing session_id from URL
        st.session_state.session_id = params['session']
    else:
        # new user — generate fresh session_id
        st.session_state.session_id = str(id(st.session_state))
        st.query_params['session'] = st.session_state.session_id

if 'messages' not in st.session_state:
    st.session_state.messages = []
    try:
        res = requests.get(
            f"http://localhost:8000/history/{st.session_state.session_id}"
        )
        if res.status_code == 200:
            st.session_state.messages = res.json()['messages']
    except:
        pass

for msg in st.session_state['messages']:
  if msg['role']=='user':
    st.chat_message('user').write(msg['content'])
  else:
    st.chat_message('assistant').write(msg['content'])    


prompt = st.chat_input('How can I help you?')
if prompt:
    st.session_state['messages'].append({'role':'user','content':prompt})
    with st.chat_message('user'):
      st.write(prompt)
    with st.chat_message('assistant'):
      with st.spinner('Thinking..'):
        try:
          api_url="http://localhost:8000/chat"
          response=requests.post(api_url,json={'message':prompt,'session_id':st.session_state.session_id})
          answer=response.json()['answer']
          sources=response.json()['sources']
          mode = response.json().get('mode', 'RAG')
          st.sidebar.write(f"Mode: {'Agent' if mode == 'Agent' else 'RAG'}")
        except Exception as e:
          answer='Sorry, something went wrong. Please try again later.'
          sources=[]
        st.write(answer)
        if sources:
          with st.expander('Sources'):
            for src in sources:
              st.markdown(f"{src['category']} -- {src['intent']}")
              st.write(src['text'][:300] + '...')  # show first 300 chars
              st.divider()
    st.session_state['messages'].append({'role':'assistant','content':answer})