import os
import json
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

ADMIN_TELEGRAM_ID = os.environ.get("ADMIN_TELEGRAM_ID")  # optionnel : notifications

ADMIN_USERNAME = "@Inocsene"   # contact Telegram
ADMIN_TEL = "+50956466804"
ADMIN_URL_WA = (
    "https://wa.me/50956466804?text="
    "Salut%20Inocsene%20Zero%2C%20je%20souhaite%20effectuer%20une%20commande%20VPN%20%21"
)

PAYMENT = "Natcash ou Binance"
LINE = "━━━━━━━━━━━━━━━━━━━━"

# ───────────── LIENS ─────────────
# Canal officiel VIP (vidéos des offres)
LINK_VIP_CHANNEL = "https://t.me/Inocsene_VIP"
DEMO_CHANNEL = "@Inocsene_VIP"

# Canal des tutoriels (envoyés quand le client tape 0 ou 1)
LINK_ACTIVER_NUIT = "https://t.me/InocseneZeroTuto/4"
LINK_KEY_NUIT = "https://t.me/InocseneZeroTuto/3"
LINK_KEY_DAYOU = "https://t.me/InocseneZeroTuto/5"
LINK_CHANNEL_PROOF = "https://t.me/InocseneZeroTuto"   # canal « Tutos & Proofs »

# Vidéo du panel dans le canal VIP
PANEL_DEMO_ID = 2

# Image / animation de bienvenue : fichiers à mettre à côté de main.py sur GitHub
# (le bot prend le premier qu'il trouve ; sans fichier, il envoie seulement le texte)
WELCOME_FILES = [
    ("animation", "welcome_animation.mp4"),
    ("photo", "welcome.png"),
    ("photo", "welcome.jpg"),
    ("photo", "welcome.jpeg"),
]
WELCOME_CACHE = {}

# Anti-spam : dernier clic par utilisateur
USER_COOLDOWN = {}
COOLDOWN_SECONDS = 1.5

# Vidéo de démo envoyée à chaque client (pour la supprimer ensuite)
DEMO_MSG = {}

# Si l'envoi direct de la vidéo échoue, on ne réessaie qu'après 10 minutes
COPY_RETRY_AT = 0.0
COPY_RETRY_DELAY = 600

# Clients déjà venus (pour dire « nouveau client » ou « client de retour »)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SEEN_FILE = os.path.join(BASE_DIR, "seen_users.json")
SEEN = set()

# ───────────── OFFRES VPN ─────────────
PRODUCTS = {
    "bouton": {
        "emoji": "🔰",
        "name": "VPN avec Bouton",
        "ticket_name": "VPN Anti-Ban (avec Bouton)",
        "features": [
            "Protection Anti-Ban maximale",
            "Gameplay fluide et ultra-stable",
            "Application avec boutons intégrés",
            "Installation guidée par vidéo",
        ],
        "price": 250,
        "old_price": 500,
        "code": "1",
        "tuto": "Dayou",
        "demo_id": 7,
        "demo_link": "https://t.me/Inocsene_VIP/7",
    },
    "auto": {
        "emoji": "❄️",
        "name": "VPN Freeze Automatique VIP",
        "ticket_name": "VPN Freeze Automatique VIP (Anti-Ban &amp; Anti-Blacklist)",
        "features": [
            "Protection Anti-Ban &amp; Anti-Blacklist (haute précision)",
            "Système Freeze automatique haute performance",
            "Gameplay fluide et ultra-stable",
            "Idéal pour les longues sessions de jeu",
        ],
        "price": 500,
        "old_price": None,
        "code": "0",
        "tuto": "Nuit Cheat All",
        "demo_id": 5,
        "demo_link": "https://t.me/Inocsene_VIP/5",
    },
}

# ───────────── PANEL PREMIUM ─────────────
PANEL_TITLE = "INNOCENT ZERO : PREMIUM PANEL"

PANEL_PLANS = {
    "p12":  {"label": "12 Days",              "label_fr": "12 jours",           "price": 1450},
    "p30":  {"label": "1 Month",              "label_fr": "1 mois",             "price": 2650},
    "p60":  {"label": "2 Months",             "label_fr": "2 mois",             "price": 5300},
    "life": {"label": "Permanent / Lifetime", "label_fr": "Permanent (à vie)",  "price": 9000},
}

# Fuseau horaire Haïti
try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo("America/Port-au-Prince")
except Exception:
    TZ = timezone(timedelta(hours=-5))

def now_local():
    return datetime.now(TZ)

# 8 clics traités en même temps (réactivité)
bot = telebot.TeleBot(TOKEN, parse_mode="HTML", threaded=True, num_threads=8)

# ───────────── BOUTONS COLORÉS ET EN GRAS ─────────────
# Les boutons prennent une vraie couleur : primary = bleu, success = vert, danger = rouge
# (visible sur les versions récentes de Telegram ; sinon le texte en gras reste lisible)
STYLE_OK = True

class StyledButton(types.InlineKeyboardButton):
    def __init__(self, text, style=None, **kwargs):
        super().__init__(text, **kwargs)
        self.btn_style = style

    def to_dict(self):
        data = super().to_dict()
        if self.btn_style:
            data["style"] = self.btn_style
        return data

def btn(text, style=None, **kwargs):
    if STYLE_OK and style:
        return StyledButton(text, style=style, **kwargs)
    return types.InlineKeyboardButton(text, **kwargs)

def bold(text):
    """Lettres grasses pour le texte des boutons."""
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

# ───────────── TEXTES ─────────────
def price_text(p):
    if p["old_price"]:
        return f"<s>{p['old_price']} HTG</s> ➡️ <b>{p['price']} HTG</b> 🔥"
    return f"<b>{p['price']} HTG</b>"

def build_welcome():
    return (
        "<b>👑 BIENVENUE CHER CLIENT 👑</b>\n"
        f"{LINE}\n\n"
        "Dans le site officiel de <b>INOCSENE ZERO</b> ⚡\n"
        "<b>VIP STORE FREE FIRE</b>\n\n"
        "<blockquote>🚀 <b>Connexion ultra-rapide et stable</b>\n"
        "🛡️ <b>Protection Anti-Ban &amp; Anti-Blacklist</b>\n"
        "🎮 <b>Gameplay fluide pour tes jeux</b></blockquote>\n\n"
        f"{LINE}\n"
        "👇 <i>Fais ton choix ci-dessous pour découvrir nos services.</i>"
    )

def build_offer(p):
    feats = "\n".join(f"✅ <b>{f}</b>" for f in p["features"])
    return (
        f"<b>{p['emoji']} {p['name'].upper()} {p['emoji']}</b>\n"
        f"{LINE}\n\n"
        f"<blockquote>{feats}</blockquote>\n\n"
        f"{LINE}\n"
        f"💰 <b>Prix :</b> {price_text(p)}\n"
        f"💳 <b>Paiement :</b> {PAYMENT}\n"
        f"{LINE}\n\n"
        "📌 <b>CONSIGNES :</b>\n"
        "Tu peux payer l'administrateur par <b>Natcash</b> ou par <b>Binance</b>.\n\n"
        "🛒 <i>Appuie sur « Continuer l'achat » pour commander.</i>"
    )

def build_panel_catalog():
    prices = "\n".join(
        f"🔹 <b>{pl['price']:,} HTG</b> ({pl['label']}) ✅" for pl in PANEL_PLANS.values()
    )
    return (
        "<b>✅ LES PANELS ANTI-BAN SONT DISPONIBLES MAINTENANT !</b>\n\n"
        f"<b>👑 {PANEL_TITLE} 👑</b>\n"
        f"{LINE}\n\n"
        "<blockquote>🟢 <b>Aimbot Vip</b>\n"
        "🟢 <b>Aimsilent</b>\n"
        "🟢 <b>Snipers Aimlock</b>\n"
        "🟢 <b>Speed Run</b>\n"
        "🟢 <b>Esp Player Location</b></blockquote>\n\n"
        "🛡️ <b>MAIN ID SAFE</b> ✅\n"
        "📱 <b>ALL ANDROID MOBILE WORK</b>\n"
        "⚙️ <b>HIDE / STREAMER MODE</b>\n\n"
        f"{LINE}\n"
        "⚡ <b>TARIFS OFFICIELS :</b>\n\n"
        f"<blockquote>{prices}</blockquote>\n\n"
        f"{LINE}\n"
        f"🟢 <b>BUY PANEL</b> ➡️ <b>{ADMIN_USERNAME}</b> 🔴\n"
        f"🟢 <b>BUY PANEL</b> ➡️ <b>WhatsApp {ADMIN_TEL}</b> 🔴\n"
        f"📢 <b>CANAL OFFICIEL</b> ➡️ {LINK_VIP_CHANNEL} 🔴\n\n"
        f"{LINE}\n"
        "📌 <b>CONSIGNES :</b>\n"
        "Tu peux payer l'administrateur par <b>Natcash</b> ou par <b>Binance</b>.\n\n"
        "🛒 <i>Choisis ta durée ci-dessous pour commander.</i>"
    )

TICKET_TEMPLATE = (
    "<b>🧾 BILLET DE COMMANDE OFFICIEL 🧾</b>\n"
    f"{LINE}\n"
    "<b>⚡ INOCSENE ZERO ⚡</b>\n"
    f"{LINE}\n\n"
    "<blockquote>📋 <b>N° de commande :</b> <code>{order}</code>\n"
    "👤 <b>Client :</b> {name}\n"
    "📅 <b>Date :</b> {date}</blockquote>\n\n"
    f"{LINE}\n"
    "🛡️ <b>Produit :</b> {product}\n"
    "✅ Connexion ultra-rapide et stable\n"
    "✅ Protection avancée pour le jeu\n"
    f"{LINE}\n\n"
    "<blockquote>💰 <b>Prix :</b> {price} HTG\n"
    f"💳 <b>Paiement :</b> {PAYMENT}\n"
    "📌 <b>Statut :</b> ⏳ En attente de paiement</blockquote>\n\n"
    f"{LINE}\n"
    "<b>✅ POUR VALIDER LA COMMANDE, CONTACTE L'ADMINISTRATEUR "
    "SUR TELEGRAM OU WHATSAPP 👇</b>\n\n"
    "📌 <b>CONSIGNES :</b>\n"
    f"1️⃣ Pour recevoir ton VPN, contacte l'administrateur sur Telegram : <b>{ADMIN_USERNAME}</b>\n"
    "2️⃣ Envoie-lui ce billet de commande et ton reçu de paiement de <b>{price} HTG</b> "
    "(Natcash ou Binance)\n"
    "3️⃣ Une fois ton VPN reçu, tape <b>{code}</b> dans ce chat "
    "pour débloquer ton tutoriel <b>{tuto}</b> 🎓\n"
    f"{LINE}\n"
    f"📲 <i>Tu peux aussi écrire sur WhatsApp ({ADMIN_TEL}) avec le bouton ci-dessous.</i>\n\n"
    "🙏 <i>Merci de ta confiance !</i>"
)

TICKET_PANEL_TEMPLATE = (
    "<b>🧾 BILLET DE COMMANDE OFFICIEL 🧾</b>\n"
    f"{LINE}\n"
    "<b>⚡ INOCSENE ZERO ⚡</b>\n"
    f"{LINE}\n\n"
    "<blockquote>📋 <b>N° de commande :</b> <code>{order}</code>\n"
    "👤 <b>Client :</b> {name}\n"
    "📅 <b>Date :</b> {date}</blockquote>\n\n"
    f"{LINE}\n"
    "👑 <b>Produit :</b> {product}\n"
    "✅ Accès Premium Panel\n"
    "✅ Mise en place guidée\n"
    f"{LINE}\n\n"
    "<blockquote>💰 <b>Prix :</b> {price} HTG\n"
    f"💳 <b>Paiement :</b> {PAYMENT}\n"
    "📌 <b>Statut :</b> ⏳ En attente de paiement</blockquote>\n\n"
    f"{LINE}\n"
    "<b>✅ POUR VALIDER LA COMMANDE, CONTACTE L'ADMINISTRATEUR "
    "SUR TELEGRAM OU WHATSAPP 👇</b>\n\n"
    "📌 <b>CONSIGNES :</b>\n"
    f"1️⃣ Pour recevoir ton panel, contacte l'administrateur sur Telegram : <b>{ADMIN_USERNAME}</b>\n"
    "2️⃣ Envoie-lui ce billet de commande et ton reçu de paiement de <b>{price} HTG</b> "
    "(Natcash ou Binance)\n"
    "3️⃣ Après vérification du paiement, tu reçois ton accès au panel 🔑\n"
    f"{LINE}\n"
    f"📲 <i>Tu peux aussi écrire sur WhatsApp ({ADMIN_TEL}) avec le bouton ci-dessous.</i>\n\n"
    "🙏 <i>Merci de ta confiance !</i>"
)

SECURITY_WARNING = (
    "⚠️ AVERTISSEMENT DE SÉCURITÉ TRÈS IMPORTANT :\n"
    "Ne clique jamais sur le bouton « Join Telegram » ou sur les liens externes "
    "situés à l'intérieur de l'application VPN.\n"
    "<b>Cela annulera instantanément ta protection Anti-Blacklist et risquera de "
    "compromettre la sécurité de ton compte de jeu.</b>\n\n"
    "🚨 <b>SI UN MESSAGE « UPDATE » (MISE À JOUR) APPARAÎT SUR TON ÉCRAN :</b>\n"
    "Ne clique sur rien et <b>supprime rapidement l'APK</b> de ton téléphone.\n\n"
)

GUIDE_NUIT_CHEAT = (
    "<b>🎬 TUTORIELS NUIT CHEAT ALL - INOCSENE ZERO 🎬</b>\n"
    f"{LINE}\n\n"
    "🔷 Étape 1 : Comment activer le Nuit Cheat All\n"
    f"👉 Regarde cette vidéo : {LINK_ACTIVER_NUIT}\n\n"
    "🔷 Étape 2 : Comment générer la clé (Key)\n"
    f"👉 Regarde cette vidéo : {LINK_KEY_NUIT}\n\n"
    + SECURITY_WARNING +
    f"{LINE}\n"
    "📢 <i>Si un lien pose problème, rejoins directement notre canal officiel :</i>\n"
    f"👉 <b>Inocsene Zero • Tutos &amp; Proofs</b> ({LINK_CHANNEL_PROOF})\n\n"
    "⚡ <b>Bon jeu et profite de ton service Inocsene Zero !</b>"
)

GUIDE_DAYOU = (
    "<b>💎 TUTORIEL DAYOU - INOCSENE ZERO 💎</b>\n"
    f"{LINE}\n\n"
    "🔷 Étape unique : Comment générer la clé (Key) de Dayou\n"
    f"👉 Regarde cette vidéo : {LINK_KEY_DAYOU}\n\n"
    + SECURITY_WARNING +
    f"{LINE}\n"
    "📢 <i>Si un lien pose problème, rejoins directement notre canal officiel :</i>\n"
    f"👉 <b>Inocsene Zero • Tutos &amp; Proofs</b> ({LINK_CHANNEL_PROOF})\n\n"
    "⚡ <b>Bon jeu et profite de ton service Inocsene Zero !</b>"
)

# ───────────── CLAVIERS ─────────────
def main_menu():
    m = types.InlineKeyboardMarkup()
    for code, p in PRODUCTS.items():
        m.row(btn(f"{p['emoji']} {bold(p['name'])}", "primary", callback_data=f"offer_{code}"))
    m.row(btn(f"🔥 {bold('PANEL ANTI-BAN VIP PRO')} 🛡️", "danger", callback_data="panel"))
    m.row(btn(f"🟢 {bold('Contacter sur WhatsApp')}", "success", url=ADMIN_URL_WA))
    m.row(
        btn(f"📢 {bold('Canal VIP')}", "primary", url=LINK_VIP_CHANNEL),
        btn(f"✅ {bold('Proofs & Tutos')}", "primary", url=LINK_CHANNEL_PROOF),
    )
    return m

def offer_menu(code):
    m = types.InlineKeyboardMarkup()
    m.row(btn(f"🛒 {bold('CONTINUER L' + chr(39) + 'ACHAT')} ✅", "success", callback_data=f"buy_{code}"))
    m.row(btn(f"➡️ {bold('Menu principal')}", "primary", callback_data="menu_home"))
    return m

def panel_menu():
    m = types.InlineKeyboardMarkup()
    for code, pl in PANEL_PLANS.items():
        m.row(btn(
            f"🛒 {bold(pl['label_fr'])} • {pl['price']:,} HTG",
            "success",
            callback_data=f"pbuy_{code}",
        ))
    m.row(btn(f"📢 {bold('Canal officiel')}", "primary", url=LINK_VIP_CHANNEL))
    m.row(btn(f"🟢 {bold('Contacter sur WhatsApp')}", "success", url=ADMIN_URL_WA))
    m.row(btn(f"➡️ {bold('Menu principal')}", "primary", callback_data="menu_home"))
    return m

def contact_buttons():
    m = types.InlineKeyboardMarkup()
    m.row(btn(f"🟢 {bold('Contacter sur WhatsApp')}", "success", url=ADMIN_URL_WA))
    m.row(btn(f"➡️ {bold('Menu principal')}", "primary", callback_data="menu_home"))
    return m

# ───────────── OUTILS ─────────────
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
    """Tâche en arrière-plan pour ne pas ralentir la réponse au client."""
    threading.Thread(target=fn, args=args, daemon=True).start()

# ----- envoi / modification de messages (avec retour sans couleur si Telegram refuse) -----
def send(chat, text, markup_fn=None, **kwargs):
    global STYLE_OK
    try:
        return bot.send_message(chat, text, reply_markup=(markup_fn() if markup_fn else None), **kwargs)
    except Exception as e:
        err = str(e).lower()
        if STYLE_OK and markup_fn and ("button" in err or "style" in err):
            STYLE_OK = False   # Telegram refuse les couleurs : on continue sans
            return bot.send_message(chat, text, reply_markup=markup_fn(), **kwargs)
        raise

def edit(chat, msg_id, text, markup_fn=None):
    """Remplace le contenu d'une page ; si impossible, envoie une nouvelle page."""
    try:
        bot.edit_message_text(text, chat, msg_id, reply_markup=(markup_fn() if markup_fn else None))
    except Exception as e:
        if "not modified" in str(e).lower():
            return
        send(chat, text, markup_fn)

def remove_msg(chat, msg_id):
    try:
        bot.delete_message(chat, msg_id)
    except Exception:
        pass

def send_catalog(chat, text, markup_fn):
    """Envoie le catalogue sans aperçu de lien."""
    try:
        return send(chat, text, markup_fn, link_preview_options=types.LinkPreviewOptions(is_disabled=True))
    except Exception:
        try:
            return send(chat, text, markup_fn, disable_web_page_preview=True)
        except Exception:
            return send(chat, text, markup_fn)

def send_welcome_media(chat_id, caption):
    """Envoie l'image ou l'animation de bienvenue (si un fichier est présent)."""
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

    for kind, name in WELCOME_FILES:
        path = os.path.join(BASE_DIR, name)
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

def send_demo(chat_id, p):
    """Vidéo de l'offre en premier : vidéo directe si possible, sinon lien avec aperçu."""
    global COPY_RETRY_AT
    sent = None
    if time.time() >= COPY_RETRY_AT:
        try:
            sent = bot.copy_message(chat_id, DEMO_CHANNEL, p["demo_id"])
        except Exception:
            COPY_RETRY_AT = time.time() + COPY_RETRY_DELAY
    if sent is None:
        try:
            sent = bot.send_message(chat_id, f"🎬 <b>Démonstration en vidéo</b>\n👉 {p['demo_link']}")
        except Exception:
            pass
    if sent is not None:
        if len(DEMO_MSG) > 1000:
            DEMO_MSG.clear()
        DEMO_MSG[chat_id] = sent.message_id

def clear_demo(chat_id):
    """Retire l'ancienne vidéo (suppression en arrière-plan)."""
    mid = DEMO_MSG.pop(chat_id, None)
    if mid:
        run_bg(remove_msg, chat_id, mid)

# ----- notifications pour l'administrateur -----
def load_seen():
    try:
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            SEEN.update(json.load(f))
    except Exception:
        pass

def save_seen():
    try:
        with open(SEEN_FILE, "w", encoding="utf-8") as f:
            json.dump(sorted(SEEN), f)
    except Exception:
        pass

def is_new_user(user_id):
    if user_id in SEEN:
        return False
    SEEN.add(user_id)
    run_bg(save_seen)
    return True

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
    """Notification admin envoyée en arrière-plan."""
    if ADMIN_TELEGRAM_ID:
        run_bg(_notify, user, action)

load_seen()

# ───────────── HANDLERS ─────────────
@bot.message_handler(commands=["start"])
def start(message):
    chat = message.chat.id
    user = message.from_user
    tag = "🆕 Nouveau client" if is_new_user(user.id) else "🔁 Client de retour"
    notify_admin(user, f"{tag} : démarrage du bot (/start)")
    clear_demo(chat)
    send_welcome_media(chat, "<b>👑 INOCSENE ZERO • OFFICIEL 👑</b>")   # 1) image / animation (si présente)
    send(chat, build_welcome(), main_menu)                              # 2) bienvenue + boutons

@bot.message_handler(func=is_zero)
def send_guide_nuit(message):
    notify_admin(message.from_user, "Demande tutoriel Nuit Cheat All (0)")
    bot.send_message(message.chat.id, GUIDE_NUIT_CHEAT)

@bot.message_handler(func=is_one)
def send_guide_dayou(message):
    notify_admin(message.from_user, "Demande tutoriel Dayou (1)")
    bot.send_message(message.chat.id, GUIDE_DAYOU)

@bot.message_handler(content_types=["text"])
def any_text(message):
    """Le client n'a pas de réponse, mais tu es prévenu de ce qu'il écrit."""
    user = message.bot.infinity_polling(skip_pending=True)
