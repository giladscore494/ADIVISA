import streamlit as st
from google import genai
from google.genai import types
from templates import PROMPT_TEMPLATES
import traceback

# --- 1. הגדרות עמוד ועיצוב (CSS מתקדם) ---
st.set_page_config(page_title="Soldier2Civ AI", page_icon="🎗️", layout="centered")

# הזרקת CSS ליצירת כרטיסיות, צבעים וגרדיאנטים
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@400;700;900&display=swap');
    
    /* הגדרות בסיס */
    html, body, [class*="css"] { 
        font-family: 'Heebo', sans-serif; 
        direction: rtl; 
        text-align: right;
        background-color: #f0f2f6; /* רקע אפור בהיר מאוד */
    }
    
    /* --- עיצוב כרטיסיות (Cards) --- */
    .st-card {
        background-color: #ffffff;
        padding: 2rem;
        border-radius: 20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.05);
        border: 1px solid #e0e0e0;
        margin-bottom: 20px;
        transition: transform 0.3s ease;
    }
    .st-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 15px 35px rgba(0,0,0,0.1);
    }

    /* כרטיסיית תוצאה */
    .result-card {
        background: linear-gradient(135deg, #ffffff 0%, #f9faff 100%);
        border-right: 6px solid #4b6cb7; /* פס כחול בצד */
    }
    
    /* כרטיסיית פרומפט */
    .prompt-card {
         background-color: #1e1e1e; /* רקע כהה */
         color: #00ff00 !important; /* טקסט ירוק זוהר */
         border: 2px solid #333;
    }

    /* --- כותרות צבעוניות --- */
    h1 {
        background: -webkit-linear-gradient(left, #182848, #4b6cb7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 900 !important;
    }
    h3 { color: #4b6cb7; font-weight: 700; }

    /* --- עיצוב כפתורים מודרני --- */
    .stButton>button { 
        width: 100%; 
        border-radius: 15px; 
        height: 3.5em; 
        font-weight: bold; 
        font-size: 18px; 
        border: none;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    /* כפתור ראשי - גרדיאנט כחול */
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) button {
        background: linear-gradient(90deg, #182848 0%, #4b6cb7 100%);
        color: white;
    }
    div[data-testid="stHorizontalBlock"] > div:nth-child(1) button:hover {
        box-shadow: 0 8px 25px rgba(75, 108, 183, 0.4);
        transform: scale(1.02);
    }
    /* כפתור משני - לבן עם מסגרת */
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) button {
        background-color: white;
        color: #182848;
        border: 2px solid #182848;
    }
    div[data-testid="stHorizontalBlock"] > div:nth-child(2) button:hover {
        background-color: #f0f2f6;
    }

    /* הסתרת אלמנטים מיותרים */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stCode { direction: ltr; text-align: left; background-color: #2d2d2d !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. אתחול משתני זיכרון ---
if "generated_response" not in st.session_state:
    st.session_state.generated_response = None
if "last_prompt_mode" not in st.session_state:
    st.session_state.last_prompt_mode = None

# --- 3. פונקציית הליבה (ללא שינוי מהגרסה הקודמת) ---
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
        
        google_search_tool = types.Tool(google_search=types.GoogleSearch())

        try:
            # שיניתי את הוראות המערכת שיהיו קצרות יותר לפי בקשתך הקודמת
            system_instruction = "You are a concise Israeli advisor. Answer in Hebrew. Use bullet points. Keep answers short, direct, and under 150 words. No introduction or summary paragraphs."
            
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=full_query,
                config=types.GenerateContentConfig(
                    tools=[google_search_tool],
                    system_instruction=system_instruction
                )
            )
        except Exception:
            response = client.models.generate_content(
                model='gemini-2.0-flash',
                contents=full_query,
                config=types.GenerateContentConfig(
                    tools=[google_search_tool],
                    system_instruction=system_instruction
                )
            )

        return {"status": "success", "text": response.text}

    except Exception as e:
        return {
            "status": "error", 
            "message": str(e),
            "traceback": traceback.format_exc()
        }

# --- 4. ממשק המשתמש (UI) החדש ---

# כותרת ראשית
st.markdown("<h1>🎗️ Soldier2Civ AI</h1>", unsafe_allow_html=True)
st.markdown("<h3>המדריך החכם לאזרחות | תכל'ס, קצר ולעניין.</h3>", unsafe_allow_html=True)

# --- כרטיסיית הקלט (Input Card) ---
# עוטף את כל אזור הבחירה והכתיבה בכרטיסייה מעוצבת
st.markdown('<div class="st-card">', unsafe_allow_html=True)

option = st.selectbox("בחר נושא:", list(PROMPT_TEMPLATES.keys()))
template = PROMPT_TEMPLATES[option]

# שימוש באלמנט צבעוני של סטרים ליט להסבר
st.info(f"ℹ️ **מה מקבלים?** {template['description']}")

user_input = st.text_area("פרט את בקשתך (תפקיד, יחידה, מטרות):", height=100)

col1, col2 = st.columns(2)
trigger_search = False
trigger_prompt = False

with col1:
    # הכפתור הזה יקבל אוטומטית את עיצוב הגרדיאנט הכחול מה-CSS
    if st.button("🚀 קבל תשובה (AI)"):
        trigger_search = True
with col2:
    # הכפתור הזה יקבל את עיצוב המסגרת
    if st.button("📝 רק פרומפט להעתקה"):
        trigger_prompt = True

st.markdown('</div>', unsafe_allow_html=True) # סגירת כרטיסיית הקלט
# ------------------------------------


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

# --- 6. תצוגת תוצאות (בתוך כרטיסיות צבעוניות) ---
if st.session_state.generated_response:
    result = st.session_state.generated_response
    if isinstance(result, str): result = {"status": "success", "text": result}

    st.write("") # מרווח קטן

    # מקרה שגיאה
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
        # פתיחת דיב של כרטיסיית תוצאה
        st.markdown('<div class="st-card result-card">', unsafe_allow_html=True)
        
        st.success("✅ התשובה מוכנה (Gemini 2.5 Flash)")
        st.markdown(result.get("text", ""))
        
        st.markdown('</div>', unsafe_allow_html=True) # סגירת דיב
        
        if st.button("🔄 התחל מחדש"):
            st.session_state.generated_response = None
            st.rerun()

    # --- כרטיסיית פרומפט להעתקה ---
    elif st.session_state.last_prompt_mode == "prompt":
        # פתיחת דיב של כרטיסיית פרומפט כהה
        st.markdown('<div class="st-card prompt-card">', unsafe_allow_html=True)
        
        st.markdown("**הפרומפט מוכן. העתק והדבק בצ'אט אחר:**")
        st.code(result.get("text", ""), language="text")
        
        st.markdown('</div>', unsafe_allow_html=True) # סגירת דיב

# --- פוטר ---
st.markdown("""
<div style='text-align: center; color: #888; font-size: 0.8em; margin-top: 30px;'>
    🔒 המידע מאובטח ואינו נשמר | פותח עבור משתחררים 2025
</div>
""", unsafe_allow_html=True)
