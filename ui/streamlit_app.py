import streamlit as st
import asyncio
from autogen import AssistantAgent, UserProxyAgent
from os import getenv
from dotenv import load_dotenv, find_dotenv                                                                                                                                 
load_dotenv(find_dotenv())

TRIAL="use trial keys"
CUSTOM="use custom keys"
DFLT_FREE_TRIAL_COUNT=5

def init_trial_config():
    try:
        dflt = (getenv("DFLT", "||")).split("|")
    except:
        dflt = ["","",""] 
    t = {
        "api_type": "azure",
        "base_url": dflt[0],
        "api_version": "2024-02-15-preview",
        "model": dflt[2],
        "api_key": dflt[1]
    }
    return t

def increment_counter():
    if 'count' not in st.session_state:
        st.session_state.count = 0
    st.session_state.count += 1

def check_free_quota():
    if 'count' not in st.session_state:
        st.session_state.count = 0

    return st.session_state.count < getenv("FREE_TRIAL_COUNT", DFLT_FREE_TRIAL_COUNT)

def get_current_config():
    if st.session_state.key_type == CUSTOM:
        if st.session_state.custom_config["base_url"] and st.session_state.custom_config["api_key"] and st.session_state.custom_config["model"]:
            return { "valid":True, "config": st.session_state.custom_config }
        else:
            return { "valid": False, "error": 'Custom keys selected. You must provide valid Azure OpenAI API key and the deployment model'}

    if st.session_state.key_type == TRIAL: 
        if check_free_quota():
            return { "valid": True, 
                "info":"using trial quota ("+ str(st.session_state.count + 1) + "/" + str(getenv("FREE_TRIAL_COUNT", DFLT_FREE_TRIAL_COUNT)) + ")", 
                "config": st.session_state.trial_config }
        else:
            return {"valid": False, "error": 'Free Quota Exceeded! Come back after an hour or provide custom keys to proceed'}

    return {"valid" : False, "error": "Invalid Configuration Keys Selection"}


st.html('<font color="#bbbbbb"><b style="color:black;">GenX </b><b style="color:black;"></b><b style="color:black;">Playground</b></font>')
st.write("""# AutoGen Chat Agents""")

class TrackableAssistantAgent(AssistantAgent):
    def _process_received_message(self, message, sender, silent):
        with st.chat_message(sender.name):
            st.markdown(message)
        return super()._process_received_message(message, sender, silent)


class TrackableUserProxyAgent(UserProxyAgent):
    def _process_received_message(self, message, sender, silent):
        with st.chat_message(sender.name):
            st.markdown(message)
        return super()._process_received_message(message, sender, silent)

st.session_state.key_type = TRIAL
st.session_state.trial_config = init_trial_config()
st.session_state.custom_config = {
    "api_type": "azure",
    "base_url": None,
    "api_version": "2024-02-15-preview",
    "model": None,
    "api_key": None
}

with st.sidebar:
    st.header("Azure OpenAI Configuration")
    st.session_state.key_type = st.radio("",  options=[TRIAL, CUSTOM], index=0)
    st.session_state.custom_config["base_url"] = st.text_input("Azure Endpoint", placeholder="https://<custom>.openai.azure.com")
    st.session_state.custom_config["api_key"] = st.text_input("API Key", type="password", placeholder="enter custom key")
    st.session_state.custom_config["model"] = st.text_input("Deployment Model", placeholder="name of the deployment to use")

with st.container():
    # for message in st.session_state["messages"]:
    #    st.markdown(message)
    c = get_current_config()
    if c["valid"] == False:
            st.warning(c["error"], icon="⚠️")
            st.stop()
    if "info" in c and c["info"]:
        st.info(c["info"])

    user_input = st.chat_input("Give some goal for the agent ...")

    if user_input:  

        increment_counter()
        try:
          llm_config = {
            #"request_timeout": 600,
            "config_list": [ c["config"] ],
            "cache_seed": None,
          }
          #st.write(llm_config)

          # create an AssistantAgent instance named "assistant"
          assistant = TrackableAssistantAgent(
            name="assistant", human_input_mode="NEVER", llm_config=llm_config)

          # create a UserProxyAgent instance named "user"
          user_proxy = TrackableUserProxyAgent(
            name="user", human_input_mode="NEVER", llm_config=llm_config)

          # Create an event loop
          loop = asyncio.new_event_loop()
          asyncio.set_event_loop(loop)

          # Define an asynchronous function
          async def initiate_chat():
            await user_proxy.a_initiate_chat(
                assistant,
                message=user_input,
                max_turns=20
            )

          # Run the asynchronous function within the event loop
          loop.run_until_complete(initiate_chat()) 

        except Exception as E:
            st.error(E)