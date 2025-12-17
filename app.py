import streamlit as st
from google import genai
from google.genai import types
from templates import PROMPT_TEMPLATES
import traceback

# --- 1. הגדרות עמוד ועיצוב ---
st.set_page_config(page_title="Soldier2Civ AI", page_icon="🎗️", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Assistant:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Assistant', sans-serif; direction: rtl; text-align: right; }
    
    .stButton>button { 
        width: 100%; border-radius: 12px; height: 3em; font-weight: bold; font-size: 16px; 
        transition: 0.3s; border: none; box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.2); }
    .stCode { direction: ltr; text-align: left; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. אתחול משתני זיכרון ---
if "generated_response" not in st.session_state:
    st.session_state.generated_response = None
if "last_prompt_mode" not in st.session_state:
    st.session_state.last_prompt_mode = None

# --- 3. פונקציית הליבה עם הספרייה החדשה (Google GenAI SDK) ---
@st.cache_data(ttl=3600, show_spinner=False)
def get_cached_response(template_prompt, user_input, mode="full"):
    try:
        # בדיקת מפתח API
        if "GEMINI_API_KEY" not in st.secrets:
            return {"status": "error", "message": "חסר מפתח GEMINI_API_KEY ב-Secrets"}
            
        api_key = st.secrets["GEMINI_API_KEY"]
        
        # יצירת הקליינט החדש (New SDK Syntax)
        client = genai.Client(api_key=api_key)
        
        full_query = template_prompt.format(user_input=user_input)
        
        # אם המשתמש רוצה רק את הפרומפט
        if mode == "prompt_only":
            return {"status": "success", "text": full_query}
        
        # הגדרת כלי החיפוש בסינטקס החדש
        google_search_tool = types.Tool(
            google_search=types.GoogleSearch()
        )

        # קריאה למודל המעודכן (Gemini 2.5 Flash)
        # שימוש במנגנון fallback: אם 2.5 לא זמין באזורך, ננסה את 2.0
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=full_query,
                config=types.GenerateContentConfig(
                    tools=[google_search_tool],
                    system_instruction="You are an expert Israeli veteran consultant. Always answer in Hebrew. Be precise and factual."
                )
            )
        except Exception:
            # נסיון משני עם מודל 2.0 אם 2.5 נכשל
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=full_query,
                config=types.GenerateContentConfig(
                    tools=[google_search_tool],
                    system_instruction="You are an expert Israeli veteran consultant. Always answer in Hebrew."
                )
            )

        return {"status": "success", "text": response.text}

    except Exception as e:
        return {
            "status": "error", 
            "message": str(e),
            "traceback": traceback.format_exc()
        }

# --- 4. ממשק המשתמש ---
st.title("🎗️ Soldier2Civ AI")
st.caption("המדריך החכם לאזרחות | מבוסס Gemini 2.5")

option = st.selectbox("בחר נושא:", list(PROMPT_TEMPLATES.keys()))
template = PROMPT_TEMPLATES[option]

with st.expander("ℹ️ הסבר על הקטגוריה", expanded=False):
    st.write(template["description"])

user_input = st.text_area("פרט את בקשתך (תפקיד, יחידה, מטרות):", height=100)

col1, col2 = st.columns(2)
trigger_search = False
trigger_prompt = False

with col1:
    if st.button("🚀 קבל תשובה מלאה", type="primary"):
        trigger_search = True

with col2:
    if st.button("📝 העתק פרומפט"):
        trigger_prompt = True

# --- 5. לוגיקה ---
if (trigger_search or trigger_prompt) and len(user_input) < 3:
    st.toast("⚠️ נא לכתוב לפחות 3 תווים.", icon="🛑")

elif trigger_search:
    with st.spinner("🤖 מתחבר לגוגל (Gemini 2.5) ומנתח נתונים..."):
        result = get_cached_response(template["prompt"], user_input, mode="full")
        st.session_state.generated_response = result
        st.session_state.last_prompt_mode = "full"

elif trigger_prompt:
    result = get_cached_response(template["prompt"], user_input, mode="prompt_only")
    st.session_state.generated_response = result
    st.session_state.last_prompt_mode = "prompt"

# --- 6. תצוגת תוצאות ---
if st.session_state.generated_response:
    result = st.session_state.generated_response
    
    # תאימות לאחור
    if isinstance(result, str):
        result = {"status": "success", "text": result}

    st.markdown("---")
    
    if result.get("status") == "error":
        st.error("❌ שגיאה בתקשורת עם המודל החדש")
        st.code(result.get("message", "Unknown Error"), language="text")
        with st.expander("Traceback למפתחים"):
            st.code(result.get("traceback", ""), language="python")
        
        if st.button("נסה שוב"):
            st.cache_data.clear()
            st.session_state.generated_response = None
            st.rerun()

    elif st.session_state.last_prompt_mode == "full":
        st.success("התשובה מוכנה! (Gemini 2.5 Flash) 👇")
        st.markdown(result.get("text", ""))
        
        if st.button("🔄 נקה"):
            st.session_state.generated_response = None
            st.rerun()

    elif st.session_state.last_prompt_mode == "prompt":
        st.info("הפרומפט מוכן להעתקה 👇")
        st.code(result.get("text", ""), language="text")
