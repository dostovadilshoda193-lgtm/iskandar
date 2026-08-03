import os
import json
import csv
import math
import time
import random
import threading
import logging
from datetime import datetime, timedelta

import requests
import telebot
from telebot import types
from telebot.handler_backends import BaseMiddleware
from google import genai
try:
    from google.genai import types as genai_types
except Exception:
    genai_types = None
from fpdf import FPDF

# ============================================================
#  LOGGING SOZLAMALARI
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("bot")

# ============================================================
#  ASOSIY SOZLAMALAR
# ============================================================
# ⚠️ ESLATMA: bu tokenlarni ENDI ALMASHTIRING (BotFather /revoke va Gemini
# konsolida yangi kalit) — eski qiymatlar ochiq suhbatda ko'rilgan.
BOT_TOKEN = "8933589522:AAGOVM9KkV-2fBwZQ8pVMykAcN0BqPPkehc"

ADMIN_ID = 8548782312
ADMIN_USERNAME = "dostovv"
ADMIN_LINK = f"https://t.me/{ADMIN_USERNAME}"

GEMINI_API_KEY = "AQ.Ab8RN6JCiGsBcZAn_3TKVokbrgEcxqYZA6w1bc8J61njczG84A"
ai_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
if not ai_client:
    log.warning("GEMINI_API_KEY yo'q — Gemini AI bo'limi ishlamaydi.")

GURUH_LINK = "https://t.me/+sqdu-Tik3Q4wMmIy"
KANAL_ID = -1004302760890

# 🌐 Bizning veb-sayt havolasi
SAYT_LINK = "https://website-1x1-multipla-pu3o.bolt.host"

bot = telebot.TeleBot(BOT_TOKEN, use_class_middlewares=True)

DB_FILE = "users.json"
ELON_FILE = "elonlar.json"
IMTIXON_FILE = "imtixon.json"
RUXSATNOMA_FILE = "ruxsatnomalar.json"
TAKSI_FILE = "taksi_buyurtmalar.json"
HAYDOVCHI_FILE = "haydovchilar.json"

TAKSI_BOSHLANGICH_NARX = 5000
TAKSI_KM_NARXI = 2000
TAKSI_QIDIRUV_RADIUSI_KM = 15

ELON_MUDDATI_KUN = 30

FANLAR = [
    ("📐 Matematika", "mat"), ("⚛️ Fizika", "fiz"), ("🧪 Kimyo", "kim"),
    ("🧬 Biologiya", "bio"), ("🌍 Tarix", "tar"), ("🗣 Ingliz tili", "ing"),
    ("📖 Ona tili va adabiyot", "ona"), ("💻 Informatika", "inf"), ("🧮 Boshqa fan", "bshq_fan"),
]

TAQIQLANGAN_SOZLAR_BOSHLANGICH = ["tentak", "axmoq", "jinni", "aroq", "narkotik"]
BLACKLIST_FILE = "blacklist.json"
NEWS_FILE = "yangiliklar.json"
EVENTS_FILE = "tadbirlar.json"
QUIZ_FILE = "savollar.json"

# ---- STATIK MA'LUMOTLAR BAZASI ----
VILOYATLAR = [
    ("Toshkent sh.", "tosh_sh"), ("Toshkent vil.", "tosh_v"), ("Samarqand", "sam"),
    ("Farg'ona", "far"), ("Andijon", "and"), ("Namangan", "nam"), ("Buxoro", "bux"),
    ("Navoiy", "nav"), ("Xorazm", "xor"), ("Qashqadaryo", "qash"), ("Surxondaryo", "sur"),
    ("Jizzax", "jiz"), ("Sirdaryo", "sir"), ("Qoraqalpog'iston", "qorq")
]

TUMANLAR = {
    "tosh_sh": [
        ("Yunusobod t.", "yunus"), ("Chilonzor t.", "chilonzor"), ("Mirzo Ulug'bek t.", "m_ulugbek"),
        ("Yashnobod t.", "yashnobod"), ("Olmazor t.", "olmazor"), ("Sergeli t.", "sergeli"),
        ("Mirobod t.", "mirobod"), ("Yakkasaroy t.", "yakkasaroy"), ("Bektemir t.", "bektemir"),
        ("Uchtepa t.", "uchtepa"), ("Shayxontohur t.", "shayxontohur"), ("Yangihayot t.", "yangihayot")
    ],
    "tosh_v": [
        ("Chirchiq sh.", "chirchiq"), ("Olmaliq sh.", "olmaliq"), ("Angren sh.", "angren"),
        ("Bekobod sh.", "bekobod_sh"), ("Nurafshon sh.", "nurafshon"), ("Yangiyo'l sh.", "yangiyul_sh"),
        ("Bekobod t.", "bekobod_t"), ("Bo'stanliq t.", "bostonliq"), ("Bo'ka t.", "buka"),
        ("Chinoz t.", "chinoz"), ("Qibray t.", "qibray"), ("Parkent t.", "parkent"),
        ("Piskent t.", "piskent"), ("Quyi Chirchiq t.", "q_chirchiq"), ("O'rtachirchiq t.", "o_chirchiq"),
        ("Yuqori Chirchiq t.", "y_chirchiq"), ("Yangiyo'l t.", "yangiyul_t"), ("Toshkent t.", "tosh_t"),
        ("Zangiota t.", "zangiota"), ("Oqqorg'on t.", "oqqorgon")
    ],
    "sam": [
        ("Samarqand sh.", "sam_sh"), ("Kattaqo'rg'on sh.", "katta_sh"), ("Bulung'ur t.", "bulungur"),
        ("Ishtixon t.", "ishtixon"), ("Jomboy t.", "jomboy"), ("Kattaqo'rg'on t.", "katta_t"),
        ("Qo'shrabot t.", "qoshrabot"), ("Narpay t.", "narpay"), ("Nurobod t.", "nurobod"),
        ("Oqdaryo t.", "oqdaryo"), ("Paxtachi t.", "paxtachi"), ("Payariq t.", "payariq"),
        ("Pastdarg'om t.", "pastdar"), ("Samarqand t.", "sam_t"), ("Toyloq t.", "toyloq"), ("Urgut t.", "urgut")
    ],
    "far": [
        ("Farg'ona sh.", "far_sh"), ("Qo'qon sh.", "qoqon"), ("Marg'ilon sh.", "margilon"),
        ("Quvasoy sh.", "quvasoy"), ("Oltiariq t.", "oltiariq"), ("Bag'dod t.", "bagdod"),
        ("Beshariq t.", "beshariq"), ("Buvayda t.", "buvayda"), ("Dang'ara t.", "dangara"),
        ("Farg'ona t.", "far_t"), ("Furqat t.", "furqat"), ("Qo'shtepa t.", "qoshtepa"),
        ("Quva t.", "quva"), ("Rishton t.", "rishton"), ("So'x t.", "sox"),
        ("Toshloq t.", "toshloq"), ("Uchko'prik t.", "uchkoprik"), ("Yozyovon t.", "yozyovon"),
        ("O'zbekiston t.", "uzbekiston_t")
    ],
    "and": [
        ("Andijon sh.", "and_sh"), ("Xonobod sh.", "xonobod"), ("Andijon t.", "and_t"),
        ("Asaka t.", "asaka"), ("Baliqchi t.", "baliqchi"), ("Bo'ston t.", "boston"),
        ("Buloqboshi t.", "buloqboshi"), ("Izboskan t.", "izboskan"), ("Jalaquduq t.", "jalaquduq"),
        ("Marhamat t.", "marhamat"), ("Oltinko'l t.", "oltinkol"), ("Paxtaobod t.", "paxtaobod"),
        ("Qorasuv sh.", "qorasuv"), ("Shahrixon t.", "shahrixon"), ("Ulug'nor t.", "ulugnor"),
        ("Xo'jaobod t.", "xojaobod")
    ],
    "nam": [
        ("Namangan sh.", "nam_sh"), ("Chortoq t.", "chortoq"), ("Chust t.", "chust"),
        ("Kosonsoy t.", "kosonsoy"), ("Mingbuloq t.", "mingbuloq"), ("Namangan t.", "nam_t"),
        ("Norin t.", "norin"), ("Pop t.", "pop"), ("To'raqo'rg'on t.", "toraqur"),
        ("Uychi t.", "uychi"), ("Uchqo'rg'on t.", "uchqorgon"), ("Yangiqo'rg'on t.", "yangiqorgon"),
        ("Davlatobod t.", "davlatobod"), ("Yangi Namangan t.", "y_namangan")
    ],
    "bux": [
        ("Buxoro sh.", "bux_sh"), ("Kogon sh.", "kogon"), ("Buxoro t.", "bux_t"),
        ("Gijduvon t.", "gijduvon"), ("Jondor t.", "jondor"), ("Kogon t.", "kogon_t"),
        ("Qorako'l t.", "qorakol"), ("Qorovulbozor t.", "qorovulbozor"), ("Olot t.", "olot"),
        ("Peshku t.", "peshku"), ("Romitan t.", "romitan"), ("Shofirkon t.", "shofirkon"), ("Vobkent t.", "vobkent")
    ],
    "nav": [
        ("Navoiy sh.", "nav_sh"), ("Zarafshon sh.", "zarafshon"), ("Gozg'on sh.", "gozgon"),
        ("Karmana t.", "karmana"), ("Konimex t.", "konimex"), ("Navbahor t.", "navbahor"),
        ("Nurota t.", "nurota"), ("Qiziltepa t.", "qiziltepa"), ("Tomdi t.", "tomdi"),
        ("Uchquduq t.", "uchquduq"), ("Xatirchi t.", "xatirchi")
    ],
    "xor": [
        ("Urganch sh.", "urganch"), ("Xiva sh.", "xiva"), ("Bog'ot t.", "bogot"),
        ("Gurlan t.", "gurlan"), ("Qo'shko'pir t.", "qushkopir"), ("Shovot t.", "shovot"),
        ("Tuproqqal'a t.", "tuproqqala"), ("Urganch t.", "urganch_t"), ("Xanka t.", "xonqa"),
        ("Xazorasp t.", "xazorasp"), ("Xiva t.", "xiva_t"), ("Yangiarik t.", "yangiarik"),
        ("Yangibozor t.", "yangibozor")
    ],
    "qash": [
        ("Qarshi sh.", "qarshi"), ("Shahrisabz sh.", "shahrisabz"), ("Chiroqchi t.", "chiroqchi"),
        ("Dehqonobod t.", "dehqonobod"), ("G'uzor t.", "guzor"), ("Qamashi t.", "kamashi"),
        ("Karbi t.", "karbi"), ("Kasbi t.", "kasbi"), ("Kitob t.", "kitob"),
        ("Koson t.", "koson"), ("Mirishkor t.", "mirishkor"), ("Muborak t.", "muborak"),
        ("Nishon t.", "nishon"), ("Shahrisabz t.", "shahrisabz_t"), ("Yakkabog' t.", "yakkabog"),
        ("Ko'kdala t.", "kukdala")
    ],
    "sur": [
        ("Termiz sh.", "termiz_sh"), ("Angor t.", "angor"), ("Boysun t.", "boysun"),
        ("Denov t.", "denov"), ("Jarqo'rg'on t.", "jarqurgon"), ("Qiziriq t.", "qiziriq"),
        ("Qumqo'rg'on t.", "qumqurgon"), ("Muzrabot t.", "muzrabot"), ("Oltinsoy t.", "oltinsoy"),
        ("Sariosiyo t.", "sariosiyo"), ("Sherobod t.", "sherobod"), ("Sho'rchi t.", "shurchi"),
        ("Termiz t.", "termiz_t"), ("Uzun t.", "uzun")
    ],
    "jiz": [
        ("Jizzax sh.", "jiz_sh"), ("Arnasoy t.", "arnasoy"), ("Baxmal t.", "baxmal"),
        ("Do'stlik t.", "dostlik"), ("Forish t.", "forish"), ("G'allaorol t.", "gallaorol"),
        ("Sharof Rashidov t.", "sh_rashidov"), ("Mirzacho'l t.", "mirzachol"), ("Paxtakor t.", "paxtakor"),
        ("Yangiobod t.", "yangiobod"), ("Zafarobod t.", "zafarobod"), ("Zarbdor t.", "zarbdor"), ("Zomin t.", "zomin")
    ],
    "sir": [
        ("Guliston sh.", "guliston"), ("Shirin sh.", "shirin_s"), ("Yangiyer sh.", "yangiyer"),
        ("Boyovut t.", "boyovut"), ("Guliston t.", "guliston_t"), ("Oqoltin t.", "oqoltin"),
        ("Sardoba t.", "sardoba"), ("Sayxunobod t.", "sayxun"), ("Sirdaryo t.", "sirdaryo_t"),
        ("Xovos t.", "xovos"), ("Mirzaobod t.", "mirzaobod")
    ],
    "qorq": [
        ("Nukus sh.", "nukus"), ("Amudaryo t.", "amudaryo"), ("Beruniy t.", "betuniy"),
        ("Chimboy t.", "chimboy"), ("Ellikqal'a t.", "ellikqala"), ("Kegeyli t.", "kegeyli"),
        ("Mo'ynoq t.", "moynoq"), ("Nukus t.", "nukus_t"), ("Qonliko'l t.", "qonlikol"),
        ("Qo'ng'irot t.", "qongirot"), ("Qorao'zak t.", "qoraozak"), ("Shumanay t.", "shumanay"),
        ("Taxtakopir t.", "taxtakopir"), ("To'rtko'l t.", "turtkol"), ("Xo'jayli t.", "xojayli"),
        ("Taxiatosh sh.", "taxiatosh"), ("Bo'zatov t.", "bozatov")
    ]
}

KATEGORIYALAR = [
    ("🏠 Uy-joy", "uy"), ("🚗 Avtomobil", "avto"), ("📱 Telefon", "tel"),
    ("💻 Kompyuter", "comp"), ("🛋 Mebel", "meb"), ("👕 Kiyim", "kiym"),
    ("🐄 Qishloq xo'jaligi", "qshq"), ("🔧 Asbob-uskuna", "asbob"),
    ("📚 Kitob", "ktb"), ("🎮 O'yin-kulgi", "oyn"), ("💍 Zargarlik", "zgar"),
    ("🏋 Sport", "sprt"), ("🐶 Hayvonlar", "hayv"), ("💼 Biznes", "biz"),
    ("💼 Ish o'rni", "ish"), ("🏠 Ijaraga uy", "ijara"), ("🚚 Yetkazib berish", "yetkaz"),
    ("🚗 Hamrohlik taksi", "poputka"), ("🔎 Yo'qolgan/Topilgan", "topilma"),
    ("🔁 Boshqa", "bshq")
]

# 📞 Tez yordam raqamlari (statik ma'lumot)
TEZ_YORDAM_RAQAMLARI = [
    ("🚒 Yong'in xizmati", "101"),
    ("👮 Politsiya", "102"),
    ("🚑 Tez tibbiy yordam", "103"),
    ("🔧 Gaz xizmati", "104"),
    ("💧 Suv/kanalizatsiya", "1055"),
    ("⚡ Elektr xizmati", "1054"),
]

user_state = {}
user_data_temp = {}

# ============================================================
#  MARKDOWN UCHUN XAVFSIZ MATN (foydalanuvchi kiritgan matnni escape qilish)
# ============================================================
# Foydalanuvchi tavsif/sarlavha/narx ichiga "*", "_", "[", "`" belgilarini
# yozib qo'ysa, Telegram "can't parse entities" xatoligi bilan xabarni
# UMUMAN yubormay qo'yardi (shu sabab e'lon kanalga chiqmay qolgan bo'lishi
# ehtimoli katta). Endi bunday belgilar avtomatik "escape" qilinadi.
def md_escape(matn):
    if matn is None:
        return ""
    matn = str(matn)
    for belgi in ["\\", "_", "*", "`", "["]:
        matn = matn.replace(belgi, "\\" + belgi)
    return matn


def xavfsiz_yuborish(chat_id, matn, reply_markup=None, parse_mode="Markdown", **kwargs):
    """Markdown bilan yuborishga urinadi; agar Telegram parse xatoligi bersa,
    formatsiz (oddiy matn) qilib qayta yuboradi — shunda xabar HECH BO'LMAGANDA
    yetib boradi va sabab bot.log'da ko'rinadi."""
    try:
        return bot.send_message(chat_id, matn, parse_mode=parse_mode, reply_markup=reply_markup, **kwargs)
    except Exception as e:
        log.error(f"Markdown bilan yuborishda xatolik ({chat_id}): {e} — formatsiz qayta urinilmoqda")
        try:
            return bot.send_message(chat_id, matn, reply_markup=reply_markup, **kwargs)
        except Exception as e2:
            log.error(f"Formatsiz ham yuborilmadi ({chat_id}): {e2}")
            raise


def xavfsiz_photo_yuborish(chat_id, photo, caption, reply_markup=None, parse_mode="Markdown", **kwargs):
    try:
        return bot.send_photo(chat_id, photo, caption=caption, parse_mode=parse_mode, reply_markup=reply_markup, **kwargs)
    except Exception as e:
        log.error(f"Markdown bilan rasm yuborishda xatolik ({chat_id}): {e} — formatsiz qayta urinilmoqda")
        try:
            return bot.send_photo(chat_id, photo, caption=caption, reply_markup=reply_markup, **kwargs)
        except Exception as e2:
            log.error(f"Formatsiz rasm ham yuborilmadi ({chat_id}): {e2}")
            raise


# ============================================================
#  FAYLLARGA XAVFSIZ (THREAD-SAFE, ATOMIK) YOZISH
# ============================================================
_file_locks = {}
_locks_guard = threading.Lock()


def _get_lock(path):
    with _locks_guard:
        if path not in _file_locks:
            _file_locks[path] = threading.Lock()
        return _file_locks[path]


def _load_json(path):
    lock = _get_lock(path)
    with lock:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                log.error(f"{path} o'qishda xatolik: {e}")
                return {}
        return {}


def _save_json(path, data):
    lock = _get_lock(path)
    with lock:
        tmp_path = path + ".tmp"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, path)
        except Exception as e:
            log.error(f"{path} yozishda xatolik: {e}")


# ============================================================
#  MA'LUMOTLAR BAZASI FUNKSIYALARI (USERS)
# ============================================================
def load_db():
    return _load_json(DB_FILE)


def save_db(data):
    _save_json(DB_FILE, data)


def get_user(user_id):
    db = load_db()
    uid = str(user_id)
    if uid not in db:
        db[uid] = {
            "name": "", "tg_username": "", "phone": "", "premium": False,
            "is_banned": False, "elon_count": 0, "elonlar": [], "sevimlilar": [],
            "referral_count": 0, "referred_by": None,
            "joined_date": datetime.now().strftime("%d.%m.%Y"),
            "balance": 0, "balance_tarix": [],
            "bildirishnoma": True, "tungi_rejim": False, "promo_ishlatilgan": [],
            "xp": 0, "streak_count": 0, "last_checkin": None, "ai_ishlatish_soni": 0,
            "taksi_km_jami": 0
        }
        save_db(db)
    return db[uid]


def update_user(user_id, data):
    db = load_db()
    db[str(user_id)] = data
    save_db(db)


# ============================================================
#  E'LONLAR BAZASI FUNKSIYALARI
# ============================================================
def load_elonlar():
    return _load_json(ELON_FILE)


def save_elonlar(data):
    _save_json(ELON_FILE, data)


def yangi_elon_id():
    elonlar = load_elonlar()
    if not elonlar:
        return "1"
    return str(max(int(k) for k in elonlar.keys()) + 1)


def elon_qoshish(elon_id, elon_obj):
    elonlar = load_elonlar()
    elonlar[elon_id] = elon_obj
    save_elonlar(elonlar)


def elon_ochirish(elon_id):
    elonlar = load_elonlar()
    if elon_id in elonlar:
        elonlar[elon_id]["status"] = "ochirilgan"
        save_elonlar(elonlar)
        return True
    return False


def elon_faolmi(elon):
    if elon.get("status") != "active":
        return False
    try:
        created = datetime.strptime(elon["created_at"], "%d.%m.%Y %H:%M")
    except Exception:
        return True
    return datetime.now() - created < timedelta(days=ELON_MUDDATI_KUN)


def faol_elonlar_royxati(kategoriya_kod=None, qidiruv=None):
    elonlar = load_elonlar()
    natija = []
    for eid, e in elonlar.items():
        if not elon_faolmi(e):
            continue
        if kategoriya_kod and e.get("kategoriya_kod") != kategoriya_kod:
            continue
        if qidiruv:
            matn = (e.get("sarlavha", "") + " " + e.get("tavsif", "")).lower()
            if qidiruv.lower() not in matn:
                continue
        natija.append(eid)

    def _sort_kaliti(eid):
        e = elonlar[eid]
        boost_ts = e.get("boost_at")
        asosiy_qiymat = boost_ts if boost_ts else int(eid)
        return (not e.get("is_vip", False), -asosiy_qiymat)

    natija.sort(key=_sort_kaliti)
    return natija


def elon_matni(eid, elon, tolik=True):
    vip_belgi = "🔥 VIP\n" if elon.get("is_vip") else ""
    lokatsiya_matn = f"[Xaritada ko'rish]({elon['location']})" if elon.get("location") else "Kiritilmagan"
    matn = (
        f"{vip_belgi}"
        f"🆔 №{eid}\n"
        f"📌 **{md_escape(elon['sarlavha'])}**\n"
        f"📂 Kategoriya: {md_escape(elon['kategoriya'])}\n"
        f"📍 Hudud: {md_escape(elon['hudud'])}, {md_escape(elon['tuman'])}\n"
        f"💰 Narx: {md_escape(elon['narx'])}\n"
    )
    if tolik:
        matn += (
            f"📝 Tavsif: {md_escape(elon['tavsif'])}\n"
            f"📍 Lokatsiya: {lokatsiya_matn}\n\n"
            f"👤 Aloqa: {md_escape(elon.get('egasi_ism',''))}\n"
            f"🔗 Profil: {md_escape(elon.get('egasi_username',''))}\n"
        )
    return matn


# ============================================================
#  IMTIXON ARIZALARI BAZASI FUNKSIYALARI
# ============================================================
def load_imtixon():
    return _load_json(IMTIXON_FILE)


def save_imtixon(data):
    _save_json(IMTIXON_FILE, data)


def yangi_ariza_id():
    arizalar = load_imtixon()
    if not arizalar:
        return "EX1"
    raqamlar = [int(k[2:]) for k in arizalar.keys() if k.startswith("EX") and k[2:].isdigit()]
    return f"EX{max(raqamlar, default=0) + 1}"


def ariza_qoshish(ariza_id, obj):
    arizalar = load_imtixon()
    arizalar[ariza_id] = obj
    save_imtixon(arizalar)


# ============================================================
#  PDF HUJJAT YARATISH FUNKSIYALARI
# ============================================================
PDF_TMP_DIR = "pdf_tmp"
os.makedirs(PDF_TMP_DIR, exist_ok=True)


def ruxsatnoma_pdf_yarat(ariza_id, ariza):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 12, "ABITURIYENT RUXSATNOMASI", ln=True, align="C")
    pdf.set_font("Helvetica", "", 11)
    pdf.ln(4)
    pdf.cell(0, 8, f"Ariza raqami: {ariza_id}", ln=True)
    pdf.cell(0, 8, f"F.I.Sh: {ariza.get('ism', '')}", ln=True)
    pdf.cell(0, 8, f"Fan: {ariza.get('fan', '')}", ln=True)
    if ariza.get("pasport"):
        pdf.cell(0, 8, f"Pasport/ID seriya-raqami: {ariza['pasport']}", ln=True)
    pdf.cell(0, 8, f"Telefon: {ariza.get('telefon', '')}", ln=True)
    pdf.cell(0, 8, f"Ariza sanasi: {ariza.get('sana', '')}", ln=True)
    pdf.ln(6)
    pdf.set_font("Helvetica", "I", 10)
    pdf.multi_cell(0, 6, "Ushbu hujjat botimiz tomonidan tasdiqlangan ariza asosida "
                         "avtomatik shakllantirilgan. Imtihon kunida ehtiyot uchun ID-kartangizni "
                         "olib boring.")
    path = os.path.join(PDF_TMP_DIR, f"ruxsatnoma_{ariza_id}.pdf")
    pdf.output(path)
    return path


def natija_pdf_yarat(ariza_id, ariza):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 12, "IMTIHON NATIJASI", ln=True, align="C")
    pdf.set_font("Helvetica", "", 11)
    pdf.ln(4)
    pdf.cell(0, 8, f"Ariza raqami: {ariza_id}", ln=True)
    pdf.cell(0, 8, f"F.I.Sh: {ariza.get('ism', '')}", ln=True)
    pdf.cell(0, 8, f"Fan: {ariza.get('fan', '')}", ln=True)
    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 10, f"BALL: {ariza.get('ball', '')}", ln=True)
    path = os.path.join(PDF_TMP_DIR, f"natija_{ariza_id}.pdf")
    pdf.output(path)
    return path


# ============================================================
#  RUXSATNOMALAR BAZASI FUNKSIYALARI
# ============================================================
def load_ruxsatnoma():
    return _load_json(RUXSATNOMA_FILE)


def save_ruxsatnoma(data):
    _save_json(RUXSATNOMA_FILE, data)


def yangi_ruxsatnoma_id():
    ruxsatnomalar = load_ruxsatnoma()
    if not ruxsatnomalar:
        return "RX1"
    raqamlar = [int(k[2:]) for k in ruxsatnomalar.keys() if k.startswith("RX") and k[2:].isdigit()]
    return f"RX{max(raqamlar, default=0) + 1}"


def ruxsatnoma_qoshish(rid, obj):
    ruxsatnomalar = load_ruxsatnoma()
    ruxsatnomalar[rid] = obj
    save_ruxsatnoma(ruxsatnomalar)


# ============================================================
#  🚖 TAKSI BUYURTMALARI VA HAYDOVCHILAR BAZASI
# ============================================================
def load_taksi():
    return _load_json(TAKSI_FILE)


def save_taksi(data):
    _save_json(TAKSI_FILE, data)


def yangi_taksi_id():
    buyurtmalar = load_taksi()
    if not buyurtmalar:
        return "T1"
    raqamlar = [int(k[1:]) for k in buyurtmalar.keys() if k.startswith("T") and k[1:].isdigit()]
    return f"T{max(raqamlar, default=0) + 1}"


def load_haydovchilar():
    return _load_json(HAYDOVCHI_FILE)


def save_haydovchilar(data):
    _save_json(HAYDOVCHI_FILE, data)


def masofa_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def narxni_hisobla(km):
    narx = TAKSI_BOSHLANGICH_NARX + km * TAKSI_KM_NARXI
    return round(narx / 500) * 500


def som_format(narx):
    return f"{narx:,.0f}".replace(",", " ") + " so'm"


def haydovchi_reyting_matni(h):
    soni = h.get("rating_count", 0)
    if soni == 0:
        return "⭐ Baholanmagan"
    orta = h.get("rating_sum", 0) / soni
    return f"⭐ {orta:.1f} ({soni} ta baho)"


# ============================================================
#  🚫 DINAMIK TAQIQLANGAN SO'ZLAR RO'YXATI (admin boshqara oladi)
# ============================================================
def load_blacklist():
    data = _load_json(BLACKLIST_FILE)
    if not data or "sozlar" not in data:
        data = {"sozlar": list(TAQIQLANGAN_SOZLAR_BOSHLANGICH)}
        _save_json(BLACKLIST_FILE, data)
    return data["sozlar"]


def save_blacklist(sozlar):
    _save_json(BLACKLIST_FILE, {"sozlar": sozlar})


def matnda_taqiqlangan_soz_bormi(matn):
    sozlar = load_blacklist()
    matn_l = matn.lower()
    return any(soz in matn_l for soz in sozlar)


# ============================================================
#  📰 YANGILIKLAR ARXIVI VA 📅 TADBIRLAR TAXTASI
# ============================================================
def load_news():
    data = _load_json(NEWS_FILE)
    return data.get("yangiliklar", []) if data else []


def news_qoshish(matn):
    data = _load_json(NEWS_FILE) or {"yangiliklar": []}
    data.setdefault("yangiliklar", []).append({
        "sana": datetime.now().strftime("%d.%m.%Y %H:%M"), "matn": matn
    })
    _save_json(NEWS_FILE, data)


def load_events():
    data = _load_json(EVENTS_FILE)
    return data.get("tadbirlar", []) if data else []


def event_qoshish(matn):
    data = _load_json(EVENTS_FILE) or {"tadbirlar": []}
    data.setdefault("tadbirlar", []).append({
        "sana": datetime.now().strftime("%d.%m.%Y %H:%M"), "matn": matn
    })
    _save_json(EVENTS_FILE, data)


def load_quizzes():
    return _load_json(QUIZ_FILE)


def save_quizzes(data):
    _save_json(QUIZ_FILE, data)


# ============================================================
#  OBUNA TEKSHIRISH
# ============================================================
def check_sub(user_id):
    if user_id == ADMIN_ID:
        return True
    try:
        member = bot.get_chat_member(KANAL_ID, user_id)
        return member.status in ['creator', 'administrator', 'member', 'restricted']
    except Exception as e:
        log.warning(f"Obuna tekshirishda xatolik ({user_id}): {e}")
        return False


def send_sub_message(user_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📢 Guruhga a'zo bo'lish", url=GURUH_LINK))
    markup.add(types.InlineKeyboardButton("✅ Tekshirish", callback_data="check_subscription"))
    bot.send_message(
        user_id,
        "👋 Botimizdan foydalanishdan oldin guruhimizga a'zo bo'lishingiz kerak.\n\n"
        "👉 Guruhga a'zo bo'lib, keyin '✅ Tekshirish' tugmasini bosing!",
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data == "check_subscription")
def check_sub_callback(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    if check_sub(uid):
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception as e:
            log.warning(f"Xabar o'chirishda xatolik: {e}")
        bot.send_message(uid, "✅ Rahmat! Obuna tasdiqlandi. /start buyrug'ini bosing.")
    else:
        bot.send_message(uid, "❌ Siz hali guruhga a'zo bo'lmadingiz. Iltimos, a'zo bo'ling va qayta tekshiring.")


def check_ban(message):
    uid = message.from_user.id
    user = get_user(uid)
    if user.get("is_banned", False):
        bot.send_message(uid, f"❌ Siz botdan bloklangansiz! Murojaat uchun admin: @{ADMIN_USERNAME}")
        return True
    return False


# ============================================================
#  🛡 ADMIN NAZORAT MIDDLEWARE — HAR BIR HARAKATNI KO'RSATISH
# ============================================================
_flood_tracker = {}
FLOOD_LIMIT = 5
FLOOD_OYNA_SONIYA = 10


def _flood_tekshir(uid):
    now = time.time()
    times = _flood_tracker.get(uid, [])
    times = [t for t in times if now - t < FLOOD_OYNA_SONIYA]
    times.append(now)
    _flood_tracker[uid] = times
    return len(times) > FLOOD_LIMIT


class AdminNazoratMiddleware(BaseMiddleware):
    def __init__(self):
        super().__init__()
        self.update_types = ['message', 'callback_query']

    def pre_process(self, update_obj, data):
        try:
            user = getattr(update_obj, 'from_user', None)
            if not user or user.id == ADMIN_ID:
                return

            if _flood_tekshir(user.id):
                return

            uname = f"@{user.username}" if user.username else "Yo'q"
            ism = f"{user.first_name or ''} {user.last_name or ''}".strip() or "Noma'lum"

            if hasattr(update_obj, 'data') and update_obj.data is not None:
                harakat = f"🔘 Tugma bosdi: `{md_escape(update_obj.data)}`"
            elif getattr(update_obj, 'content_type', None) == 'text':
                matn = update_obj.text or ""
                if len(matn) > 300:
                    matn = matn[:300] + "…"
                harakat = f"✍️ Xabar yozdi: {md_escape(matn)}"
            elif hasattr(update_obj, 'content_type'):
                harakat = f"📎 Yubordi: {update_obj.content_type}"
            else:
                harakat = "❓ Noma'lum harakat"

            log_matni = (
                f"👁 **Foydalanuvchi faoliyati**\n\n"
                f"👤 Ism: {md_escape(ism)}\n"
                f"🔗 Username: {md_escape(uname)}\n"
                f"🆔 ID: `{user.id}`\n\n"
                f"{harakat}"
            )
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton("🚫 Tezkor Ban", callback_data=f"quickban_{user.id}"),
                types.InlineKeyboardButton("🔍 Profilni ko'rish", callback_data=f"quickview_{user.id}"),
            )
            xavfsiz_yuborish(ADMIN_ID, log_matni, reply_markup=markup)
        except Exception as e:
            log.error(f"AdminNazoratMiddleware xatoligi: {e}")

    def post_process(self, update_obj, data, exception=None):
        if exception:
            log.error(f"Handler xatoligi: {exception}")


bot.setup_middleware(AdminNazoratMiddleware())


def _foydalanuvchi_profil_matni(uid_str, user):
    holat = "🚫 Bloklangan" if user.get("is_banned") else "✅ Faol"
    premium = "💎 Ha" if user.get("premium") else "❌ Yo'q"
    return (
        f"👤 **Foydalanuvchi profili**\n\n"
        f"🆔 ID: `{uid_str}`\n"
        f"📛 Ism: {md_escape(user.get('name', 'Kiritilmagan'))}\n"
        f"🔗 Username: {md_escape(user.get('tg_username', 'Kiritilmagan'))}\n"
        f"📞 Telefon: {md_escape(user.get('phone', 'Kiritilmagan'))}\n"
        f"💎 Premium: {premium}\n"
        f"📌 Holat: {holat}\n"
        f"📢 E'lonlari: {len(user.get('elonlar', []))} ta\n"
        f"🎁 Referal: {user.get('referral_count', 0)} ta\n"
        f"📅 Qo'shilgan: {user.get('joined_date', '-')}"
    )


def _profil_boshqaruv_markup(uid_str, user):
    markup = types.InlineKeyboardMarkup(row_width=2)
    if user.get("is_banned"):
        markup.add(types.InlineKeyboardButton("✅ Blokdan chiqarish", callback_data=f"adm_unban_{uid_str}"))
    else:
        markup.add(types.InlineKeyboardButton("🚫 Bloklash", callback_data=f"adm_ban_{uid_str}"))
    if user.get("premium"):
        markup.add(types.InlineKeyboardButton("➖ Premiumni olib tashlash", callback_data=f"adm_unprem_{uid_str}"))
    else:
        markup.add(types.InlineKeyboardButton("💎 Premium berish", callback_data=f"adm_prem_{uid_str}"))
    markup.add(types.InlineKeyboardButton("✉️ Xabar yuborish", callback_data=f"adm_msg_{uid_str}"))
    return markup


@bot.callback_query_handler(func=lambda call: call.data.startswith("quickban_") and call.from_user.id == ADMIN_ID)
def quickban_callback(call):
    uid_str = call.data.replace("quickban_", "")
    bot.answer_callback_query(call.id, "Bloklanmoqda...")
    db = load_db()
    if uid_str in db:
        db[uid_str]["is_banned"] = True
        save_db(db)
        bot.send_message(ADMIN_ID, f"✅ `{uid_str}` muvaffaqiyatli bloklandi.", parse_mode="Markdown")
        try:
            bot.send_message(int(uid_str), f"❌ Siz botdan bloklandingiz. Murojaat: @{ADMIN_USERNAME}")
        except Exception as e:
            log.warning(f"Ban xabarini yuborib bo'lmadi: {e}")
    else:
        bot.send_message(ADMIN_ID, "❌ Bu foydalanuvchi hali /start bosmagan, bazada yo'q.")


@bot.callback_query_handler(func=lambda call: call.data.startswith("quickview_") and call.from_user.id == ADMIN_ID)
def quickview_callback(call):
    uid_str = call.data.replace("quickview_", "")
    bot.answer_callback_query(call.id)
    db = load_db()
    user = db.get(uid_str)
    if not user:
        bot.send_message(ADMIN_ID, "❌ Bu foydalanuvchi bazada topilmadi.")
        return
    xavfsiz_yuborish(ADMIN_ID, _foydalanuvchi_profil_matni(uid_str, user),
                     reply_markup=_profil_boshqaruv_markup(uid_str, user))


@bot.callback_query_handler(func=lambda call: call.data.startswith("adm_") and call.from_user.id == ADMIN_ID)
def admin_profil_amallar(call):
    bot.answer_callback_query(call.id)
    try:
        amal, uid_str = call.data.split("_", 2)[1], call.data.split("_", 2)[2]
    except Exception:
        return

    if amal == "msg":
        user_state[ADMIN_ID] = "admin_shaxsiy_xabar"
        user_data_temp[ADMIN_ID] = {"maqsad_uid": uid_str}
        bot.send_message(ADMIN_ID, f"✉️ `{uid_str}` ga yuboriladigan xabarni kiriting:", parse_mode="Markdown")
        return

    db = load_db()
    user = db.get(uid_str)
    if not user:
        bot.send_message(ADMIN_ID, "❌ Foydalanuvchi topilmadi.")
        return

    if amal == "ban":
        user["is_banned"] = True
        xabar_uid = f"❌ Siz botdan bloklandingiz. Murojaat: @{ADMIN_USERNAME}"
    elif amal == "unban":
        user["is_banned"] = False
        xabar_uid = "✅ Siz blokdan chiqarildingiz. Botdan yana foydalanishingiz mumkin."
    elif amal == "prem":
        user["premium"] = True
        xabar_uid = "🎉 Sizga Premium 💎 maqomi berildi!"
    elif amal == "unprem":
        user["premium"] = False
        xabar_uid = None
    else:
        return

    db[uid_str] = user
    save_db(db)

    try:
        if xabar_uid:
            bot.send_message(int(uid_str), xabar_uid)
    except Exception as e:
        log.warning(f"Foydalanuvchiga xabar yuborilmadi: {e}")

    xavfsiz_yuborish(ADMIN_ID, _foydalanuvchi_profil_matni(uid_str, user),
                     reply_markup=_profil_boshqaruv_markup(uid_str, user))


@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == "admin_shaxsiy_xabar" and m.from_user.id == ADMIN_ID)
def admin_shaxsiy_xabar_yuborish(message):
    maqsad_uid = user_data_temp.get(ADMIN_ID, {}).get("maqsad_uid")
    user_state.pop(ADMIN_ID, None)
    user_data_temp.pop(ADMIN_ID, None)
    if not maqsad_uid:
        return
    try:
        bot.send_message(int(maqsad_uid), f"📩 Admindan xabar:\n\n{message.text}")
        bot.send_message(ADMIN_ID, "✅ Xabar yuborildi.")
    except Exception as e:
        bot.send_message(ADMIN_ID, f"❌ Xabar yuborilmadi: {e}")


# ============================================================
#  💬 IKKI TOMONLAMA SUPPORT (Admin bilan bog'lanish)
# ============================================================
@bot.message_handler(func=lambda m: m.text == "💬 Admin bilan bog'lanish")
def support_start(message):
    if check_ban(message): return
    uid = message.from_user.id
    if uid == ADMIN_ID:
        return
    user_state[uid] = "support_msg"
    bot.send_message(uid, "💬 Adminga yuboriladigan xabaringizni yozing:", reply_markup=types.ReplyKeyboardRemove())


@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == "support_msg")
def support_msg_yuborish(message):
    uid = message.from_user.id
    user_state.pop(uid, None)
    user = get_user(uid)

    matn = (
        f"💬 **Yangi murojaat**\n\n"
        f"👤 {md_escape(user.get('name','?'))}\n"
        f"🔗 {md_escape(user.get('tg_username','?'))}\n"
        f"🆔 `{uid}`\n\n"
        f"✉️ {md_escape(message.text)}"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("↩️ Javob berish", callback_data=f"supreply_{uid}"))
    try:
        xavfsiz_yuborish(ADMIN_ID, matn, reply_markup=markup)
        bot.send_message(uid, "✅ Murojaatingiz adminga yuborildi. Tez orada javob berishadi.",
                         reply_markup=get_main_keyboard(uid))
    except Exception as e:
        log.error(f"Support xabari yuborilmadi: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("supreply_") and call.from_user.id == ADMIN_ID)
def support_reply_start(call):
    uid_str = call.data.replace("supreply_", "")
    bot.answer_callback_query(call.id)
    user_state[ADMIN_ID] = "support_reply_msg"
    user_data_temp[ADMIN_ID] = {"maqsad_uid": uid_str}
    bot.send_message(ADMIN_ID, f"↩️ `{uid_str}` ga javobingizni yozing:", parse_mode="Markdown")


@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == "support_reply_msg" and m.from_user.id == ADMIN_ID)
def support_reply_yuborish(message):
    maqsad_uid = user_data_temp.get(ADMIN_ID, {}).get("maqsad_uid")
    user_state.pop(ADMIN_ID, None)
    user_data_temp.pop(ADMIN_ID, None)
    if not maqsad_uid:
        return
    try:
        bot.send_message(int(maqsad_uid), f"💬 **Admin javobi:**\n\n{message.text}", parse_mode="Markdown")
        bot.send_message(ADMIN_ID, "✅ Javob yuborildi.")
    except Exception as e:
        bot.send_message(ADMIN_ID, f"❌ Yuborilmadi: {e}")


# ============================================================
#  /find — ADMIN UCHUN TEZKOR FOYDALANUVCHI QIDIRUV
# ============================================================
@bot.message_handler(commands=['find'])
def admin_find_user(message):
    if message.from_user.id != ADMIN_ID:
        return
    qismlar = message.text.split(maxsplit=1)
    if len(qismlar) < 2:
        bot.reply_to(message, "⚠️ Format: `/find 123456789` yoki `/find @username`", parse_mode="Markdown")
        return

    qidiruv = qismlar[1].strip()
    db = load_db()

    if qidiruv.startswith("@"):
        topilgan = None
        for uid_str, u in db.items():
            if u.get("tg_username", "").lower() == qidiruv.lower():
                topilgan = uid_str
                break
        if not topilgan:
            bot.reply_to(message, "❌ Bunday username bilan foydalanuvchi topilmadi.")
            return
        uid_str, user = topilgan, db[topilgan]
    else:
        uid_str = qidiruv
        user = db.get(uid_str)
        if not user:
            bot.reply_to(message, "❌ Bunday ID bilan foydalanuvchi topilmadi.")
            return

    xavfsiz_yuborish(ADMIN_ID, _foydalanuvchi_profil_matni(uid_str, user),
                     reply_markup=_profil_boshqaruv_markup(uid_str, user))


# ============================================================
#  /admin — ADMIN BOSH MENYUSI
# ============================================================
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return
    matn = (
        "🛠 **Admin panel**\n\n"
        "/find `ID yoki @username` — foydalanuvchini topish\n"
        "/ban `ID` — bloklash\n"
        "/unban `ID` — blokdan chiqarish\n"
        "/premium `ID` — Premium berish\n"
        "/unpremium `ID` — Premium olib tashlash\n"
        "/ball `ARIZA_ID BALL` — imtihon ballini qo'yish\n"
        "/export — foydalanuvchilar CSV\n"
        "/export_haydovchi — haydovchilar CSV\n"
        "/push `ELON_ID` — e'lonni ro'yxat boshiga chiqarish\n"
        "/top — referal bo'yicha TOP-15\n"
        "/backup — barcha JSON fayllarni yuklab olish\n"
        "/words — taqiqlangan so'zlar ro'yxati\n"
        "/addword `so'z` — taqiqlangan so'z qo'shish\n"
        "/delword `so'z` — taqiqlangan so'zni olib tashlash\n\n"
        "📢 Hammaga xabar yuborish — asosiy menyudagi tugma orqali\n"
        "💬 Foydalanuvchi yozganida — sizga \"↩️ Javob berish\" tugmasi bilan keladi"
    )
    bot.send_message(ADMIN_ID, matn, parse_mode="Markdown", reply_markup=get_main_keyboard(ADMIN_ID))


# ============================================================
#  /push — E'LONNI TEPAGA CHIQARISH (admin)
# ============================================================
@bot.message_handler(commands=['push'])
def admin_push_elon(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        eid = message.text.split()[1]
    except IndexError:
        bot.reply_to(message, "⚠️ Format: `/push ELON_ID` (masalan: /push 12)", parse_mode="Markdown")
        return

    elonlar = load_elonlar()
    if eid not in elonlar:
        bot.reply_to(message, "❌ Bunday e'lon topilmadi.")
        return

    elonlar[eid]["boost_at"] = int(time.time())
    save_elonlar(elonlar)
    bot.reply_to(message, f"⚡ E'lon №{eid} ro'yxat boshiga chiqarildi.")

    try:
        bot.send_message(elonlar[eid]["user_id"], f"⚡ Sizning №{eid} e'loningiz ro'yxat boshiga chiqarildi!")
    except Exception as e:
        log.warning(f"Push xabari yuborilmadi: {e}")


# ============================================================
#  /top — REFERAL REYTINGI (admin)
# ============================================================
@bot.message_handler(commands=['top'])
def admin_top_referral(message):
    if message.from_user.id != ADMIN_ID: return
    db = load_db()
    royxat = sorted(db.items(), key=lambda x: x[1].get("referral_count", 0), reverse=True)[:15]
    if not royxat:
        bot.reply_to(message, "📊 Hozircha ma'lumot yo'q.")
        return
    matn = "🏆 **Referal bo'yicha TOP-15:**\n\n"
    for i, (uid_str, u) in enumerate(royxat, 1):
        matn += f"{i}. {md_escape(u.get('name','?'))} — {u.get('referral_count', 0)} ta (`{uid_str}`)\n"
    xavfsiz_yuborish(message.chat.id, matn)


# ============================================================
#  /backup — BARCHA JSON FAYLLARNI YUKLAB OLISH (admin)
# ============================================================
@bot.message_handler(commands=['backup'])
def admin_backup(message):
    if message.from_user.id != ADMIN_ID: return
    fayllar = [DB_FILE, ELON_FILE, IMTIXON_FILE, RUXSATNOMA_FILE, TAKSI_FILE, HAYDOVCHI_FILE, BLACKLIST_FILE]
    yuborildi = 0
    for f in fayllar:
        if os.path.exists(f):
            try:
                with open(f, "rb") as fh:
                    bot.send_document(ADMIN_ID, fh, caption=f"💾 {f}")
                yuborildi += 1
            except Exception as e:
                log.error(f"Backup xatoligi ({f}): {e}")
    bot.send_message(ADMIN_ID, f"✅ Zaxira nusxa tayyor: {yuborildi} ta fayl yuborildi.")


# ============================================================
#  🚫 SO'ZLARNI BOSHQARISH (admin)
# ============================================================
@bot.message_handler(commands=['words'])
def admin_words_list(message):
    if message.from_user.id != ADMIN_ID: return
    sozlar = load_blacklist()
    matn = "🚫 **Taqiqlangan so'zlar ro'yxati:**\n\n" + ", ".join(sozlar) if sozlar else "Ro'yxat bo'sh."
    bot.reply_to(message, matn, parse_mode="Markdown")


@bot.message_handler(commands=['addword'])
def admin_add_word(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        soz = message.text.split(maxsplit=1)[1].strip().lower()
    except IndexError:
        bot.reply_to(message, "⚠️ Format: `/addword so'z`", parse_mode="Markdown")
        return
    sozlar = load_blacklist()
    if soz in sozlar:
        bot.reply_to(message, "ℹ️ Bu so'z ro'yxatda allaqachon bor.")
        return
    sozlar.append(soz)
    save_blacklist(sozlar)
    bot.reply_to(message, f"✅ `{soz}` taqiqlangan so'zlar ro'yxatiga qo'shildi.", parse_mode="Markdown")


@bot.message_handler(commands=['delword'])
def admin_del_word(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        soz = message.text.split(maxsplit=1)[1].strip().lower()
    except IndexError:
        bot.reply_to(message, "⚠️ Format: `/delword so'z`", parse_mode="Markdown")
        return
    sozlar = load_blacklist()
    if soz not in sozlar:
        bot.reply_to(message, "❌ Bu so'z ro'yxatda yo'q.")
        return
    sozlar.remove(soz)
    save_blacklist(sozlar)
    bot.reply_to(message, f"✅ `{soz}` ro'yxatdan olib tashlandi.", parse_mode="Markdown")


# ============================================================
#  📊 KUNLIK SAVOLNOMA / VIKTORINA (XP tizimi) — admin boshqaradi
# ============================================================
@bot.message_handler(commands=['savol'])
def admin_savol_yuborish(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        qismlar = message.text.split(maxsplit=1)[1].split("|")
        savol_matni = qismlar[0].strip()
        variantlar = [v.strip() for v in qismlar[1:-1]]
        togri_idx = int(qismlar[-1].strip()) - 1
        if not (0 <= togri_idx < len(variantlar)) or len(variantlar) < 2:
            raise ValueError
    except Exception:
        bot.reply_to(
            message,
            "⚠️ Format: `/savol Savol matni?|Variant1|Variant2|Variant3|Variant4|TogriRaqam`\n"
            "Masalan: `/savol Poytaxtimiz qaysi shahar?|Samarqand|Toshkent|Buxoro|Xiva|2`",
            parse_mode="Markdown"
        )
        return

    quizzes = load_quizzes() or {}
    qid = str(int(time.time()))
    quizzes[qid] = {"savol": savol_matni, "variantlar": variantlar, "togri": togri_idx, "javob_berganlar": {}}
    save_quizzes(quizzes)

    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, v in enumerate(variantlar):
        markup.add(types.InlineKeyboardButton(v, callback_data=f"quizans_{qid}_{i}"))

    db = load_db()
    yuborildi = 0
    for uid_str in db.keys():
        try:
            bot.send_message(int(uid_str), f"🧠 **Bugungi savol!**\n\n{savol_matni}\n\n"
                                           f"✅ To'g'ri javob bersangiz +10 XP olasiz!",
                             parse_mode="Markdown", reply_markup=markup)
            yuborildi += 1
        except Exception:
            pass
    bot.reply_to(message, f"✅ Savol {yuborildi} ta foydalanuvchiga yuborildi.")


@bot.callback_query_handler(func=lambda call: call.data.startswith("quizans_"))
def savolga_javob(call):
    uid = call.from_user.id
    _, qid, tanlangan_idx = call.data.split("_")
    tanlangan_idx = int(tanlangan_idx)
    quizzes = load_quizzes() or {}
    quiz = quizzes.get(qid)
    if not quiz:
        bot.answer_callback_query(call.id, "❌ Bu savol muddati tugagan.")
        return
    if str(uid) in quiz.get("javob_berganlar", {}):
        bot.answer_callback_query(call.id, "ℹ️ Siz bu savolga allaqachon javob bergansiz.", show_alert=True)
        return

    togri = tanlangan_idx == quiz["togri"]
    quiz.setdefault("javob_berganlar", {})[str(uid)] = tanlangan_idx
    quizzes[qid] = quiz
    save_quizzes(quizzes)

    if togri:
        user = get_user(uid)
        user["xp"] = user.get("xp", 0) + 10
        update_user(uid, user)
        bot.answer_callback_query(call.id, "✅ To'g'ri! +10 XP", show_alert=True)
    else:
        togri_matn = quiz["variantlar"][quiz["togri"]]
        bot.answer_callback_query(call.id, f"❌ Noto'g'ri. To'g'ri javob: {togri_matn}", show_alert=True)


# ============================================================
#  🔁 ESKI TUGMA FUNKSIYALARINI YANGI INLINE MENYUDAN QAYTA
#  ISHLATISH UCHUN "SOXTA XABAR" YORDAMCHISI
# ============================================================
# Ko'p eski funksiyalar (masalan taksi_chaqirish_start, elon_berish...)
# faqat message.from_user.id va message.chat.id dan foydalanadi.
# Shu sababli ularni chaqirish uchun to'liq Telegram Message obyekti
# yaratish shart emas — quyidagi yengil "shim" yetarli. Bu orqali kodni
# ikki marta yozmasdan, YANGI HUB-MENYUDAGI tugmalar ESKI ishlaydigan
# funksiyalarni to'g'ridan-to'g'ri chaqiradi.
class _FakeUser:
    def __init__(self, uid):
        self.id = uid
        self.username = None
        self.first_name = None
        self.last_name = None


class _FakeChat:
    def __init__(self, uid):
        self.id = uid


class FakeMessage:
    def __init__(self, uid, text=""):
        self.from_user = _FakeUser(uid)
        self.chat = _FakeChat(uid)
        self.text = text


# ---- ASOSIY MENU (bo'limlarga bo'lingan) ----
def get_main_keyboard(uid):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🛒 E'lonlar", "🚖 Taksi")
    markup.add("🤖 AI yordamchi", "💰 Pul va Premium")
    markup.add("👤 Profil", "💼 Ish va Xizmatlar")
    markup.add("📢 Qo'shimcha", "⚙️ Sozlamalar")
    markup.add("🌐 Saytimiz", "❓ Yordam")
    markup.add("💬 Admin bilan bog'lanish")
    if uid == ADMIN_ID:
        markup.add("🛠 Admin panel")
    return markup


# ============================================================
#  🌐 SAYTIMIZGA O'TISH
# ============================================================
@bot.message_handler(func=lambda m: m.text == "🌐 Saytimiz")
def saytga_otish(message):
    if check_ban(message): return
    uid = message.from_user.id
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🌐 Saytimizga o'tish", url=SAYT_LINK))
    bot.send_message(uid, "🌐 Rasmiy veb-saytimizga xush kelibsiz!\n\nQuyidagi tugma orqali o'ting:",
                     reply_markup=markup)


# ============================================================
#  🛒 E'LONLAR BO'LIMI (hub)
# ============================================================
@bot.message_handler(func=lambda m: m.text == "🛒 E'lonlar")
def hub_elonlar(message):
    if check_ban(message): return
    uid = message.from_user.id
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("➕ Yangi e'lon", callback_data="hub_yangi_elon"),
        types.InlineKeyboardButton("✏️ Tahrirlash", callback_data="hub_elon_tahrir"),
        types.InlineKeyboardButton("🔍 Ko'rish/Qidirish", callback_data="hub_elon_korish"),
        types.InlineKeyboardButton("❤️ Sevimlilarim", callback_data="hub_sevimli"),
        types.InlineKeyboardButton("🚀 VIP / Tepaga chiqarish", callback_data="hub_vip_qilish"),
        types.InlineKeyboardButton("📤 Ulashish", callback_data="hub_elon_ulashish"),
        types.InlineKeyboardButton("👀 Ko'rilganlar", callback_data="hub_korilganlar"),
        types.InlineKeyboardButton("💬 Xaridorlar xabarlari", callback_data="hub_xaridor_xabarlar"),
        types.InlineKeyboardButton("📸 AI bilan rasmdan e'lon", callback_data="hub_smart_skaner"),
    )
    bot.send_message(uid, "🛒 **E'lonlar bo'limi:**", parse_mode="Markdown", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "hub_yangi_elon")
def hub_yangi_elon(call):
    bot.answer_callback_query(call.id)
    elon_berish(FakeMessage(call.from_user.id))


@bot.callback_query_handler(func=lambda call: call.data == "hub_elon_tahrir")
def hub_elon_tahrir(call):
    bot.answer_callback_query(call.id)
    mening_elonlarim(FakeMessage(call.from_user.id))


@bot.callback_query_handler(func=lambda call: call.data == "hub_elon_korish")
def hub_elon_korish(call):
    bot.answer_callback_query(call.id)
    elonlarni_korish_start(FakeMessage(call.from_user.id))


@bot.callback_query_handler(func=lambda call: call.data == "hub_sevimli")
def hub_sevimli(call):
    bot.answer_callback_query(call.id)
    sevimlilarim(FakeMessage(call.from_user.id))


@bot.callback_query_handler(func=lambda call: call.data == "hub_vip_qilish")
def hub_vip_qilish(call):
    bot.answer_callback_query(call.id)
    biznes_xizmatlar(FakeMessage(call.from_user.id, "⭐ Obuna / VIP"))


@bot.callback_query_handler(func=lambda call: call.data == "hub_elon_ulashish")
def hub_elon_ulashish(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    bot_username = bot.get_me().username
    havola = f"https://t.me/{bot_username}"
    bot.send_message(uid, f"📤 Botimizni do'stlaringizga ulashing:\n{havola}")


@bot.callback_query_handler(func=lambda call: call.data == "hub_korilganlar")
def hub_korilganlar(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    user = get_user(uid)
    elonlar = load_elonlar()
    mening = [(eid, elonlar[eid]) for eid in user.get("elonlar", []) if eid in elonlar]
    if not mening:
        bot.send_message(uid, "👀 Sizda hali e'lon yo'q, shuning uchun ko'rishlar statistikasi ham yo'q.")
        return
    mening.sort(key=lambda x: x[1].get("korishlar", 0), reverse=True)
    matn = "👀 **E'lonlaringiz ko'rishlar soni bo'yicha:**\n\n" + "\n".join(
        f"• №{eid} — {md_escape(e.get('sarlavha','?'))}: {e.get('korishlar', 0)} marta ko'rilgan"
        for eid, e in mening
    )
    bot.send_message(uid, matn, parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data == "hub_xaridor_xabarlar")
def hub_xaridor_xabarlar(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    user = get_user(uid)
    xabarlar = user.get("sotuvchi_xabarlar", [])
    if not xabarlar:
        bot.send_message(uid, "💬 Hozircha xaridorlardan xabar kelmagan. E'lonlaringiz ko'rilganda, "
                              "xaridorlar '✉️ Sotuvchiga yozish' tugmasi orqali sizga yozishi mumkin.")
        return
    matn = "💬 **Xaridorlardan kelgan so'nggi xabarlar:**\n\n" + "\n\n".join(
        f"📅 {x.get('sana','')} (e'lon №{x.get('eid','')})\n👤 {md_escape(x.get('kimdan','?'))}: {md_escape(x.get('matn',''))}"
        for x in xabarlar[-10:]
    )
    bot.send_message(uid, matn, parse_mode="Markdown")


# ============================================================
#  🚖 TAKSI BO'LIMI (hub)
# ============================================================
@bot.message_handler(func=lambda m: m.text == "🚖 Taksi")
def hub_taksi(message):
    if check_ban(message): return
    uid = message.from_user.id
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🚖 Taksi chaqirish", callback_data="hub_taksi_chaqir"),
        types.InlineKeyboardButton("🚕 Haydovchi bo'lish", callback_data="hub_haydovchi"),
        types.InlineKeyboardButton("📜 Buyurtmalar tarixi", callback_data="hub_taksi_tarix"),
        types.InlineKeyboardButton("🚨 SOS", callback_data="hub_sos"),
        types.InlineKeyboardButton("📍 Jonli joylashuv", callback_data="hub_jonli_lokatsiya"),
    )
    bot.send_message(uid, "🚖 **Taksi bo'limi:**", parse_mode="Markdown", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "hub_taksi_chaqir")
def hub_taksi_chaqir(call):
    bot.answer_callback_query(call.id)
    taksi_chaqirish_start(FakeMessage(call.from_user.id))


@bot.callback_query_handler(func=lambda call: call.data == "hub_haydovchi")
def hub_haydovchi(call):
    bot.answer_callback_query(call.id)
    haydovchi_paneli(FakeMessage(call.from_user.id))


@bot.callback_query_handler(func=lambda call: call.data == "hub_taksi_tarix")
def hub_taksi_tarix(call):
    bot.answer_callback_query(call.id)
    buyurtmalarim(FakeMessage(call.from_user.id))


@bot.callback_query_handler(func=lambda call: call.data == "hub_jonli_lokatsiya")
def hub_jonli_lokatsiya(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    taksilar = load_taksi()
    faol = [t for t in taksilar.values()
            if t.get("yolovchi_id") == uid and t.get("holat") == "qabul_qilindi" and t.get("haydovchi_id")]
    if not faol:
        bot.send_message(uid, "📍 Sizda hozir yo'lda bo'lgan (haydovchi tayinlangan) faol buyurtma yo'q.")
        return
    buyurtma = faol[-1]
    haydovchilar = load_haydovchilar()
    h = haydovchilar.get(str(buyurtma["haydovchi_id"]))
    if not h or h.get("last_lat") is None:
        bot.send_message(uid, "📍 Haydovchining joylashuvi hali aniqlanmagan. Birozdan so'ng qayta urinib ko'ring.")
        return
    bot.send_message(uid, f"🚗 Haydovchi ({h.get('ism','')}) so'nggi joylashuvi:")
    bot.send_location(uid, h["last_lat"], h["last_lon"])


@bot.callback_query_handler(func=lambda call: call.data == "hub_sos")
def hub_sos_start(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    user_state[uid] = "sos_lokatsiya"
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton("🚨 Joylashuvimni yuborish", request_location=True))
    bot.send_message(
        uid,
        "🚨 **SOS!** Joriy joylashuvingizni yuboring — adminga zudlik bilan xabar beriladi.",
        parse_mode="Markdown", reply_markup=markup
    )


@bot.message_handler(content_types=["location"], func=lambda m: user_state.get(m.from_user.id) == "sos_lokatsiya")
def sos_lokatsiya_qabul(message):
    uid = message.from_user.id
    user = get_user(uid)
    user_state.pop(uid, None)
    lat, lon = message.location.latitude, message.location.longitude
    bot.send_message(uid, "🚨 SOS xabaringiz adminga yuborildi. Tinchlaning, yordam yo'lda!",
                     reply_markup=get_main_keyboard(uid))
    try:
        bot.send_message(
            ADMIN_ID,
            f"🚨🚨🚨 **SOS SIGNALI!** 🚨🚨🚨\n\n"
            f"👤 {md_escape(user.get('name','?'))}\n📞 {md_escape(user.get('phone','?'))}\n🆔 `{uid}`",
            parse_mode="Markdown"
        )
        bot.send_location(ADMIN_ID, lat, lon)
    except Exception as e:
        log.error(f"SOS xabari yuborilmadi: {e}")


# ============================================================
#  🤖 AI BO'LIMI (hub)
# ============================================================
@bot.message_handler(func=lambda m: m.text == "🤖 AI yordamchi")
def hub_ai(message):
    if check_ban(message): return
    uid = message.from_user.id
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🧠 Erkin suhbat", callback_data="hub_ai_chat"),
        types.InlineKeyboardButton("📝 Matn yozish", callback_data="hub_ai_matn"),
        types.InlineKeyboardButton("🌍 Tarjimon", callback_data="hub_ai_tarjima"),
        types.InlineKeyboardButton("💻 Kod yozish", callback_data="hub_ai_kod"),
        types.InlineKeyboardButton("📄 PDF yaratish", callback_data="hub_ai_pdf"),
        types.InlineKeyboardButton("🖼️ Rasm yaratish", callback_data="hub_ai_rasm"),
        types.InlineKeyboardButton("🧮 Masalani rasmdan yech", callback_data="hub_ai_masala"),
        types.InlineKeyboardButton("📝 Kunlik test (5 savol)", callback_data="hub_ai_kunlik_test"),
    )
    bot.send_message(
        uid,
        "🤖 **AI bo'limi** — nima qilishni xohlaysiz?\n\n"
        "🎤 _Istalgan vaqtda menga to'g'ridan-to'g'ri ovozli xabar yuborsangiz ham, "
        "uni matnga o'girib javob beraman!_",
        parse_mode="Markdown", reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data == "hub_ai_chat")
def hub_ai_chat(call):
    bot.answer_callback_query(call.id)
    gemini_ai_start(FakeMessage(call.from_user.id))


AI_PRESET_PROMPTLAR = {
    "hub_ai_matn": ("ai_matn_kutish",
                     "📝 Qanday matn kerak? Mavzusini yozing (masalan: 'Bahor haqida qisqa insho'):",
                     "Sen professional matn muallifisan. O'zbek tilida, chiroyli va tushunarli qilib yoz:\n\n"),
    "hub_ai_tarjima": ("ai_tarjima_kutish",
                       "🌍 Tarjima qilinadigan matnni yuboring (avtomatik til aniqlanadi, o'zbek/rus/ingliz tiliga tarjima qilinadi):",
                       "Quyidagi matnni aniqla va uni o'zbek, rus va ingliz tillariga tarjima qilib ber:\n\n"),
    "hub_ai_kod": ("ai_kod_kutish",
                   "💻 Qanday kod kerak? Vazifasini tasvirlab yozing (masalan: 'Python\\'da ikki sonni qo\\'shuvchi funksiya'):",
                   "Sen tajribali dasturchisan. So'ralgan kodni izohlar bilan yoz:\n\n"),
}


def _ai_preset_callback_factory(callback_key):
    def _handler(call):
        uid = call.from_user.id
        bot.answer_callback_query(call.id)
        holat, taklif_matni, _ = AI_PRESET_PROMPTLAR[callback_key]
        user_state[uid] = holat
        bot.send_message(uid, taklif_matni)
    return _handler


for _key in AI_PRESET_PROMPTLAR:
    bot.callback_query_handler(func=lambda call, k=_key: call.data == k)(_ai_preset_callback_factory(_key))


@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) in
                      [holat for holat, _, _ in AI_PRESET_PROMPTLAR.values()])
def ai_preset_javob(message):
    uid = message.from_user.id
    holat = user_state.pop(uid)
    if not ai_client:
        bot.send_message(uid, "❌ Gemini AI hozircha sozlanmagan (API kalit yo'q).", reply_markup=get_main_keyboard(uid))
        return
    prefiks = next(pref for h, _, pref in AI_PRESET_PROMPTLAR.values() if h == holat)
    sent_msg = bot.send_message(uid, "⏳ Tayyorlanmoqda...")
    try:
        response = ai_client.models.generate_content(model='gemini-2.5-flash', contents=prefiks + message.text)
        bot.edit_message_text(response.text, chat_id=uid, message_id=sent_msg.message_id)
        ai_ishlatish_belgila(uid)
    except Exception as e:
        log.error(f"AI preset xatoligi: {e}")
        bot.edit_message_text("❌ Xatolik yuz berdi, qayta urinib ko'ring.", chat_id=uid, message_id=sent_msg.message_id)
    bot.send_message(uid, "Yana kerak bo'lsa, 🤖 AI yordamchi bo'limiga qayting.", reply_markup=get_main_keyboard(uid))


@bot.callback_query_handler(func=lambda call: call.data == "hub_ai_pdf")
def hub_ai_pdf_start(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    user_state[uid] = "ai_pdf_matn_kutish"
    bot.send_message(uid, "📄 PDF ichiga yoziladigan matnni yuboring:")


@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == "ai_pdf_matn_kutish")
def ai_pdf_yaratish(message):
    uid = message.from_user.id
    user_state.pop(uid, None)
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "", 12)
    pdf.multi_cell(0, 8, message.text)
    yoli = os.path.join(PDF_TMP_DIR, f"hujjat_{uid}_{int(time.time())}.pdf")
    pdf.output(yoli)
    with open(yoli, "rb") as f:
        bot.send_document(uid, f, caption="📄 Hujjatingiz tayyor!")
    ai_ishlatish_belgila(uid)
    bot.send_message(uid, "Yana nima qilamiz?", reply_markup=get_main_keyboard(uid))


@bot.callback_query_handler(func=lambda call: call.data == "hub_ai_rasm")
def hub_ai_rasm_start(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    user_state[uid] = "ai_rasm_matn_kutish"
    bot.send_message(uid, "🖼️ Qanday rasm chizilsin? Tasvirlab yozing (masalan: 'qor bosgan tog\\'lar, quyosh chiqishi'):")


@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == "ai_rasm_matn_kutish")
def ai_rasm_yaratish(message):
    import urllib.parse
    uid = message.from_user.id
    user_state.pop(uid, None)
    sent_msg = bot.send_message(uid, "🎨 Rasm chizilmoqda, biroz kuting...")
    try:
        prompt_encoded = urllib.parse.quote(message.text)
        url = f"https://image.pollinations.ai/prompt/{prompt_encoded}?width=768&height=768&nologo=true"
        r = requests.get(url, timeout=40)
        r.raise_for_status()
        bot.delete_message(uid, sent_msg.message_id)
        bot.send_photo(uid, r.content, caption=f"🖼️ Tayyor: {message.text}")
        ai_ishlatish_belgila(uid)
    except Exception as e:
        log.warning(f"Rasm generatsiyasida xatolik: {e}")
        try:
            bot.edit_message_text("❌ Rasm chizishda xatolik yuz berdi. Qayta urinib ko'ring.",
                                  chat_id=uid, message_id=sent_msg.message_id)
        except Exception:
            pass
    bot.send_message(uid, "Yana nima qilamiz?", reply_markup=get_main_keyboard(uid))


def ai_ishlatish_belgila(uid):
    user = get_user(uid)
    user["ai_ishlatish_soni"] = user.get("ai_ishlatish_soni", 0) + 1
    update_user(uid, user)


# ============================================================
#  🎤 OVOZLI XABARNI TUSHUNUVCHI AI (Voice-to-Text)
# ============================================================
@bot.message_handler(content_types=["voice"])
def ovozli_xabar_qabul(message):
    if check_ban(message): return
    uid = message.from_user.id
    if not ai_client or genai_types is None:
        bot.send_message(uid, "❌ Ovozli xabarlarni tushunish hozircha sozlanmagan.")
        return

    sent_msg = bot.send_message(uid, "🎤 Ovozli xabaringiz tinglanmoqda...")
    try:
        file_info = bot.get_file(message.voice.file_id)
        audio_bytes = bot.download_file(file_info.file_path)
        audio_part = genai_types.Part.from_bytes(data=audio_bytes, mime_type="audio/ogg")
        response = ai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                audio_part,
                "Bu foydalanuvchidan kelgan ovozli xabar. Avval uni matnga o'gir (bir qatorda), "
                "so'ng shu so'rovga o'zbek tilida qisqa va aniq javob ber. Format:\n"
                "🎤 Aytganingiz: <matn>\n\n💬 Javob: <javob>"
            ],
        )
        bot.edit_message_text(response.text, chat_id=uid, message_id=sent_msg.message_id)
        ai_ishlatish_belgila(uid)
    except Exception as e:
        log.error(f"Ovozli xabarni qayta ishlashda xatolik: {e}")
        try:
            bot.edit_message_text("❌ Ovozli xabarni tushunishda xatolik yuz berdi. Qayta urinib ko'ring yoki matn yozing.",
                                  chat_id=uid, message_id=sent_msg.message_id)
        except Exception:
            pass


# ============================================================
#  🧮 MASALANI RASMDAN YECHISH (AI o'quv assistenti)
# ============================================================
@bot.callback_query_handler(func=lambda call: call.data == "hub_ai_masala")
def hub_ai_masala_start(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    user_state[uid] = "ai_masala_rasm_kutish"
    bot.send_message(uid, "🧮 Yechilishi kerak bo'lgan masala/misolning rasmini yuboring:")


@bot.message_handler(content_types=["photo"], func=lambda m: user_state.get(m.from_user.id) == "ai_masala_rasm_kutish")
def ai_masala_yechish(message):
    uid = message.from_user.id
    user_state.pop(uid, None)
    if not ai_client or genai_types is None:
        bot.send_message(uid, "❌ AI hozircha sozlanmagan.", reply_markup=get_main_keyboard(uid))
        return

    sent_msg = bot.send_message(uid, "🧮 Masala tahlil qilinmoqda...")
    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        img_bytes = bot.download_file(file_info.file_path)
        img_part = genai_types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg")
        response = ai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                img_part,
                "Rasmdagi matematik/fizika/kimyo masalasini aniqla va uni bosqichma-bosqich, "
                "har bir qadamni tushuntirib, o'zbek tilida yech. Oxirida javobni aniq ko'rsat."
            ],
        )
        bot.edit_message_text(response.text[:4000], chat_id=uid, message_id=sent_msg.message_id)
        ai_ishlatish_belgila(uid)
    except Exception as e:
        log.error(f"Masala yechishda xatolik: {e}")
        try:
            bot.edit_message_text("❌ Masalani tahlil qilishda xatolik yuz berdi. Rasm aniqroq bo'lishi kerak.",
                                  chat_id=uid, message_id=sent_msg.message_id)
        except Exception:
            pass
    bot.send_message(uid, "Yana nima qilamiz?", reply_markup=get_main_keyboard(uid))


# ============================================================
#  📝 KUNLIK TEST (AI o'quv assistenti)
# ============================================================
@bot.callback_query_handler(func=lambda call: call.data == "hub_ai_kunlik_test")
def hub_ai_kunlik_test_fan(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [types.InlineKeyboardButton(nom, callback_data=f"kunliktest_{kod}") for nom, kod in FANLAR]
    markup.add(*buttons)
    bot.send_message(uid, "📝 Qaysi fandan kunlik test (5 ta savol) kerak?", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("kunliktest_"))
def hub_ai_kunlik_test_generatsiya(call):
    uid = call.from_user.id
    kod = call.data.replace("kunliktest_", "")
    nom = next((n for n, k in FANLAR if k == kod), kod)
    bot.answer_callback_query(call.id)
    if not ai_client:
        bot.send_message(uid, "❌ AI hozircha sozlanmagan.")
        return
    sent_msg = bot.send_message(uid, f"📝 {nom} fanidan test tayyorlanmoqda...")
    try:
        response = ai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=(
                f"'{nom}' fanidan o'quvchilar uchun 5 ta test savoli tuz (A/B/C/D variantlari bilan). "
                f"Har bir savoldan keyin to'g'ri javobni ham yoz. O'zbek tilida, tushunarli qilib."
            ),
        )
        bot.edit_message_text(response.text[:4000], chat_id=uid, message_id=sent_msg.message_id)
        ai_ishlatish_belgila(uid)
    except Exception as e:
        log.error(f"Kunlik test yaratishda xatolik: {e}")
        try:
            bot.edit_message_text("❌ Test tayyorlashda xatolik yuz berdi. Qayta urinib ko'ring.",
                                  chat_id=uid, message_id=sent_msg.message_id)
        except Exception:
            pass


# ============================================================
#  📸 AI "SMART-SKANER" — rasmdan e'lon va narxni aniqlash
# ============================================================
@bot.callback_query_handler(func=lambda call: call.data == "hub_smart_skaner")
def hub_smart_skaner_start(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    if check_sub(uid) is False:
        send_sub_message(uid)
        return
    user_state[uid] = "smart_skaner_rasm_kutish"
    bot.send_message(uid, "📸 Sotmoqchi bo'lgan buyumingiz rasmini yuboring — AI uni tahlil qilib, "
                          "sarlavha, tavsif va taxminiy narxni o'zi taklif qiladi:")


@bot.message_handler(content_types=["photo"], func=lambda m: user_state.get(m.from_user.id) == "smart_skaner_rasm_kutish")
def hub_smart_skaner_tahlil(message):
    uid = message.from_user.id
    user_state.pop(uid, None)
    file_id = message.photo[-1].file_id

    if not ai_client or genai_types is None:
        bot.send_message(uid, "❌ AI hozircha sozlanmagan.", reply_markup=get_main_keyboard(uid))
        return

    sent_msg = bot.send_message(uid, "📸 Rasm tahlil qilinmoqda...")
    sarlavha, tavsif, narx = None, None, None
    try:
        file_info = bot.get_file(file_id)
        img_bytes = bot.download_file(file_info.file_path)
        img_part = genai_types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg")
        response = ai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                img_part,
                "Rasmdagi mahsulotni aniqla (masalan telefon modeli, kiyim turi, avtomobil markasi va h.k.). "
                "Javobni ANIQ shu 3 qatorda ber, boshqa hech narsa yozma:\n"
                "SARLAVHA: <qisqa sarlavha>\n"
                "TAVSIF: <1-2 gapli tavsif, holati taxminiy>\n"
                "NARX: <O'zbekiston bozoridagi taxminiy narx, so'mda>"
            ],
        )
        for qator in response.text.splitlines():
            if qator.upper().startswith("SARLAVHA:"):
                sarlavha = qator.split(":", 1)[1].strip()
            elif qator.upper().startswith("TAVSIF:"):
                tavsif = qator.split(":", 1)[1].strip()
            elif qator.upper().startswith("NARX:"):
                narx = qator.split(":", 1)[1].strip()
        ai_ishlatish_belgila(uid)
    except Exception as e:
        log.error(f"Smart-skaner xatoligi: {e}")

    if not sarlavha:
        bot.edit_message_text("❌ Rasmni tahlil qilib bo'lmadi. Qayta urinib ko'ring yoki oddiy '➕ Yangi e'lon' orqali davom eting.",
                              chat_id=uid, message_id=sent_msg.message_id)
        bot.send_message(uid, "Menyu:", reply_markup=get_main_keyboard(uid))
        return

    try:
        bot.delete_message(uid, sent_msg.message_id)
    except Exception:
        pass

    user_data_temp[uid] = {
        "is_vip": False, "photo": file_id, "location": None,
        "hudud": "Kiritilmagan", "tuman": "Kiritilmagan",
        "sarlavha": sarlavha, "tavsif": tavsif or "", "narx": narx or "Kelishiladi",
    }
    matn = (
        f"📸 **AI taklifi:**\n\n📌 Sarlavha: {md_escape(sarlavha)}\n📝 Tavsif: {md_escape(tavsif or '')}\n"
        f"💰 Taxminiy narx: {md_escape(narx or 'Kelishiladi')}\n\n"
        f"👇 Endi kategoriyani tanlang, e'lon shu ma'lumotlar bilan tayyorlanadi:"
    )
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [types.InlineKeyboardButton(nom, callback_data=f"smartkot_{kod}") for nom, kod in KATEGORIYALAR]
    markup.add(*buttons)
    bot.send_message(uid, matn, parse_mode="Markdown", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("smartkot_"))
def hub_smart_skaner_kategoriya(call):
    uid = call.from_user.id
    kod = call.data.replace("smartkot_", "")
    nom = next((n for n, k in KATEGORIYALAR if k == kod), kod)
    bot.answer_callback_query(call.id)
    if uid not in user_data_temp:
        bot.send_message(uid, "⚠️ Xatolik, qaytadan boshlang.", reply_markup=get_main_keyboard(uid))
        return
    user_data_temp[uid]["kategoriya"] = nom
    user_data_temp[uid]["kategoriya_kod"] = kod
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass
    elon_tekshirish_bosqichi(uid)



def hub_pul(message):
    if check_ban(message): return
    uid = message.from_user.id
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("💳 Hamyonim", callback_data="hub_hamyon"),
        types.InlineKeyboardButton("💎 Premium sotib olish", callback_data="hub_premium"),
        types.InlineKeyboardButton("🎁 Promo kod", callback_data="hub_promo"),
        types.InlineKeyboardButton("📜 To'lovlar tarixi", callback_data="hub_tolov_tarix"),
        types.InlineKeyboardButton("💸 Hisobni to'ldirish", callback_data="hub_toldirish"),
        types.InlineKeyboardButton("💵 Pul yechish", callback_data="hub_pul_yechish"),
        types.InlineKeyboardButton("🎁 Cashback", callback_data="hub_cashback"),
    )
    bot.send_message(uid, "💰 **Pul va Premium bo'limi:**", parse_mode="Markdown", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "hub_hamyon")
def hub_hamyon(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    user = get_user(uid)
    matn = (
        f"💳 **Hamyoningiz**\n\n"
        f"💰 Balans: {som_format(user.get('balance', 0))} (bonus)\n\n"
        f"ℹ️ _Hozircha bu — bot ichidagi bonus balans (referal, promo kodlar orqali to'ladi). "
        f"Haqiqiy pul bilan to'ldirish/yechish uchun Click yoki Payme integratsiyasi sozlanishi kerak._"
    )
    bot.send_message(uid, matn, parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data == "hub_premium")
def hub_premium(call):
    bot.answer_callback_query(call.id)
    biznes_xizmatlar(FakeMessage(call.from_user.id, "⭐ Obuna / VIP"))


@bot.callback_query_handler(func=lambda call: call.data == "hub_tolov_tarix")
def hub_tolov_tarix(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    user = get_user(uid)
    tarix = user.get("balance_tarix", [])
    if not tarix:
        bot.send_message(uid, "📜 Hozircha balans tarixingiz bo'sh.")
        return
    matn = "📜 **Balans tarixi:**\n\n" + "\n".join(
        f"• {t.get('sana','')} — {t.get('izoh','')}: {'+' if t.get('miqdor',0) >= 0 else ''}{t.get('miqdor',0)} so'm"
        for t in tarix[-15:]
    )
    bot.send_message(uid, matn, parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data == "hub_toldirish")
def hub_toldirish_start(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    user_state[uid] = "toldirish_summa_kutish"
    bot.send_message(
        uid,
        "💸 Hamyoningizga qo'shmoqchi bo'lgan summani kiriting (so'mda, faqat raqam):\n\n"
        "ℹ️ _Bu bonus balansingizga qo'shiladi. So'rovingiz adminga yuboriladi — admin siz bilan "
        "to'lov usulini (naqd/karta) kelishib, so'ng tasdiqlaydi._",
        parse_mode="Markdown"
    )


@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == "toldirish_summa_kutish")
def hub_toldirish_summa(message):
    uid = message.from_user.id
    user_state.pop(uid, None)
    try:
        summa = int("".join(ch for ch in message.text if ch.isdigit()))
        if summa <= 0:
            raise ValueError
    except ValueError:
        bot.send_message(uid, "❌ Iltimos, faqat musbat raqam kiriting.", reply_markup=get_main_keyboard(uid))
        return

    user = get_user(uid)
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"topup_accept_{uid}_{summa}"),
        types.InlineKeyboardButton("❌ Rad etish", callback_data=f"topup_reject_{uid}"),
    )
    try:
        bot.send_message(
            ADMIN_ID,
            f"💸 **Hisobni to'ldirish so'rovi**\n\n👤 {md_escape(user.get('name','?'))} (`{uid}`)\n"
            f"💰 So'ralgan summa: {som_format(summa)}",
            parse_mode="Markdown", reply_markup=markup
        )
        bot.send_message(uid, "✅ So'rovingiz adminga yuborildi. Tez orada javob berishadi.",
                         reply_markup=get_main_keyboard(uid))
    except Exception as e:
        log.error(f"To'ldirish so'rovi yuborilmadi: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("topup_accept_"))
def hub_toldirish_qabul(call):
    if call.from_user.id != ADMIN_ID: return
    bot.answer_callback_query(call.id)
    _, _, uid_str, summa_str = call.data.split("_")
    summa = int(summa_str)
    user = get_user(int(uid_str))
    user["balance"] = user.get("balance", 0) + summa
    user.setdefault("balance_tarix", []).append({
        "sana": datetime.now().strftime("%d.%m.%Y %H:%M"), "miqdor": summa, "izoh": "Hisob to'ldirildi (admin tasdiqladi)"
    })
    update_user(int(uid_str), user)
    try:
        bot.edit_message_text(f"{call.message.text}\n\n✅ TASDIQLANDI VA HISOBGA QO'SHILDI", ADMIN_ID, call.message.message_id)
    except Exception:
        pass
    try:
        bot.send_message(int(uid_str), f"🎉 Hamyoningizga {som_format(summa)} qo'shildi!")
    except Exception:
        pass


@bot.callback_query_handler(func=lambda call: call.data.startswith("topup_reject_"))
def hub_toldirish_rad(call):
    if call.from_user.id != ADMIN_ID: return
    bot.answer_callback_query(call.id)
    uid_str = call.data.replace("topup_reject_", "")
    try:
        bot.edit_message_text(f"{call.message.text}\n\n❌ RAD ETILDI", ADMIN_ID, call.message.message_id)
    except Exception:
        pass
    try:
        bot.send_message(int(uid_str), "❌ Hisobni to'ldirish so'rovingiz rad etildi. Admin bilan bog'laning: @" + ADMIN_USERNAME)
    except Exception:
        pass


@bot.callback_query_handler(func=lambda call: call.data == "hub_pul_yechish")
def hub_pul_yechish_start(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    user = get_user(uid)
    balans = user.get("balance", 0)
    if balans <= 0:
        bot.send_message(uid, f"💵 Hamyoningizda yechib olish uchun mablag' yo'q. Joriy balans: {som_format(balans)}")
        return
    user_state[uid] = "pulyechish_summa_kutish"
    bot.send_message(
        uid,
        f"💵 Joriy balansingiz: {som_format(balans)}\n\nYechib olmoqchi bo'lgan summani kiriting:"
    )


@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == "pulyechish_summa_kutish")
def hub_pul_yechish_summa(message):
    uid = message.from_user.id
    user_state.pop(uid, None)
    user = get_user(uid)
    balans = user.get("balance", 0)
    try:
        summa = int("".join(ch for ch in message.text if ch.isdigit()))
        if summa <= 0 or summa > balans:
            raise ValueError
    except ValueError:
        bot.send_message(uid, f"❌ Noto'g'ri summa. Joriy balansingiz: {som_format(balans)}",
                         reply_markup=get_main_keyboard(uid))
        return

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"withdraw_accept_{uid}_{summa}"),
        types.InlineKeyboardButton("❌ Rad etish", callback_data=f"withdraw_reject_{uid}"),
    )
    bot.send_message(
        ADMIN_ID,
        f"💵 **Pul yechish so'rovi**\n\n👤 {md_escape(user.get('name','?'))} (`{uid}`)\n"
        f"📞 {md_escape(user.get('phone','?'))}\n💰 So'ralgan summa: {som_format(summa)}",
        parse_mode="Markdown", reply_markup=markup
    )
    bot.send_message(uid, "✅ So'rovingiz yuborildi. Admin siz bilan bog'lanib, to'lovni amalga oshiradi.",
                     reply_markup=get_main_keyboard(uid))


@bot.callback_query_handler(func=lambda call: call.data.startswith("withdraw_accept_"))
def hub_pulyechish_qabul(call):
    if call.from_user.id != ADMIN_ID: return
    bot.answer_callback_query(call.id)
    _, _, uid_str, summa_str = call.data.split("_")
    summa = int(summa_str)
    user = get_user(int(uid_str))
    if user.get("balance", 0) < summa:
        bot.send_message(ADMIN_ID, "❌ Foydalanuvchining balansi yetarli emas, so'rov bekor qilindi.")
        return
    user["balance"] -= summa
    user.setdefault("balance_tarix", []).append({
        "sana": datetime.now().strftime("%d.%m.%Y %H:%M"), "miqdor": -summa, "izoh": "Pul yechildi (admin tasdiqladi)"
    })
    update_user(int(uid_str), user)
    try:
        bot.edit_message_text(f"{call.message.text}\n\n✅ TASDIQLANDI VA YECHILDI", ADMIN_ID, call.message.message_id)
    except Exception:
        pass
    try:
        bot.send_message(int(uid_str), f"✅ {som_format(summa)} balansingizdan yechildi. Admin siz bilan bog'lanadi.")
    except Exception:
        pass


@bot.callback_query_handler(func=lambda call: call.data.startswith("withdraw_reject_"))
def hub_pulyechish_rad(call):
    if call.from_user.id != ADMIN_ID: return
    bot.answer_callback_query(call.id)
    uid_str = call.data.replace("withdraw_reject_", "")
    try:
        bot.edit_message_text(f"{call.message.text}\n\n❌ RAD ETILDI", ADMIN_ID, call.message.message_id)
    except Exception:
        pass
    try:
        bot.send_message(int(uid_str), "❌ Pul yechish so'rovingiz rad etildi. Admin bilan bog'laning: @" + ADMIN_USERNAME)
    except Exception:
        pass


@bot.callback_query_handler(func=lambda call: call.data == "hub_cashback")
def hub_cashback(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    user = get_user(uid)
    jami = sum(t.get("miqdor", 0) for t in user.get("balance_tarix", []) if "Cashback" in t.get("izoh", ""))
    bot.send_message(
        uid,
        f"🎁 **Cashback**\n\nHar bir yakunlangan taksi safaringizdan 1% avtomatik hamyoningizga qaytadi.\n\n"
        f"💰 Hozirgacha jami cashback: {som_format(jami)}",
        parse_mode="Markdown"
    )


# ---- PROMO KOD (ba'zilari cheklangan sonli — "birinchi N kishi" tipida) ----
PROMO_ISHLATISH_FILE = "promo_ishlatish.json"
PROMO_KODLAR = {
    "WELCOME2026": {"miqdor": 5000, "limit": None},
    "SALOM10": {"miqdor": 3000, "limit": None},
    "YANGIYIL2026": {"miqdor": 10000, "limit": 50},
}


def promo_ishlatish_sonini_ol(kod):
    data = _load_json(PROMO_ISHLATISH_FILE) or {}
    return data.get(kod, 0)


def promo_ishlatish_sonini_oshir(kod):
    data = _load_json(PROMO_ISHLATISH_FILE) or {}
    data[kod] = data.get(kod, 0) + 1
    _save_json(PROMO_ISHLATISH_FILE, data)


@bot.callback_query_handler(func=lambda call: call.data == "hub_promo")
def hub_promo_start(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    user_state[uid] = "promo_kod_kutish"
    bot.send_message(uid, "🎁 Promo kodingizni kiriting:")


@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == "promo_kod_kutish")
def promo_kod_qabul(message):
    uid = message.from_user.id
    user_state.pop(uid, None)
    kod = message.text.strip().upper()
    user = get_user(uid)

    if kod not in PROMO_KODLAR:
        bot.send_message(uid, "❌ Bunday promo kod topilmadi.", reply_markup=get_main_keyboard(uid))
        return
    if kod in user.get("promo_ishlatilgan", []):
        bot.send_message(uid, "ℹ️ Siz bu promo kodni allaqachon ishlatgansiz.", reply_markup=get_main_keyboard(uid))
        return

    promo = PROMO_KODLAR[kod]
    limit = promo.get("limit")
    if limit is not None and promo_ishlatish_sonini_ol(kod) >= limit:
        bot.send_message(uid, f"❌ Afsuski, «{kod}» promo kod limiti (birinchi {limit} kishi) allaqachon to'lgan.",
                         reply_markup=get_main_keyboard(uid))
        return

    miqdor = promo["miqdor"]
    user["balance"] = user.get("balance", 0) + miqdor
    user.setdefault("promo_ishlatilgan", []).append(kod)
    user.setdefault("balance_tarix", []).append({
        "sana": datetime.now().strftime("%d.%m.%Y %H:%M"), "miqdor": miqdor, "izoh": f"Promo kod: {kod}"
    })
    promo_ishlatish_sonini_oshir(kod)
    update_user(uid, user)
    bot.send_message(uid, f"🎉 Promo kod qabul qilindi! Hamyoningizga {som_format(miqdor)} qo'shildi.",
                     reply_markup=get_main_keyboard(uid))


# ============================================================
#  👤 PROFIL BO'LIMI (hub)
# ============================================================
@bot.message_handler(func=lambda m: m.text == "👤 Profil")
def hub_profil(message):
    if check_ban(message): return
    uid = message.from_user.id
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("👤 Profilim", callback_data="hub_profilim"),
        types.InlineKeyboardButton("✏️ Tahrirlash", callback_data="hub_profil_tahrir"),
        types.InlineKeyboardButton("🏆 Reytingim", callback_data="hub_reyting"),
        types.InlineKeyboardButton("🎁 Do'st taklif qilish", callback_data="hub_referal"),
        types.InlineKeyboardButton("📍 Manzillarim", callback_data="hub_manzillar"),
        types.InlineKeyboardButton("🔒 Xavfsizlik", callback_data="hub_xavfsizlik"),
        types.InlineKeyboardButton("✅ Kunlik kirish (Chek-in)", callback_data="hub_checkin"),
        types.InlineKeyboardButton("📊 Batafsil statistikam", callback_data="hub_batafsil_stat"),
    )
    bot.send_message(uid, "👤 **Profil bo'limi:**", parse_mode="Markdown", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "hub_profilim")
def hub_profilim(call):
    bot.answer_callback_query(call.id)
    mystats(FakeMessage(call.from_user.id))


@bot.callback_query_handler(func=lambda call: call.data == "hub_profil_tahrir")
def hub_profil_tahrir(call):
    bot.answer_callback_query(call.id)
    sozlamalar(FakeMessage(call.from_user.id))


@bot.callback_query_handler(func=lambda call: call.data == "hub_referal")
def hub_referal(call):
    bot.answer_callback_query(call.id)
    dost_taklif(FakeMessage(call.from_user.id))


@bot.callback_query_handler(func=lambda call: call.data == "hub_reyting")
def hub_reyting(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    db = load_db()
    royxat = sorted(db.items(), key=lambda x: x[1].get("referral_count", 0), reverse=True)[:10]
    mening_orin = None
    tartiblangan = sorted(db.items(), key=lambda x: x[1].get("referral_count", 0), reverse=True)
    for i, (uid_str, u) in enumerate(tartiblangan, 1):
        if uid_str == str(uid):
            mening_orin = i
            break

    matn = "🏆 **TOP-10 foydalanuvchilar (referal bo'yicha):**\n\n"
    for i, (uid_str, u) in enumerate(royxat, 1):
        matn += f"{i}. {md_escape(u.get('name','?'))} — {u.get('referral_count', 0)} ta\n"
    if mening_orin:
        matn += f"\n📍 Sizning o'rningiz: {mening_orin}-o'rin"
    bot.send_message(uid, matn, parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data == "hub_manzillar")
def hub_manzillar(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    user = get_user(uid)
    manzillar = user.get("manzillar", [])
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("➕ Yangi manzil qo'shish", callback_data="manzil_qoshish"))
    if not manzillar:
        bot.send_message(uid, "📍 Sizda hali saqlangan manzil yo'q.", reply_markup=markup)
        return
    for i, m in enumerate(manzillar):
        markup.add(types.InlineKeyboardButton(f"🗑 O'chirish: {m}", callback_data=f"manzil_del_{i}"))
    matn = "📍 **Saqlangan manzillaringiz:**\n\n" + "\n".join(f"• {md_escape(m)}" for m in manzillar)
    bot.send_message(uid, matn, parse_mode="Markdown", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "manzil_qoshish")
def manzil_qoshish_start(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    user_state[uid] = "manzil_matn_kutish"
    bot.send_message(uid, "📍 Manzil nomi va tavsifini yozing (masalan: 'Uy — Chilonzor, 12-kvartal, 5-uy'):")


@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == "manzil_matn_kutish")
def manzil_qoshish_yakun(message):
    uid = message.from_user.id
    user_state.pop(uid, None)
    user = get_user(uid)
    user.setdefault("manzillar", []).append(message.text.strip())
    update_user(uid, user)
    bot.send_message(uid, "✅ Manzil saqlandi!", reply_markup=get_main_keyboard(uid))


@bot.callback_query_handler(func=lambda call: call.data.startswith("manzil_del_"))
def manzil_ochirish(call):
    uid = call.from_user.id
    idx = int(call.data.replace("manzil_del_", ""))
    bot.answer_callback_query(call.id)
    user = get_user(uid)
    manzillar = user.get("manzillar", [])
    if 0 <= idx < len(manzillar):
        manzillar.pop(idx)
        user["manzillar"] = manzillar
        update_user(uid, user)
    bot.send_message(uid, "🗑 Manzil o'chirildi.")


@bot.callback_query_handler(func=lambda call: call.data == "hub_xavfsizlik")
def hub_xavfsizlik(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    matn = (
        "🔒 **Xavfsizlik bo'yicha maslahatlar:**\n\n"
        "• Hech qachon parol, kartangiz PIN-kodi yoki SMS-kodni hech kimga (shu jumladan admin nomidan "
        "yozganlarga ham) yubormang.\n"
        "• To'lovni faqat bot ichidagi rasmiy jarayon orqali amalga oshiring.\n"
        "• Shubhali havolalarni bosmang, notanish shaxslar bilan shaxsiy ma'lumot almashmang.\n"
        "• Firibgarlik holatini sezsangiz, darhol \"💬 Admin bilan bog'lanish\" orqali xabar bering."
    )
    bot.send_message(uid, matn, parse_mode="Markdown")


# ============================================================
#  ✅ KUNLIK KIRISH (Chek-in) VA KETMA-KETLIK MUKOFOTI (Streak)
# ============================================================
CHEKIN_MUKOFOTLAR = {3: 2000, 7: 5000, 30: 20000}


@bot.callback_query_handler(func=lambda call: call.data == "hub_checkin")
def hub_checkin(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    user = get_user(uid)
    bugun = datetime.now().date()
    oxirgi = user.get("last_checkin")
    oxirgi_sana = datetime.strptime(oxirgi, "%d.%m.%Y").date() if oxirgi else None

    if oxirgi_sana == bugun:
        bot.send_message(uid, f"✅ Siz bugun allaqachon chek-in qilgansiz!\n🔥 Joriy ketma-ketlik: {user.get('streak_count', 0)} kun")
        return

    if oxirgi_sana == bugun - timedelta(days=1):
        user["streak_count"] = user.get("streak_count", 0) + 1
    else:
        user["streak_count"] = 1

    user["last_checkin"] = bugun.strftime("%d.%m.%Y")
    streak = user["streak_count"]

    matn = f"✅ Chek-in qabul qilindi!\n🔥 Ketma-ketlik: {streak} kun"

    if streak in CHEKIN_MUKOFOTLAR:
        mukofot = CHEKIN_MUKOFOTLAR[streak]
        user["balance"] = user.get("balance", 0) + mukofot
        user.setdefault("balance_tarix", []).append({
            "sana": datetime.now().strftime("%d.%m.%Y %H:%M"), "miqdor": mukofot,
            "izoh": f"Chek-in mukofoti ({streak} kunlik ketma-ketlik)"
        })
        matn += f"\n\n🎉 Tabriklaymiz! {streak} kunlik ketma-ketlik uchun {som_format(mukofot)} bonus oldingiz!"

    update_user(uid, user)
    bot.send_message(uid, matn)


# ============================================================
#  📊 SHAXSIY STATISTIKA VA INFOGRAFIKA
# ============================================================
@bot.callback_query_handler(func=lambda call: call.data == "hub_batafsil_stat")
def hub_batafsil_stat(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    user = get_user(uid)
    elonlar = load_elonlar()
    mening_elonlar = [eid for eid in user.get("elonlar", []) if eid in elonlar]
    jami_korish = sum(elonlar[eid].get("korishlar", 0) for eid in mening_elonlar)

    matn = (
        f"📊 **Sizning shaxsiy statistikangiz**\n\n"
        f"📢 Bergan e'lonlaringiz: {len(mening_elonlar)} ta (jami {jami_korish} marta ko'rilgan)\n"
        f"🚖 Taksida bosib o'tilgan masofa: {round(user.get('taksi_km_jami', 0), 1)} km\n"
        f"🤖 AI xizmatlaridan foydalanish: {user.get('ai_ishlatish_soni', 0)} marta\n"
        f"🧠 Viktorina XP balingiz: {user.get('xp', 0)} XP\n"
        f"🔥 Chek-in ketma-ketligi: {user.get('streak_count', 0)} kun\n"
        f"🎁 Taklif qilgan do'stlaringiz: {user.get('referral_count', 0)} ta\n"
        f"💰 Bonus balans: {som_format(user.get('balance', 0))}\n"
        f"📅 Botga qo'shilgan sana: {user.get('joined_date','-')}"
    )
    bot.send_message(uid, matn, parse_mode="Markdown")


# ============================================================
#  💼 ISH VA XIZMATLAR BO'LIMI (hub)
# ============================================================
@bot.message_handler(func=lambda m: m.text == "💼 Ish va Xizmatlar")
def hub_ish(message):
    if check_ban(message): return
    uid = message.from_user.id
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🤝 Ish topish", callback_data="hub_ish_topish"),
        types.InlineKeyboardButton("💼 Ish e'loni berish", callback_data="hub_ish_elon"),
        types.InlineKeyboardButton("🏠 Ijara uylar", callback_data="hub_ijara"),
        types.InlineKeyboardButton("🛍️ Marketplace", callback_data="hub_market"),
        types.InlineKeyboardButton("🚚 Yetkazib berish", callback_data="hub_yetkazib"),
        types.InlineKeyboardButton("📝 Imtixonga ariza berish", callback_data="hub_imtixon"),
        types.InlineKeyboardButton("🎓 Natijani bilish", callback_data="hub_natija"),
        types.InlineKeyboardButton("📋 Ruxsatnomani yuklash", callback_data="hub_ruxsatnoma"),
        types.InlineKeyboardButton("🚗 Hamrohlik taksi (Poputka)", callback_data="hub_poputka"),
        types.InlineKeyboardButton("🔎 Yo'qolgan/Topilgan", callback_data="hub_topilma"),
    )
    bot.send_message(uid, "💼 **Ish va Xizmatlar bo'limi:**", parse_mode="Markdown", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "hub_poputka")
def hub_poputka(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🔍 Mavjud yo'nalishlarni ko'rish", callback_data="poputka_korish"),
        types.InlineKeyboardButton("➕ Yo'nalish e'lon qilish", callback_data="poputka_elon"),
    )
    bot.send_message(uid, "🚗 **Hamrohlik taksi (Poputka):**\n\nYo'lni bo'lishib, yo'l haqini tejang!",
                     parse_mode="Markdown", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "poputka_korish")
def poputka_korish(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    eid_list = faol_elonlar_royxati(kategoriya_kod="poputka")
    elonni_yuborish(uid, eid_list, 0)


@bot.callback_query_handler(func=lambda call: call.data == "poputka_elon")
def poputka_elon_start(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    if check_sub(uid) is False:
        send_sub_message(uid)
        return
    user_data_temp[uid] = {"is_vip": False, "kategoriya": "🚗 Hamrohlik taksi", "kategoriya_kod": "poputka",
                           "hudud": "Kiritilmagan", "tuman": "Kiritilmagan", "location": None}
    user_state[uid] = "elon_sarlavha"
    bot.send_message(uid, "✍️ **Yo'nalishni yozing** (masalan: 'Toshkent — Samarqand, bugun soat 14:00, 2 o'rin bor'):",
                     parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data == "hub_topilma")
def hub_topilma(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🔍 E'lonlarni ko'rish", callback_data="topilma_korish"),
        types.InlineKeyboardButton("➕ E'lon berish", callback_data="topilma_elon"),
    )
    bot.send_message(uid, "🔎 **Yo'qolgan/Topilgan buyumlar:**\n\nHujjat, kalit, hamyon, uy hayvoni va h.k.",
                     parse_mode="Markdown", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "topilma_korish")
def topilma_korish(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    eid_list = faol_elonlar_royxati(kategoriya_kod="topilma")
    elonni_yuborish(uid, eid_list, 0)


@bot.callback_query_handler(func=lambda call: call.data == "topilma_elon")
def topilma_elon_start(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    if check_sub(uid) is False:
        send_sub_message(uid)
        return
    user_data_temp[uid] = {"is_vip": False, "kategoriya": "🔎 Yo'qolgan/Topilgan", "kategoriya_kod": "topilma",
                           "hudud": "Kiritilmagan", "tuman": "Kiritilmagan", "location": None}
    user_state[uid] = "elon_sarlavha"
    bot.send_message(uid, "✍️ **Nima yo'qolgan/topilgan? Qisqacha yozing** (masalan: 'Yunusobodda hujjat topildi'):",
                     parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data == "hub_imtixon")
def hub_imtixon(call):
    bot.answer_callback_query(call.id)
    imtixon_ariza_start(FakeMessage(call.from_user.id))


@bot.callback_query_handler(func=lambda call: call.data == "hub_natija")
def hub_natija(call):
    bot.answer_callback_query(call.id)
    natija_bilish_start(FakeMessage(call.from_user.id))


@bot.callback_query_handler(func=lambda call: call.data == "hub_ruxsatnoma")
def hub_ruxsatnoma(call):
    bot.answer_callback_query(call.id)
    ruxsatnoma_start(FakeMessage(call.from_user.id))


@bot.callback_query_handler(func=lambda call: call.data == "hub_ish_topish")
def hub_ish_topish(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass
    eid_list = faol_elonlar_royxati(kategoriya_kod="ish")
    elonni_yuborish(uid, eid_list, 0)


@bot.callback_query_handler(func=lambda call: call.data == "hub_ish_elon")
def hub_ish_elon(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    if check_sub(uid) is False:
        send_sub_message(uid)
        return
    user_data_temp[uid] = {"is_vip": False, "kategoriya": "💼 Ish o'rni", "kategoriya_kod": "ish"}
    user_state[uid] = "elon_sarlavha"
    user_data_temp[uid]["hudud"] = "Kiritilmagan"
    user_data_temp[uid]["tuman"] = "Kiritilmagan"
    user_data_temp[uid]["location"] = None
    bot.send_message(uid, "✍️ **Ish e'loni sarlavhasini kiriting** (masalan: 'Sotuvchi kerak, oylik 3 mln'):",
                     parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data == "hub_ijara")
def hub_ijara(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    eid_list = faol_elonlar_royxati(kategoriya_kod="ijara")
    elonni_yuborish(uid, eid_list, 0)


@bot.callback_query_handler(func=lambda call: call.data == "hub_market")
def hub_market(call):
    bot.answer_callback_query(call.id)
    elonlarni_korish_start(FakeMessage(call.from_user.id))


@bot.callback_query_handler(func=lambda call: call.data == "hub_yetkazib")
def hub_yetkazib(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    eid_list = faol_elonlar_royxati(kategoriya_kod="yetkaz")
    elonni_yuborish(uid, eid_list, 0)


# ============================================================
#  📢 QO'SHIMCHA BO'LIM (hub) — yangiliklar, bonuslar, foydali vositalar
# ============================================================
@bot.message_handler(func=lambda m: m.text == "📢 Qo'shimcha")
def hub_qoshimcha(message):
    if check_ban(message): return
    uid = message.from_user.id
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("💬 Jamoat chati", url=GURUH_LINK),
        types.InlineKeyboardButton("🏦 Valyuta kursi", callback_data="hub_valyuta"),
        types.InlineKeyboardButton("🌦️ Ob-havo", callback_data="hub_obhavo"),
        types.InlineKeyboardButton("📅 Kalendar", callback_data="hub_kalendar"),
        types.InlineKeyboardButton("📞 Tez yordam raqamlari", callback_data="hub_tez_yordam"),
        types.InlineKeyboardButton("🎮 Mini o'yin", callback_data="hub_oyin"),
        types.InlineKeyboardButton("📊 Statistika", callback_data="hub_statistika"),
        types.InlineKeyboardButton("📜 Qoidalar", callback_data="hub_qoidalar"),
        types.InlineKeyboardButton("🆔 Chat ID bilish", callback_data="hub_chatid"),
        types.InlineKeyboardButton("🤖 Bot yasatish", callback_data="hub_bot_yasatish"),
        types.InlineKeyboardButton("📰 Yangiliklar", callback_data="hub_yangiliklar"),
        types.InlineKeyboardButton("🎁 Bonuslar", callback_data="hub_bonuslar"),
        types.InlineKeyboardButton("🎯 Aksiyalar", callback_data="hub_aksiyalar"),
        types.InlineKeyboardButton("📅 Tadbirlar", callback_data="hub_tadbirlar"),
    )
    bot.send_message(uid, "📢 **Qo'shimcha bo'lim:**", parse_mode="Markdown", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "hub_statistika")
def hub_statistika(call):
    bot.answer_callback_query(call.id)
    menu_boshqa_tugmalar(FakeMessage(call.from_user.id, "📊 Statistika"))


@bot.callback_query_handler(func=lambda call: call.data == "hub_qoidalar")
def hub_qoidalar(call):
    bot.answer_callback_query(call.id)
    menu_boshqa_tugmalar(FakeMessage(call.from_user.id, "📜 Qoidalar"))


@bot.callback_query_handler(func=lambda call: call.data == "hub_chatid")
def hub_chatid(call):
    bot.answer_callback_query(call.id)
    chat_id_bilish(FakeMessage(call.from_user.id))


@bot.callback_query_handler(func=lambda call: call.data == "hub_bot_yasatish")
def hub_bot_yasatish(call):
    bot.answer_callback_query(call.id)
    bot_yasatish_start(FakeMessage(call.from_user.id))


@bot.callback_query_handler(func=lambda call: call.data == "hub_yangiliklar")
def hub_yangiliklar(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    yangiliklar = load_news()
    if not yangiliklar:
        bot.send_message(uid, "📰 Hozircha yangiliklar yo'q.")
        return
    matn = "📰 **So'nggi yangiliklar:**\n\n" + "\n\n".join(
        f"📅 {n['sana']}\n{md_escape(n['matn'])}" for n in yangiliklar[-5:][::-1]
    )
    bot.send_message(uid, matn, parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data == "hub_bonuslar")
def hub_bonuslar(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    user = get_user(uid)
    matn = (
        "🎁 **Bonus qanday to'planadi?**\n\n"
        "• 🎁 Do'st taklif qilish — har 5 ta do'stingiz uchun Premium 💎\n"
        "• 🎟 Promo kodlar — vaqti-vaqti bilan e'lon qilinadi\n"
        "• 🚖 Taksi cashback — har safardan 1% hamyoningizga qaytadi\n\n"
        f"💰 Joriy bonus balansingiz: {som_format(user.get('balance', 0))}"
    )
    bot.send_message(uid, matn, parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data == "hub_aksiyalar")
def hub_aksiyalar(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    qatorlar = []
    for kod, promo in PROMO_KODLAR.items():
        qator = f"• `{kod}` — {som_format(promo['miqdor'])} bonus"
        if promo.get("limit") is not None:
            qolgan = max(0, promo["limit"] - promo_ishlatish_sonini_ol(kod))
            qator += f" (faqat birinchi {promo['limit']} kishi uchun, {qolgan} ta o'rin qoldi)"
        qatorlar.append(qator)
    matn = "🎯 **Hozirda faol aksiya (promo) kodlar:**\n\n" + "\n".join(qatorlar) + \
        "\n\n👉 Kodni faollashtirish uchun 💰 Pul va Premium → 🎁 Promo kod bo'limiga o'ting."
    bot.send_message(uid, matn, parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data == "hub_tadbirlar")
def hub_tadbirlar(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    tadbirlar = load_events()
    if not tadbirlar:
        bot.send_message(uid, "📅 Hozircha rejalashtirilgan tadbirlar yo'q.")
        return
    matn = "📅 **Yaqinlashib kelayotgan tadbirlar:**\n\n" + "\n\n".join(
        f"📅 {t['sana']}\n{md_escape(t['matn'])}" for t in tadbirlar[-10:][::-1]
    )
    bot.send_message(uid, matn, parse_mode="Markdown")


@bot.message_handler(commands=['event'])
def admin_event_qoshish(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        matn = message.text.split(maxsplit=1)[1]
    except IndexError:
        bot.reply_to(message, "⚠️ Format: `/event Tadbir haqida matn`", parse_mode="Markdown")
        return
    event_qoshish(matn)
    bot.reply_to(message, "✅ Tadbir qo'shildi va foydalanuvchilarga ko'rinadi.")


@bot.callback_query_handler(func=lambda call: call.data == "hub_valyuta")
def hub_valyuta(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    try:
        r = requests.get("https://api.frankfurter.app/latest?from=USD&to=UZS,EUR,RUB", timeout=8)
        d = r.json()["rates"]
        matn = (
            f"🏦 **Valyuta kurslari (1 USD):**\n\n"
            f"🇺🇿 UZS: {d.get('UZS', '-'):,.0f}\n"
            f"🇪🇺 EUR: {d.get('EUR', '-'):.3f}\n"
            f"🇷🇺 RUB: {d.get('RUB', '-'):.2f}"
        )
    except Exception as e:
        log.warning(f"Valyuta APIsi ishlamadi: {e}")
        matn = "❌ Valyuta kurslarini olishda xatolik. Birozdan so'ng qayta urinib ko'ring."
    bot.send_message(uid, matn, parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data == "hub_obhavo")
def hub_obhavo_start(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    user_state[uid] = "obhavo_shahar_kutish"
    bot.send_message(uid, "🌦️ Qaysi shahar uchun ob-havo kerak? (masalan: Tashkent)")


@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == "obhavo_shahar_kutish")
def hub_obhavo_natija(message):
    uid = message.from_user.id
    user_state.pop(uid, None)
    shahar = message.text.strip()
    try:
        r = requests.get(f"https://wttr.in/{shahar}?format=3&lang=ru", timeout=8)
        matn = f"🌦️ {r.text.strip()}"
    except Exception as e:
        log.warning(f"Ob-havo APIsi ishlamadi: {e}")
        matn = "❌ Ob-havo ma'lumotini olishda xatolik. Shahar nomini tekshirib qayta urinib ko'ring."
    bot.send_message(uid, matn, reply_markup=get_main_keyboard(uid))


@bot.callback_query_handler(func=lambda call: call.data == "hub_kalendar")
def hub_kalendar(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    kunlar = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"]
    hozir = datetime.now()
    matn = f"📅 Bugun: **{hozir.strftime('%d.%m.%Y')}**, {kunlar[hozir.weekday()]}"
    bot.send_message(uid, matn, parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data == "hub_tez_yordam")
def hub_tez_yordam(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    matn = "📞 **Tez yordam raqamlari (O'zbekiston):**\n\n" + "\n".join(
        f"{nom}: `{raqam}`" for nom, raqam in TEZ_YORDAM_RAQAMLARI
    )
    bot.send_message(uid, matn, parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data == "hub_oyin")
def hub_oyin(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(
        types.InlineKeyboardButton("🎲", callback_data="oyin_🎲"),
        types.InlineKeyboardButton("🎯", callback_data="oyin_🎯"),
        types.InlineKeyboardButton("🏀", callback_data="oyin_🏀"),
        types.InlineKeyboardButton("⚽", callback_data="oyin_⚽"),
        types.InlineKeyboardButton("🎳", callback_data="oyin_🎳"),
        types.InlineKeyboardButton("🎰", callback_data="oyin_🎰"),
    )
    bot.send_message(uid, "🎮 Qaysi mini-o'yinni sinab ko'rmoqchisiz?", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("oyin_"))
def oyin_otkazish(call):
    uid = call.from_user.id
    emoji = call.data.replace("oyin_", "")
    bot.answer_callback_query(call.id)
    try:
        bot.send_dice(uid, emoji=emoji)
    except Exception as e:
        log.warning(f"Mini o'yin yuborilmadi: {e}")
        bot.send_message(uid, "❌ Bu o'yin hozircha ishlamayapti.")


# ============================================================
#  ⚙️ SOZLAMALAR BO'LIMI (hub — kengaytirilgan)
# ============================================================
@bot.message_handler(func=lambda m: m.text == "⚙️ Sozlamalar")
def hub_sozlamalar(message):
    if check_ban(message): return
    uid = message.from_user.id
    user = get_user(uid)
    markup = types.InlineKeyboardMarkup(row_width=2)
    bildir_matn = "🔔 Bildirishnoma: Yoqilgan" if user.get("bildirishnoma", True) else "🔕 Bildirishnoma: O'chirilgan"
    tungi_matn = "🌙 Tungi rejim: Yoqilgan" if user.get("tungi_rejim", False) else "☀️ Tungi rejim: O'chirilgan"
    markup.add(
        types.InlineKeyboardButton("📝 Ismni o'zgartirish", callback_data="set_name"),
        types.InlineKeyboardButton("🔗 Profil nomini o'zgartirish", callback_data="set_tg_username"),
        types.InlineKeyboardButton("📞 Raqamni o'zgartirish", callback_data="set_phone"),
        types.InlineKeyboardButton(bildir_matn, callback_data="toggle_bildirishnoma"),
        types.InlineKeyboardButton(tungi_matn, callback_data="toggle_tungi_rejim"),
        types.InlineKeyboardButton(f"🌐 Til: {user.get('til', 'uz').upper()}", callback_data="toggle_til"),
        types.InlineKeyboardButton("🔒 Maxfiylik", callback_data="hub_maxfiylik"),
        types.InlineKeyboardButton("📱 Qurilmalar", callback_data="hub_qurilmalar"),
        types.InlineKeyboardButton("🗑 Akkauntni o'chirish", callback_data="delete_account_start"),
    )
    bot.send_message(
        uid,
        f"⚙️ *Sozlamalar:*\n\n👤 *Ism:* {user['name']}\n🔗 *Profil:* {user.get('tg_username', 'Kiritilmagan')}\n"
        f"📞 *Telefon:* {user['phone'] if user['phone'] else 'Kiritilmagan'}",
        parse_mode="Markdown", reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data in ["toggle_bildirishnoma", "toggle_tungi_rejim"])
def toggle_sozlama(call):
    uid = call.from_user.id
    user = get_user(uid)
    maydon = "bildirishnoma" if call.data == "toggle_bildirishnoma" else "tungi_rejim"
    user[maydon] = not user.get(maydon, False if maydon == "tungi_rejim" else True)
    update_user(uid, user)
    bot.answer_callback_query(call.id, "✅ Yangilandi!")
    hub_sozlamalar(FakeMessage(uid))


TIL_TSIKLI = ["uz", "ru", "en"]


@bot.callback_query_handler(func=lambda call: call.data == "toggle_til")
def toggle_til(call):
    uid = call.from_user.id
    user = get_user(uid)
    joriy = user.get("til", "uz")
    keyingi = TIL_TSIKLI[(TIL_TSIKLI.index(joriy) + 1) % len(TIL_TSIKLI)] if joriy in TIL_TSIKLI else "uz"
    user["til"] = keyingi
    update_user(uid, user)
    nom = {"uz": "O'zbekcha", "ru": "Русский", "en": "English"}[keyingi]
    bot.answer_callback_query(call.id, f"✅ Til: {nom}")
    if keyingi != "uz":
        bot.send_message(uid, f"ℹ️ Til {nom} qilib saqlandi. Hozircha botning asosiy matnlari o'zbek tilida, "
                              f"lekin AI yordamchi orqali istalgan tilda muloqot qilishingiz mumkin.")
    hub_sozlamalar(FakeMessage(uid))


@bot.callback_query_handler(func=lambda call: call.data == "hub_maxfiylik")
def hub_maxfiylik(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    matn = (
        "🔒 **Maxfiylik siyosati:**\n\n"
        "• Ism, telefon raqami va Telegram profilingiz — e'lon/taksi xizmatlarini ko'rsatish uchun saqlanadi.\n"
        "• Ma'lumotlaringiz uchinchi shaxslarga sotilmaydi.\n"
        "• Faqat admin va xizmat ko'rsatish jarayonida zarur tomon (masalan taksi haydovchisi) ma'lumotlaringizni ko'radi.\n"
        "• \"⚙️ Sozlamalar → 🗑 Akkauntni o'chirish\" orqali istalgan vaqtda ma'lumotlaringizni o'chirtirishingiz mumkin."
    )
    bot.send_message(uid, matn, parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data == "hub_qurilmalar")
def hub_qurilmalar(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    user = get_user(uid)
    matn = (
        "📱 **Qurilmalar haqida:**\n\n"
        "Telegram bot API xavfsizlik sabablari bilan botlarga ulangan qurilmalar ro'yxatini ko'rish imkonini bermaydi.\n\n"
        f"📅 Botga qo'shilgan sana: {user.get('joined_date','-')}\n\n"
        "ℹ️ O'z Telegram akkauntingizga ulangan qurilmalarni ko'rish uchun: "
        "Telegram ilovasi → Sozlamalar → Qurilmalar bo'limiga o'ting."
    )
    bot.send_message(uid, matn, parse_mode="Markdown")


# ============================================================
#  🛠 ADMIN PANEL (hub — mavjud /admin komandalarga yo'naltiradi)
# ============================================================
@bot.message_handler(func=lambda m: m.text == "🛠 Admin panel" and m.from_user.id == ADMIN_ID)
def hub_admin_panel(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📈 Statistika", callback_data="hub_admin_stat"),
        types.InlineKeyboardButton("📢 Reklama yuborish", callback_data="hub_admin_broadcast"),
        types.InlineKeyboardButton("📂 Backup", callback_data="hub_admin_backup"),
        types.InlineKeyboardButton("📝 Loglar", callback_data="hub_admin_loglar"),
        types.InlineKeyboardButton("💰 To'lovlar", callback_data="hub_admin_tolovlar"),
    )
    bot.send_message(
        ADMIN_ID,
        "🛠 **Admin panel**\n\nQo'shimcha buyruqlar uchun /admin yozing "
        "(foydalanuvchi qidirish, ban/unban, premium berish va h.k.)",
        parse_mode="Markdown", reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data == "hub_admin_stat" and call.from_user.id == ADMIN_ID)
def hub_admin_stat(call):
    bot.answer_callback_query(call.id)
    bot.send_message(ADMIN_ID, stat_matnini_hosil_qil(), parse_mode="Markdown")


@bot.callback_query_handler(func=lambda call: call.data == "hub_admin_broadcast" and call.from_user.id == ADMIN_ID)
def hub_admin_broadcast(call):
    bot.answer_callback_query(call.id)
    broadcast_start(FakeMessage(ADMIN_ID))


@bot.callback_query_handler(func=lambda call: call.data == "hub_admin_backup" and call.from_user.id == ADMIN_ID)
def hub_admin_backup(call):
    bot.answer_callback_query(call.id)
    admin_backup(FakeMessage(ADMIN_ID, "/backup"))


@bot.callback_query_handler(func=lambda call: call.data == "hub_admin_loglar" and call.from_user.id == ADMIN_ID)
def hub_admin_loglar(call):
    bot.answer_callback_query(call.id)
    try:
        with open("bot.log", "r", encoding="utf-8") as f:
            qatorlar = f.readlines()[-40:]
        matn = "📝 **Oxirgi loglar:**\n\n```\n" + "".join(qatorlar)[-3500:] + "\n```"
        bot.send_message(ADMIN_ID, matn, parse_mode="Markdown")
    except Exception as e:
        bot.send_message(ADMIN_ID, f"❌ Loglarni o'qib bo'lmadi: {e}")


@bot.callback_query_handler(func=lambda call: call.data == "hub_admin_tolovlar" and call.from_user.id == ADMIN_ID)
def hub_admin_tolovlar(call):
    bot.answer_callback_query(call.id)
    db = load_db()
    jami_toldirilgan = 0
    jami_yechilgan = 0
    songi_amallar = []
    for uid_str, u in db.items():
        for t in u.get("balance_tarix", []):
            if "to'ldirildi" in t.get("izoh", "").lower():
                jami_toldirilgan += t.get("miqdor", 0)
            elif "yechildi" in t.get("izoh", "").lower():
                jami_yechilgan += abs(t.get("miqdor", 0))
            songi_amallar.append((t.get("sana", ""), u.get("name", "?"), t.get("izoh", ""), t.get("miqdor", 0)))

    songi_amallar.sort(key=lambda x: x[0], reverse=True)
    matn = (
        f"💰 **To'lovlar bo'yicha umumiy hisobot:**\n\n"
        f"➕ Jami to'ldirilgan: {som_format(jami_toldirilgan)}\n"
        f"➖ Jami yechilgan: {som_format(jami_yechilgan)}\n\n"
        f"📜 **So'nggi 10 ta amal:**\n"
    ) + "\n".join(
        f"• {sana} — {md_escape(ism)}: {izoh} ({'+' if miqdor >= 0 else ''}{miqdor} so'm)"
        for sana, ism, izoh, miqdor in songi_amallar[:10]
    )
    bot.send_message(ADMIN_ID, matn if songi_amallar else "💰 Hozircha to'lov amallari yo'q.", parse_mode="Markdown")


# ---- START BUYRUG'I ----
@bot.message_handler(commands=["start"])
def start(message):
    if check_ban(message): return
    uid = message.from_user.id

    if not check_sub(uid):
        send_sub_message(uid)
        return

    user = get_user(uid)

    parts = message.text.split()
    if len(parts) > 1 and parts[1].startswith("ref_") and not user.get("referred_by"):
        try:
            taklifchi_id = int(parts[1].replace("ref_", ""))
            if taklifchi_id != uid:
                taklifchi = get_user(taklifchi_id)
                user["referred_by"] = taklifchi_id
                update_user(uid, user)
                taklifchi["referral_count"] = taklifchi.get("referral_count", 0) + 1
                yangi_soni = taklifchi["referral_count"]
                if yangi_soni > 0 and yangi_soni % 5 == 0 and not taklifchi.get("premium"):
                    taklifchi["premium"] = True
                    try:
                        bot.send_message(taklifchi_id,
                                         f"🎉 Tabriklaymiz! Siz {yangi_soni} ta do'stingizni taklif qildingiz "
                                         f"va Premium 💎 maqomiga ega bo'ldingiz!")
                    except Exception as e:
                        log.warning(f"Referal xabari yuborilmadi: {e}")
                update_user(taklifchi_id, taklifchi)
        except (ValueError, IndexError):
            pass

    if not user["name"]:
        user_state[uid] = "reg_name"
        f_name = message.from_user.first_name if message.from_user.first_name else ""
        l_name = message.from_user.last_name if message.from_user.last_name else ""
        full_tg_name = f"{f_name} {l_name}".strip()

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        if full_tg_name:
            markup.add(types.KeyboardButton(full_tg_name))

        bot.send_message(
            uid,
            "👋 Xush kelibsiz! Botdan to'liq foydalanish uchun ismingizni kiriting:\n"
            "_(Pastdagi tugmani bossangiz, Telegramdagi ismingiz avtomatik kiritiladi)_",
            reply_markup=markup, parse_mode="Markdown"
        )
        return

    if not user.get("tg_username"):
        user_state[uid] = "reg_tg_username"
        current_username = f"@{message.from_user.username}" if message.from_user.username else ""
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        if current_username:
            markup.add(current_username)
        bot.send_message(uid,
                         "🔗 Telegram profilingiz ismini kiriting (Masalan: @username):\n_(Agar pastda tayyor chiqsa, uni bossangiz ham bo'ladi)_",
                         reply_markup=markup, parse_mode="Markdown")
        return

    if not user["phone"]:
        user_state[uid] = "reg_phone"
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(types.KeyboardButton("📞 Telefon raqamni yuborish", request_contact=True))
        bot.send_message(uid, "📱 Iltimos, pastdagi tugmani bosib telefon raqamingizni ulashing:", reply_markup=markup)
        return

    premium_text = "✅ Premium 💎" if user["premium"] else "❌ Bepul (3 ta limit)"
    bot.send_message(
        uid,
        f"Assalomu alaykum, {user['name']}!\n\n"
        f"📋 E'lon platformasiga xush kelibsiz!\n"
        f"💎 Sizning holatingiz: {premium_text}\n\n"
        f"Quyidagi tugmalardan foydanlaning:",
        reply_markup=get_main_keyboard(uid)
    )


# ---- 🤖 GEMINI AI BO'LIMI ----
@bot.message_handler(func=lambda m: m.text == "🤖 Gemini AI")
def gemini_ai_start(message):
    if check_ban(message): return
    uid = message.from_user.id
    user_state[uid] = "gemini_chat"

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🔙 Asosiy menu")

    bot.send_message(
        uid,
        "🤖 **Gemini AI chat rejimiga xush kelibsiz!**\n\n"
        "Menga istalgan savolingizni yo'llashingiz mumkin, jon deb javob beraman. "
        "Chatdan chiqish uchun quyidagi '🔙 Asosiy menu' tugmasini bosing.",
        reply_markup=markup
    )


@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == "gemini_chat")
def gemini_chat_handle(message):
    uid = message.from_user.id
    text = message.text

    if text == "🔙 Asosiy menu":
        user_state.pop(uid, None)
        bot.send_message(uid, "Asosiy menuga qaytdingiz.", reply_markup=get_main_keyboard(uid))
        return

    if not ai_client:
        bot.send_message(uid, "❌ Gemini AI hozircha sozlanmagan (API kalit yo'q).")
        return

    sent_msg = bot.send_message(uid, "⏳ O'ylayapman...")

    try:
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=text,
        )
        bot.edit_message_text(response.text, chat_id=uid, message_id=sent_msg.message_id)
    except Exception as e:
        log.error(f"Gemini AI xatoligi: {e}")
        bot.edit_message_text("❌ Kechirasiz, javob olishda xatolik yuz berdi. Birozdan so'ng qayta urinib ko'ring.",
                              chat_id=uid, message_id=sent_msg.message_id)


# ---- 🤖 BOT YASATISH BO'LIMI ----
@bot.message_handler(func=lambda m: m.text == "🤖 Bot yasatish")
def bot_yasatish_start(message):
    if check_ban(message): return
    uid = message.from_user.id
    user_state[uid] = "bot_ariza_tavsif"
    bot.send_message(
        uid,
        "🤖 Bot yasatish bo'yicha ariza berish bo'limi\n\n"
        "Iltimos, qanday bot kerakligi va uning funksiyalari haqida batafsil yozing.\n"
        "Masalan: 'Menga e'lonlar boti yoki do'kon boti kerak, vazifasi bunday bo'lsin...'",
        reply_markup=types.ReplyKeyboardRemove()
    )


@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == "bot_ariza_tavsif")
def bot_yasatish_yakun(message):
    uid = message.from_user.id
    tavsif = message.text
    user = get_user(uid)

    ariza_matni = (
        f"🔔 YANGI BOT YASASH UCHUN ARIZA\n\n"
        f"👤 Foydalanuvchi: {user['name']}\n"
        f"🔗 Profil: {user.get('tg_username', 'Mavjud emas')}\n"
        f"📞 Telefon: {user['phone']}\n"
        f"🆔 ID: {uid}\n\n"
        f"📝 Bot tavsifi:\n{tavsif}"
    )

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"accept_{uid}"),
        types.InlineKeyboardButton("❌ Bekor qilish", callback_data=f"reject_{uid}")
    )

    try:
        bot.send_message(ADMIN_ID, ariza_matni, reply_markup=markup)
    except Exception as e:
        log.error(f"Adminga ariza yuborishda muammo: {e}")

    user_state.pop(uid, None)

    bot.send_message(
        uid,
        "✅ Arizangiz muvaffaqiyatli adminga yuborildi!\n\nTez orada admin arizangizni ko'rib chiqadi.",
        reply_markup=get_main_keyboard(uid)
    )


# ---- ADMIN PANEL ARIZA HANDLERLARI ----
@bot.callback_query_handler(func=lambda call: call.data.startswith("accept_") or call.data.startswith("reject_"))
def handle_ariza_buttons(call):
    if call.from_user.id != ADMIN_ID: return
    action, user_id = call.data.split("_")
    bot.answer_callback_query(call.id)

    if action == "accept":
        bot.edit_message_text(f"{call.message.text}\n\n🟢 ADMIN TOMONIDAN QABUL QILINDI", ADMIN_ID,
                              call.message.message_id)
        try:
            bot.send_message(int(user_id),
                             "🎉 Sizning bot yasash bo'yicha arizangiz admin tomonidan qabul qilindi! Tez orada aloqaga chiqishadi.")
        except Exception as e:
            log.warning(f"Xabar yuborilmadi: {e}")
    else:
        bot.edit_message_text(f"{call.message.text}\n\n🔴 ADMIN TOMONIDAN RAD ETILDI", ADMIN_ID, call.message.message_id)
        try:
            bot.send_message(int(user_id),
                             "❌ Afsuski, sizning bot yasash bo'yicha arizangiz admin tomonidan rad etildi.")
        except Exception as e:
            log.warning(f"Xabar yuborilmadi: {e}")


# ============================================================
#  🔍 E'LONLARNI KO'RISH / 🔎 QIDIRUV
# ============================================================
def elonni_yuborish(uid, eid_list, index, message_id=None):
    if not eid_list:
        text = "😕 Hozircha mos e'lon topilmadi."
        if message_id:
            try:
                bot.edit_message_caption(text, uid, message_id)
            except Exception:
                try:
                    bot.edit_message_text(text, uid, message_id)
                except Exception:
                    bot.send_message(uid, text)
        else:
            bot.send_message(uid, text)
        return

    index = index % len(eid_list)
    eid = eid_list[index]
    elonlar = load_elonlar()
    elon = elonlar.get(eid)
    if not elon:
        return

    # 👀 Ko'rilganlar hisoblagichi — egasi o'zi ko'rsa hisoblanmaydi
    if elon.get("user_id") != uid:
        elon["korishlar"] = elon.get("korishlar", 0) + 1
        elonlar[eid] = elon
        save_elonlar(elonlar)

    matn = elon_matni(eid, elon, tolik=True)
    matn += f"\n👀 Ko'rishlar: {elon.get('korishlar', 0)}"
    matn += f"\n📄 {index + 1}/{len(eid_list)}"

    nav = types.InlineKeyboardMarkup(row_width=3)
    nav.add(
        types.InlineKeyboardButton("⬅️", callback_data="browse_prev"),
        types.InlineKeyboardButton("❤️ Saqlash", callback_data=f"fav_{eid}"),
        types.InlineKeyboardButton("➡️", callback_data="browse_next"),
    )
    if elon.get("user_id") != uid:
        nav.add(types.InlineKeyboardButton("✉️ Sotuvchiga yozish", callback_data=f"msgowner_{eid}"))
    nav.add(types.InlineKeyboardButton("🚩 Shikoyat", callback_data=f"report_{eid}"))

    user_data_temp.setdefault(uid, {})
    user_data_temp[uid]["browse_list"] = eid_list
    user_data_temp[uid]["browse_index"] = index

    if elon.get("photo"):
        xavfsiz_photo_yuborish(uid, elon["photo"], matn, reply_markup=nav)
    else:
        xavfsiz_yuborish(uid, matn, reply_markup=nav)


@bot.message_handler(func=lambda m: m.text == "🔍 E'lonlarni ko'rish")
def elonlarni_korish_start(message):
    if check_ban(message): return
    uid = message.from_user.id
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [types.InlineKeyboardButton(nom, callback_data=f"korish_kot_{kod}") for nom, kod in KATEGORIYALAR]
    markup.add(*buttons)
    markup.add(types.InlineKeyboardButton("📃 Barcha e'lonlar", callback_data="korish_kot_all"))
    bot.send_message(uid, "📂 Qaysi kategoriyadagi e'lonlarni ko'rmoqchisiz?", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("korish_kot_"))
def elonlarni_korish_kategoriya(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    kod = call.data.replace("korish_kot_", "")
    kod_filter = None if kod == "all" else kod
    eid_list = faol_elonlar_royxati(kategoriya_kod=kod_filter)
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass
    elonni_yuborish(uid, eid_list, 0)


@bot.message_handler(func=lambda m: m.text == "🔎 Qidiruv")
def qidiruv_start(message):
    if check_ban(message): return
    uid = message.from_user.id
    user_state[uid] = "qidiruv_kutish"
    bot.send_message(uid, "🔎 Qidirmoqchi bo'lgan so'zni kiriting (masalan: iPhone, kvartira, Cobalt):")


@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == "qidiruv_kutish")
def qidiruv_natija(message):
    uid = message.from_user.id
    user_state.pop(uid, None)
    eid_list = faol_elonlar_royxati(qidiruv=message.text)
    elonni_yuborish(uid, eid_list, 0)


@bot.callback_query_handler(func=lambda call: call.data in ["browse_next", "browse_prev"])
def elon_navigatsiya(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    data = user_data_temp.get(uid, {})
    eid_list = data.get("browse_list", [])
    index = data.get("browse_index", 0)
    if not eid_list:
        return
    index = index + 1 if call.data == "browse_next" else index - 1
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass
    elonni_yuborish(uid, eid_list, index)


@bot.callback_query_handler(func=lambda call: call.data.startswith("fav_"))
def elon_saqlash(call):
    uid = call.from_user.id
    eid = call.data.split("_")[1]
    user = get_user(uid)
    if eid in user["sevimlilar"]:
        bot.answer_callback_query(call.id, "ℹ️ Bu e'lon allaqachon sevimlilarda bor.")
        return
    user["sevimlilar"].append(eid)
    update_user(uid, user)
    bot.answer_callback_query(call.id, "❤️ Sevimlilarga qo'shildi!")


@bot.callback_query_handler(func=lambda call: call.data.startswith("report_"))
def elon_shikoyat(call):
    uid = call.from_user.id
    eid = call.data.split("_")[1]
    bot.answer_callback_query(call.id, "🚩 Shikoyatingiz adminga yuborildi, rahmat!")
    try:
        bot.send_message(
            ADMIN_ID,
            f"🚩 YANGI SHIKOYAT\n\n🆔 E'lon №{eid} uchun shikoyat.\n👤 Shikoyatchi ID: {uid}\n"
            f"Ko'rib chiqish uchun: /elon_{eid}"
        )
    except Exception as e:
        log.warning(f"Shikoyat yuborilmadi: {e}")


# ============================================================
#  ✉️ SOTUVCHIGA YOZISH (xaridor <-> sotuvchi xabar almashinuvi)
# ============================================================
@bot.callback_query_handler(func=lambda call: call.data.startswith("msgowner_"))
def sotuvchiga_yozish_start(call):
    uid = call.from_user.id
    eid = call.data.replace("msgowner_", "")
    elonlar = load_elonlar()
    elon = elonlar.get(eid)
    bot.answer_callback_query(call.id)
    if not elon:
        bot.send_message(uid, "❌ E'lon topilmadi.")
        return
    user_state[uid] = "sotuvchiga_xabar_kutish"
    user_data_temp.setdefault(uid, {})
    user_data_temp[uid]["msgowner_eid"] = eid
    bot.send_message(uid, f"✉️ №{eid} e'lon egasiga yubormoqchi bo'lgan xabaringizni yozing:")


@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == "sotuvchiga_xabar_kutish")
def sotuvchiga_xabar_yuborish(message):
    uid = message.from_user.id
    eid = user_data_temp.get(uid, {}).pop("msgowner_eid", None)
    user_state.pop(uid, None)
    if not eid:
        return
    elonlar = load_elonlar()
    elon = elonlar.get(eid)
    if not elon:
        bot.send_message(uid, "❌ E'lon topilmadi.", reply_markup=get_main_keyboard(uid))
        return

    egasi_id = elon.get("user_id")
    xaridor = get_user(uid)
    matn = (
        f"✉️ **Yangi xabar (e'lon №{eid} bo'yicha)**\n\n"
        f"👤 Kimdan: {md_escape(xaridor.get('name','?'))} ({md_escape(xaridor.get('tg_username','?'))})\n"
        f"🆔 `{uid}`\n\n"
        f"💬 {md_escape(message.text)}"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("↩️ Javob berish", callback_data=f"ownerreply_{uid}_{eid}"))

    try:
        xavfsiz_yuborish(egasi_id, matn, reply_markup=markup)
        # Sotuvchi keyinroq ko'rishi uchun o'z profilida ham saqlaymiz
        egasi = get_user(egasi_id)
        egasi.setdefault("sotuvchi_xabarlar", []).append({
            "sana": datetime.now().strftime("%d.%m.%Y %H:%M"), "eid": eid,
            "kimdan": xaridor.get("name", "?"), "matn": message.text
        })
        update_user(egasi_id, egasi)
        bot.send_message(uid, "✅ Xabaringiz sotuvchiga yuborildi!", reply_markup=get_main_keyboard(uid))
    except Exception as e:
        log.warning(f"Sotuvchiga xabar yuborilmadi: {e}")
        bot.send_message(uid, "❌ Xabar yuborilmadi (foydalanuvchi botni bloklagan bo'lishi mumkin).",
                         reply_markup=get_main_keyboard(uid))


@bot.callback_query_handler(func=lambda call: call.data.startswith("ownerreply_"))
def sotuvchi_javob_start(call):
    uid = call.from_user.id
    _, xaridor_uid, eid = call.data.split("_")
    bot.answer_callback_query(call.id)
    user_state[uid] = "ownerreply_kutish"
    user_data_temp.setdefault(uid, {})
    user_data_temp[uid]["ownerreply_target"] = xaridor_uid
    user_data_temp[uid]["ownerreply_eid"] = eid
    bot.send_message(uid, "↩️ Xaridorga javobingizni yozing:")


@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == "ownerreply_kutish")
def sotuvchi_javob_yuborish(message):
    uid = message.from_user.id
    target = user_data_temp.get(uid, {}).pop("ownerreply_target", None)
    eid = user_data_temp.get(uid, {}).pop("ownerreply_eid", "?")
    user_state.pop(uid, None)
    if not target:
        return
    try:
        bot.send_message(int(target), f"↩️ **Sotuvchi javobi (e'lon №{eid}):**\n\n{message.text}", parse_mode="Markdown")
        bot.send_message(uid, "✅ Javobingiz yuborildi.", reply_markup=get_main_keyboard(uid))
    except Exception as e:
        log.warning(f"Javob yuborilmadi: {e}")
        bot.send_message(uid, "❌ Yuborilmadi (foydalanuvchi botni bloklagan bo'lishi mumkin).",
                         reply_markup=get_main_keyboard(uid))


@bot.message_handler(func=lambda m: m.text.startswith("/elon_") and m.from_user.id == ADMIN_ID)
def admin_elonni_kor(message):
    eid = message.text.replace("/elon_", "").strip()
    elonlar = load_elonlar()
    elon = elonlar.get(eid)
    if not elon:
        bot.reply_to(message, "❌ Bunday e'lon topilmadi.")
        return
    matn = elon_matni(eid, elon, tolik=True)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🗑 E'lonni o'chirish", callback_data=f"admindel_{eid}"))
    if elon.get("photo"):
        xavfsiz_photo_yuborish(message.chat.id, elon["photo"], matn, reply_markup=markup)
    else:
        xavfsiz_yuborish(message.chat.id, matn, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("admindel_") and call.from_user.id == ADMIN_ID)
def admin_elonni_ochir(call):
    eid = call.data.split("_")[1]
    bot.answer_callback_query(call.id)
    if elon_ochirish(eid):
        bot.send_message(ADMIN_ID, f"✅ E'lon №{eid} o'chirildi.")
    else:
        bot.send_message(ADMIN_ID, "❌ Topilmadi.")


# ============================================================
#  👤 MENING E'LONLARIM
# ============================================================
@bot.message_handler(func=lambda m: m.text == "👤 Mening e'lonlarim")
def mening_elonlarim(message):
    if check_ban(message): return
    uid = message.from_user.id
    user = get_user(uid)
    elonlar = load_elonlar()
    mening = [eid for eid in user.get("elonlar", []) if eid in elonlar]

    if not mening:
        bot.send_message(uid, "👤 Sizda hali e'lonlar yo'q. '📢 E'lon berish' orqali birinchi e'loningizni joylang!")
        return

    for eid in mening:
        elon = elonlar[eid]
        holat = "✅ Faol" if elon_faolmi(elon) else "⏳ Muddati tugagan / o'chirilgan"
        matn = elon_matni(eid, elon, tolik=False) + f"\n📌 Holati: {holat}"
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✏️ Narxni tahrirlash", callback_data=f"menedit_{eid}"),
            types.InlineKeyboardButton("🗑 O'chirish", callback_data=f"mendel_{eid}"),
        )
        xavfsiz_yuborish(uid, matn, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("menedit_"))
def elonimni_tahrirlash_start(call):
    uid = call.from_user.id
    eid = call.data.split("_")[1]
    user = get_user(uid)
    bot.answer_callback_query(call.id)
    if eid not in user.get("elonlar", []):
        bot.send_message(uid, "❌ Bu sizning e'loningiz emas.")
        return
    user_state[uid] = "elon_narx_tahrirlash"
    user_data_temp.setdefault(uid, {})
    user_data_temp[uid]["tahrir_eid"] = eid
    bot.send_message(uid, "💰 Yangi narxni kiriting:")


@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == "elon_narx_tahrirlash")
def _narxdan_son_ajratish(narx_matni):
    """'500 y.u.e' yoki '3 000 000 so'm' kabi matndan raqamli qiymatni ajratib olishga urinadi."""
    raqamlar = "".join(ch if ch.isdigit() else " " for ch in str(narx_matni)).split()
    if not raqamlar:
        return None
    try:
        return int("".join(raqamlar))
    except ValueError:
        return None


def elonimni_tahrirlash_yakun(message):
    uid = message.from_user.id
    eid = user_data_temp.get(uid, {}).get("tahrir_eid")
    user_state.pop(uid, None)
    user_data_temp.pop(uid, None)

    if not eid:
        bot.send_message(uid, "⚠️ Xatolik yuz berdi, qaytadan urinib ko'ring.", reply_markup=get_main_keyboard(uid))
        return

    elonlar = load_elonlar()
    elon = elonlar.get(eid)
    if not elon:
        bot.send_message(uid, "❌ E'lon topilmadi.", reply_markup=get_main_keyboard(uid))
        return

    eski_narx = elon.get("narx")
    elon["narx"] = message.text
    elonlar[eid] = elon
    save_elonlar(elonlar)

    bot.send_message(uid, f"✅ Narx yangilandi: {message.text}", reply_markup=get_main_keyboard(uid))

    # 🎯 Aqlli narx tushishi bildirishnomasi — bu e'lonni sevimlilarga saqlaganlarga xabar beramiz
    eski_son = _narxdan_son_ajratish(eski_narx)
    yangi_son = _narxdan_son_ajratish(message.text)
    if eski_son is not None and yangi_son is not None and yangi_son < eski_son:
        db = load_db()
        for uid_str, u in db.items():
            if eid in u.get("sevimlilar", []) and u.get("bildirishnoma", True):
                try:
                    bot.send_message(
                        int(uid_str),
                        f"🎯 **Narx tushdi!**\n\nSiz kuzatayotgan «{md_escape(elon.get('sarlavha',''))}» "
                        f"e'loni narxi {md_escape(eski_narx)} dan {md_escape(message.text)} ga tushdi!",
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    log.warning(f"Narx tushishi xabari yuborilmadi ({uid_str}): {e}")

    if elon.get("kanal_msg_id"):
        try:
            yangi_matn = elon_matni(eid, elon, tolik=True) + f"\n\n🤖 @{bot.get_me().username} orqali joylandi."
            if elon.get("photo"):
                bot.edit_message_caption(yangi_matn, KANAL_ID, elon["kanal_msg_id"], parse_mode="Markdown")
            else:
                bot.edit_message_text(yangi_matn, KANAL_ID, elon["kanal_msg_id"], parse_mode="Markdown")
        except Exception as e:
            log.error(f"Kanal postini yangilashda xatolik: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("mendel_"))
def elonimni_ochir(call):
    uid = call.from_user.id
    eid = call.data.split("_")[1]
    user = get_user(uid)
    if eid not in user.get("elonlar", []):
        bot.answer_callback_query(call.id, "❌ Bu sizning e'loningiz emas.")
        return
    elon_ochirish(eid)
    bot.answer_callback_query(call.id, "🗑 E'lon o'chirildi.")
    try:
        bot.edit_message_text("🗑 Ushbu e'lon o'chirildi.", call.message.chat.id, call.message.message_id)
    except Exception:
        try:
            bot.edit_message_caption("🗑 Ushbu e'lon o'chirildi.", call.message.chat.id, call.message.message_id)
        except Exception:
            pass


# ============================================================
#  ❤️ SEVIMLILARIM
# ============================================================
@bot.message_handler(func=lambda m: m.text == "❤️ Sevimlilarim")
def sevimlilarim(message):
    if check_ban(message): return
    uid = message.from_user.id
    user = get_user(uid)
    elonlar = load_elonlar()
    mavjud = [eid for eid in user.get("sevimlilar", []) if eid in elonlar]

    if not mavjud:
        bot.send_message(uid, "❤️ Sevimlilar ro'yxati bo'sh. E'lonlarni ko'rish paytida ❤️ tugmasini bosing.")
        return

    for eid in mavjud:
        elon = elonlar[eid]
        matn = elon_matni(eid, elon, tolik=True)
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💔 Ro'yxatdan chiqarish", callback_data=f"favdel_{eid}"))
        if elon.get("photo"):
            xavfsiz_photo_yuborish(uid, elon["photo"], matn, reply_markup=markup)
        else:
            xavfsiz_yuborish(uid, matn, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("favdel_"))
def sevimlidan_ochir(call):
    uid = call.from_user.id
    eid = call.data.split("_")[1]
    user = get_user(uid)
    if eid in user.get("sevimlilar", []):
        user["sevimlilar"].remove(eid)
        update_user(uid, user)
    bot.answer_callback_query(call.id, "💔 Sevimlilardan olib tashlandi.")
    try:
        bot.edit_message_text("💔 Sevimlilardan olib tashlandi.", call.message.chat.id, call.message.message_id)
    except Exception:
        try:
            bot.edit_message_caption("💔 Sevimlilardan olib tashlandi.", call.message.chat.id, call.message.message_id)
        except Exception:
            pass


# ============================================================
#  📝 IMTIXONGA ARIZA BERISH
# ============================================================
@bot.message_handler(func=lambda m: m.text == "📝 Imtixonga ariza berish")
def imtixon_ariza_start(message):
    if check_ban(message): return
    uid = message.from_user.id
    user_data_temp.setdefault(uid, {})
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [types.InlineKeyboardButton(nom, callback_data=f"examfan_{kod}") for nom, kod in FANLAR]
    markup.add(*buttons)
    bot.send_message(uid, "🎓 Qaysi fandan imtixon topshirmoqchisiz?", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("examfan_"))
def imtixon_fan_tanlandi(call):
    uid = call.from_user.id
    kod = call.data.replace("examfan_", "")
    nom = next((n for n, k in FANLAR if k == kod), kod)
    bot.answer_callback_query(call.id)
    user_data_temp.setdefault(uid, {})
    user_data_temp[uid]["exam_fan"] = nom
    user_state[uid] = "exam_ism"

    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass

    user = get_user(uid)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    if user.get("name"):
        markup.add(types.KeyboardButton(user["name"]))
    bot.send_message(uid, "👤 To'liq ismingizni (F.I.Sh) kiriting:", reply_markup=markup)


@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == "exam_ism")
def imtixon_ism_qabul(message):
    uid = message.from_user.id
    user_data_temp[uid]["exam_ism"] = message.text
    user_state[uid] = "exam_pasport"
    bot.send_message(
        uid,
        "🆔 Pasport yoki ID-karta seriya va raqamingizni kiriting:\n"
        "_(Masalan: AD1234567 — bu faqat ruxsatnomangizda ko'rsatish uchun, botimiz ichida saqlanadi)_",
        parse_mode="Markdown"
    )


@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == "exam_pasport")
def imtixon_pasport_qabul(message):
    uid = message.from_user.id
    user_data_temp[uid]["exam_pasport"] = message.text.strip()
    user_state[uid] = "exam_tasdiqlash"

    user = get_user(uid)
    data = user_data_temp[uid]
    matn = (
        f"🧐 **Arizangizni tekshiring:**\n\n"
        f"🎓 **Fan:** {data['exam_fan']}\n"
        f"👤 **F.I.Sh:** {md_escape(data['exam_ism'])}\n"
        f"🆔 **Pasport/ID:** {md_escape(data['exam_pasport'])}\n"
        f"📞 **Telefon:** {user['phone'] if user['phone'] else 'Kiritilmagan'}\n\n"
        f"Ma'lumotlar to'g'rimi? Tasdiqlasangiz adminga yuboriladi."
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Tasdiqlash", callback_data="exam_confirm"),
        types.InlineKeyboardButton("❌ Bekor qilish", callback_data="exam_cancel"),
    )
    xavfsiz_yuborish(uid, matn, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data in ["exam_confirm", "exam_cancel"])
def imtixon_yakuniy_qaror(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass

    if call.data == "exam_cancel":
        user_data_temp.pop(uid, None)
        user_state.pop(uid, None)
        bot.send_message(uid, "❌ Ariza bekor qilindi.", reply_markup=get_main_keyboard(uid))
        return

    data = user_data_temp.get(uid)
    if not data:
        bot.send_message(uid, "⚠️ Xatolik! Ma'lumotlar topilmadi.", reply_markup=get_main_keyboard(uid))
        return

    user = get_user(uid)
    ariza_id = yangi_ariza_id()
    ariza_obj = {
        "user_id": uid,
        "fan": data["exam_fan"],
        "ism": data["exam_ism"],
        "pasport": data.get("exam_pasport", ""),
        "telefon": user.get("phone", ""),
        "holat": "kutilmoqda",
        "ball": None,
        "sana": datetime.now().strftime("%d.%m.%Y %H:%M"),
    }
    ariza_qoshish(ariza_id, ariza_obj)

    admin_matn = (
        f"🔔 YANGI IMTIXON ARIZASI\n\n"
        f"🆔 Ariza raqami: {ariza_id}\n"
        f"🎓 Fan: {data['exam_fan']}\n"
        f"👤 F.I.Sh: {data['exam_ism']}\n"
        f"📞 Telefon: {user.get('phone','')}\n"
        f"🆔 Foydalanuvchi ID: {uid}"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Qabul qilish", callback_data=f"examaccept_{ariza_id}"),
        types.InlineKeyboardButton("❌ Rad etish", callback_data=f"examreject_{ariza_id}"),
    )
    try:
        bot.send_message(ADMIN_ID, admin_matn, reply_markup=markup)
    except Exception as e:
        log.error(f"Adminga imtixon arizasi yuborishda xatolik: {e}")

    bot.send_message(
        uid,
        f"✅ Arizangiz muvaffaqiyatli yuborildi!\n\n🆔 Sizning ariza raqamingiz: **{ariza_id}**\n"
        f"_(Bu raqamni saqlab qo'ying — natija chiqqach shu raqam orqali ballingizni bilib olasiz)_",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard(uid)
    )

    user_data_temp.pop(uid, None)
    user_state.pop(uid, None)


@bot.callback_query_handler(func=lambda call: call.data.startswith("examaccept_") or call.data.startswith("examreject_"))
def imtixon_admin_qaror(call):
    if call.from_user.id != ADMIN_ID: return
    bot.answer_callback_query(call.id)
    if call.data.startswith("examaccept_"):
        ariza_id = call.data.replace("examaccept_", "")
        holat_yangi = "qabul qilindi"
        xabar = f"🎉 Sizning {ariza_id} raqamli imtixon arizangiz qabul qilindi! Natija e'lon qilinganda shu raqam orqali bilib olasiz."
    else:
        ariza_id = call.data.replace("examreject_", "")
        holat_yangi = "rad etildi"
        xabar = f"❌ Afsuski, sizning {ariza_id} raqamli imtixon arizangiz rad etildi."

    arizalar = load_imtixon()
    ariza = arizalar.get(ariza_id)
    if not ariza:
        bot.send_message(ADMIN_ID, "❌ Ariza topilmadi.")
        return
    ariza["holat"] = holat_yangi
    arizalar[ariza_id] = ariza
    save_imtixon(arizalar)

    try:
        bot.edit_message_text(f"{call.message.text}\n\n📌 Holat: {holat_yangi.upper()}", ADMIN_ID, call.message.message_id)
    except Exception:
        pass
    try:
        bot.send_message(ariza["user_id"], xabar)
        if holat_yangi == "qabul qilindi":
            pdf_yoli = ruxsatnoma_pdf_yarat(ariza_id, ariza)
            with open(pdf_yoli, "rb") as f:
                bot.send_document(ariza["user_id"], f, caption="📋 Sizning abituriyent ruxsatnomangiz.")
    except Exception as e:
        log.error(f"Ruxsatnoma PDF yuborishda xatolik: {e}")


# ---- ADMIN: BALL QO'YISH ----
@bot.message_handler(commands=['ball'])
def admin_ball_qoyish(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        qismlar = message.text.split()
        ariza_id = qismlar[1]
        ball = qismlar[2]
        arizalar = load_imtixon()
        if ariza_id not in arizalar:
            bot.reply_to(message, "❌ Bunday ariza raqami topilmadi.")
            return
        arizalar[ariza_id]["ball"] = ball
        save_imtixon(arizalar)
        bot.reply_to(message, f"✅ {ariza_id} uchun ball saqlandi: {ball}")
        try:
            bot.send_message(
                arizalar[ariza_id]["user_id"],
                f"📢 Natijangiz e'lon qilindi!\n\n🆔 Ariza: {ariza_id}\n🎓 Fan: {arizalar[ariza_id]['fan']}\n🏆 Ball: {ball}"
            )
            pdf_yoli = natija_pdf_yarat(ariza_id, arizalar[ariza_id])
            with open(pdf_yoli, "rb") as f:
                bot.send_document(arizalar[ariza_id]["user_id"], f, caption="🏆 Rasmiy natija hujjatingiz.")
        except Exception as e:
            log.warning(f"Natija yuborilmadi: {e}")
    except (IndexError, ValueError):
        bot.reply_to(message, "⚠️ To'g'ri format: `/ball ARIZA_ID BALL` (masalan: /ball EX1 87)", parse_mode="Markdown")


# ============================================================
#  🆔 CHAT ID BILISH
# ============================================================
@bot.message_handler(func=lambda m: m.text == "🆔 Chat ID bilish")
def chat_id_bilish(message):
    if check_ban(message): return
    uid = message.from_user.id
    uname = f"@{message.from_user.username}" if message.from_user.username else "Kiritilmagan"
    matn = (
        f"🆔 **Sizning ma'lumotlaringiz:**\n\n"
        f"👤 Foydalanuvchi ID: `{uid}`\n"
        f"🔗 Username: {uname}\n"
        f"💬 Ushbu chat ID: `{message.chat.id}`\n\n"
        f"ℹ️ Botni biror guruh yoki kanalga qo'shib, u yerdan istalgan xabarni "
        f"shu botga **forward** qiling — o'sha guruh/kanalning ID raqamini ham chiqarib beraman."
    )
    bot.send_message(uid, matn, parse_mode="Markdown")


@bot.message_handler(func=lambda m: m.forward_from_chat is not None)
def forward_chat_id(message):
    fc = message.forward_from_chat
    matn = (
        f"📡 **Manba chat ma'lumotlari:**\n\n"
        f"📛 Nomi: {fc.title if fc.title else '-'}\n"
        f"🏷 Turi: {fc.type}\n"
        f"🆔 ID: `{fc.id}`\n\n"
        f"_(Buni KANAL_ID sifatida botingiz sozlamalariga qo'yishingiz mumkin)_"
    )
    bot.send_message(message.chat.id, matn, parse_mode="Markdown")


@bot.message_handler(func=lambda m: m.forward_from is not None)
def forward_user_id(message):
    fu = message.forward_from
    username_qatori = f"🔗 Username: @{fu.username}" if fu.username else "🔗 Username: Kiritilmagan"
    matn = (
        f"👤 **Manba foydalanuvchi ma'lumotlari:**\n\n"
        f"📛 Ism: {fu.first_name or ''} {fu.last_name or ''}\n"
        f"{username_qatori}\n"
        f"🆔 ID: `{fu.id}`"
    )
    bot.send_message(message.chat.id, matn, parse_mode="Markdown")


# ============================================================
#  🎁 DO'ST TAKLIF QILISH (REFERAL TIZIMI)
# ============================================================
@bot.message_handler(func=lambda m: m.text == "🎁 Do'st taklif qilish")
def dost_taklif(message):
    if check_ban(message): return
    uid = message.from_user.id
    user = get_user(uid)
    bot_username = bot.get_me().username
    havola = f"https://t.me/{bot_username}?start=ref_{uid}"
    soni = user.get("referral_count", 0)
    qolgan = 5 - (soni % 5) if not user.get("premium") else 0

    matn = (
        f"🎁 **Do'stlaringizni taklif qiling va Premium 💎 yutib oling!**\n\n"
        f"🔗 Sizning shaxsiy taklif havolangiz:\n{havola}\n\n"
        f"👥 Hozirgacha taklif qilganlaringiz: {soni} ta\n"
    )
    if user.get("premium"):
        matn += "\n✅ Siz allaqachon Premium 💎 maqomiga egasiz!"
    else:
        matn += f"⏳ Yana {qolgan} ta do'stingiz qo'shilsa — Premium 💎 avtomatik faollashadi!"

    bot.send_message(uid, matn, parse_mode="Markdown")


# ============================================================
#  🚖 TAKSI CHAQIRISH (yo'lovchi tomoni)
# ============================================================
@bot.message_handler(func=lambda m: m.text == "🚖 Taksi chaqirish")
def taksi_chaqirish_start(message):
    if check_ban(message): return
    uid = message.from_user.id
    user_state[uid] = "taksi_qayerdan"
    user_data_temp[uid] = {}
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton("📍 Qayerdaligimni yuborish", request_location=True))
    bot.send_message(uid, "📍 Qayerdan olib ketishini xohlaysiz? Lokatsiyangizni yuboring:", reply_markup=markup)


@bot.message_handler(content_types=["location"], func=lambda m: user_state.get(m.from_user.id) == "taksi_qayerdan")
def taksi_qayerdan_qabul(message):
    uid = message.from_user.id
    user_data_temp.setdefault(uid, {})
    user_data_temp[uid]["pickup_lat"] = message.location.latitude
    user_data_temp[uid]["pickup_lon"] = message.location.longitude
    user_state[uid] = "taksi_qayerga"

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton("📍 Manzilni lokatsiya orqali yuborish", request_location=True))
    bot.send_message(
        uid,
        "🎯 Endi qayerga borishni xohlaysiz?\n"
        "_(Lokatsiya yuboring, yoki manzilni oddiy matn ko'rinishida yozing)_",
        parse_mode="Markdown",
        reply_markup=markup
    )


@bot.message_handler(content_types=["location"], func=lambda m: user_state.get(m.from_user.id) == "taksi_qayerga")
def taksi_qayerga_lokatsiya(message):
    uid = message.from_user.id
    data = user_data_temp.setdefault(uid, {})
    data["dest_lat"] = message.location.latitude
    data["dest_lon"] = message.location.longitude
    km = masofa_km(data["pickup_lat"], data["pickup_lon"], data["dest_lat"], data["dest_lon"])
    narx = narxni_hisobla(km)
    data["masofa_km"] = round(km, 1)
    data["narx"] = narx
    taksi_buyurtma_tasdiqlash(uid, matn_qoshimcha=f"📏 Taxminiy masofa: {round(km,1)} km")


@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == "taksi_qayerga")
def taksi_qayerga_matn(message):
    uid = message.from_user.id
    data = user_data_temp.setdefault(uid, {})
    data["dest_matn"] = message.text
    data["narx"] = None
    taksi_buyurtma_tasdiqlash(uid, matn_qoshimcha="ℹ️ Aniq manzil kiritilmagani uchun narx haydovchi bilan kelishiladi.")


def taksi_buyurtma_tasdiqlash(uid, matn_qoshimcha=""):
    user_state[uid] = "taksi_tasdiqlash"
    data = user_data_temp[uid]
    narx_matni = som_format(data["narx"]) if data.get("narx") else "Kelishiladi"

    matn = (
        f"🚖 **Buyurtmangizni tekshiring:**\n\n"
        f"📍 Qayerdan: [Xaritada ko'rish](https://maps.google.com/?q={data['pickup_lat']},{data['pickup_lon']})\n"
    )
    if data.get("dest_lat"):
        matn += f"🎯 Qayerga: [Xaritada ko'rish](https://maps.google.com/?q={data['dest_lat']},{data['dest_lon']})\n"
    else:
        matn += f"🎯 Qayerga: {md_escape(data.get('dest_matn',''))}\n"
    matn += f"\n{matn_qoshimcha}\n💰 **Taxminiy narx: {narx_matni}**\n\nBuyurtma berishni tasdiqlaysizmi?"

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Buyurtma berish", callback_data="taksi_tasdiqla"),
        types.InlineKeyboardButton("❌ Bekor qilish", callback_data="taksi_bekor"),
    )
    xavfsiz_yuborish(uid, matn, reply_markup=markup, disable_web_page_preview=True)


@bot.callback_query_handler(func=lambda call: call.data in ["taksi_tasdiqla", "taksi_bekor"])
def taksi_yakuniy_qaror(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass

    user_state.pop(uid, None)

    if call.data == "taksi_bekor":
        user_data_temp.pop(uid, None)
        bot.send_message(uid, "❌ Buyurtma bekor qilindi.", reply_markup=get_main_keyboard(uid))
        return

    data = user_data_temp.pop(uid, None)
    if not data:
        bot.send_message(uid, "⚠️ Xatolik yuz berdi.", reply_markup=get_main_keyboard(uid))
        return

    user = get_user(uid)
    tid = yangi_taksi_id()
    buyurtma = {
        "yolovchi_id": uid,
        "yolovchi_ism": user["name"],
        "yolovchi_telefon": user.get("phone", ""),
        "pickup_lat": data["pickup_lat"],
        "pickup_lon": data["pickup_lon"],
        "dest_lat": data.get("dest_lat"),
        "dest_lon": data.get("dest_lon"),
        "dest_matn": data.get("dest_matn", ""),
        "masofa_km": data.get("masofa_km"),
        "narx": data.get("narx"),
        "holat": "kutilmoqda",
        "haydovchi_id": None,
        "rated": False,
        "created_at": datetime.now().strftime("%d.%m.%Y %H:%M"),
    }
    taksilar = load_taksi()
    taksilar[tid] = buyurtma
    save_taksi(taksilar)

    cancel_markup = types.InlineKeyboardMarkup()
    cancel_markup.add(types.InlineKeyboardButton("❌ Buyurtmani bekor qilish", callback_data=f"taksicancel_{tid}"))
    bot.send_message(
        uid,
        f"✅ Buyurtmangiz qabul qilindi! 🆔 №{tid}\n⏳ Yaqin atrofdagi haydovchilar qidirilmoqda...",
        reply_markup=get_main_keyboard(uid)
    )
    bot.send_message(uid, "Haydovchi topilguncha buyurtmani bekor qilishingiz mumkin:", reply_markup=cancel_markup)

    haydovchilar = load_haydovchilar()
    narx_matni = som_format(buyurtma["narx"]) if buyurtma["narx"] else "Kelishiladi"
    dest_matni = (f"[Xaritada ko'rish](https://maps.google.com/?q={buyurtma['dest_lat']},{buyurtma['dest_lon']})"
                 if buyurtma.get("dest_lat") else md_escape(buyurtma.get("dest_matn", "Kiritilmagan")))

    nomzodlar = []
    for hid, h in haydovchilar.items():
        if h.get("holat") == "tasdiqlangan" and h.get("online"):
            masofa = None
            if h.get("last_lat") is not None and h.get("last_lon") is not None:
                masofa = masofa_km(buyurtma["pickup_lat"], buyurtma["pickup_lon"], h["last_lat"], h["last_lon"])
            nomzodlar.append((hid, h, masofa))

    nomzodlar.sort(key=lambda x: (x[2] is None, x[2] if x[2] is not None else 0))

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Qabul qilish", callback_data=f"taksiaccept_{tid}"))

    yuborildi_soni = 0
    for hid, h, masofa in nomzodlar:
        masofa_matni = f"\n📏 Sizdan taxminan: {round(masofa, 1)} km" if masofa is not None else ""
        haydovchi_matni = (
            f"🚖 **YANGI BUYURTMA №{tid}**\n\n"
            f"📍 Qayerdan: [Xaritada ko'rish](https://maps.google.com/?q={buyurtma['pickup_lat']},{buyurtma['pickup_lon']})\n"
            f"🎯 Qayerga: {dest_matni}\n"
            f"💰 Narx: {narx_matni}"
            f"{masofa_matni}\n"
            f"👤 Yo'lovchi: {md_escape(user['name'])}"
        )
        try:
            xavfsiz_yuborish(int(hid), haydovchi_matni, reply_markup=markup, disable_web_page_preview=True)
            yuborildi_soni += 1
        except Exception as e:
            log.warning(f"Haydovchiga yuborilmadi ({hid}): {e}")

    if yuborildi_soni == 0:
        bot.send_message(
            uid,
            "😕 Afsuski, hozircha onlayn haydovchilar yo'q. Birozdan so'ng qayta urinib ko'ring yoki buyurtmani bekor qiling."
        )
        try:
            bot.send_message(ADMIN_ID, f"⚠️ №{tid} buyurtma uchun onlayn haydovchi topilmadi.")
        except Exception:
            pass


@bot.callback_query_handler(func=lambda call: call.data.startswith("taksicancel_"))
def taksi_yolovchi_bekor_qildi(call):
    uid = call.from_user.id
    tid = call.data.replace("taksicancel_", "")
    bot.answer_callback_query(call.id)

    taksilar = load_taksi()
    buyurtma = taksilar.get(tid)
    if not buyurtma or buyurtma["yolovchi_id"] != uid:
        bot.send_message(uid, "❌ Bu buyurtma sizga tegishli emas.")
        return
    if buyurtma["holat"] != "kutilmoqda":
        bot.send_message(uid, "ℹ️ Bu buyurtmani endi bekor qilib bo'lmaydi — haydovchi allaqachon qabul qilgan yoki safar yakunlangan.")
        return

    buyurtma["holat"] = "bekor_qilindi"
    taksilar[tid] = buyurtma
    save_taksi(taksilar)

    try:
        bot.edit_message_text(f"❌ Buyurtma №{tid} bekor qilindi.", call.message.chat.id, call.message.message_id)
    except Exception:
        try:
            bot.edit_message_text(f"❌ Buyurtma №{tid} bekor qilindi.", uid, call.message.message_id)
        except Exception:
            bot.send_message(uid, f"❌ Buyurtma №{tid} bekor qilindi.")


@bot.callback_query_handler(func=lambda call: call.data.startswith("taksiaccept_"))
def taksi_haydovchi_qabul_qildi(call):
    hid = call.from_user.id
    tid = call.data.replace("taksiaccept_", "")
    taksilar = load_taksi()
    buyurtma = taksilar.get(tid)

    if not buyurtma or buyurtma["holat"] != "kutilmoqda":
        bot.answer_callback_query(call.id, "😕 Bu buyurtma allaqachon band qilingan yoki bekor qilingan.")
        try:
            bot.edit_message_text("⛔ Bu buyurtma allaqachon band qilingan yoki bekor qilingan.", call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        return

    haydovchilar = load_haydovchilar()
    haydovchi = haydovchilar.get(str(hid))
    if not haydovchi or haydovchi.get("holat") != "tasdiqlangan":
        bot.answer_callback_query(call.id, "❌ Siz tasdiqlangan haydovchi emassiz.")
        return

    buyurtma["holat"] = "qabul_qilindi"
    buyurtma["haydovchi_id"] = hid
    taksilar[tid] = buyurtma
    save_taksi(taksilar)

    bot.answer_callback_query(call.id, "✅ Buyurtma sizga tayinlandi!")
    try:
        bot.edit_message_text(f"{call.message.text}\n\n✅ SIZ QABUL QILDINGIZ", call.message.chat.id, call.message.message_id)
    except Exception:
        pass

    yakunlash_markup = types.InlineKeyboardMarkup()
    yakunlash_markup.add(types.InlineKeyboardButton("🏁 Safarni yakunlash", callback_data=f"taksitugat_{tid}"))
    bot.send_message(
        hid,
        f"📞 Yo'lovchi telefoni: {buyurtma.get('yolovchi_telefon','Kiritilmagan')}\n"
        f"👤 Ismi: {buyurtma.get('yolovchi_ism','')}\n\nSafar tugagach quyidagi tugmani bosing:",
        reply_markup=yakunlash_markup
    )

    try:
        bot.send_message(
            buyurtma["yolovchi_id"],
            f"🎉 Haydovchi topildi!\n\n👤 {haydovchi.get('ism','')}\n🚗 {haydovchi.get('avto_model','')} "
            f"({haydovchi.get('avto_raqam','')})\n📞 {haydovchi.get('telefon','')}\n"
            f"{haydovchi_reyting_matni(haydovchi)}\n\nHaydovchi tez orada yetib boradi!"
        )
    except Exception as e:
        log.warning(f"Yo'lovchiga xabar yuborilmadi: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("taksitugat_"))
def taksi_safar_yakunlash(call):
    hid = call.from_user.id
    tid = call.data.replace("taksitugat_", "")
    taksilar = load_taksi()
    buyurtma = taksilar.get(tid)
    bot.answer_callback_query(call.id)

    if not buyurtma or buyurtma.get("haydovchi_id") != hid:
        bot.send_message(hid, "❌ Bu buyurtma sizga tegishli emas.")
        return

    buyurtma["holat"] = "yakunlandi"
    taksilar[tid] = buyurtma
    save_taksi(taksilar)

    haydovchilar = load_haydovchilar()
    h = haydovchilar.get(str(hid), {})
    h["daromad"] = h.get("daromad", 0) + (buyurtma.get("narx") or 0)
    h["safar_soni"] = h.get("safar_soni", 0) + 1
    haydovchilar[str(hid)] = h
    save_haydovchilar(haydovchilar)

    # 🎁 Avtomatik cashback: safar narxining 1% yo'lovchi hamyoniga qaytadi
    if buyurtma.get("narx"):
        cashback_summa = round(buyurtma["narx"] * 0.01 / 500) * 500
        if cashback_summa > 0:
            yolovchi = get_user(buyurtma["yolovchi_id"])
            yolovchi["balance"] = yolovchi.get("balance", 0) + cashback_summa
            yolovchi.setdefault("balance_tarix", []).append({
                "sana": datetime.now().strftime("%d.%m.%Y %H:%M"), "miqdor": cashback_summa,
                "izoh": f"Cashback (safar №{tid})"
            })
            update_user(buyurtma["yolovchi_id"], yolovchi)

    # 📊 Shaxsiy statistika uchun: bosib o'tilgan masofani hisoblab boramiz
    if buyurtma.get("masofa_km"):
        yolovchi2 = get_user(buyurtma["yolovchi_id"])
        yolovchi2["taksi_km_jami"] = yolovchi2.get("taksi_km_jami", 0) + buyurtma["masofa_km"]
        update_user(buyurtma["yolovchi_id"], yolovchi2)

    bot.send_message(hid, f"🏁 Safar №{tid} yakunlandi. Rahmat!")
    try:
        reyting_markup = types.InlineKeyboardMarkup(row_width=5)
        reyting_markup.add(*[
            types.InlineKeyboardButton(f"{i}⭐", callback_data=f"taksirate_{tid}_{i}") for i in range(1, 6)
        ])
        bot.send_message(
            buyurtma["yolovchi_id"],
            f"🏁 Safaringiz (№{tid}) yakunlandi. Xavfsiz yo'l tilaymiz! 🚖\n\n"
            f"Haydovchini baholab qo'ying:",
            reply_markup=reyting_markup
        )
    except Exception as e:
        log.warning(f"Baholash so'rovi yuborilmadi: {e}")


@bot.callback_query_handler(func=lambda call: call.data.startswith("taksirate_"))
def taksi_baholash(call):
    uid = call.from_user.id
    _, tid, ball = call.data.split("_")
    ball = int(ball)
    bot.answer_callback_query(call.id, f"Rahmat! Siz {ball}⭐ baho berdingiz.")

    taksilar = load_taksi()
    buyurtma = taksilar.get(tid)
    if not buyurtma or buyurtma["yolovchi_id"] != uid or buyurtma.get("rated"):
        try:
            bot.edit_message_text("ℹ️ Bu buyurtma allaqachon baholangan.", call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        return

    hid = str(buyurtma.get("haydovchi_id"))
    haydovchilar = load_haydovchilar()
    h = haydovchilar.get(hid)
    if h:
        h["rating_sum"] = h.get("rating_sum", 0) + ball
        h["rating_count"] = h.get("rating_count", 0) + 1
        haydovchilar[hid] = h
        save_haydovchilar(haydovchilar)

    buyurtma["rated"] = True
    buyurtma["baho"] = ball
    taksilar[tid] = buyurtma
    save_taksi(taksilar)

    try:
        bot.edit_message_text(f"✅ Baho qabul qilindi: {ball}⭐ Rahmat!", call.message.chat.id, call.message.message_id)
    except Exception:
        pass


# ============================================================
#  📜 BUYURTMALARIM (yo'lovchi taksi tarixi)
# ============================================================
HOLAT_BELGILAR = {
    "kutilmoqda": "⏳ Haydovchi kutilmoqda",
    "qabul_qilindi": "🚗 Haydovchi yo'lda",
    "yakunlandi": "✅ Yakunlandi",
    "bekor_qilindi": "❌ Bekor qilindi",
}


@bot.message_handler(func=lambda m: m.text == "📜 Buyurtmalarim")
def buyurtmalarim(message):
    if check_ban(message): return
    uid = message.from_user.id
    taksilar = load_taksi()
    meniki = [(tid, t) for tid, t in taksilar.items() if t.get("yolovchi_id") == uid]
    meniki.sort(key=lambda x: x[0], reverse=True)

    if not meniki:
        bot.send_message(uid, "📜 Sizda hali taksi buyurtmalari yo'q.")
        return

    for tid, t in meniki[:10]:
        narx_matni = som_format(t["narx"]) if t.get("narx") else "Kelishiladi"
        holat_matni = HOLAT_BELGILAR.get(t.get("holat"), t.get("holat", ""))
        matn = (
            f"🆔 №{tid} — {t.get('created_at','')}\n"
            f"📌 Holat: {holat_matni}\n"
            f"💰 Narx: {narx_matni}\n"
        )
        if t.get("rated"):
            matn += f"⭐ Sizning bahoyingiz: {t.get('baho')}\n"
        bot.send_message(uid, matn)


# ============================================================
#  🚕 HAYDOVCHI PANELI
# ============================================================
@bot.message_handler(func=lambda m: m.text == "🚕 Haydovchi paneli")
def haydovchi_paneli(message):
    if check_ban(message): return
    uid = message.from_user.id
    haydovchilar = load_haydovchilar()
    h = haydovchilar.get(str(uid))

    if not h:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📝 Haydovchi bo'lish uchun ariza berish", callback_data="haydovchi_ariza_start"))
        bot.send_message(uid, "🚕 Siz hali haydovchi sifatida ro'yxatdan o'tmagansiz.", reply_markup=markup)
        return

    if h["holat"] == "kutilmoqda":
        bot.send_message(uid, "⏳ Arizangiz hali admin tomonidan ko'rib chiqilmoqda.")
        return
    if h["holat"] == "rad etildi":
        bot.send_message(uid, "❌ Arizangiz rad etilgan edi. Admin bilan bog'laning: @" + ADMIN_USERNAME)
        return

    holat_belgi = "🟢 Onlayn" if h.get("online") else "🔴 Oflayn"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        "🔴 Oflayn bo'lish" if h.get("online") else "🟢 Onlayn bo'lish (lokatsiya yuboriladi)",
        callback_data="haydovchi_holat_almashtir"
    ))
    markup.add(types.InlineKeyboardButton("📍 Joylashuvni yangilash", callback_data="haydovchi_joylashuv_yangilash"))
    matn = (
        f"🚕 **Haydovchi paneli**\n\n"
        f"👤 {h.get('ism','')}\n🚗 {h.get('avto_model','')} ({h.get('avto_raqam','')})\n"
        f"📌 Holat: {holat_belgi}\n"
        f"{haydovchi_reyting_matni(h)}\n\n"
        f"📊 Jami safarlar: {h.get('safar_soni', 0)} ta\n"
        f"💰 Jami daromad: {som_format(h.get('daromad', 0))}"
    )
    xavfsiz_yuborish(uid, matn, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "haydovchi_holat_almashtir")
def haydovchi_holat_almashtir(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    haydovchilar = load_haydovchilar()
    h = haydovchilar.get(str(uid))
    if not h:
        bot.answer_callback_query(call.id, "❌ Siz haydovchi emassiz.")
        return

    if not h.get("online"):
        user_state[uid] = "haydovchi_online_lokatsiya"
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except Exception:
            pass
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(types.KeyboardButton("📍 Joylashuvni yuborish", request_location=True))
        bot.send_message(
            uid,
            "🟢 Onlayn bo'lish uchun joriy joylashuvingizni yuboring — shunda sizga eng yaqin buyurtmalar keladi:",
            reply_markup=markup
        )
        return

    h["online"] = False
    haydovchilar[str(uid)] = h
    save_haydovchilar(haydovchilar)
    try:
        bot.edit_message_text("🔴 Oflayn bo'ldingiz.", call.message.chat.id, call.message.message_id)
    except Exception:
        pass
    bot.send_message(uid, "🔴 Endi buyurtmalar kelmaydi.", reply_markup=get_main_keyboard(uid))


@bot.message_handler(content_types=["location"],
                     func=lambda m: user_state.get(m.from_user.id) == "haydovchi_online_lokatsiya")
def haydovchi_online_lokatsiya_qabul(message):
    uid = message.from_user.id
    haydovchilar = load_haydovchilar()
    h = haydovchilar.get(str(uid))
    if not h:
        bot.send_message(uid, "❌ Siz haydovchi emassiz.", reply_markup=get_main_keyboard(uid))
        user_state.pop(uid, None)
        return

    h["online"] = True
    h["last_lat"] = message.location.latitude
    h["last_lon"] = message.location.longitude
    haydovchilar[str(uid)] = h
    save_haydovchilar(haydovchilar)
    user_state.pop(uid, None)

    bot.send_message(uid, "🟢 Onlayn bo'ldingiz! Endi sizga eng yaqin buyurtmalar keladi.",
                     reply_markup=get_main_keyboard(uid))


@bot.callback_query_handler(func=lambda call: call.data == "haydovchi_joylashuv_yangilash")
def haydovchi_joylashuv_yangilash(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    haydovchilar = load_haydovchilar()
    if str(uid) not in haydovchilar:
        return
    user_state[uid] = "haydovchi_lokatsiya_yangilash"
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton("📍 Joriy joylashuvni yuborish", request_location=True))
    bot.send_message(uid, "📍 Joriy joylashuvingizni yuboring:", reply_markup=markup)


@bot.message_handler(content_types=["location"],
                     func=lambda m: user_state.get(m.from_user.id) == "haydovchi_lokatsiya_yangilash")
def haydovchi_lokatsiya_yangilash_qabul(message):
    uid = message.from_user.id
    haydovchilar = load_haydovchilar()
    h = haydovchilar.get(str(uid))
    if h:
        h["last_lat"] = message.location.latitude
        h["last_lon"] = message.location.longitude
        haydovchilar[str(uid)] = h
        save_haydovchilar(haydovchilar)
    user_state.pop(uid, None)
    bot.send_message(uid, "✅ Joylashuvingiz yangilandi.", reply_markup=get_main_keyboard(uid))


@bot.callback_query_handler(func=lambda call: call.data == "haydovchi_ariza_start")
def haydovchi_ariza_start(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    user_state[uid] = "haydovchi_avto_model"
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass
    bot.send_message(uid, "🚗 Avtomobilingiz markasi va modelini kiriting (masalan: Chevrolet Cobalt):")


@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == "haydovchi_avto_model")
def haydovchi_avto_model_qabul(message):
    uid = message.from_user.id
    user_data_temp.setdefault(uid, {})
    user_data_temp[uid]["avto_model"] = message.text
    user_state[uid] = "haydovchi_avto_raqam"
    bot.send_message(uid, "🔢 Avtomobil davlat raqamini kiriting (masalan: 01A123BC):")


@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == "haydovchi_avto_raqam")
def haydovchi_avto_raqam_qabul(message):
    uid = message.from_user.id
    user_data_temp[uid]["avto_raqam"] = message.text
    user_state[uid] = "haydovchi_litsenziya"
    bot.send_message(uid, "📋 Haydovchilik guvohnomangiz rasmini yuboring:")


@bot.message_handler(content_types=["photo"], func=lambda m: user_state.get(m.from_user.id) == "haydovchi_litsenziya")
def haydovchi_litsenziya_qabul(message):
    uid = message.from_user.id
    user_data_temp[uid]["litsenziya_file_id"] = message.photo[-1].file_id
    user_state.pop(uid, None)

    user = get_user(uid)
    data = user_data_temp.pop(uid)

    haydovchilar = load_haydovchilar()
    haydovchilar[str(uid)] = {
        "ism": user["name"],
        "telefon": user.get("phone", ""),
        "avto_model": data["avto_model"],
        "avto_raqam": data["avto_raqam"],
        "litsenziya_file_id": data["litsenziya_file_id"],
        "holat": "kutilmoqda",
        "online": False,
        "last_lat": None,
        "last_lon": None,
        "daromad": 0,
        "safar_soni": 0,
        "rating_sum": 0,
        "rating_count": 0,
    }
    save_haydovchilar(haydovchilar)

    admin_matn = (
        f"🔔 YANGI HAYDOVCHI ARIZASI\n\n"
        f"👤 {user['name']}\n📞 {user.get('phone','')}\n"
        f"🚗 {data['avto_model']} ({data['avto_raqam']})\n🆔 ID: {uid}"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"haydaccept_{uid}"),
        types.InlineKeyboardButton("❌ Rad etish", callback_data=f"haydreject_{uid}"),
    )
    try:
        bot.send_photo(ADMIN_ID, data["litsenziya_file_id"], caption=admin_matn, reply_markup=markup)
    except Exception as e:
        log.error(f"Adminga haydovchi arizasi yuborishda xatolik: {e}")

    bot.send_message(uid, "✅ Arizangiz adminga yuborildi. Tasdiqlangach xabar beramiz!",
                     reply_markup=get_main_keyboard(uid))


@bot.callback_query_handler(func=lambda call: call.data.startswith("haydaccept_") or call.data.startswith("haydreject_"))
def haydovchi_admin_qaror(call):
    if call.from_user.id != ADMIN_ID: return
    bot.answer_callback_query(call.id)

    if call.data.startswith("haydaccept_"):
        hid = call.data.replace("haydaccept_", "")
        holat_yangi = "tasdiqlangan"
        xabar = "🎉 Tabriklaymiz! Siz haydovchi sifatida tasdiqlandingiz. Endi '🚕 Haydovchi paneli' orqali onlayn bo'lib buyurtma qabul qilishingiz mumkin!"
    else:
        hid = call.data.replace("haydreject_", "")
        holat_yangi = "rad etildi"
        xabar = "❌ Afsuski, haydovchilik arizangiz rad etildi."

    haydovchilar = load_haydovchilar()
    if hid not in haydovchilar:
        bot.send_message(ADMIN_ID, "❌ Haydovchi topilmadi.")
        return
    haydovchilar[hid]["holat"] = holat_yangi
    save_haydovchilar(haydovchilar)

    try:
        yangi_caption = f"{call.message.caption}\n\n📌 Holat: {holat_yangi.upper()}"
        bot.edit_message_caption(yangi_caption, ADMIN_ID, call.message.message_id)
    except Exception:
        pass
    try:
        bot.send_message(int(hid), xabar)
    except Exception as e:
        log.warning(f"Haydovchiga xabar yuborilmadi: {e}")


# ============================================================
#  📋 RUXSATNOMANI YUKLASH
# ============================================================
@bot.message_handler(func=lambda m: m.text == "📋 Ruxsatnomani yuklash")
def ruxsatnoma_start(message):
    if check_ban(message): return
    uid = message.from_user.id
    user_state[uid] = "ruxsat_fayl_kutish"
    bot.send_message(
        uid,
        "📋 **Ruxsatnomangizni yuklang:**\n\n"
        "_(Hujjatni rasm yoki fayl (PDF/DOC) ko'rinishida yuborishingiz mumkin)_",
        parse_mode="Markdown",
        reply_markup=types.ReplyKeyboardRemove()
    )


@bot.message_handler(content_types=["photo", "document"],
                     func=lambda m: user_state.get(m.from_user.id) == "ruxsat_fayl_kutish")
def ruxsatnoma_fayl_qabul(message):
    uid = message.from_user.id
    user_data_temp.setdefault(uid, {})

    if message.content_type == "photo":
        user_data_temp[uid]["ruxsat_file_id"] = message.photo[-1].file_id
        user_data_temp[uid]["ruxsat_turi"] = "photo"
    else:
        user_data_temp[uid]["ruxsat_file_id"] = message.document.file_id
        user_data_temp[uid]["ruxsat_turi"] = "document"

    user_state[uid] = "ruxsat_izoh"
    bot.send_message(uid, "📝 Ruxsatnoma haqida qisqacha izoh yozing (masalan: qaysi maqsadda, muddati va h.k.):")


@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == "ruxsat_fayl_kutish")
def ruxsatnoma_notogri_format(message):
    bot.send_message(message.from_user.id, "❌ Iltimos, hujjatni rasm yoki fayl ko'rinishida yuboring.")


@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == "ruxsat_izoh")
def ruxsatnoma_izoh_qabul(message):
    uid = message.from_user.id
    user_data_temp[uid]["ruxsat_izoh"] = message.text
    user_state.pop(uid, None)

    user = get_user(uid)
    rid = yangi_ruxsatnoma_id()
    data = user_data_temp[uid]

    ruxsat_obj = {
        "user_id": uid,
        "file_id": data["ruxsat_file_id"],
        "turi": data["ruxsat_turi"],
        "izoh": data["ruxsat_izoh"],
        "holat": "kutilmoqda",
        "sana": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "egasi_ism": user["name"],
    }
    ruxsatnoma_qoshish(rid, ruxsat_obj)

    admin_matn = (
        f"🔔 YANGI RUXSATNOMA\n\n"
        f"🆔 Raqami: {rid}\n"
        f"👤 F.I.Sh: {user['name']}\n"
        f"🔗 Profil: {user.get('tg_username','')}\n"
        f"📞 Telefon: {user.get('phone','')}\n"
        f"📝 Izoh: {data['ruxsat_izoh']}\n"
        f"🆔 Foydalanuvchi ID: {uid}"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"ruxsataccept_{rid}"),
        types.InlineKeyboardButton("❌ Rad etish", callback_data=f"ruxsatreject_{rid}"),
    )

    try:
        if data["ruxsat_turi"] == "photo":
            bot.send_photo(ADMIN_ID, data["ruxsat_file_id"], caption=admin_matn, reply_markup=markup)
        else:
            bot.send_document(ADMIN_ID, data["ruxsat_file_id"], caption=admin_matn, reply_markup=markup)
    except Exception as e:
        log.error(f"Adminga ruxsatnoma yuborishda xatolik: {e}")

    bot.send_message(
        uid,
        f"✅ Ruxsatnomangiz muvaffaqiyatli yuborildi!\n\n🆔 Ariza raqami: **{rid}**\n"
        f"Admin ko'rib chiqqach sizga xabar beriladi.",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard(uid)
    )
    user_data_temp.pop(uid, None)


@bot.callback_query_handler(func=lambda call: call.data.startswith("ruxsataccept_") or call.data.startswith("ruxsatreject_"))
def ruxsatnoma_admin_qaror(call):
    if call.from_user.id != ADMIN_ID: return
    bot.answer_callback_query(call.id)

    if call.data.startswith("ruxsataccept_"):
        rid = call.data.replace("ruxsataccept_", "")
        holat_yangi = "tasdiqlandi"
        xabar = f"🎉 Sizning {rid} raqamli ruxsatnomangiz tasdiqlandi!"
    else:
        rid = call.data.replace("ruxsatreject_", "")
        holat_yangi = "rad etildi"
        xabar = f"❌ Afsuski, sizning {rid} raqamli ruxsatnomangiz rad etildi."

    ruxsatnomalar = load_ruxsatnoma()
    ruxsat = ruxsatnomalar.get(rid)
    if not ruxsat:
        bot.send_message(ADMIN_ID, "❌ Ruxsatnoma topilmadi.")
        return
    ruxsat["holat"] = holat_yangi
    ruxsatnomalar[rid] = ruxsat
    save_ruxsatnoma(ruxsatnomalar)

    try:
        yangi_caption = f"{call.message.caption}\n\n📌 Holat: {holat_yangi.upper()}"
        bot.edit_message_caption(yangi_caption, ADMIN_ID, call.message.message_id)
    except Exception:
        pass
    try:
        bot.send_message(ruxsat["user_id"], xabar)
    except Exception as e:
        log.warning(f"Xabar yuborilmadi: {e}")


# ============================================================
#  🎓 NATIJANI BILISH (imtixon balini tekshirish)
# ============================================================
@bot.message_handler(func=lambda m: m.text == "🎓 Natijani bilish")
def natija_bilish_start(message):
    if check_ban(message): return
    uid = message.from_user.id
    user_state[uid] = "natija_kutish"
    bot.send_message(uid, "🆔 Ariza raqamingizni kiriting (masalan: EX1):")


@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == "natija_kutish")
def natija_bilish_natija(message):
    uid = message.from_user.id
    user_state.pop(uid, None)
    ariza_id = message.text.strip().upper()
    arizalar = load_imtixon()
    ariza = arizalar.get(ariza_id)

    if not ariza:
        bot.send_message(uid, "❌ Bunday ariza raqami topilmadi. Raqamni tekshirib qayta kiriting.",
                         reply_markup=get_main_keyboard(uid))
        return

    holat = ariza.get("holat", "kutilmoqda")
    matn = f"🆔 **Ariza:** {ariza_id}\n🎓 **Fan:** {ariza['fan']}\n👤 **F.I.Sh:** {ariza['ism']}\n📌 **Holat:** {holat}\n"

    if ariza.get("ball") is not None:
        matn += f"🏆 **Ball:** {ariza['ball']}"
    elif holat == "qabul qilindi":
        matn += "⏳ Natija hali e'lon qilinmagan. Birozdan so'ng qayta tekshiring."
    elif holat == "rad etildi":
        matn += "❌ Ariza rad etilgan, natija mavjud emas."
    else:
        matn += "⏳ Arizangiz hali ko'rib chiqilmoqda."

    bot.send_message(uid, matn, parse_mode="Markdown", reply_markup=get_main_keyboard(uid))


def stat_matnini_hosil_qil():
    db = load_db()
    elonlar = load_elonlar()
    faol_soni = sum(1 for e in elonlar.values() if elon_faolmi(e))
    kot_stat = {}
    for e in elonlar.values():
        if elon_faolmi(e):
            kot_stat[e["kategoriya"]] = kot_stat.get(e["kategoriya"], 0) + 1
    arizalar = load_imtixon()
    kutilmoqda = sum(1 for a in arizalar.values() if a.get("holat") == "kutilmoqda")
    qabul = sum(1 for a in arizalar.values() if a.get("holat") == "qabul qilindi")

    taksilar = load_taksi()
    haydovchilar = load_haydovchilar()
    taksi_jami = len(taksilar)
    taksi_yakunlangan = sum(1 for t in taksilar.values() if t.get("holat") == "yakunlandi")
    taksi_bekor = sum(1 for t in taksilar.values() if t.get("holat") == "bekor_qilindi")
    onlayn_haydovchi = sum(1 for h in haydovchilar.values() if h.get("holat") == "tasdiqlangan" and h.get("online"))
    tasdiqlangan_haydovchi = sum(1 for h in haydovchilar.values() if h.get("holat") == "tasdiqlangan")
    taksi_daromad = sum(t.get("narx") or 0 for t in taksilar.values() if t.get("holat") == "yakunlandi")
    bloklangan_soni = sum(1 for u in db.values() if u.get("is_banned"))
    premium_soni = sum(1 for u in db.values() if u.get("premium"))

    stat_matn = (
        f"📊 **Bot statistikasi:**\n\n"
        f"👥 Umumiy foydalanuvchilar: {len(db)} ta\n"
        f"💎 Premium: {premium_soni} ta\n"
        f"🚫 Bloklangan: {bloklangan_soni} ta\n"
        f"📢 Faol e'lonlar: {faol_soni} ta\n"
    )
    stat_matn += f"🎓 Imtixon arizalari: {len(arizalar)} ta (⏳ {kutilmoqda} kutilmoqda, ✅ {qabul} qabul qilingan)\n\n"
    stat_matn += (
        f"🚖 **Taksi statistikasi:**\n"
        f"• Jami buyurtmalar: {taksi_jami} ta\n"
        f"• Yakunlangan: {taksi_yakunlangan} ta\n"
        f"• Bekor qilingan: {taksi_bekor} ta\n"
        f"• Tasdiqlangan haydovchilar: {tasdiqlangan_haydovchi} ta ({onlayn_haydovchi} onlayn)\n"
        f"• Umumiy taksi aylanmasi: {som_format(taksi_daromad)}\n\n"
    )
    if kot_stat:
        stat_matn += "📂 Kategoriyalar bo'yicha:\n"
        for k, v in sorted(kot_stat.items(), key=lambda x: -x[1]):
            stat_matn += f"• {k}: {v} ta\n"
    return stat_matn


def kunlik_hisobot_oqimi():
    while True:
        time.sleep(24 * 60 * 60)
        try:
            bot.send_message(ADMIN_ID, "📅 **Kunlik avtomatik hisobot:**\n\n" + stat_matnini_hosil_qil(),
                             parse_mode="Markdown")
        except Exception as e:
            log.error(f"Kunlik hisobot yuborilmadi: {e}")


# ---- QOLGAN MENU TUGMALARI (Yordam, Qoidalar, Statistika) ----
@bot.message_handler(func=lambda m: m.text in ["📊 Statistika", "❓ Yordam", "📜 Qoidalar"])
def menu_boshqa_tugmalar(message):
    if check_ban(message): return
    uid = message.from_user.id
    text = message.text

    if text == "📊 Statistika":
        bot.send_message(uid, stat_matnini_hosil_qil(), parse_mode="Markdown")
    elif text == "❓ Yordam":
        bot.send_message(uid, f"❓ Muammo yoki savollar bo'lsa admin: @{ADMIN_USERNAME}")
    elif text == "📜 Qoidalar":
        bot.send_message(uid,
                         "Qoidalar: Har qanday qonun buzilishi ADMIN tomonidan doimiy bloklanishga (BAN) sabab bo'ladi!")


# ============================================================
#  /mystats — FOYDALANUVCHI O'Z STATISTIKASINI KO'RISHI
# ============================================================
@bot.message_handler(commands=['mystats'])
def mystats(message):
    if check_ban(message): return
    uid = message.from_user.id
    user = get_user(uid)
    elonlar = load_elonlar()
    faol_elonlar = sum(1 for eid in user.get("elonlar", []) if eid in elonlar and elon_faolmi(elonlar[eid]))

    matn = (
        f"📊 **Sizning statistikangiz:**\n\n"
        f"👤 Ism: {user.get('name','?')}\n"
        f"💎 Premium: {'Ha' if user.get('premium') else 'Yoq'}\n"
        f"📢 Jami e'lonlaringiz: {len(user.get('elonlar', []))} ta (faol: {faol_elonlar} ta)\n"
        f"❤️ Sevimlilar: {len(user.get('sevimlilar', []))} ta\n"
        f"🎁 Taklif qilganlar: {user.get('referral_count', 0)} ta\n"
        f"📅 Qo'shilgan sana: {user.get('joined_date','-')}"
    )
    bot.send_message(uid, matn, parse_mode="Markdown")


# ============================================================
#  /haydovchilar_top — ADMIN UCHUN ENG YAXSHI HAYDOVCHILAR
# ============================================================
@bot.message_handler(commands=['haydovchilar_top'])
def admin_haydovchilar_top(message):
    if message.from_user.id != ADMIN_ID: return
    haydovchilar = load_haydovchilar()
    tasdiqlangan = [(hid, h) for hid, h in haydovchilar.items() if h.get("holat") == "tasdiqlangan"]
    tasdiqlangan.sort(key=lambda x: x[1].get("safar_soni", 0), reverse=True)

    if not tasdiqlangan:
        bot.reply_to(message, "🚕 Hozircha tasdiqlangan haydovchilar yo'q.")
        return

    matn = "🏆 **Haydovchilar reytingi (safarlar soni bo'yicha):**\n\n"
    for i, (hid, h) in enumerate(tasdiqlangan[:15], 1):
        matn += (
            f"{i}. {h.get('ism','?')} — {h.get('safar_soni', 0)} safar, "
            f"{haydovchi_reyting_matni(h)}, {som_format(h.get('daromad', 0))}\n"
        )
    bot.reply_to(message, matn, parse_mode="Markdown")


# ---- ADMIN XABAR YUBORISH ----
@bot.message_handler(func=lambda m: m.text == "📢 Hammaga Xabar Yuborish" and m.from_user.id == ADMIN_ID)
def broadcast_start(message):
    user_state[ADMIN_ID] = "broadcast_msg"
    bot.send_message(ADMIN_ID, "📢 Barcha foydalanuvchilarga yuboriladigan xabar matnini kiriting:",
                     reply_markup=types.ReplyKeyboardRemove())


@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == "broadcast_msg" and m.from_user.id == ADMIN_ID)
def broadcast_send(message):
    db = load_db()
    count = 0
    xato = 0
    for uid in db.keys():
        try:
            bot.send_message(int(uid), message.text)
            count += 1
        except Exception as e:
            xato += 1
            log.warning(f"Broadcast xatoligi ({uid}): {e}")
    news_qoshish(message.text)
    user_state.pop(ADMIN_ID, None)
    bot.send_message(ADMIN_ID, f"✅ Xabar {count} ta foydalanuvchiga yuborildi. ({xato} ta xatolik)",
                     reply_markup=get_main_keyboard(ADMIN_ID))


# ---- ADMIN: FOYDALANUVCHILARNI CSV FORMATIDA EKSPORT QILISH ----
@bot.message_handler(commands=['export'])
def admin_export_users(message):
    if message.from_user.id != ADMIN_ID: return
    db = load_db()
    path = os.path.join(PDF_TMP_DIR, "foydalanuvchilar.csv")
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Ism", "Username", "Telefon", "Premium", "Bloklangan",
                         "Elonlar_soni", "Referal_soni", "Qoshilgan_sana"])
        for uid, u in db.items():
            writer.writerow([
                uid, u.get("name", ""), u.get("tg_username", ""), u.get("phone", ""),
                "Ha" if u.get("premium") else "Yo'q", "Ha" if u.get("is_banned") else "Yo'q",
                u.get("elon_count", 0), u.get("referral_count", 0), u.get("joined_date", "")
            ])
    with open(path, "rb") as f:
        bot.send_document(ADMIN_ID, f, caption=f"📊 Jami {len(db)} ta foydalanuvchi eksport qilindi.")


# ---- ADMIN: TAKSI HAYDOVCHILARINI CSV FORMATIDA EKSPORT QILISH ----
@bot.message_handler(commands=['export_haydovchi'])
def admin_export_haydovchilar(message):
    if message.from_user.id != ADMIN_ID: return
    haydovchilar = load_haydovchilar()
    path = os.path.join(PDF_TMP_DIR, "haydovchilar.csv")
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Ism", "Telefon", "Avto", "Raqam", "Holat", "Onlayn",
                         "Safar_soni", "Daromad", "Reyting"])
        for hid, h in haydovchilar.items():
            soni = h.get("rating_count", 0)
            reyting = round(h.get("rating_sum", 0) / soni, 2) if soni else "-"
            writer.writerow([
                hid, h.get("ism", ""), h.get("telefon", ""), h.get("avto_model", ""),
                h.get("avto_raqam", ""), h.get("holat", ""), "Ha" if h.get("online") else "Yo'q",
                h.get("safar_soni", 0), h.get("daromad", 0), reyting
            ])
    with open(path, "rb") as f:
        bot.send_document(ADMIN_ID, f, caption=f"🚕 Jami {len(haydovchilar)} ta haydovchi eksport qilindi.")


# ---- ADMIN PREMIUM FUNKSIYALARI ----
@bot.message_handler(commands=['premium'])
def give_premium(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        uid = message.text.split()[1]
        db = load_db()
        if uid in db:
            db[uid]["premium"] = True
            save_db(db)
            bot.reply_to(message, f"✅ Foydalanuvchi {uid} uchun Premium 💎 muvaffaqiyatli yoqildi!")
            try:
                bot.send_message(int(uid),
                                 "🎉 Tabriklaymiz! Admin sizga Premium 💎 maqomini berdi. Endi cheksiz e'lon joylay olasiz!")
            except Exception as e:
                log.warning(f"Xabar yuborilmadi: {e}")
        else:
            bot.reply_to(message, "❌ Bunday foydalanuvchi topilmadi.")
    except Exception:
        bot.reply_to(message, "⚠️ To'g'ri format: `/premium USER_ID`", parse_mode="Markdown")


@bot.message_handler(commands=['unpremium'])
def remove_premium(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        uid = message.text.split()[1]
        db = load_db()
        if uid in db:
            db[uid]["premium"] = False
            save_db(db)
            bot.reply_to(message, f"✅ Foydalanuvchi {uid} dan Premium olib tashlandi.")
        else:
            bot.reply_to(message, "❌ Bunday foydalanuvchi topilmadi.")
    except Exception:
        bot.reply_to(message, "⚠️ To'g'ri format: `/unpremium USER_ID`", parse_mode="Markdown")


# ---- BAN/UNBAN QILISH FUNKSIYASI ----
@bot.message_handler(commands=['ban'])
def ban_user(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        uid = message.text.split()[1]
        db = load_db()
        if uid in db:
            db[uid]["is_banned"] = True
            save_db(db)
            bot.reply_to(message, f"✅ Foydalanuvchi {uid} muvaffaqiyatli bloklandi.")
            try:
                bot.send_message(int(uid), f"❌ Siz botdan bloklandingiz. Murojaat: @{ADMIN_USERNAME}")
            except Exception:
                pass
        else:
            bot.reply_to(message, "❌ Foydalanuvchi topilmadi.")
    except Exception:
        bot.reply_to(message, "⚠️ To'g'ri format: /ban USER_ID")


@bot.message_handler(commands=['unban'])
def unban_user(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        uid = message.text.split()[1]
        db = load_db()
        if uid in db:
            db[uid]["is_banned"] = False
            save_db(db)
            bot.reply_to(message, f"✅ {uid} blokdan chiqarildi.")
            try:
                bot.send_message(int(uid), "✅ Siz blokdan chiqarildingiz.")
            except Exception:
                pass
        else:
            bot.reply_to(message, "❌ Foydalanuvchi topilmadi.")
    except Exception:
        bot.reply_to(message, "⚠️ To'g'ri format: /unban USER_ID")


# ---- RO'YXATDAN O'TISH ----
@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == "reg_name")
def register_name(message):
    uid = message.from_user.id
    user = get_user(uid)
    user["name"] = message.text
    update_user(uid, user)

    user_state[uid] = "reg_tg_username"
    current_username = f"@{message.from_user.username}" if message.from_user.username else ""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    if current_username:
        markup.add(current_username)
    bot.send_message(uid, "✅ Ism saqlandi. Endi Telegram profilingiz ismini kiriting (Masalan: @username):",
                     reply_markup=markup)


@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == "reg_tg_username")
def register_tg_username(message):
    uid = message.from_user.id
    user = get_user(uid)
    text = message.text if message.text.startswith("@") else f"@{message.text}"
    user["tg_username"] = text
    update_user(uid, user)

    user_state[uid] = "reg_phone"
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton("📞 Telefon raqamni yuborish", request_contact=True))
    bot.send_message(uid, "✅ Profil nomi saqlandi. Endi pastdagi tugma orqali telefon raqamingizni yuboring:",
                     reply_markup=markup)


@bot.message_handler(content_types=["contact"], func=lambda m: user_state.get(m.from_user.id) == "reg_phone")
def register_phone(message):
    uid = message.from_user.id
    user = get_user(uid)
    user["phone"] = message.contact.phone_number
    update_user(uid, user)
    user_state.pop(uid, None)
    bot.send_message(uid,
                     f"🎉 Ro'yxatdan muvaffaqiyatli o'tdingiz, {user['name']}!\nEndi botdan to'liq foydalanishishingiz mumkin.",
                     reply_markup=get_main_keyboard(uid))


# ---- ⚙️ SOZLAMALAR BO'LIMI ----
@bot.message_handler(func=lambda m: m.text == "⚙️ Sozlamalar")
def sozlamalar(message):
    if check_ban(message): return
    uid = message.from_user.id
    user = get_user(uid)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📝 Ismni o'zgartirish", callback_data="set_name"))
    markup.add(types.InlineKeyboardButton("🔗 Profil nomini o'zgartirish", callback_data="set_tg_username"))
    markup.add(types.InlineKeyboardButton("📞 Raqamni o'zgartirish", callback_data="set_phone"))
    markup.add(types.InlineKeyboardButton("🗑 Akkauntni o'chirish", callback_data="delete_account_start"))
    bot.send_message(
        uid,
        f"⚙️ *Profil sozlamalari:*\n\n👤 *Ismingiz:* {user['name']}\n🔗 *Profil:* {user.get('tg_username', 'Kiritilmagan')}\n📞 *Telefoningiz:* {user['phone'] if user['phone'] else 'Kiritilmagan'}",
        parse_mode="Markdown", reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data == "delete_account_start")
def delete_account_start(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Ha, o'chirish", callback_data="delete_account_confirm"),
        types.InlineKeyboardButton("❌ Bekor qilish", callback_data="delete_account_cancel"),
    )
    bot.send_message(
        uid,
        "⚠️ **Diqqat!** Akkauntingiz va barcha ma'lumotlaringiz (ism, telefon, e'lonlar ro'yxati) "
        "o'chiriladi. Bu amalni ortga qaytarib bo'lmaydi. Rostdan ham davom etasizmi?",
        parse_mode="Markdown", reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data in ["delete_account_confirm", "delete_account_cancel"])
def delete_account_yakun(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass

    if call.data == "delete_account_cancel":
        bot.send_message(uid, "❌ Bekor qilindi.", reply_markup=get_main_keyboard(uid))
        return

    db = load_db()
    uid_str = str(uid)
    if uid_str in db:
        for eid in db[uid_str].get("elonlar", []):
            elon_ochirish(eid)
        del db[uid_str]
        save_db(db)

    user_state.pop(uid, None)
    user_data_temp.pop(uid, None)
    bot.send_message(uid, "🗑 Akkauntingiz o'chirildi. Qayta boshlash uchun /start bosing.",
                     reply_markup=types.ReplyKeyboardRemove())


@bot.callback_query_handler(func=lambda call: call.data in ["set_name", "set_tg_username", "set_phone"])
def sozlama_tanlov(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass

    if call.data == "set_name":
        user_state[uid] = "ism_o_zgartirish"
        bot.send_message(uid, "📝 Yangi ismingizni kiriting:")
    elif call.data == "set_tg_username":
        user_state[uid] = "profil_o_zgartirish"
        bot.send_message(uid, "🔗 Yangi profil nomini kiriting (Masalan: @username):")
    elif call.data == "set_phone":
        user_state[uid] = "raqam_o_zgartirish"
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(types.KeyboardButton("📞 Yangi raqamni yuborish", request_contact=True))
        bot.send_message(uid, "📱 Pastdagi tugmani bosib yangi telefon raqamingizni yuboring:", reply_markup=markup)


@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == "ism_o_zgartirish")
def ism_yangila(message):
    uid = message.from_user.id
    user = get_user(uid)
    user["name"] = message.text
    update_user(uid, user)
    user_state.pop(uid, None)
    bot.send_message(uid, f"✅ Ismingiz yangilandi!", reply_markup=get_main_keyboard(uid))


@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == "profil_o_zgartirish")
def profil_yangila(message):
    uid = message.from_user.id
    user = get_user(uid)
    text = message.text if message.text.startswith("@") else f"@{message.text}"
    user["tg_username"] = text
    update_user(uid, user)
    user_state.pop(uid, None)
    bot.send_message(uid, f"✅ Telegram profil nomi yangilandi!", reply_markup=get_main_keyboard(uid))


@bot.message_handler(content_types=["contact"], func=lambda m: user_state.get(m.from_user.id) == "raqam_o_zgartirish")
def raqam_yangila(message):
    uid = message.from_user.id
    user = get_user(uid)
    user["phone"] = message.contact.phone_number
    update_user(uid, user)
    user_state.pop(uid, None)
    bot.send_message(uid, f"✅ Telefon raqamingiz muvaffaqiyatli saqlandi!", reply_markup=get_main_keyboard(uid))


# ---- ⭐ REKLAMA VA VIP XIZMATLAR ----
@bot.message_handler(func=lambda m: m.text in ["💼 Reklama", "⭐ Obuna / VIP"])
def biznes_xizmatlar(message):
    if check_ban(message): return
    uid = message.from_user.id
    markup = types.InlineKeyboardMarkup(row_width=1)

    if message.text == "💼 Reklama":
        text = (
            "💼 *Botda va Kanalda reklama xizmatlari!*\n\n"
            "💵 *Oddiy reklama posti:* 5 000 so'm\n"
            "🖼 *Banner reklama (Bot ichida doimiy):* 30 000 so'm\n"
            "🤖 *Kanalga avtomatik reklama postlari:* 50 000 so'm\n\n"
            "👉 Kerakli xizmat tugmasini bosing va adminga buyurtma bering:"
        )
        markup.add(
            types.InlineKeyboardButton("📣 Oddiy reklama (5.000 so'm)", url=f"{ADMIN_LINK}?text=Oddiy_reklama_5000"),
            types.InlineKeyboardButton("🖼 Banner reklama (30.000 so'm)", url=f"{ADMIN_LINK}?text=Banner_reklama_30000"),
            types.InlineKeyboardButton("🤖 Avtomatik reklama (50.000 so'm)", url=f"{ADMIN_LINK}?text=Avto_reklama_50000")
        )
    else:
        text = (
            "⭐ *Monetizatsiya va VIP Xizmatlar:*\n\n"
            "💎 *Premium Obuna:* 15 000 so'm (Oylik)\n"
            "└ ♾ Cheksiz e'lon joylash + Ism yonida maxsus `💎` belgi\n\n"
            "🔥 *VIP E'lon:* 10 000 so'm\n"
            "└ E'lon qidiruv ro'yxatida doim eng yuqorida turadi\n\n"
            "⚡ *E'lonni 7 kun tepaga chiqarish:* 7 000 so'm\n"
            "└ Har kuni avtomatik eng birinchi o'ringa ko'tariladi\n\n"
            "👉 Kerakli xizmat ustiga bosib faollashtiring:"
        )
        markup.add(
            types.InlineKeyboardButton("💎 Premium obuna (15.000 so'm)", url=f"{ADMIN_LINK}?text=Premium_obuna_15000"),
            types.InlineKeyboardButton("🔥 VIP e'lon sotib olish (10.000 so'm)", url=f"{ADMIN_LINK}?text=VIP_elon_10000"),
            types.InlineKeyboardButton("⚡ 7 kun tepaga chiqarish (7.000 so'm)", url=f"{ADMIN_LINK}?text=Tepaga_chiqarish_7000")
        )

    bot.send_message(uid, text, parse_mode="Markdown", reply_markup=markup)


# ---- 📢 E'LON BERISH JARAYONI ----
@bot.message_handler(func=lambda m: m.text == "📢 E'lon berish")
def elon_berish(message):
    if check_ban(message): return
    uid = message.from_user.id
    if not check_sub(uid):
        send_sub_message(uid)
        return

    user = get_user(uid)
    if not user["premium"] and user["elon_count"] >= 3:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💳 Premium faollashtirish", url=ADMIN_LINK))
        bot.send_message(uid, "❌ Bepul limit tugadi (Maks 3 ta e'lon).\n⭐ Davom etish uchun Premium obuna oling.",
                         reply_markup=markup)
        return

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📝 Oddiy e'lon (Bepul)", callback_data="elonturi_oddiy"))
    markup.add(types.InlineKeyboardButton("🔥 VIP e'lon (10 000 so'm)", callback_data="elonturi_vip"))
    bot.send_message(uid, "✨ E'lon turini tanlang:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("elonturi_"))
def elon_turi_tanlandi(call):
    uid = call.from_user.id
    turi = call.data.split("_")[1]
    bot.answer_callback_query(call.id)
    user_data_temp[uid] = {"is_vip": (turi == "vip")}

    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [types.InlineKeyboardButton(nom, callback_data=f"elonhudud_{kod}") for nom, kod in VILOYATLAR]
    markup.add(*buttons)
    bot.edit_message_text("📍 E'lon qaysi hududga (viloyatga) tegishli? Tanlang:", call.message.chat.id,
                          call.message.message_id, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("elonhudud_"))
def elon_hudud_tanlandi(call):
    uid = call.from_user.id
    kod = call.data.split("_")[1]
    bot.answer_callback_query(call.id)
    nom = next((n for n, k in VILOYATLAR if k == kod), kod)

    user_data_temp[uid]["hudud_kod"] = kod
    user_data_temp[uid]["hudud"] = nom

    markup = types.InlineKeyboardMarkup(row_width=2)
    tumanlar_list = TUMANLAR.get(kod, [])
    buttons = [types.InlineKeyboardButton(t_nom, callback_data=f"elontuman_{t_kod}") for t_nom, t_kod in tumanlar_list]
    markup.add(*buttons)

    bot.edit_message_text(f"🏙 Siz {nom}ni tanladingiz. Endi tuman/shaharni tanlang:", call.message.chat.id,
                          call.message.message_id, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("elontuman_"))
def elon_tuman_tanlandi(call):
    uid = call.from_user.id
    tuman_kod = call.data.split("_")[1]
    bot.answer_callback_query(call.id)

    hudud_kod = user_data_temp[uid].get("hudud_kod", "tosh_sh")
    tuman_nomi = next((n for n, k in TUMANLAR[hudud_kod] if k == tuman_kod), tuman_kod)
    user_data_temp[uid]["tuman"] = tuman_nomi

    user_state[uid] = "elon_lokatsiya"

    reply_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    reply_markup.add(types.KeyboardButton("📍 Lokatsiyani yuborish", request_location=True))

    inline_markup = types.InlineKeyboardMarkup()
    inline_markup.add(types.InlineKeyboardButton("O'tkazib yuborish ⏭", callback_data="skip_location"))

    bot.send_message(
        uid,
        "📍 **E'lon joylashgan lokatsiyani yuboring:**\n\n"
        "_(Pastdagi tugma orqali aniq lokatsiya yuborishingiz mumkin. Agar lokatsiya shart bo'lmasa, 'O'tkazib yuborish' tugmasini bosing)_",
        reply_markup=reply_markup
    )
    bot.send_message(uid, "Yoki lokatsiyani tashlamasdan davom eting:", reply_markup=inline_markup)


@bot.callback_query_handler(func=lambda call: call.data == "skip_location")
def skip_location(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    if uid in user_data_temp:
        user_data_temp[uid]["location"] = None
        otish_kategoriya_bosqichi(call.message.chat.id, uid)


@bot.message_handler(content_types=["location"], func=lambda m: user_state.get(m.from_user.id) == "elon_lokatsiya")
def elon_lokatsiya_qabul(message):
    uid = message.from_user.id
    lat = message.location.latitude
    lon = message.location.longitude
    user_data_temp[uid]["location"] = f"https://maps.google.com/?q={lat},{lon}"

    bot.send_message(uid, "✅ Lokatsiya saqlandi.", reply_markup=types.ReplyKeyboardRemove())
    otish_kategoriya_bosqichi(message.chat.id, uid)


def otish_kategoriya_bosqichi(chat_id, uid):
    user_state[uid] = "elon_kategoriya_kutish"
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [types.InlineKeyboardButton(nom, callback_data=f"elonkoti_{kod}") for nom, kod in KATEGORIYALAR]
    markup.add(*buttons)
    bot.send_message(chat_id, "📂 E'lon uchun mos kategoriyani tanlang:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("elonkoti_"))
def elon_kategoriya_tanlandi(call):
    uid = call.from_user.id
    kod = call.data.split("_")[1]
    bot.answer_callback_query(call.id)
    nom = next((n for n, k in KATEGORIYALAR if k == kod), kod)

    user_data_temp[uid]["kategoriya"] = nom
    user_data_temp[uid]["kategoriya_kod"] = kod
    user_state[uid] = "elon_sarlavha"

    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass

    bot.send_message(uid,
                     "✍️ **E'lon sarlavhasini kiriting:**\n(Masalan: iPhone 13 Pro Max sotiladi yoki Uy ijaraga beriladi)",
                     reply_markup=types.ReplyKeyboardRemove())


@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == "elon_sarlavha")
def elon_sarlavha_qabul(message):
    uid = message.from_user.id
    if matnda_taqiqlangan_soz_bormi(message.text):
        bot.send_message(uid, "❌ E'lon sarlavhasida odobsiz so'zlar bor! Iltimos, boshqa sarlavha yozing:")
        return

    user_data_temp[uid]["sarlavha"] = message.text
    user_state[uid] = "elon_tavsif"
    bot.send_message(uid,
                     "📝 **E'lon haqida batafsil ma'lumot (tavsif) yozing:**\n(Holati, rangi, parametrlari va h.k.)")


@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == "elon_tavsif")
def elon_tavsif_qabul(message):
    uid = message.from_user.id
    if matnda_taqiqlangan_soz_bormi(message.text):
        bot.send_message(uid, "❌ E'lon tavsifida haqoratli so'zlar aniqlandi! Qaytadan toza tavsif yozing:")
        return

    user_data_temp[uid]["tavsif"] = message.text
    user_state[uid] = "elon_narx"
    bot.send_message(uid,
                     "💰 **Mahsulot/Xizmat narxini kiriting:**\n(Masalan: 500 y.u.e yoki 3 000 000 so'm yoki Kelishiladi)")


@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == "elon_narx")
def elon_narx_qabul(message):
    uid = message.from_user.id
    user_data_temp[uid]["narx"] = message.text
    user_state[uid] = "elon_rasm"

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Rasmiz davom etish ⏭", callback_data="skip_photo"))
    bot.send_message(uid, "🖼 **E'lon uchun rasm yuboring:**\n(Agar rasm yo'q bo'lsa, quyidagi tugmani bosing)",
                     reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "skip_photo")
def skip_photo(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    user_data_temp[uid]["photo"] = None
    elon_tekshirish_bosqichi(uid)


@bot.message_handler(content_types=["photo"], func=lambda m: user_state.get(m.from_user.id) == "elon_rasm")
def elon_rasm_qabul(message):
    uid = message.from_user.id
    file_id = message.photo[-1].file_id
    user_data_temp[uid]["photo"] = file_id
    elon_tekshirish_bosqichi(uid)


def elon_tekshirish_bosqichi(uid):
    user_state[uid] = "elon_tasdiqlash"
    data = user_data_temp[uid]
    user = get_user(uid)

    vip_belgi = "🔥 VIP " if data["is_vip"] else "📝 Oddiy "
    lokatsiya_matn = f"[Xaritada ko'rish]({data['location']})" if data["location"] else "Kiritilmagan"

    tekshirish_matni = (
        f"🧐 **E'loningizni tekshiring:**\n\n"
        f"🏷 **Tur:** {vip_belgi}\n"
        f"📂 **Kategoriya:** {md_escape(data['kategoriya'])}\n"
        f"📍 **Hudud:** {md_escape(data['hudud'])}, {md_escape(data['tuman'])}\n"
        f"📌 **Sarlavha:** {md_escape(data['sarlavha'])}\n"
        f"📝 **Tavsif:** {md_escape(data['tavsif'])}\n"
        f"💰 **Narx:** {md_escape(data['narx'])}\n"
        f"📍 **Lokatsiya:** {lokatsiya_matn}\n\n"
        f"👤 **Aloqa:** {md_escape(user['name'])} ({md_escape(user['phone'])})\n"
        f"🔗 **Telegram:** {md_escape(user['tg_username'])}\n\n"
        f"Ma'lumotlar to'g'rimi? Tasdiqlasangiz kanalga joylanadi."
    )

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Tasdiqlash", callback_data="confirm_elon"),
        types.InlineKeyboardButton("❌ Rad etish", callback_data="cancel_elon")
    )

    if data["photo"]:
        xavfsiz_photo_yuborish(uid, data["photo"], tekshirish_matni, reply_markup=markup)
    else:
        xavfsiz_yuborish(uid, tekshirish_matni, reply_markup=markup, disable_web_page_preview=False)


@bot.callback_query_handler(func=lambda call: call.data in ["confirm_elon", "cancel_elon"])
def elon_yakuniy_qaror(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)

    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception:
        pass

    if call.data == "cancel_elon":
        user_data_temp.pop(uid, None)
        user_state.pop(uid, None)
        bot.send_message(uid, "❌ E'lon bekor qilindi.", reply_markup=get_main_keyboard(uid))
        return

    data = user_data_temp.get(uid)
    if not data:
        bot.send_message(uid, "⚠️ Xatolik! Ma'lumotlar topilmadi.", reply_markup=get_main_keyboard(uid))
        return

    user = get_user(uid)
    eid = yangi_elon_id()

    elon_obj = {
        "user_id": uid,
        "kategoriya": data["kategoriya"],
        "kategoriya_kod": data.get("kategoriya_kod", ""),
        "hudud": data["hudud"],
        "tuman": data["tuman"],
        "sarlavha": data["sarlavha"],
        "tavsif": data["tavsif"],
        "narx": data["narx"],
        "photo": data.get("photo"),
        "location": data.get("location"),
        "is_vip": data["is_vip"],
        "status": "active",
        "created_at": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "egasi_ism": user["name"],
        "egasi_username": user["tg_username"],
    }
    elon_qoshish(eid, elon_obj)

    user["elonlar"].append(eid)
    user["elon_count"] += 1
    update_user(uid, user)

    vip_header = "🔥 VIP E'LON 🔥\n\n" if data["is_vip"] else "📢 YANGI E'LON 📢\n\n"
    lokatsiya_matn = f"[Xaritada ko'rish]({data['location']})" if data["location"] else "Kiritilmagan"

    kanal_matni = (
        f"{vip_header}"
        f"🆔 №{eid}\n"
        f"📌 **Sarlavha:** {md_escape(data['sarlavha'])}\n"
        f"📂 **Kategoriya:** {md_escape(data['kategoriya'])}\n"
        f"📍 **Hudud:** {md_escape(data['hudud'])}, {md_escape(data['tuman'])}\n"
        f"💰 **Narx:** {md_escape(data['narx'])}\n"
        f"📝 **Batafsil:** {md_escape(data['tavsif'])}\n"
        f"📍 **Lokatsiya:** {lokatsiya_matn}\n\n"
        f"👤 **Aloqa:** {md_escape(user['name'])}\n"
        f"📞 **Telefon:** {md_escape(user['phone'])}\n"
        f"🔗 **Profil:** {md_escape(user['tg_username'])}\n\n"
        f"🤖 @{bot.get_me().username} orqali joylandi."
    )

    kanal_markup = types.InlineKeyboardMarkup()
    kanal_markup.add(
        types.InlineKeyboardButton("❤️ Saqlash", callback_data=f"fav_{eid}"),
        types.InlineKeyboardButton("🚩 Shikoyat", callback_data=f"report_{eid}"),
    )

    # ⚠️ MUHIM TUZATISH: avval bu yerda faqat parse_mode="Markdown" bilan
    # yuborilar edi. Agar sarlavha/tavsif/narx ichida "_" yoki "*" kabi
    # belgilar bo'lsa, Telegram "can't parse entities" xatoligi bilan
    # xabarni UMUMAN yubormay, e'lon jim-jimida kanalga chiqmay qolardi.
    # Endi md_escape() bilan tozalanadi VA yuborish muvaffaqiyatsiz bo'lsa
    # (masalan bot kanalda admin emasligi sababli) sizga ANIQ xato matni bilan
    # xabar beriladi — shunda muammoni tezda topa olasiz.
    try:
        if data["photo"]:
            yuborilgan = xavfsiz_photo_yuborish(KANAL_ID, data["photo"], kanal_matni, reply_markup=kanal_markup)
        else:
            yuborilgan = xavfsiz_yuborish(KANAL_ID, kanal_matni, reply_markup=kanal_markup)

        elonlar = load_elonlar()
        elonlar[eid]["kanal_msg_id"] = yuborilgan.message_id
        save_elonlar(elonlar)

        bot.send_message(uid, "🎉 Tabriklaymiz! E'loningiz muvaffaqiyatli tarzda kanalga joylashtirildi.",
                         reply_markup=get_main_keyboard(uid))
    except Exception as e:
        log.error(f"Kanalga yuborishda xatolik: {e}")
        bot.send_message(
            uid,
            "❌ E'lonni kanalga yuborishda muammo chiqdi. Odatda buning sababi:\n"
            "1) Bot kanalda ADMIN emas yoki 'Xabar joylash' huquqi yo'q;\n"
            "2) KANAL_ID noto'g'ri.\n\n"
            "Adminга xabar berildi, tez orada tekshiriladi.",
            reply_markup=get_main_keyboard(uid)
        )
        try:
            bot.send_message(ADMIN_ID, f"⚠️ E'lon №{eid} kanalga yuborilmadi.\nSabab: {e}")
        except Exception:
            pass

    user_data_temp.pop(uid, None)
    user_state.pop(uid, None)


# ---- BOTNI ISHGA TUSHIRISH ----
if __name__ == "__main__":
    log.info("Bot muvaffaqiyatli ishga tushdi...")

    hisobot_thread = threading.Thread(target=kunlik_hisobot_oqimi, daemon=True)
    hisobot_thread.start()

    while True:
        try:
            bot.infinity_polling(timeout=30, long_polling_timeout=30)
        except Exception as e:
            log.error(f"Poll qilishda kutilmagan xatolik: {e}")
            time.sleep(5)
