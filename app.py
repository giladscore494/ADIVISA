import streamlit as st
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from templates import PROMPT_TEMPLATES

# --- 1. הגדרות עמוד ועיצוב ---
st.set_page_config(page_title="Soldier2Civ AI", page_icon="🎗️", layout="centered")

# עיצוב CSS מותאם אישית (RTL + Mobile Fixes)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Assistant:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Assistant', sans-serif; direction: rtl; text-align: right; }
    
    /* עיצוב כפתורים מודרני */
    .stButton>button { 
        width: 100%; 
        border-radius: 12px; 
        height: 3em; 
        font-weight: bold; 
        font-size: 16px; 
        transition: 0.3s; 
        border: none;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .stButton>button:hover { 
        transform: translateY(-2px); 
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* יישור קוד לשמאל */
    .stCode { direction: ltr; text-align: left; }
    
    /* הסתרת אלמנטים מיותרים של המערכת למראה נקי */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. אתחול משתני זיכרון (Session State) ---
# מונע מהתשובה להיעלם ברענון הדף או לחיצה על כפתורים
if "generated_response" not in st.session_state:
    st.session_state.generated_response = None
if "last_prompt_mode" not in st.session_state:
    st.session_state.last_prompt_mode = None

# --- 3. חיבור API מאובטח (מתוך ה-Secrets) ---
try:
    # כאן הקוד מושך את המפתח שהגדרת בסיקרט
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
except FileNotFoundError:
    st.error("⚠️ קובץ Secrets לא נמצא (בפיתוח מקומי יש ליצור .streamlit/secrets.toml)")
    st.stop()
except KeyError:
    st.error("⚠️ המפתח 'GEMINI_API_KEY' חסר בהגדרות ה-Secrets של סטרים-ליט.")
    st.stop()

# הגדרות בטיחות - מאפשר דיון בנושאים צבאיים בלי חסימות מיותרות
safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
}

# --- שיפור קריטי: CACHING (מטמון) ---
# שומר את התשובה בזיכרון לשעה כדי לחסוך קריאות ל-API ולהאיץ את האתר
@st.cache_data(ttl=3600, show_spinner=False)
def get_cached_response(template_prompt, user_input, mode="full"):
    try:
        # הגדרת המודל עם חיבור לחיפוש בגוגל
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            tools=[{"google_search_retrieval": {}}],
            system_instruction="You are an expert Israeli veteran consultant. Provide accurate, source-backed answers in Hebrew.",
            safety_settings=safety_settings
        )
        
        full_query = template_prompt.format(user_input=user_input)
        
        if mode == "prompt_only":
            return full_query
        
        response = model.generate_content(full_query)
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

# --- 4. ממשק המשתמש (UI) ---
st.title("🎗️ Soldier2Civ AI")
st.markdown("### המדריך החכם לאזרחות | מבוסס AI ונתוני אמת")

# בחירת קטגוריה
option = st.selectbox("בחר נושא:", list(PROMPT_TEMPLATES.keys()))
template = PROMPT_TEMPLATES[option]

# תצוגת הסבר נפתחת
with st.expander("ℹ️ איך זה עובד?", expanded=False):
    st.write(template["description"])

# טופס קלט
user_input = st.text_area("פרט את בקשתך (תפקיד, יחידה, מטרות):", 
                         height=100, 
                         placeholder="דוגמה: הייתי לוחם בחיל הים, משתחרר עוד חודש, רוצה לדעת איזה מלגות מתאימות ללימודי הנדסה...")

# כפתורי פעולה בטורים
col1, col2 = st.columns(2)

# משתנים לזיהוי איזה כפתור נלחץ
trigger_search = False
trigger_prompt = False

with col1:
    if st.button("🚀 קבל תשובה מלאה"):
        trigger_search = True

with col2:
    if st.button("📝 העתק פרומפט"):
        trigger_prompt = True

# --- 5. לוגיקה ועיבוד ---

# בדיקת תקינות קלט (Validation)
if (trigger_search or trigger_prompt) and len(user_input) < 3:
    st.toast("⚠️ נא לכתוב לפחות 3 תווים כדי שנוכל לעזור.", icon="🛑")

elif trigger_search:
    with st.spinner("🤖 סורק את הרשת ומנתח נתונים..."):
        # קריאה לפונקציה (משתמשת במטמון אם קיים)
        response_text = get_cached_response(template["prompt"], user_input, mode="full")
        
        # שמירה ב-State
        st.session_state.generated_response = response_text
        st.session_state.last_prompt_mode = "full"

elif trigger_prompt:
    # יצירת פרומפט בלבד
    prompt_text = get_cached_response(template["prompt"], user_input, mode="prompt_only")
    st.session_state.generated_response = prompt_text
    st.session_state.last_prompt_mode = "prompt"

# --- 6. אזור התצוגה (Persistent Display) ---
# מציג את התוצאה כל עוד היא קיימת בזיכרון, גם אחרי רענון
if st.session_state.generated_response:
    st.markdown("---")
    
    # טיפול בשגיאות טכניות
    if "Error:" in st.session_state.generated_response:
        st.error("אופס, הייתה בעיה בתקשורת עם השרת. אנא נסה שוב בעוד רגע.")
        st.caption(st.session_state.generated_response) # הצגת שגיאה למפתח (אופציונלי)
    
    # הצגת תשובה מלאה
    elif st.session_state.last_prompt_mode == "full":
        st.success("התשובה מוכנה! 👇")
        st.markdown(st.session_state.generated_response)
        
        # כפתור ניקוי
        if st.button("🔄 התחל מחדש / נקה"):
            st.session_state.generated_response = None
            st.rerun()
            
    # הצגת פרומפט להעתקה
    elif st.session_state.last_prompt_mode == "prompt":
        st.info("הפרומפט מוכן להעתקה 👇")
        st.code(st.session_state.generated_response, language="text")
        st.caption("טיפ: העתק את הטקסט והדבק אותו ב-ChatGPT או Claude לקבלת ניתוח מעמיק נוסף.")

st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
<div style='text-align: center; color: #888; font-size: 0.8em;'>
    🔒 המידע מעובד בזמן אמת ואינו נשמר בשרתים שלנו.<br>
    © 2025 Soldier2Civ AI
</div>
""", unsafe_allow_html=True)
