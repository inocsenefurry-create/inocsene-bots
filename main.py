import os
import html
import time
import threading
import unicodedata
from datetime import datetime, timedelta, timezone

import telebot
from telebot import types
from flask import Flask

# ───────────── CONFIGURATION ─────────────
TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise SystemExit("BOT_TOKEN manquant dans Render > Environment")

ADMIN_TELEGRAM_ID = os.environ.get("ADMIN_TELEGRAM_ID")

ADMIN_USERNAME = "@Inocsene"
ADMIN_TEL = "+50956466804"
ADMIN_URL_WA = (
    "https://wa.me/50956466804?text="
    "Salut%20Inocsene%20Zero%2C%20je%20souhaite%20effectuer%20une%20commande%20%21"
)

LINE = "━━━━━━━━━━━━━━━━━━━━"

# ───────────── LIENS DU CANAL PRIVÉ ─────────────
LINK_CHANNEL_PRIVATE = "https://t.me/+y3h3gH9IWIg4M2E5"

DEMO_PANEL      = "https://t.me/c/4457015176/2"
DEMO_VPN_AUTO   = "https://t.me/c/4457015176/5"
DEMO_VPN_BUTTON = "https://t.me/c/4457015176/7"

LINK_KEY_NUIT = "https://t.me/InocseneZeroTuto/3"
LINK_KEY_DAYOU = "https://t.me/InocseneZeroTuto/5"

WELCOME_FILES = [
    ("animation", "welcome_animation.mp4"),
    ("photo", "welcome.png"),
    ("photo", "welcome.jpg"),
    ("photo", "welcome.jpeg"),
]
WELCOME_CACHE = {}

USER_COOLDOWN = {}
COOLDOWN_SECONDS = 1.5

# ───────────── OFFRES VPN (SANS BLABLA, PRO) ─────────────
PRODUCTS = {
    "bouton": {
        "emoji": "🛡️",
        "name": "VPN Anti-Ban Pro",
        "ticket_name": "VPN Anti-Ban Pro",
        "price": 250,
        "old_price": 500,
        "code": "1",
        "tuto": "Dayou",
        "demo_link": DEMO_VPN_BUTTON,
    },
    "auto": {
        "emoji": "❄️",
        "name": "VPN Freeze Automatique",
        "ticket_name": "VPN Freeze Automatique",
        "price": 500,
        "old_price": None,
        "code": "0",
        "tuto": "Nuit Cheat All",
        "demo_link": DEMO_VPN_AUTO,
    },
}

# ───────────── PANEL PREMIUM ─────────────
PANEL_TITLE = "INOCSENE ZERO : PANEL VIP"

PANEL_PLANS = {
    "p12":  {"label_fr": "12 jours",           "price": 1450},
    "p30":  {"label_fr": "1 mois",             "price": 2650},
    "p60":  {"label_fr": "2 mois",             "price": 5300},
    "life": {"label_fr": "Permanent (à vie)",  "price": 9000},
}

try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo("America/Port-au-Prince")
except Exception:
    TZ = timezone(timedelta(hours=-5))

def now_local():
    return datetime.now(TZ)

bot = telebot.TeleBot(TOKEN, parse_mode="HTML", threaded=True, num_threads=8)
app = Flask(__name__)

def bold(text):
    out = []
    for c in text:
        if "A" <= c <= "Z":
            out.append(chr(0x1D5D4 + ord(c) - 65))
        elif "a" <= c <= "z":
            out.append(chr(0x1D5EE + ord(c) - 97))
        elif "0" <= c <= "9":
            out.append(chr(0x1D7EC + ord(c) - 48))
        else:
            out.append(c)
    return "".join(out)

def price_text(p):
    if p["old_price"]:
        return f"<s>{p['old_price']} HTG</s> ➡️ <b>{p['price']} HTG</b> 🔥"
    return f"<b>{p['price']} HTG</b>"

def build_welcome(name):
    return (
        "<b>⚡ INOCSENE ZERO • SERVICE OFFICIEL ⚡</b>\n"
        "<b>👑 VIP STORE FREE FIRE 👑</b>\n"
        f"{LINE}\n\n"
        f"Salut <b>{name}</b> ! 👋 Bienvenue sur la plateforme officielle.\n\n"
        "👇 <i>Fais ton choix ci-dessous pour accéder aux démonstrations et commander.</i>"
    )

def build_offer_page(p):
    return (
        f"<b>{p['emoji']} {p['name'].upper()} {p['emoji']}</b>\n"
        f"{LINE}\n\n"
        f"💰 <b>Prix :</b> {price_text(p)}\n\n"
        "🎥 <b>Démonstration vidéo :</b>\n"
        f"👉 <a href=\"{p['demo_link']}\">Regarder la vidéo officielle</a>\n\n"
        f"{LINE}\n"
        "💳 <b>MODES DE PAIEMENT :</b>\n"
        "<b>• Natcash\n• Binance</b>\n\n"
        "📌 <b>CONSIGNES DE PAIEMENT :</b>\n"
        "<b>1️⃣ Clique sur « Continuer l'achat » pour générer ton billet.\n"
        f"2️⃣ Contacte l'administrateur ({ADMIN_USERNAME}) ou WhatsApp ({ADMIN_TEL}).\n"
        "3️⃣ Envoie ton reçu pour recevoir ton accès instantanément.</b>"
    )

def build_panel_catalog():
    prices = "\n".join(
        f"🔹 <b>{pl['price']:,} HTG</b> ({pl['label_fr']}) ✅" for pl in PANEL_PLANS.values()
    )
    return (
        f"<b>👑 {PANEL_TITLE} 👑</b>\n"
        f"{LINE}\n\n"
        f"⚡ <b>TARIFS OFFICIELS :</b>\n\n"
        f"<blockquote>{prices}</blockquote>\n\n"
        "🎥 <b>Démonstration vidéo :</b>\n"
        f"👉 <a href=\"{DEMO_PANEL}\">Regarder la vidéo officielle</a>\n\n"
        f"{LINE}\n"
        "💳 <b>MODES DE PAIEMENT :</b>\n"
        "<b>• Natcash\n• Binance</b>\n\n"
        "📌 <b>CONSIGNES DE PAIEMENT :</b>\n"
        "<b>1️⃣ Sélectionne ta durée ci-dessous pour générer ton billet.\n"
        f"2️⃣ Contacte l'administrateur ({ADMIN_USERNAME}) ou WhatsApp ({ADMIN_TEL}).\n"
        "3️⃣ Envoie ton reçu pour recevoir ton accès instantanément.</b>"
    )

TICKET_TEMPLATE = (
    "<b>🧾 BILLET DE COMMANDE OFFICIEL 🧾</b>\n"
    f"{LINE}\n"
    "<b>⚡ INOCSENE ZERO ⚡</b>\n"
    f"{LINE}\n\n"
    "<blockquote>📋 <b>N° :</b> <code>{order}</code>\n"
    "👤 <b>Client :</b> {name}\n"
    "📅 <b>Date :</b> {date}</blockquote>\n\n"
    f"{LINE}\n"
    "🛡️ <b>Produit :</b> {product}\n"
    f"{LINE}\n\n"
    "<blockquote>💰 <b>Prix :</b> {price} HTG\n"
    "💳 <b>Paiement :</b> Natcash / Binance</blockquote>\n\n"
    f"{LINE}\n"
    "📌 <b>CONSIGNES POUR VALIDER :</b>\n"
    f"<b>1️⃣ Contacte l'admin : {ADMIN_USERNAME} / WhatsApp ({ADMIN_TEL})\n"
    "2️⃣ Envoie ton billet et ton reçu de paiement\n"
    "3️⃣ Tape {code} dans ce chat pour ton tutoriel {tuto} 🎓</b>"
)

TICKET_PANEL_TEMPLATE = (
    "<b>🧾 BILLET DE COMMANDE OFFICIEL 🧾</b>\n"
    f"{LINE}\n"
    "<b>⚡ INOCSENE ZERO ⚡</b>\n"
    f"{LINE}\n\n"
    "<blockquote>📋 <b>N° :</b> <code>{order}</code>\n"
    "👤 <b>Client :</b> {name}\n"
    "📅 <b>Date :</b> {date}</blockquote>\n\n"
    f"{LINE}\n"
    "👑 <b>Produit :</b> {product}\n"
    f"{LINE}\n\n"
    "<blockquote>💰 <b>Prix :</b> {price} HTG\n"
    "💳 <b>Paiement :</b> Natcash / Binance</blockquote>\n\n"
    f"{LINE}\n"
    "📌 <b>CONSIGNES POUR VALIDER :</b>\n"
    f"<b>1️⃣ Contacte l'admin : {ADMIN_USERNAME} / WhatsApp ({ADMIN_TEL})\n"
    "2️⃣ Envoie ton billet et ton reçu de paiement\n"
    "3️⃣ Reçois ton accès panel instantanément 🔑</b>"
)

def main_menu():
    m = types.InlineKeyboardMarkup()
    for code, p in PRODUCTS.items():
        m.row(types.InlineKeyboardButton(f"{p['emoji']} {bold(p['name'])}", callback_data=f"offer_{code}"))
    m.row(types.InlineKeyboardButton(f"🔥 {bold('PANEL VIP PRO')} 🛡️", callback_data="panel"))
    m.row(types.InlineKeyboardButton(f"🟢 {bold('Contacter sur WhatsApp')}", url=ADMIN_URL_WA))
    m.row(types.InlineKeyboardButton(f"📢 {bold('Canal Privé & Démos')}", url=LINK_CHANNEL_PRIVATE))
    return m

def offer_menu(code):
    m = types.InlineKeyboardMarkup()
    m.row(types.InlineKeyboardButton(f"🛒 {bold('CONTINUER L' + chr(39) + 'ACHAT')} ✅", callback_data=f"buy_{code}"))
    m.row(types.InlineKeyboardButton(f"➡️ {bold('Retour au menu')}", callback_data="menu_home"))
    return m

def panel_menu():
    m = types.InlineKeyboardMarkup()
    for code, pl in PANEL_PLANS.items():
        m.row(types.InlineKeyboardButton(
            f"🛒 {bold(pl['label_fr'])} • {pl['price']:,} HTG",
            callback_data=f"pbuy_{code}",
        ))
    m.row(types.InlineKeyboardButton(f"📢 {bold('Canal Privé & Démos')}", url=LINK_CHANNEL_PRIVATE))
    m.row(types.InlineKeyboardButton(f"🟢 {bold('Contacter sur WhatsApp')}", url=ADMIN_URL_WA))
    m.row(types.InlineKeyboardButton(f"➡️ {bold('Retour au menu')}", callback_data="menu_home"))
    return m

def contact_buttons():
    m = types.InlineKeyboardMarkup()
    m.row(types.InlineKeyboardButton(f"🟢 {bold('Contacter sur WhatsApp')}", url=ADMIN_URL_WA))
    m.row(types.InlineKeyboardButton(f"➡️ {bold('Menu principal')}", callback_data="menu_home"))
    return m

def get_name(user):
    first = user.first_name if user else None
    return html.escape(first) if first else "cher client"

def normalize(text):
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return "".join(c for c in text.lower() if c.isalnum())

def is_zero(message):
    return bool(message.text) and normalize(message.text) in {"0", "o", "zero"}

def is_one(message):
    return bool(message.text) and normalize(message.text) in {"1", "un", "one"}

def make_order_number(user_id):
    now = now_local()
    return f"IZ-{now.strftime('%y%m%d')}-{str(user_id)[-4:]}{now.strftime('%H%M')}"

def run_bg(fn, *args):
    threading.Thread(target=fn, args=args, daemon=True).start()

def remove_msg(chat, msg_id):
    try:
        bot.delete_message(chat, msg_id)
    except Exception:
        pass

def send_welcome_media(chat_id, caption):
    if WELCOME_CACHE:
        kind, fid = WELCOME_CACHE["kind"], WELCOME_CACHE["id"]
        try:
            if kind == "animation":
                bot.send_animation(chat_id, fid, caption=caption)
            else:
                bot.send_photo(chat_id, fid, caption=caption)
            return True
        except Exception:
            WELCOME_CACHE.clear()

    base = os.path.dirname(os.path.abspath(__file__))
    for kind, name in WELCOME_FILES:
        path = os.path.join(base, name)
        if not os.path.isfile(path):
            continue
        try:
            with open(path, "rb") as f:
                if kind == "animation":
                    msg = bot.send_animation(chat_id, f, duration=6, width=1280, height=720, caption=caption)
                    media = msg.animation or msg.document
                    fid = media.file_id
                else:
                    msg = bot.send_photo(chat_id, f, caption=caption)
                    fid = msg.photo[-1].file_id
            WELCOME_CACHE.update(kind=kind, id=fid)
            return True
        except Exception:
            continue
    return False

def send_catalog(chat, text, markup):
    try:
        return bot.send_message(chat, text, reply_markup=markup,
                                link_preview_options=types.LinkPreviewOptions(is_disabled=False))
    except Exception:
        try:
            return bot.send_message(chat, text, reply_markup=markup, disable_web_page_preview=False)
        except Exception:
            return bot.send_message(chat, text, reply_markup=markup)

def _notify(user, action):
    try:
        username = f"@{user.username}" if user.username else "Pas de pseudo"
        msg = (
            "🚨 <b>NOTIFICATION INOCSENE ZERO</b> 🚨\n"
            f"👤 <b>Client :</b> {get_name(user)} ({html.escape(username)})\n"
            f"🆔 <b>ID :</b> <code>{user.id}</code>\n"
            f"📌 <b>Action :</b> {html.escape(action)}\n"
            f"⏰ <b>Heure :</b> {now_local().strftime('%d/%m/%Y %H:%M:%S')}"
        )
        bot.send_message(ADMIN_TELEGRAM_ID, msg)
    except Exception:
        pass

def notify_admin(user, action):
    if ADMIN_TELEGRAM_ID:
        run_bg(_notify, user, action)

@bot.message_handler(commands=["start"])
def start(message):
    chat = message.chat.id
    name = get_name(message.from_user)
    notify_admin(message.from_user, "Démarrage du bot (/start)")
    send_welcome_media(chat, f"👑 <b>Bienvenue {name} !</b> 👑")
    bot.send_message(chat, build_welcome(name), reply_markup=main_menu())

@bot.message_handler(func=is_zero)
def send_guide_nuit(message):
    notify_admin(message.from_user, "Demande tutoriel Nuit Cheat All (0)")
    bot.send_message(message.chat.id, "<b>🎬 Tutoriel Nuit Cheat All :</b> " + LINK_KEY_NUIT)

@bot.message_handler(func=is_one)
def send_guide_dayou(message):
    notify_admin(message.from_user, "Demande tutoriel Dayou (1)")
    bot.send_message(message.chat.id, "<b>💎 Tutoriel Dayou :</b> " + LINK_KEY_DAYOU)

@bot.callback_query_handler(func=lambda call: True)
def on_click(call):
    user_id = call.from_user.id
    now = time.time()

    if len(USER_COOLDOWN) > 1000:
        for uid in [u for u, t in USER_COOLDOWN.items() if now - t > 60]:
            USER_COOLDOWN.pop(uid, None)

    if user_id in USER_COOLDOWN and (now - USER_COOLDOWN[user_id]) < COOLDOWN_SECONDS:
        bot.answer_callback_query(call.id, "⚠️ Patiente une seconde...", show_alert=False)
        return

    USER_COOLDOWN[user_id] = now
    bot.answer_callback_query(call.id)

    chat = call.message.chat.id
    msg_id = call.message.message_id
    data = call.data or ""

    if data == "menu_home":
        notify_admin(call.from_user, "Retour au menu principal")
        welcome = build_welcome(get_name(call.from_user))
        if "BILLET DE COMMANDE" in (call.message.text or ""):
            bot.send_message(chat, welcome, reply_markup=main_menu())
        else:
            try:
                bot.edit_message_text(welcome, chat, msg_id, reply_markup=main_menu())
            except Exception:
                bot.send_message(chat, welcome, reply_markup=main_menu())

    elif data == "panel":
        notify_admin(call.from_user, "Consultation Catalogue Panel Premium")
        run_bg(remove_msg, chat, msg_id)
        send_catalog(chat, build_panel_catalog(), panel_menu())

    elif data.startswith("pbuy_"):
        code = data.split("_", 1)[1]
        if code in PANEL_PLANS:
            pl = PANEL_PLANS[code]
            ticket = TICKET_PANEL_TEMPLATE.format(
                order=make_order_number(call.from_user.id),
                name=get_name(call.from_user),
                date=now_local().strftime("%d/%m/%Y à %H:%M (heure d'Haïti)"),
                product=f"Panel VIP ({pl['label_fr']})",
                price=f"{pl['price']:,}",
            )
            notify_admin(call.from_user, f"Billet Panel : {pl['label_fr']} ({pl['price']:,} HTG)")
            try:
                bot.edit_message_text(ticket, chat, msg_id, reply_markup=contact_buttons())
            except Exception:
                bot.send_message(chat, ticket, reply_markup=contact_buttons())

    elif data.startswith("offer_"):
        code = data.split("_", 1)[1]
        if code in PRODUCTS:
            p = PRODUCTS[code]
            notify_admin(call.from_user, f"Consultation offre : {p['name']}")
            run_bg(remove_msg, chat, msg_id)
            send_catalog(chat, build_offer_page(p), offer_menu(code))

    elif data.startswith("buy_"):
        code = data.split("_", 1)[1]
        if code in PRODUCTS:
            p = PRODUCTS[code]
            ticket = TICKET_TEMPLATE.format(
                order=make_order_number(call.from_user.id),
                name=get_name(call.from_user),
                date=now_local().strftime("%d/%m/%Y à %H:%M (heure d'Haïti)"),
                product=p["ticket_name"],
                price=p["price"],
                code=p["code"],
                tuto=p["tuto"],
            )
            notify_admin(call.from_user, f"Billet de commande : {p['name']} ({p['price']} HTG)")
            try:
                bot.edit_message_text(ticket, chat, msg_id, reply_markup=contact_buttons())
            except Exception:
                bot.send_message(chat, ticket, reply_markup=contact_buttons())

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    t = threading.Thread(target=run_flask, daemon=True)
    t.start()
    print("Bot is starting...")
    bot.remove_webhook()
    time.sleep(1)
    bot.infinity_polling(skip_pending=True)
    
