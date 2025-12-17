import streamlit as st
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
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

# --- 3. חיבור API וטיפול במפתחות ---
try:
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
        genai.configure(api_key=api_key)
    else:
        st.error("⚠️ מפתח ה-API חסר. נא להגדיר ב-Secrets.")
        st.stop()
except Exception as e:
    st.error(f"⚠️ שגיאה בהגדרת המפתח: {str(e)}")
    st.stop()

safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
}

# --- פונקציית הליבה עם מנגנון גיבוי (Fallback) ---
@st.cache_data(ttl=3600, show_spinner=False)
def get_cached_response(template_prompt, user_input, mode="full"):
    full_query = template_prompt.format(user_input=user_input)
    
    # אם המשתמש רוצה רק פרומפט, אין צורך לקרוא ל-API
    if mode == "prompt_only":
        return {"status": "success", "text": full_query}

    # ניסיון ראשון: מודל FLASH (מהיר וזול)
    try:
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            tools=[{"google_search_retrieval": {}}],
            system_instruction="You are an expert Israeli veteran consultant. Always answer in Hebrew. Be precise.",
            safety_settings=safety_settings
        )
        response = model.generate_content(full_query)
        return {"status": "success", "text": response.text}

    except Exception as e_flash:
        # אם מודל FLASH נכשל (שגיאת 404 וכו'), מנסים את מודל PRO
        try:
            # print(f"Flash failed, trying Pro. Error: {e_flash}") # לדיבוג פנימי
            model_backup = genai.GenerativeModel(
                model_name='gemini-pro', # מודל גיבוי שתמיד עובד
                system_instruction="You are an expert Israeli veteran consultant. Always answer in Hebrew.",
                safety_settings=safety_settings
            )
            response = model_backup.generate_content(full_query)
            return {"status": "success", "text": response.text + "\n\n*(נוצר באמצעות מודל גיבוי)*"}
            
        except Exception as e_final:
            # אם גם הגיבוי נכשל - מחזירים שגיאה
            return {
                "status": "error", 
                "message": str(e_flash), # מציגים את השגיאה המקורית
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

# --- 6. תצוגת תוצאות (עם התיקון לקריסה) ---
if st.session_state.generated_response:
    result = st.session_state.generated_response
    
    # --- תיקון תאימות לאחור (מונע את ה-TypeError) ---
    if isinstance(result, str):
        result = {"status": "success", "text": result}
    # --- סוף תיקון ---

    st.markdown("---")
    
    # 1. טיפול בשגיאה
    if result.get("status") == "error":
        st.error("❌ התגלתה שגיאה בתקשורת")
        st.warning("פרטי השגיאה למפתחים:")
        st.code(result.get("message", "Unknown Error"), language="text")
        with st.expander("ראה Traceback מלא"):
            st.code(result.get("traceback", ""), language="python")
        
        if st.button("נסה שוב (נקה מטמון)"):
            st.cache_data.clear()
            st.session_state.generated_response = None
            st.rerun()

    # 2. הצלחה - תשובה מלאה
    elif st.session_state.last_prompt_mode == "full":
        st.success("התשובה מוכנה! 👇")
        st.markdown(result.get("text", ""))
        
        if st.button("🔄 נקה תוצאות"):
            st.session_state.generated_response = None
            st.rerun()

    # 3. הצלחה - פרומפט
    elif st.session_state.last_prompt_mode == "prompt":
        st.info("הפרומפט מוכן להעתקה 👇")
        st.code(result.get("text", ""), language="text")
