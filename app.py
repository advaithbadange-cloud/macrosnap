from google import genai
from google.genai import types 
import streamlit as st
from prompts import SYSTEM_PROMPT,WELCOME_MESSAGE_TEMPLATE,SUMMARY_REQUEST_PROMPT

MODEL_NAME = "gemini-3.5-flash"




GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key = GEMINI_API_KEY)
gemini_client = get_gemini_client()


def render_message(message):
    with st.chat_message(message["role"]):
        if message["kind"] == "text":
            st.write(message["content"])
        elif message["kind"] == "image":
            st.image(message["content"])

def add_message(role,kind,content):
    st.session_state.messages.append({"role": role, "kind": kind, "content": content})
    render_message(st.session_state.messages[-1])
    
    
def ask_gemini(parts):
    try:
        return st.session_state.chat.send_message(parts).text
    except Exception as error:
        return f"Sorry something went wrong {error}"




#taking details
if "onboarded" not in st.session_state:
    st.title("Macrosnap")
    st.caption("Snap it Crack it")
    with st.form("Onboarding form"):
        name = st.text_input("Your full name")
        whatsappnumber = st.text_input(
            "whatsapp number with country code",
            placeholder="+91xxxxxxxxxx",
        )
        submitted = st.form_submit_button("Lets go")
    if submitted:
        if not name.strip() or not whatsappnumber.strip():
            st.warning("Please enter your full details")
        else:
            st.session_state.name = name
            st.session_state.whatsappnumber = whatsappnumber
            st.session_state.chat = gemini_client.chats.create(
                model = MODEL_NAME,
                config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
            )
            st.session_state.messages = []
            st.session_state.onboarded = True
    st.stop()

#create a chat interface

header_col,button_col = st.columns([5,2],vertical_alignment="center")

with header_col:
    st.title("Macrosnap")

with button_col:
    send_disabled = len(st.session_state.messages) <= 1
    #if st.button("Send to whatsapp",disabled = send_disabled,use_container_width = True):
        #with st.spinner("Summarizing your day"):
            
st.caption(f"Logged in as {st.session_state.name} - update will be sent to number{st.session_state.whatsappnumber}")
if not st.session_state.messages:
    add_message("assistant","text",WELCOME_MESSAGE_TEMPLATE.format(name=st.session_state.name))
else:
    for message in st.session_state.messages:
        render_message(message)

user_input = st.chat_input(
    "Ask a question or attach a photo of your meal  ",
    accept_file= True,
    file_type = ["jpg",'jpeg','png'],
)

if user_input:
    photo = user_input.files[0] if user_input.files else None
    text = user_input.text
    parts = []

    if photo is not None:
        photo_bytes = photo.getvalue()
        add_message("user","image",photo_bytes)
        parts.append(types.Part.from_bytes(data=photo_bytes,mime_type = photo.type))
    if text:
        add_message("user","text",text)
        parts.append(text)
    elif photo is not None:
        parts.append("Give me the calories and macros")
    with st.spinner("Crunching the number"):
        answer = ask_gemini(parts)
    add_message("assistant","text",answer)
