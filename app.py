import streamlit as st
from google import genai
from google.genai import types
from templates import PROMPT_TEMPLATES
import traceback

# --- 1. הגדרות עמוד ועיצוב (CSS מתקדם) ---
st.set_page_config(page_title="Soldier2Civ AI", page_icon="🎗️", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@400;700;900&display=swap');
    
    html, body, [class*="css"] { 
        font-family: 'Heebo', sans-serif; 
        direction: rtl; 
        text-align: right;
        background-color: #f4f6f9; /* רקע כללי אפור-כחלחל בהיר */
    }
    
    /* --- כרטיסיית התוצאה (הלב של העיצוב) --- */
    .result-card {
        background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
        padding: 30px;
        border-radius: 20px;
        border-right: 6px solid #4b6cb7; /* פס כחול בצד */
        box-shadow: 0 10px 30px rgba(0,0,0,0.08);
        color: #2c3e50;
        font-size: 1.1rem;
        line-height: 1.6;
        white-space: pre-wrap; /* שומר על ירידות שורה */
        margin-top: 20px;
    }
    
    /* כרטיסיית קלט */
    .input-card {
        background-color: #ffffff;
        padding: 25px;
        border-radius: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        border: 1px solid #edf2f7;
    }

    /* כותרות */
    h1 {
        background: -webkit-linear-gradient(left, #1e3c72, #2a5298);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 900 !important;
        text-align: center;
        margin-bottom: 0px;
    }
    .subtitle {
        text-align: center;
        color: #666;
        font-size: 1.1em;
        margin-bottom: 30px;
    }

    /* כפתורים */
    .stButton>button { 
        width: 100%; border-radius: 12px; height: 3.5em; font-weight: bold; border: none;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1); transition: 0.3s;
    }
    
    /* כפתור ראשי */
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) button {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        color: white;
    }
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(30, 60, 114, 0.3);
    }
    
    /* כפתור משני */
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) button {
        background-color: #ffffff;
        color: #1e3c72;
        border: 2px solid #e1e4e8;
    }

    /* הסתרת רכיבי מערכת */
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .stCode { direction: ltr; text-align: left; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. אתחול משתני זיכרון ---
if "generated_response" not in st.session_state:
    st.session_state.generated_response = None
if "last_prompt_mode" not in st.session_state:
    st.session_state.last_prompt_mode = None

# --- 3. פונקציית הליבה (Gemini 2.5 + Caching) ---
@st.cache_data(ttl=3600, show_spinner=False)
def get_cached_response(template_prompt, user_input, mode="full"):
    try:
        if "GEMINI_API_KEY" not in st.secrets:
            return {"status": "error", "message": "חסר מפתח GEMINI_API_KEY ב-Secrets"}
        
        api_key = st.secrets["GEMINI_API_KEY"]
        client = genai.Client(api_key=api_key)
        
        full_query = template_prompt.format(user_input=user_input)
        
        if mode == "prompt_only":
            return {"status": "success", "text": full_query}
        
        # הגדרת חיפוש
        google_search_tool = types.Tool(google_search=types.GoogleSearch())
        
        # הוראות מערכת קצרות וקולעות
        sys_instruct = "You are a concise Israeli advisor. Answer in Hebrew. Use bullet points and spacing. Keep answers short, direct, and under 200 words."

        # ניסיון ראשי: Gemini 2.5 Flash
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=full_query,
                config=types.GenerateContentConfig(
                    tools=[google_search_tool],
                    system_instruction=sys_instruct
                )
            )
        except Exception:
            # גיבוי: Gemini 2.0 Flash
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=full_query,
                config=types.GenerateContentConfig(
                    tools=[google_search_tool],
                    system_instruction=sys_instruct
                )
            )

        return {"status": "success", "text": response.text}

    except Exception as e:
        return {
            "status": "error", 
            "message": str(e),
            "traceback": traceback.format_exc()
        }

# --- 4. ממשק המשתמש (UI) ---

st.markdown("<h1>🎗️ Soldier2Civ AI</h1>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>המדריך החכם לאזרחות | תכל'ס, קצר ולעניין.</div>", unsafe_allow_html=True)

# --- כרטיסיית הקלט ---
st.markdown('<div class="input-card">', unsafe_allow_html=True)

option = st.selectbox("בחר נושא:", list(PROMPT_TEMPLATES.keys()))
template = PROMPT_TEMPLATES[option]

st.info(f"ℹ️ **מה מקבלים?** {template['description']}")

user_input = st.text_area("פרט את בקשתך (תפקיד, יחידה, מטרות):", height=100)

col1, col2 = st.columns(2)
trigger_search = False
trigger_prompt = False

with col1:
    if st.button("🚀 קבל תשובה"):
        trigger_search = True
with col2:
    if st.button("📝 העתק פרומפט"):
        trigger_prompt = True

st.markdown('</div>', unsafe_allow_html=True)

# --- 5. לוגיקה ---
if (trigger_search or trigger_prompt) and len(user_input) < 3:
    st.toast("⚠️ נא לכתוב לפחות 3 תווים.", icon="🛑")

elif trigger_search:
    with st.spinner("🤖 מנתח נתונים וסורק את גוגל..."):
        result = get_cached_response(template["prompt"], user_input, mode="full")
        st.session_state.generated_response = result
        st.session_state.last_prompt_mode = "full"

elif trigger_prompt:
    result = get_cached_response(template["prompt"], user_input, mode="prompt_only")
    st.session_state.generated_response = result
    st.session_state.last_prompt_mode = "prompt"

# --- 6. תצוגת תוצאות (בתוך כרטיסיות מעוצבות) ---
if st.session_state.generated_response:
    result = st.session_state.generated_response
    if isinstance(result, str): result = {"status": "success", "text": result}

    # שגיאה
    if result.get("status") == "error":
        st.error("❌ שגיאה בתקשורת")
        with st.expander("פרטים טכניים"):
             st.code(result.get("message", ""), language="text")
        if st.button("נסה שוב"):
            st.cache_data.clear()
            st.session_state.generated_response = None
            st.rerun()

    # --- כרטיסיית תשובה מלאה ---
    elif st.session_state.last_prompt_mode == "full":
        # שימוש ב-HTML מותאם אישית להצגת הכרטיסייה
        st.markdown(f"""
        <div class="result-card">
            {result.get("text", "")}
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 התחל מחדש"):
            st.session_state.generated_response = None
            st.rerun()

    # --- כרטיסיית פרומפט ---
    elif st.session_state.last_prompt_mode == "prompt":
        st.info("הפרומפט מוכן להעתקה 👇")
        st.code(result.get("text", ""), language="text")

# --- פוטר ---
st.markdown("""
<div style='text-align: center; color: #888; font-size: 0.8em; margin-top: 40px;'>
    🔒 המידע מאובטח ואינו נשמר | פותח עבור משתחררים 2025
</div>
""", unsafe_allow_html=True)
