import streamlit as st
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from templates import PROMPT_TEMPLATES

# --- 1. הגדרות עמוד ועיצוב ---
st.set_page_config(page_title="Soldier2Civ AI", page_icon="🎗️", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Assistant:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Assistant', sans-serif; direction: rtl; text-align: right; }
    .stButton>button { width: 100%; border-radius: 12px; height: 3em; font-weight: bold; font-size: 16px; }
    .stCode { direction: ltr; text-align: left; }
    /* התאמת כותרות לימין */
    h1, h2, h3 { text-align: right; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. חיבור ל-API וטיפול בשגיאות ---
if "GEMINI_API_KEY" not in st.secrets:
    st.error("⚠️ שגיאה: מפתח ה-API חסר. יש להגדיר GEMINI_API_KEY ב-Secrets.")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# הגדרות בטיחות - למנוע חסימה של תכנים צבאיים (נשק/מלחמה)
safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
}

def get_response(template_prompt, user_input, mode="full"):
    """
    פונקציה מרכזית לתקשורת עם Gemini
    """
    try:
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            tools=[{"google_search_retrieval": {}}], # חיבור לאינטרנט
            system_instruction="You are a helpful, professional assistant for Israeli discharged soldiers. Always answer in Hebrew.",
            safety_settings=safety_settings
        )
        
        full_query = template_prompt.format(user_input=user_input)
        
        # אם המשתמש רוצה רק את הפרומפט להעתקה
        if mode == "prompt_only":
            return full_query
        
        # יצירת תשובה מלאה
        response = model.generate_content(full_query)
        return response.text

    except Exception as e:
        return f"⚠️ אירעה שגיאה בתקשורת עם ה-AI: {str(e)}\n\nאנא נסה שוב בעוד רגע."

# --- 3. ממשק המשתמש (UI) ---
st.title("🎗️ Soldier2Civ AI")
st.caption("הכלי החכם למשתחררים: קורות חיים, מלגות וייעוץ בחינם")

# בחירת נושא
option = st.selectbox("בחר מה אתה צריך:", list(PROMPT_TEMPLATES.keys()))
template = PROMPT_TEMPLATES[option]
st.info(template["description"])

# טופס קלט
user_input = st.text_area("הכנס פרטים (תפקיד, שאיפות, ניסיון):", height=100, placeholder="דוגמה: הייתי סמבצית בחיל האוויר, אני רוצה ללמוד פסיכולוגיה...")

# כפתורי פעולה
col1, col2 = st.columns(2)

with col1:
    if st.button("🚀 קבל תשובה מלאה (AI)"):
        if user_input:
            with st.spinner("🤖 המודל סורק את הרשת ומנתח..."):
                answer = get_response(template["prompt"], user_input)
                st.markdown("---")
                st.markdown(answer)
        else:
            st.toast("נא לכתוב פרטים בתיבה למעלה 👆")

with col2:
    if st.button("📝 העתק פרומפט ל-ChatGPT"):
        if user_input:
            pro_prompt = get_response(template["prompt"], user_input, mode="prompt_only")
            st.markdown("---")
            st.success("הפרומפט נוצר! העתק אותו מכאן:")
            st.code(pro_prompt, language="text")
        else:
            st.toast("נא לכתוב פרטים בתיבה למעלה 👆")

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.8em;'>
    נבנה עבור חיילים משוחררים | מבוסס על Gemini 1.5 Flash <br>
    המידע אינו נשמר ומאובטח באופן מלא.
</div>
""", unsafe_allow_html=True)
