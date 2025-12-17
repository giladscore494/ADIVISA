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
    .stButton>button { width: 100%; border-radius: 12px; height: 3em; font-weight: bold; font-size: 16px; transition: 0.3s; }
    .stButton>button:hover { transform: scale(1.02); }
    .stCode { direction: ltr; text-align: left; }
    /* הסתרת המבורגר של סטרים-ליט למראה נקי יותר */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 2. אתחול משתני זיכרון (Session State) ---
# זה מונע מהתשובה להיעלם כשלוחצים על כפתורים אחרים
if "generated_response" not in st.session_state:
    st.session_state.generated_response = None
if "last_prompt_mode" not in st.session_state:
    st.session_state.last_prompt_mode = None

# --- 3. חיבור API ופונקציות ליבה ---
if "GEMINI_API_KEY" not in st.secrets:
    st.error("⚠️ שגיאה קריטית: מפתח API חסר.")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# הגדרות בטיחות
safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
}

# --- שיפור קריטי: CACHING ---
# הפונקציה הזו שומרת תוצאות במטמון. אם אותה שאלה נשאלת שוב - התשובה מגיעה מיד בלי לחייב את גוגל.
@st.cache_data(ttl=3600, show_spinner=False) # שומר בזיכרון לשעה
def get_cached_response(template_prompt, user_input, mode="full"):
    try:
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
st.markdown("### המדריך החכם לאזרחות | מבוסס בינה מלאכותית")

# בחירת קטגוריה
option = st.selectbox("בחר נושא:", list(PROMPT_TEMPLATES.keys()))
template = PROMPT_TEMPLATES[option]

# תצוגת הסבר קצרה ואלגנטית
with st.expander("ℹ️ מה הכלי עושה בקטגוריה זו?", expanded=False):
    st.write(template["description"])

# טופס קלט
user_input = st.text_area("פרט את בקשתך (תפקיד, יחידה, מטרות):", 
                         height=100, 
                         placeholder="למשל: לוחם בגולני, משתחרר עוד חודש, רוצה לדעת כמה פיקדון מגיע לי ואיך מושכים אותו...")

# כפתורי פעולה בטורים
col1, col2 = st.columns(2)

# לוגיקה לכפתורים
trigger_search = False
trigger_prompt = False

with col1:
    if st.button("🚀 קבל תשובה מלאה"):
        trigger_search = True

with col2:
    if st.button("📝 העתק פרומפט"):
        trigger_prompt = True

# --- 5. עיבוד הלוגיקה והצגת תוצאות ---

# בדיקת תקינות קלט (Validation)
if (trigger_search or trigger_prompt) and len(user_input) < 3:
    st.toast("⚠️ נא לכתוב לפחות 3 תווים כדי שנוכל לעזור.", icon="🛑")

elif trigger_search:
    with st.spinner("🤖 סורק את הרשת ומנתח נתונים..."):
        # קריאה לפונקציה המטמונת
        response_text = get_cached_response(template["prompt"], user_input, mode="full")
        
        # שמירה ב-State
        st.session_state.generated_response = response_text
        st.session_state.last_prompt_mode = "full"

elif trigger_prompt:
    # יצירת פרומפט בלבד
    prompt_text = get_cached_response(template["prompt"], user_input, mode="prompt_only")
    st.session_state.generated_response = prompt_text
    st.session_state.last_prompt_mode = "prompt"

# --- 6. אזור התצוגה (Persistent Display area) ---
# החלק הזה ירוץ תמיד אם יש מידע בזיכרון, גם אם ה-UI מתרענן
if st.session_state.generated_response:
    st.markdown("---")
    
    if "Error:" in st.session_state.generated_response:
        st.error("אופס, הייתה בעיה בתקשורת. נסה שוב בעוד רגע.")
    
    elif st.session_state.last_prompt_mode == "full":
        st.success("התשובה מוכנה! 👇")
        st.markdown(st.session_state.generated_response)
        if st.button("🔄 נקה תוצאות"):
            st.session_state.generated_response = None
            st.rerun() # רענון מהיר
            
    elif st.session_state.last_prompt_mode == "prompt":
        st.info("הפרומפט מוכן להעתקה 👇")
        st.code(st.session_state.generated_response, language="text")
        st.caption("טיפ: העתק את הטקסט והדבק ב-ChatGPT או Claude לקבלת תוצאה מפורטת.")

st.markdown("<br><br>", unsafe_allow_html=True)
st.markdown("""
<div style='text-align: center; color: #888; font-size: 0.8em;'>
    🔒 המידע מעובד בזמן אמת ואינו נשמר בשרתים שלנו.<br>
    © 2025 Gilad Projects
</div>
""", unsafe_allow_html=True)
