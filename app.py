"""
Mijozlarga xizmat ko'rsatish boti - Claude API asosida
"""
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import anthropic

app = Flask(__name__)
CORS(app)  # Vebsaytdan so'rov yuborish uchun ruxsat

# API kalitni environment variable orqali oling (hech qachon kodga yozmang!)
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# ============================================
# KOMPANIYA HAQIDA MA'LUMOT - shu yerni o'zgartiring
# ============================================
SYSTEM_PROMPT = """Siz "Kompaniya Nomi" kompaniyasining mijozlarga xizmat ko'rsatish yordamchisisiz.

QOIDALAR:
- Faqat kompaniya mahsulotlari, xizmatlari va buyurtmalar haqida javob bering
- Mijoz qaysi tilda yozsa (o'zbek, rus, ingliz), o'sha tilda javob bering
- Qisqa va aniq javob bering, keraksiz uzun matn yozmang
- Narx yoki chegirma haqida noaniq va'da bermang
- Agar savolga javobni bilmasangiz yoki muammo murakkab bo'lsa, mijozni operatorga yo'naltiring: "Iltimos, +998 XX XXX XX XX raqamiga qo'ng'iroq qiling" deb ayting
- Doim mehribon va professional bo'ling

KOMPANIYA HAQIDA MA'LUMOT (FAQ):
- Ish vaqti: Dushanba-Shanba, 9:00-18:00
- Yetkazib berish: Toshkent bo'ylab 1-2 kun, viloyatlarga 3-5 kun
- Qaytarish siyosati: 14 kun ichida, chek bilan
- To'lov usullari: naqd, Click, Payme, karta orqali

[BU YERGA O'Z KOMPANIYANGIZ MA'LUMOTLARINI QO'SHING]
"""

# Har bir mijoz uchun suhbat tarixini saqlash (oddiy versiya - xotirada)
# Ishlab chiqarish (production) uchun buni database'ga (Redis, PostgreSQL) ko'chirish kerak
conversations = {}


@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message", "")
    session_id = data.get("session_id", "default")  # Har bir mijoz uchun unikal ID

    if not user_message:
        return jsonify({"error": "Xabar bo'sh bo'lishi mumkin emas"}), 400

    # Shu mijozning oldingi suhbatini olish (agar bo'lmasa, yangi yaratish)
    if session_id not in conversations:
        conversations[session_id] = []

    history = conversations[session_id]
    history.append({"role": "user", "content": user_message})

    try:
        response = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=history,
        )
        assistant_reply = response.content[0].text

        # Javobni ham tarixga qo'shamiz, keyingi xabarlarda kontekst saqlanishi uchun
        history.append({"role": "assistant", "content": assistant_reply})

        # Tarix juda uzun bo'lib ketmasligi uchun oxirgi 20 ta xabarni saqlaymiz
        conversations[session_id] = history[-20:]

        return jsonify({"reply": assistant_reply})

    except Exception as e:
        return jsonify({"error": f"Xatolik yuz berdi: {str(e)}"}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ishlayapti"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
