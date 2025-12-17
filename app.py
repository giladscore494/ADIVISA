import streamlit as st
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from templates import PROMPT_TEMPLATES
import traceback # ספרייה לניתוח שגיאות עמוק

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
if "debug_info" not in st.session_state:
    st.session_state.debug_info = None

# --- 3. חיבור API וטיפול במפתחות ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except Exception as e:
    st.error("⚠️ שגיאה בהגדרת המפתח (Secrets):")
    st.code(str(e))
    st.stop()

safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
}

# --- שיפור: פונקציה עם טיפול שגיאות מורחב ---
@st.cache_data(ttl=3600, show_spinner=False)
def get_cached_response(template_prompt, user_input, mode="full"):
    try:
        # הגדרת המודל
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            tools=[{"google_search_retrieval": {}}], # מודול חיפוש
            system_instruction="You are an expert Israeli veteran consultant. Always answer in Hebrew. Be precise and factual.",
            safety_settings=safety_settings
        )
        
        full_query = template_prompt.format(user_input=user_input)
        
        # אם המשתמש רוצה רק את הפרומפט
        if mode == "prompt_only":
            return {"status": "success", "text": full_query}
        
        # ביצוע הקריאה ל-AI
        response = model.generate_content(full_query)
        return {"status": "success", "text": response.text}

    except Exception as e:
        # החזרת אובייקט שגיאה מפורט
        return {
            "status": "error", 
            "message": str(e),
            "traceback": traceback.format_exc()
        }

# --- 4. ממשק המשתמש ---
st.title("🎗️ Soldier2Civ AI")
st.caption("המדריך החכם לאזרחות | מבוסס בינה מלאכותית")

option = st.selectbox("בחר נושא:", list(PROMPT_TEMPLATES.keys()))
template = PROMPT_TEMPLATES[option]

with st.expander("ℹ️ הסבר על הקטגוריה", expanded=False):
    st.write(template["description"])

user_input = st.text_area("פרט את בקשתך (תפקיד, יחידה, מטרות):", height=100)

col1, col2 = st.columns(2)
trigger_search = False
trigger_prompt = False

with col1:
    # כפתור ראשי בולט
    if st.button("🚀 קבל תשובה מלאה", type="primary"):
        trigger_search = True

with col2:
    if st.button("📝 העתק פרומפט"):
        trigger_prompt = True

# --- 5. לוגיקה ---
if (trigger_search or trigger_prompt) and len(user_input) < 3:
    st.toast("⚠️ נא לכתוב לפחות 3 תווים.", icon="🛑")

elif trigger_search:
    with st.spinner("🤖 מתחבר לגוגל ומנתח נתונים..."):
        result = get_cached_response(template["prompt"], user_input, mode="full")
        st.session_state.generated_response = result
        st.session_state.last_prompt_mode = "full"

elif trigger_prompt:
    result = get_cached_response(template["prompt"], user_input, mode="prompt_only")
    st.session_state.generated_response = result
    st.session_state.last_prompt_mode = "prompt"

# --- 6. תצוגת תוצאות ודיבוג ---
if st.session_state.generated_response:
    result = st.session_state.generated_response
    st.markdown("---")
    
    # מקרה של שגיאה - תצוגה מפורטת
    if result["status"] == "error":
        st.error("❌ התגלתה שגיאה בתקשורת עם ה-AI")
        st.write("הנה פירוט השגיאה הטכנית (צלם את זה ושלח למפתח):")
        st.code(result["message"], language="text")
        
        with st.expander("🕵️ צפה ב-Log המלא (למתכנתים)"):
            st.code(result["traceback"], language="python")
            
        if st.button("נסה שוב (נקה מטמון)"):
            st.cache_data.clear()
            st.rerun()

    # מקרה הצלחה - תשובה מלאה
    elif st.session_state.last_prompt_mode == "full":
        st.success("התשובה מוכנה! 👇")
        st.markdown(result["text"])
        if st.button("🔄 נקה תוצאות"):
            st.session_state.generated_response = None
            st.rerun()

    # מקרה הצלחה - העתקת פרומפט
    elif st.session_state.last_prompt_mode == "prompt":
        st.info("הפרומפט מוכן להעתקה 👇")
        st.code(result["text"], language="text")
