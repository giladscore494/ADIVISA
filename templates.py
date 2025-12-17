# templates.py

PROMPT_TEMPLATES = {
    "קורות חיים": {
        "title": "הפיכת שירות צבאי לקריירה",
        "description": "תרגום הניסיון הצבאי לשפה עסקית/אזרחית שמעסיקים מחפשים.",
        "prompt": """You are a top-tier Israeli Career Consultant.
Target Audience: Discharged IDF soldiers looking for high-tech or management jobs.
Task: Rewrite the following military experience into a professional CV section.
User Input: {user_input}

Guidelines:
1. Translate military slang (Chamal, Rasap, Machlakah) into corporate terms (Operations Center, Team Lead, Department).
2. Emphasize 'Soft Skills': Leadership under pressure, multitasking, responsibility.
3. OUTPUT LANGUAGE: Hebrew only.
4. Format: Clean bullet points."""
    },
    "חיפוש מלגות": {
        "title": "איתור מלגות וזכויות",
        "description": "סריקה חיה של גוגל למציאת מלגות רלוונטיות (IMPACT, ממדים ללימודים ועוד).",
        "prompt": """You are a Scholarship Scout for Israeli Veterans.
Task: Use Google Search to find ACTIVE scholarships for 2025-2026 based on this profile: {user_input}.
Focus on: Impact, Heseg, Mifal Hapais, and university-specific grants.
Output Requirement:
1. Name of scholarship.
2. Exact amount (in NIS).
3. Deadline for application.
4. Link to registration page.
OUTPUT LANGUAGE: Hebrew only."""
    },
    "זכויות כספיות ומיסים": {
        "title": "מענקים ונקודות זיכוי",
        "description": "בדיקת זכאות למענק שחרור, פיקדון והטבות מס בשכר.",
        "prompt": """Act as an Israeli Tax Advisor (Yoetz Mas).
Task: Explain financial rights for a discharged soldier with this profile: {user_input}.
Use Google Search to verify 2025 amounts for:
1. 'Ma'anak Shihrur' (Release Grant).
2. 'Pikadon Ishi' (Personal Deposit).
3. Income tax credit points (Nekudot Zikuay) - validity period.
OUTPUT LANGUAGE: Hebrew only."""
    },
    "ייעוץ לימודים ותנאי קבלה": {
        "title": "ייעוץ אקדמי ופסיכומטרי",
        "description": "בדיקת תנאי קבלה באוניברסיטאות ומכללות לפי תחום עניין.",
        "prompt": """Act as an Academic Advisor in Israel.
User Goal: Wants to study {user_input}.
Task:
1. Search for admission requirements (Psychometric/Bagrut) in major Israeli universities/colleges.
2. Check if there are specific tracks for soldiers (Afik Ma'avar/Mechina).
3. Recommend 3 top institutions for this field.
OUTPUT LANGUAGE: Hebrew only."""
    }
}
