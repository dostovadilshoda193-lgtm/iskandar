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
BOT_TOKEN = "SIZNING_YANGI_BOT_TOKENINGIZ"

ADMIN_ID = 8548782312
ADMIN_USERNAME = "dostovv"
ADMIN_LINK = f"https://t.me/{ADMIN_USERNAME}"

GEMINI_API_KEY = "SIZNING_YANGI_GEMINI_KALITINGIZ"
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
SOROV_FILE = "sorovlar.json"
KONTENT_FILE = "kontent.json"

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
            "korilgan": [], "manzillar": []
        }
        save_db(db)
    user = db[uid]
    user.setdefault("korilgan", [])
    user.setdefault("manzillar", [])
    return user


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
#  💳 SO'ROVLAR (Hisob to'ldirish / Pul yechish) BAZASI
# ============================================================
def load_sorovlar():
    return _load_json(SOROV_FILE)


def save_sorovlar(data):
    _save_json(SOROV_FILE, data)


def yangi_sorov_id():
    sorovlar = load_sorovlar()
    if not sorovlar:
        return "S1"
    raqamlar = [int(k[1:]) for k in sorovlar.keys() if k.startswith("S") and k[1:].isdigit()]
    return f"S{max(raqamlar, default=0) + 1}"


# ============================================================
#  📰 KONTENT (Yangilik / Bonus / Aksiya / Tadbir) BAZASI
# ============================================================
def load_kontent():
    data = _load_json(KONTENT_FILE)
    if not data:
        data = {"yangilik": [], "bonus": [], "aksiya": [], "tadbir": []}
        _save_json(KONTENT_FILE, data)
    for k in ["yangilik", "bonus", "aksiya", "tadbir"]:
        data.setdefault(k, [])
    return data


def save_kontent(data):
    _save_json(KONTENT_FILE, data)


def kontent_qoshish(turi, matn):
    data = load_kontent()
    data[turi].append({"matn": matn, "sana": datetime.now().strftime("%d.%m.%Y %H:%M")})
    save_kontent(data)


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
        "/delword `so'z` — taqiqlangan so'zni olib tashlash\n"
        "/addnews `matn` — 📰 Yangilik qo'shish\n"
        "/addbonus `matn` — 🎁 Bonus e'lon qilish\n"
        "/addpromo_post `matn` — 🎯 Aksiya e'lon qilish\n"
        "/addevent `matn` — 📅 Tadbir qo'shish\n"
        "/sorovlar — 💳 Hisob to'ldirish/pul yechish so'rovlari\n\n"
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
    fayllar = [DB_FILE, ELON_FILE, IMTIXON_FILE, RUXSATNOMA_FILE, TAKSI_FILE, HAYDOVCHI_FILE, BLACKLIST_FILE,
               SOROV_FILE, KONTENT_FILE]
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
#  📰 ADMIN: KONTENT QO'SHISH BUYRUQLARI (Yangilik/Bonus/Aksiya/Tadbir)
# ============================================================
@bot.message_handler(commands=['addnews'])
def admin_add_news(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        matn = message.text.split(maxsplit=1)[1].strip()
    except IndexError:
        bot.reply_to(message, "⚠️ Format: `/addnews Yangilik matni`", parse_mode="Markdown")
        return
    kontent_qoshish("yangilik", matn)
    bot.reply_to(message, "✅ Yangilik qo'shildi va foydalanuvchilarga '📰 Yangiliklar' bo'limida ko'rinadi.")


@bot.message_handler(commands=['addbonus'])
def admin_add_bonus(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        matn = message.text.split(maxsplit=1)[1].strip()
    except IndexError:
        bot.reply_to(message, "⚠️ Format: `/addbonus Bonus matni`", parse_mode="Markdown")
        return
    kontent_qoshish("bonus", matn)
    bot.reply_to(message, "✅ Bonus e'lon qilindi.")


@bot.message_handler(commands=['addpromo_post'])
def admin_add_aksiya(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        matn = message.text.split(maxsplit=1)[1].strip()
    except IndexError:
        bot.reply_to(message, "⚠️ Format: `/addpromo_post Aksiya matni`", parse_mode="Markdown")
        return
    kontent_qoshish("aksiya", matn)
    bot.reply_to(message, "✅ Aksiya e'lon qilindi.")


@bot.message_handler(commands=['addevent'])
def admin_add_event(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        matn = message.text.split(maxsplit=1)[1].strip()
    except IndexError:
        bot.reply_to(message, "⚠️ Format: `/addevent Tadbir matni`", parse_mode="Markdown")
        return
    kontent_qoshish("tadbir", matn)
    bot.reply_to(message, "✅ Tadbir qo'shildi.")


# ============================================================
#  💳 ADMIN: SO'ROVLAR RO'YXATI (Hisob to'ldirish / Pul yechish)
# ============================================================
@bot.message_handler(commands=['sorovlar'])
def admin_sorovlar(message):
    if message.from_user.id != ADMIN_ID: return
    sorovlar = load_sorovlar()
    kutilmoqda = [(sid, s) for sid, s in sorovlar.items() if s.get("holat") == "kutilmoqda"]
    if not kutilmoqda:
        bot.reply_to(message, "💳 Hozircha kutilayotgan so'rovlar yo'q.")
        return
    for sid, s in kutilmoqda[:20]:
        turi_matn = "💸 Hisob to'ldirish" if s["turi"] == "topup" else "💵 Pul yechish"
        matn = (
            f"💳 **So'rov №{sid}**\n\n"
            f"🔖 Turi: {turi_matn}\n"
            f"👤 {md_escape(s.get('ism',''))} (`{s['user_id']}`)\n"
            f"💰 Miqdor: {som_format(s['miqdor'])}\n"
        )
        if s.get("karta"):
            matn += f"💳 Karta: {md_escape(s['karta'])}\n"
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"sorovok_{sid}"),
            types.InlineKeyboardButton("❌ Rad etish", callback_data=f"sorovrad_{sid}"),
        )
        xavfsiz_yuborish(ADMIN_ID, matn, reply_markup=markup)


# ============================================================
#  🔁 ESKI TUGMA FUNKSIYALARINI YANGI INLINE MENYUDAN QAYTA
#  ISHLATISH UCHUN "SOXTA XABAR" YORDAMCHISI
# ============================================================
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
        types.InlineKeyboardButton("👀 Ko'rilganlar", callback_data="hub_korilgan"),
        types.InlineKeyboardButton("💬 Xaridorlar bilan chat", callback_data="hub_xaridor_chat"),
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


# ---- 👀 KO'RILGAN E'LONLAR ----
@bot.callback_query_handler(func=lambda call: call.data == "hub_korilgan")
def hub_korilgan(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    user = get_user(uid)
    elonlar = load_elonlar()
    mavjud = [eid for eid in reversed(user.get("korilgan", [])) if eid in elonlar]

    if not mavjud:
        bot.send_message(uid, "👀 Siz hali hech qanday e'lonni ko'rmagansiz. '🔍 Ko'rish/Qidirish' orqali e'lonlarni ko'ring.")
        return

    for eid in mavjud[:15]:
        elon = elonlar[eid]
        matn = elon_matni(eid, elon, tolik=True)
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("❤️ Saqlash", callback_data=f"fav_{eid}"))
        if elon.get("photo"):
            xavfsiz_photo_yuborish(uid, elon["photo"], matn, reply_markup=markup)
        else:
            xavfsiz_yuborish(uid, matn, reply_markup=markup)


# ---- 💬 XARIDORLAR BILAN CHAT (anonim vositachi orqali) ----
@bot.callback_query_handler(func=lambda call: call.data == "hub_xaridor_chat")
def hub_xaridor_chat(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    user_state[uid] = "xarchat_eid_kutish"
    bot.send_message(uid, "💬 Qaysi e'lon egasi bilan bog'lanmoqchisiz? E'lon raqamini kiriting (masalan: 12):")


@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == "xarchat_eid_kutish")
def xarchat_eid_qabul(message):
    uid = message.from_user.id
    eid = message.text.strip()
    elonlar = load_elonlar()
    elon = elonlar.get(eid)
    if not elon:
        bot.send_message(uid, "❌ Bunday e'lon topilmadi. Qaytadan raqam kiriting yoki /start bosing.")
        return
    if elon.get("user_id") == uid:
        user_state.pop(uid, None)
        bot.send_message(uid, "ℹ️ Bu sizning o'z e'loningiz.", reply_markup=get_main_keyboard(uid))
        return
    user_data_temp.setdefault(uid, {})
    user_data_temp[uid]["xarchat_eid"] = eid
    user_data_temp[uid]["xarchat_egasi"] = elon.get("user_id")
    user_state[uid] = "xarchat_matn_kutish"
    bot.send_message(uid, f"✍️ №{eid} e'lon egasiga yubormoqchi bo'lgan xabaringizni yozing:")


@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == "xarchat_matn_kutish")
def xarchat_matn_qabul(message):
    uid = message.from_user.id
    data = user_data_temp.get(uid, {})
    eid = data.get("xarchat_eid")
    egasi_id = data.get("xarchat_egasi")
    user_state.pop(uid, None)
    user_data_temp.pop(uid, None)

    if not eid or not egasi_id:
        bot.send_message(uid, "⚠️ Xatolik yuz berdi.", reply_markup=get_main_keyboard(uid))
        return

    user = get_user(uid)
    matn = (
        f"💬 **Xaridordan yangi xabar (E'lon №{eid})**\n\n"
        f"👤 {md_escape(user.get('name','?'))}\n"
        f"🔗 {md_escape(user.get('tg_username','?'))}\n\n"
        f"✉️ {md_escape(message.text)}"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("↩️ Javob berish", callback_data=f"xarchatreply_{uid}_{eid}"))
    try:
        xavfsiz_yuborish(int(egasi_id), matn, reply_markup=markup)
        bot.send_message(uid, "✅ Xabaringiz e'lon egasiga yuborildi.", reply_markup=get_main_keyboard(uid))
    except Exception as e:
        log.warning(f"Xaridor xabari yuborilmadi: {e}")
        bot.send_message(uid, "❌ Xabar yuborilmadi, e'lon egasi botni bloklagan bo'lishi mumkin.",
                         reply_markup=get_main_keyboard(uid))


@bot.callback_query_handler(func=lambda call: call.data.startswith("xarchatreply_"))
def xarchat_reply_start(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    _, xaridor_id, eid = call.data.split("_")
    user_state[uid] = "xarchat_reply_matn"
    user_data_temp.setdefault(uid, {})
    user_data_temp[uid]["xarchat_reply_maqsad"] = xaridor_id
    user_data_temp[uid]["xarchat_reply_eid"] = eid
    bot.send_message(uid, f"↩️ №{eid} e'lon bo'yicha xaridorga javobingizni yozing:")


@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == "xarchat_reply_matn")
def xarchat_reply_yuborish(message):
    uid = message.from_user.id
    data = user_data_temp.get(uid, {})
    xaridor_id = data.get("xarchat_reply_maqsad")
    eid = data.get("xarchat_reply_eid")
    user_state.pop(uid, None)
    user_data_temp.pop(uid, None)
    if not xaridor_id:
        return
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("↩️ Javob berish", callback_data=f"xarchatreply_{uid}_{eid}"))
    try:
        bot.send_message(int(xaridor_id), f"💬 **E'lon egasining javobi (№{eid}):**\n\n{message.text}",
                         parse_mode="Markdown", reply_markup=markup)
        bot.send_message(uid, "✅ Javobingiz yuborildi.", reply_markup=get_main_keyboard(uid))
    except Exception as e:
        bot.send_message(uid, f"❌ Yuborilmadi: {e}", reply_markup=get_main_keyboard(uid))


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
        types.InlineKeyboardButton("📍 Jonli joylashuv", callback_data="hub_jonli"),
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


# ---- 📍 JONLI JOYLASHUV (yo'lovchi ↔ haydovchi) ----
@bot.callback_query_handler(func=lambda call: call.data == "hub_jonli")
def hub_jonli(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)

    taksilar = load_taksi()
    faol_safar = None
    for tid, t in taksilar.items():
        if t.get("yolovchi_id") == uid and t.get("holat") == "qabul_qilindi":
            faol_safar = (tid, t)
            break

    haydovchilar = load_haydovchilar()
    men_haydovchimi = str(uid) in haydovchilar and haydovchilar[str(uid)].get("holat") == "tasdiqlangan"

    if faol_safar:
        tid, t = faol_safar
        h = haydovchilar.get(str(t.get("haydovchi_id")))
        if h and h.get("last_lat") is not None:
            bot.send_message(uid, f"📍 Haydovchingizning so'nggi ma'lum joylashuvi (safar №{tid}):")
            bot.send_location(uid, h["last_lat"], h["last_lon"])
        else:
            bot.send_message(uid, "😕 Haydovchi hali joylashuvini yubormagan. Birozdan so'ng qayta urinib ko'ring.")
        return

    if men_haydovchimi:
        user_state[uid] = "haydovchi_lokatsiya_yangilash"
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(types.KeyboardButton("📍 Joriy joylashuvni yuborish", request_location=True))
        bot.send_message(
            uid,
            "📍 Joriy joylashuvingizni yuboring — yo'lovchilaringiz uni jonli holatda ko'rishlari uchun yangilanadi:",
            reply_markup=markup
        )
        return

    bot.send_message(uid, "📍 Hozircha sizda faol taksi safari yo'q. Taksi chaqirgach yoki haydovchi sifatida "
                          "onlayn bo'lgach, jonli joylashuvdan foydalanishingiz mumkin bo'ladi.")


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
    )
    bot.send_message(uid, "🤖 **AI bo'limi** — nima qilishni xohlaysiz?", parse_mode="Markdown", reply_markup=markup)


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
    bot.send_message(uid, "Yana nima qilamiz?", reply_markup=get_main_keyboard(uid))


# ---- 🖼️ RASM YARATISH (Gemini/Imagen orqali) ----
@bot.callback_query_handler(func=lambda call: call.data == "hub_ai_rasm")
def hub_ai_rasm_start(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    user_state[uid] = "ai_rasm_kutish"
    bot.send_message(uid, "🖼️ Qanday rasm chizishimni xohlaysiz? Tasvirlab yozing (masalan: 'Tog' fonida quyosh botishi, rangdor uslubda'):")


@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == "ai_rasm_kutish")
def ai_rasm_yaratish(message):
    uid = message.from_user.id
    user_state.pop(uid, None)
    if not ai_client:
        bot.send_message(uid, "❌ Gemini AI hozircha sozlanmagan (API kalit yo'q).", reply_markup=get_main_keyboard(uid))
        return

    sent_msg = bot.send_message(uid, "🎨 Rasm chizilmoqda, biroz kuting...")
    rasm_yoli = os.path.join(PDF_TMP_DIR, f"rasm_{uid}_{int(time.time())}.png")
    muvaffaqiyat = False
    try:
        # Imagen model orqali rasm generatsiyasi
        natija = ai_client.models.generate_images(
            model='imagen-4.0-generate-001',
            prompt=message.text,
            config={"number_of_images": 1}
        )
        if natija.generated_images:
            rasm_baytlari = natija.generated_images[0].image.image_bytes
            with open(rasm_yoli, "wb") as f:
                f.write(rasm_baytlari)
            muvaffaqiyat = True
    except Exception as e:
        log.warning(f"Imagen orqali rasm chizib bo'lmadi, Gemini rasm modeliga urinilmoqda: {e}")
        try:
            natija = ai_client.models.generate_content(
                model='gemini-2.5-flash-image',
                contents=message.text,
            )
            for qism in natija.candidates[0].content.parts:
                if getattr(qism, "inline_data", None) is not None:
                    with open(rasm_yoli, "wb") as f:
                        f.write(qism.inline_data.data)
                    muvaffaqiyat = True
                    break
        except Exception as e2:
            log.error(f"Rasm generatsiyasida xatolik: {e2}")

    try:
        bot.delete_message(uid, sent_msg.message_id)
    except Exception:
        pass

    if muvaffaqiyat and os.path.exists(rasm_yoli):
        with open(rasm_yoli, "rb") as f:
            bot.send_photo(uid, f, caption="🖼️ Tayyor! Yana boshqa rasm kerak bo'lsa, qaytadan so'rang.")
    else:
        bot.send_message(uid, "❌ Kechirasiz, hozircha rasm generatsiya qilib bo'lmadi. "
                              "Birozdan so'ng qayta urinib ko'ring yoki so'rovni boshqacharoq yozing.")
    bot.send_message(uid, "Yana nima qilamiz?", reply_markup=get_main_keyboard(uid))


# ============================================================
#  💰 PUL VA PREMIUM BO'LIMI (hub)
# ============================================================
@bot.message_handler(func=lambda m: m.text == "💰 Pul va Premium")
def hub_pul(message):
    if check_ban(message): return
    uid = message.from_user.id
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("💳 Hamyonim", callback_data="hub_hamyon"),
        types.InlineKeyboardButton("💎 Premium sotib olish", callback_data="hub_premium"),
        types.InlineKeyboardButton("🎁 Promo kod", callback_data="hub_promo"),
        types.InlineKeyboardButton("📜 To'lovlar tarixi", callback_data="hub_tolov_tarix"),
        types.InlineKeyboardButton("💸 Hisobni to'ldirish", callback_data="hub_hisob_toldir"),
        types.InlineKeyboardButton("💵 Pul yechish", callback_data="hub_pul_yech"),
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
        f"💰 Balans: {som_format(user.get('balance', 0))}\n\n"
        f"👉 '💸 Hisobni to'ldirish' orqali balansingizni to'ldirishingiz, "
        f"'💵 Pul yechish' orqali esa mavjud mablag'ni yechib olishingiz mumkin."
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


# ---- 💸 HISOBNI TO'LDIRISH ----
HISOB_TOLDIRISH_KARTA = "8600 1234 5678 9012 (F.I.SH: ADMIN)"


@bot.callback_query_handler(func=lambda call: call.data == "hub_hisob_toldir")
def hub_hisob_toldir_start(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    user_state[uid] = "hisob_toldir_miqdor"
    bot.send_message(
        uid,
        "💸 **Hisobni to'ldirish**\n\n"
        "Qancha miqdorda to'ldirmoqchisiz? Faqat son kiriting (masalan: 50000):",
        parse_mode="Markdown"
    )


@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == "hisob_toldir_miqdor")
def hisob_toldir_miqdor_qabul(message):
    uid = message.from_user.id
    matn = message.text.strip().replace(" ", "").replace("so'm", "")
    if not matn.isdigit() or int(matn) <= 0:
        bot.send_message(uid, "❌ Iltimos, faqat musbat son kiriting (masalan: 50000):")
        return
    miqdor = int(matn)
    user_data_temp.setdefault(uid, {})
    user_data_temp[uid]["toldir_miqdor"] = miqdor
    user_state[uid] = "hisob_toldir_chek"

    bot.send_message(
        uid,
        f"💳 **{som_format(miqdor)}** miqdorida quyidagi kartaga to'lov qiling:\n\n"
        f"`{HISOB_TOLDIRISH_KARTA}`\n\n"
        f"✅ To'lovni amalga oshirgach, chek/skrinshot rasmini shu yerga yuboring "
        f"(yoki agar rasm bo'lmasa, oddiy matn bilan tasdiqlab yozing):",
        parse_mode="Markdown"
    )


@bot.message_handler(content_types=["photo", "text"],
                     func=lambda m: user_state.get(m.from_user.id) == "hisob_toldir_chek")
def hisob_toldir_chek_qabul(message):
    uid = message.from_user.id
    data = user_data_temp.get(uid, {})
    miqdor = data.get("toldir_miqdor")
    user_state.pop(uid, None)
    user_data_temp.pop(uid, None)
    if not miqdor:
        bot.send_message(uid, "⚠️ Xatolik yuz berdi, qaytadan urinib ko'ring.", reply_markup=get_main_keyboard(uid))
        return

    user = get_user(uid)
    sid = yangi_sorov_id()
    sorovlar = load_sorovlar()
    sorovlar[sid] = {
        "turi": "topup",
        "user_id": uid,
        "ism": user.get("name", ""),
        "miqdor": miqdor,
        "holat": "kutilmoqda",
        "sana": datetime.now().strftime("%d.%m.%Y %H:%M"),
    }
    save_sorovlar(sorovlar)

    admin_matn = (
        f"💸 **YANGI HISOB TO'LDIRISH SO'ROVI №{sid}**\n\n"
        f"👤 {md_escape(user.get('name',''))} (`{uid}`)\n"
        f"💰 Miqdor: {som_format(miqdor)}"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"sorovok_{sid}"),
        types.InlineKeyboardButton("❌ Rad etish", callback_data=f"sorovrad_{sid}"),
    )
    try:
        if message.content_type == "photo":
            bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=admin_matn, reply_markup=markup)
        else:
            xavfsiz_yuborish(ADMIN_ID, admin_matn, reply_markup=markup)
    except Exception as e:
        log.error(f"Admin ga topup so'rovi yuborilmadi: {e}")

    bot.send_message(
        uid,
        f"✅ So'rovingiz qabul qilindi! 🆔 №{sid}\nAdmin tekshirgach, balansingiz {som_format(miqdor)} ga to'ldiriladi.",
        reply_markup=get_main_keyboard(uid)
    )


# ---- 💵 PUL YECHISH ----
@bot.callback_query_handler(func=lambda call: call.data == "hub_pul_yech")
def hub_pul_yech_start(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    user = get_user(uid)
    if user.get("balance", 0) <= 0:
        bot.send_message(uid, "❌ Hamyoningizda yechib olish uchun mablag' yo'q.")
        return
    user_state[uid] = "pul_yech_miqdor"
    bot.send_message(
        uid,
        f"💵 **Pul yechish**\n\nJoriy balansingiz: {som_format(user.get('balance', 0))}\n\n"
        f"Qancha miqdorni yechmoqchisiz? (faqat son, masalan: 20000):",
        parse_mode="Markdown"
    )


@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == "pul_yech_miqdor")
def pul_yech_miqdor_qabul(message):
    uid = message.from_user.id
    user = get_user(uid)
    matn = message.text.strip().replace(" ", "").replace("so'm", "")
    if not matn.isdigit() or int(matn) <= 0:
        bot.send_message(uid, "❌ Iltimos, faqat musbat son kiriting:")
        return
    miqdor = int(matn)
    if miqdor > user.get("balance", 0):
        bot.send_message(uid, f"❌ Balansingizda yetarli mablag' yo'q (mavjud: {som_format(user.get('balance', 0))}). Qaytadan kiriting:")
        return
    user_data_temp.setdefault(uid, {})
    user_data_temp[uid]["yech_miqdor"] = miqdor
    user_state[uid] = "pul_yech_karta"
    bot.send_message(uid, "💳 Pul o'tkaziladigan karta raqamingizni kiriting (masalan: 8600 1234 5678 9012):")


@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == "pul_yech_karta")
def pul_yech_karta_qabul(message):
    uid = message.from_user.id
    data = user_data_temp.get(uid, {})
    miqdor = data.get("yech_miqdor")
    user_state.pop(uid, None)
    user_data_temp.pop(uid, None)
    if not miqdor:
        bot.send_message(uid, "⚠️ Xatolik yuz berdi.", reply_markup=get_main_keyboard(uid))
        return

    user = get_user(uid)
    sid = yangi_sorov_id()
    sorovlar = load_sorovlar()
    sorovlar[sid] = {
        "turi": "withdraw",
        "user_id": uid,
        "ism": user.get("name", ""),
        "miqdor": miqdor,
        "karta": message.text.strip(),
        "holat": "kutilmoqda",
        "sana": datetime.now().strftime("%d.%m.%Y %H:%M"),
    }
    save_sorovlar(sorovlar)

    admin_matn = (
        f"💵 **YANGI PUL YECHISH SO'ROVI №{sid}**\n\n"
        f"👤 {md_escape(user.get('name',''))} (`{uid}`)\n"
        f"💰 Miqdor: {som_format(miqdor)}\n"
        f"💳 Karta: {md_escape(message.text.strip())}"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"sorovok_{sid}"),
        types.InlineKeyboardButton("❌ Rad etish", callback_data=f"sorovrad_{sid}"),
    )
    xavfsiz_yuborish(ADMIN_ID, admin_matn, reply_markup=markup)

    bot.send_message(
        uid,
        f"✅ So'rovingiz qabul qilindi! 🆔 №{sid}\nAdmin tasdiqlagach, {som_format(miqdor)} kartangizga o'tkaziladi.",
        reply_markup=get_main_keyboard(uid)
    )


# ---- ADMIN: SO'ROVNI TASDIQLASH / RAD ETISH ----
@bot.callback_query_handler(func=lambda call: call.data.startswith("sorovok_") or call.data.startswith("sorovrad_"))
def sorov_admin_qaror(call):
    if call.from_user.id != ADMIN_ID: return
    bot.answer_callback_query(call.id)
    tasdiqlanmoqda = call.data.startswith("sorovok_")
    sid = call.data.replace("sorovok_", "").replace("sorovrad_", "")

    sorovlar = load_sorovlar()
    s = sorovlar.get(sid)
    if not s:
        bot.send_message(ADMIN_ID, "❌ So'rov topilmadi.")
        return
    if s.get("holat") != "kutilmoqda":
        bot.send_message(ADMIN_ID, "ℹ️ Bu so'rov allaqachon ko'rib chiqilgan.")
        return

    foydalanuvchi_id = s["user_id"]
    miqdor = s["miqdor"]
    user = get_user(foydalanuvchi_id)

    if tasdiqlanmoqda:
        if s["turi"] == "topup":
            user["balance"] = user.get("balance", 0) + miqdor
            izoh = f"Hisob to'ldirish (so'rov №{sid})"
            miqdor_belgi = miqdor
            xabar = f"✅ Sizning {som_format(miqdor)} miqdoridagi hisob to'ldirish so'rovingiz tasdiqlandi!"
        else:
            if miqdor > user.get("balance", 0):
                bot.send_message(ADMIN_ID, "❌ Foydalanuvchi balansi yetarli emas, so'rov tasdiqlanmadi.")
                return
            user["balance"] = user.get("balance", 0) - miqdor
            izoh = f"Pul yechish (so'rov №{sid})"
            miqdor_belgi = -miqdor
            xabar = f"✅ Sizning {som_format(miqdor)} miqdoridagi pul yechish so'rovingiz tasdiqlandi va kartangizga o'tkazildi!"
        user.setdefault("balance_tarix", []).append({
            "sana": datetime.now().strftime("%d.%m.%Y %H:%M"), "miqdor": miqdor_belgi, "izoh": izoh
        })
        update_user(foydalanuvchi_id, user)
        s["holat"] = "tasdiqlandi"
    else:
        xabar = f"❌ Afsuski, sizning {som_format(miqdor)} miqdoridagi so'rovingiz rad etildi. Murojaat: @{ADMIN_USERNAME}"
        s["holat"] = "rad etildi"

    sorovlar[sid] = s
    save_sorovlar(sorovlar)

    try:
        bot.send_message(foydalanuvchi_id, xabar)
    except Exception as e:
        log.warning(f"So'rov natijasi yuborilmadi: {e}")

    try:
        yangi_matn = f"{call.message.text or call.message.caption}\n\n📌 Holat: {s['holat'].upper()}"
        if call.message.text:
            bot.edit_message_text(yangi_matn, ADMIN_ID, call.message.message_id)
        else:
            bot.edit_message_caption(yangi_matn, ADMIN_ID, call.message.message_id)
    except Exception:
        pass


# ---- PROMO KOD ----
PROMO_KODLAR = {
    "WELCOME2026": 5000,
    "SALOM10": 3000,
}


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

    miqdor = PROMO_KODLAR[kod]
    user["balance"] = user.get("balance", 0) + miqdor
    user.setdefault("promo_ishlatilgan", []).append(kod)
    user.setdefault("balance_tarix", []).append({
        "sana": datetime.now().strftime("%d.%m.%Y %H:%M"), "miqdor": miqdor, "izoh": f"Promo kod: {kod}"
    })
    update_user(uid, user)
    bot.send_message(uid, f"🎉 Promo kod qabul qilindi! Hamyoningizga {som_format(miqdor)} qo'shildi.",
                     reply_markup=get_main_keyboard(uid))


# ---- 🎁 CASHBACK ----
CASHBACK_FOIZ = 3  # har bir referal orqali kelgan Premium xariddan foiz sifatida balansga qaytariladi


@bot.callback_query_handler(func=lambda call: call.data == "hub_cashback")
def hub_cashback(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    user = get_user(uid)
    jami_cashback = sum(
        t.get("miqdor", 0) for t in user.get("balance_tarix", []) if "Cashback" in t.get("izoh", "")
    )
    matn = (
        f"🎁 **Cashback dasturi**\n\n"
        f"Har safar taklif qilgan do'stingiz Premium yoki VIP e'lon xarid qilsa, "
        f"xarid summasining **{CASHBACK_FOIZ}%** i avtomatik ravishda sizning hamyoningizga qaytariladi.\n\n"
        f"💰 Hozirgacha jami olingan cashback: {som_format(jami_cashback)}\n"
        f"🎁 Taklif qilganlaringiz: {user.get('referral_count', 0)} ta\n\n"
        f"👉 Ko'proq cashback uchun '🎁 Do'st taklif qilish' bo'limidan shaxsiy havolangizni ulashing."
    )
    bot.send_message(uid, matn, parse_mode="Markdown")


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


# ---- 📍 MANZILLARIM ----
def _manzillar_markup(manzillar):
    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, m in enumerate(manzillar):
        markup.add(types.InlineKeyboardButton(f"🗑 {m['nom']}", callback_data=f"manzildel_{i}"))
    markup.add(types.InlineKeyboardButton("➕ Yangi manzil qo'shish", callback_data="manzil_qoshish"))
    return markup


@bot.callback_query_handler(func=lambda call: call.data == "hub_manzillar")
def hub_manzillar(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    user = get_user(uid)
    manzillar = user.get("manzillar", [])
    if not manzillar:
        matn = "📍 Sizda hali saqlangan manzillar yo'q."
    else:
        matn = "📍 **Sizning manzillaringiz:**\n\n" + "\n".join(
            f"• **{md_escape(m['nom'])}** — {md_escape(m['manzil'])}" for m in manzillar
        )
    markup = types.InlineKeyboardMarkup(row_width=1)
    for i, m in enumerate(manzillar):
        markup.add(types.InlineKeyboardButton(f"🗑 {m['nom']}", callback_data=f"manzildel_{i}"))
    markup.add(types.InlineKeyboardButton("➕ Yangi manzil qo'shish", callback_data="manzil_qoshish"))
    bot.send_message(uid, matn, parse_mode="Markdown", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "manzil_qoshish")
def manzil_qoshish_start(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    user_state[uid] = "manzil_nom_kutish"
    bot.send_message(uid, "📝 Manzilga nom bering (masalan: 'Uy', 'Ish joyi'):")


@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == "manzil_nom_kutish")
def manzil_nom_qabul(message):
    uid = message.from_user.id
    user_data_temp.setdefault(uid, {})
    user_data_temp[uid]["manzil_nom"] = message.text.strip()
    user_state[uid] = "manzil_matn_kutish"
    bot.send_message(uid, "📍 Endi aniq manzilni yozing (masalan: 'Chilonzor tumani, 5-kvartal, 12-uy'):")


@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == "manzil_matn_kutish")
def manzil_matn_qabul(message):
    uid = message.from_user.id
    nom = user_data_temp.get(uid, {}).get("manzil_nom", "Manzil")
    user_state.pop(uid, None)
    user_data_temp.pop(uid, None)

    user = get_user(uid)
    user.setdefault("manzillar", []).append({"nom": nom, "manzil": message.text.strip()})
    update_user(uid, user)
    bot.send_message(uid, f"✅ '{nom}' manzili saqlandi!", reply_markup=get_main_keyboard(uid))


@bot.callback_query_handler(func=lambda call: call.data.startswith("manzildel_"))
def manzil_ochirish(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    idx = int(call.data.replace("manzildel_", ""))
    user = get_user(uid)
    manzillar = user.get("manzillar", [])
    if 0 <= idx < len(manzillar):
        ochirilgan = manzillar.pop(idx)
        update_user(uid, user)
        try:
            bot.edit_message_text(f"🗑 '{ochirilgan['nom']}' manzili o'chirildi.", call.message.chat.id, call.message.message_id)
        except Exception:
            bot.send_message(uid, f"🗑 '{ochirilgan['nom']}' manzili o'chirildi.")


# ---- 🔒 XAVFSIZLIK ----
@bot.callback_query_handler(func=lambda call: call.data == "hub_xavfsizlik")
def hub_xavfsizlik(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    user = get_user(uid)
    matn = (
        f"🔒 **Xavfsizlik markazi**\n\n"
        f"🆔 Foydalanuvchi ID: `{uid}`\n"
        f"📞 Tasdiqlangan telefon: {md_escape(user.get('phone','Kiritilmagan'))}\n"
        f"📅 Ro'yxatdan o'tgan sana: {user.get('joined_date','-')}\n\n"
        f"ℹ️ Hisobingiz Telegram akkauntingiz orqali himoyalangan — botga faqat siz o'z "
        f"Telegram akkauntingiz orqali kirishingiz mumkin. Agar Telegram akkauntingizda "
        f"ikki bosqichli tasdiqlash (2FA) yoqilgan bo'lsa, bu botdagi hisobingiz ham qo'shimcha himoyalangan bo'ladi."
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🚫 Shubhali faoliyat haqida xabar berish", callback_data="xavfsizlik_shikoyat"))
    bot.send_message(uid, matn, parse_mode="Markdown", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "xavfsizlik_shikoyat")
def xavfsizlik_shikoyat_start(call):
    uid = call.from_user.id
    bot.answer_callback_query(call.id)
    user_state[uid] = "xavfsizlik_shikoyat_matn"
    bot.send_message(uid, "🚫 Hisobingiz bilan bog'liq shubhali holatni tasvirlab yozing, adminga zudlik bilan yuboriladi:")


@bot.message_handler(func=lambda m: user_state.get(m.from_user.id) == "xavfsizlik_shikoyat_matn")
def xavfsizlik_shikoyat_yuborish(message):
    uid = message.from_user.id
    user_state.pop(uid, None)
    user = get_user(uid)
    matn = (
        f"🚫 **XAVFSIZLIK BO'YICHA MUROJAAT**\n\n"
        f"👤 {md_escape(user.get('name','?'))} (`{uid}`)\n\n"
        f"✉️ {md_escape(message.text)}"
    )
    try:
        xavfsiz_yuborish(ADMIN_ID, matn)
        bot.send_message(uid, "✅ Murojaatingiz adminga yuborildi.", reply_markup=get_main_keyboard(uid))
    except Exception as e:
        log.error(f"Xavfsizlik murojaati yuborilmadi: {e}")
        bot.send_message(uid, "❌ Xabar yuborilmadi, birozdan so'ng qayta urinib ko'ring.", reply_markup=get_main_keyboard(uid))
