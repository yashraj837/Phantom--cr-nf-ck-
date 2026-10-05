#!/usr/bin/env python3
# ╔══════════════════════════════════════════════════════════════╗
# ║          𝐏 ʜ ᴀ ɴ ᴛ ᴏ ᴍ  —  ɴ ꜰ  &  ᴄ ʀ  ʙ ᴏ ᴛ              ║
# ║   aiogram 3.31 · Bot API 10.3 · Rich Messages · Pillow       ║
# ╚══════════════════════════════════════════════════════════════╝

# ═══════════════════════════════════════════════════════════════
#  IMPORTS
# ═══════════════════════════════════════════════════════════════
import asyncio, gc, hashlib, io, json, logging, math, os
import random, re, secrets, time, zlib, urllib.parse
from typing import Optional, Any, Callable, Awaitable
from functools import wraps
from io import BytesIO

import aiohttp
from aiohttp import web
import cloudscraper
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from cryptography.fernet import Fernet
import motor.motor_asyncio
from motor.motor_asyncio import AsyncIOMotorClient   # ← ADD THIS
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import requests

from aiogram import Bot, Dispatcher, Router, F, BaseMiddleware
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.mongo import MongoStorage
from aiogram.types import TelegramObject
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
import aiogram.types as tg_types

# Rich Message imports — Bot API 10.1–10.3
from aiogram.types import (
    InputRichMessage,
    InputRichBlockSectionHeading,
    InputRichBlockParagraph,
    InputRichBlockDivider,
    InputRichBlockTable,
    InputRichBlockList,
    InputRichBlockListItem,
    InputRichBlockBlockQuotation,
    InputRichBlockExpandableBlockQuotation,
    InputRichBlockPreformatted,
    InputRichBlockPhoto,
    InputRichBlockButtons,
    InputRichBlockFooter,
    InputRichBlockDetails,
    RichTextBold,
    RichTextItalic,
    RichTextCode,
    RichTextCustomEmoji,
    RichTextUnderline,
    RichTextStrikethrough,
    RichTextSpoiler,
    RichTextMarked,
    RichTextUrl,
    RichTextBotCommand,
    RichTextSubscript,
    RichTextSuperscript,
    RichBlockTableCell,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("phantom")

# ═══════════════════════════════════════════════════════════════
#  CONFIG — ENV VARS
# ═══════════════════════════════════════════════════════════════
BOT_TOKEN         = os.environ.get("BOT_TOKEN", "8614516233:AAFeQoEBkbNUzIsIvTpWjT_CDiou-x5Ed2I")
MONGO_URI         = os.environ.get("MONGO_URI", "mongodb+srv://Esh-pro:p5wCQeb32BUzU8Ip@cluster0.uh9j9d7.mongodb.net/?appName=Cluster0")
RENDER_APP_NAME   = os.environ.get("RENDER_APP_NAME", "")
PORT              = int(os.environ.get("PORT", 8081))
_fk               = os.environ.get("FERNET_KEY")
FERNET_KEY        = _fk.encode() if _fk else Fernet.generate_key()
OWNER_ID          = int(os.environ.get("OWNER_ID", 8189708860))
WEBHOOK_SECRET    = os.environ.get("WEBHOOK_SECRET", secrets.token_hex(16))
_aids             = os.environ.get("ADMIN_IDS", "8189708860")
ADMIN_IDS: set[int] = {int(x) for x in _aids.split(",") if x.strip().isdigit()}
ADMIN_IDS.add(OWNER_ID)
WEBHOOK_URL       = os.environ.get("WEBHOOK_URL", f"https://{RENDER_APP_NAME}.onrender.com/webhook" if RENDER_APP_NAME else "")
DB_NAME           = "phantombot"
POLLINATIONS_BASE = "https://image.pollinations.ai/prompt/{prompt}?width=1280&height=720&nologo=true&model=flux&seed={seed}"
# Semaphores — RAM guard (512MB Render free tier)
NF_SEM     = asyncio.Semaphore(4)
CR_SEM     = asyncio.Semaphore(3)
PHONE_SEM  = asyncio.Semaphore(2)
COOKIE_SEM = asyncio.Semaphore(8)

TV_CODE_RE = re.compile(r"^[A-Za-z0-9]{4,8}$")

# ═══════════════════════════════════════════════════════════════
#  PLANS
# ═══════════════════════════════════════════════════════════════
PLANS = {
    "free":  {"daily": 2,  "methods": ["tv","login"],               "priority": 0, "badge": "ꜰʀᴇᴇ",  "color": "⬜"},
    "core":  {"daily": 10, "methods": ["tv","login","phone"],        "priority": 1, "badge": "ᴄᴏʀᴇ",  "color": "🟦"},
    "elite": {"daily": 20, "methods": ["tv","login","phone","pc"],   "priority": 2, "badge": "ᴇʟɪᴛᴇ", "color": "🟪"},
    "root":  {"daily": 30, "methods": ["tv","login","phone","pc"],   "priority": 3, "badge": "ʀᴏᴏᴛ",  "color": "🟥"},
}

# ═══════════════════════════════════════════════════════════════
#  PREMIUM EMOJI IDS  (NO plain emojis anywhere in bot text)
# ═══════════════════════════════════════════════════════════════
M_EMOJI = {
    # status
    "check":      "6298612102709909362",
    "cross":      "5440681540541502133",
    "bolt":       "6026367225466720832",
    "star":       "5104966345267610825",
    "warn":       "5407025283456606479",
    "lock":       "5472055112702629499",
    "unlock":     "5471952986970267163",
    "fire":       "5407025283456606479",
    "gem":        "6098804790398889129",
    "crown":      "6098804790398889129",
    "shield":     "5471952986970267163",
    "check2":     "5206607081334906820",
    # navigation
    "arrow":      "6001440193058444284",
    "back":       "5904671680891539456",
    "menu":       "5841441419790484972",
    "next":       "5904671680891539456",
    "up":         "5948491699729898636",
    "down":       "5948491956814923271",
    # services
    "netflix":    "5116175844837950263",
    "cr":         "5174748216524014435",
    "phone":      "5104966345267610825",
    "pc":         "5116590266232341370",
    "tv":         "5188488717480202251",
    "login":      "5471952986970267163",
    # user
    "user":       "5373141891321699086",
    "users":      "5373141891321699086",
    "id":         "5471952986970267163",
    "admin":      "5472055112702629499",
    "owner":      "6098804790398889129",
    "ban":        "5440681540541502133",
    # features
    "key":        "6001440193058444284",
    "gift":       "5453902265922376743",
    "refer":      "5373141891321699086",
    "trial":      "5104966345267610825",
    "history":    "5841441419790484972",
    "settings":   "5471952986970267163",
    "bell":       "5453902265922376743",
    "info":       "6026367225466720832",
    "time":       "5948491699729898636",
    "chart":      "5841441419790484972",
    "link":       "5472055112702629499",
    "media":      "5188488717480202251",
    "wrench":     "5471952986970267163",
    "search":     "5373141891321699086",
    "copy":       "6001440193058444284",
    "trash":      "5440681540541502133",
    "upload":     "6026367225466720832",
    "download":   "5104966345267610825",
    "refresh":    "5948491956814923271",
    "broadcast":  "5453902265922376743",
    "plan":       "6098804790398889129",
    "cookie":     "5188488717480202251",
    "account":    "5373141891321699086",
    "proxy":      "5472055112702629499",
    "stats":      "5841441419790484972",
    "audit":      "5841441419790484972",
    "backup":     "5471952986970267163",
    "alert":      "5453902265922376743",
    "cleanup":    "5440681540541502133",
    "sakura":     "5104966345267610825",
    "moon":       "5948491699729898636",
    "wave":       "5948491956814923271",
    "crystal":    "6098804790398889129",
    "magic":      "5453902265922376743",
}

RANDOM_BUTTON_EMOJI_IDS = [
    "6001440193058444284","6026367225466720832","5104966345267610825",
    "5116175844837950263","5174748216524014435","5116590266232341370",
    "5188488717480202251","5471952986970267163","5472055112702629499",
    "5373141891321699086","5841441419790484972","5948491699729898636",
    "5948491956814923271","6098804790398889129","5453902265922376743",
    "5440681540541502133","5407025283456606479","5206607081334906820",
    "5298612102709909362","6127426554849929217",
    "5222136736136753494","5373141891321699086","6001440193058444284",
    "5472164496311726781","5467890235691741200","5465665476971471368",
    "5282699544952782230","5377288716158927474","5374366625665505622",
    "5420323339723800738","5440681540541502133","5449235201388090376",
    "5451882682551827774","5456194979920923119","5458308118498461793",
    "5461494004557964463","5463116009568669671","5465228956730126388",
    "5465553393566069824","5466644736009408519","5467044602448049168",
    "5467352019827566965","5467580415555022871","5467861667225547819",
    "5468432386729577613","5468647541323906654",
    "5222136736136753494","5244789596305455527","6282112395940484254",
    "6282112395940484254","5471723860490506219","5472055112702629499",
    "5472164496311726781","5388468004548460546","5395217649218799018",
    "5402468983765589476","5407025283456606479","5411001474512396569",
    "5414590019588993679","5415928765215038467","5418119398040568907",
    "5420323339723800738","5421528745793024068","5434043434834030501",
    "5435394728987218744","5436603001572388997",
    "6322756827137049862","5267932176944799421","5282699544952782230",
    "5376003396814213888","5294634943984926668","5309880403017069764",
    "5316827918426572860","5318855754838956232","5322154744978726108",
    "5328803501294041163","5334549459999917100",
    "5336162662272866338",
    "5104966345267610825","5373141891321699086","5453902265922376743",
]
# Clean the list — keep only digit-only IDs
RANDOM_BUTTON_EMOJI_IDS = [
    x for x in RANDOM_BUTTON_EMOJI_IDS if x.isdigit()
]

def e(key: str, fb: str = "·") -> str:
    eid = M_EMOJI.get(key)
    if not eid: return fb
    return f'<tg-emoji emoji-id="{eid}">{fb}</tg-emoji>'

def rb() -> str:
    return random.choice(RANDOM_BUTTON_EMOJI_IDS)

def rt_emoji(key: str) -> RichTextCustomEmoji:
    eid = M_EMOJI.get(key, M_EMOJI["star"])
    return RichTextCustomEmoji(custom_emoji_id=eid, text="·")

# ═══════════════════════════════════════════════════════════════
#  FONT HELPERS
# ═══════════════════════════════════════════════════════════════
_SC_MAP = str.maketrans(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴩQʀꜱᴛᴜᴠᴡxʏᴢᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴩQʀꜱᴛᴜᴠᴡxʏᴢ"
)
def sc(s: str) -> str:
    return s.translate(_SC_MAP)

def spaced(s: str) -> str:
    return " ".join(s)

# ═══════════════════════════════════════════════════════════════
#  SEPARATORS
# ═══════════════════════════════════════════════════════════════
DIV   = "━━━━━━━━━━━━━━━━━━━━━━━━"
SDIV  = "· · ─────────────── · ·"
BDIV  = "◈━━━━━━━━━━━━━━━━━━━━━━◈"
LDIV  = "⬥────────────────────⬥"
NDIV  = "╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌"
DDIV  = "· · · · · · · · · · · ·"

# ═══════════════════════════════════════════════════════════════
#  CRYPTO
# ═══════════════════════════════════════════════════════════════
_fernet = Fernet(FERNET_KEY)

def _encrypt(data: str) -> str:
    return _fernet.encrypt(zlib.compress(data.encode())).decode()

def _decrypt(token: str) -> str:
    return zlib.decompress(_fernet.decrypt(token.encode())).decode()

# ═══════════════════════════════════════════════════════════════
#  POLLINATIONS + PILLOW  — Anime image generator
# ═══════════════════════════════════════════════════════════════
ANIME_PROMPTS = {
    "main":    "stunning anime girl cherry blossom sakura garden night glowing paper lanterns soft purple pink light cinematic 4k masterpiece",
    "netflix": "anime girl sitting watching glowing TV neon purple blue dark room aesthetic japanese night city rain window reflection cinematic",
    "cr":      "cute anime girl crunchyroll orange aesthetic sakura petals floating ancient japanese temple golden hour dusk magical",
    "phone":   "anime girl holding glowing smartphone cyberpunk tokyo neon rain reflections night street wet pavement purple cyan glow",
    "pc":      "anime hacker girl dual holographic monitor setup dark room purple cyan neon aesthetic tokyo skyline glass reflection",
    "plans":   "anime girl surrounded floating crystal gems glowing tiers golden crown celestial japanese garden stars bokeh",
    "admin":   "anime samurai girl dark armour glowing purple energy katana fog ancient castle midnight moonlight dramatic",
    "keys":    "anime girl holding magical glowing key enchanted forest japanese stone lanterns fireflies twilight",
    "stats":   "anime girl holographic data charts floating tokyo skyline dusk purple gradient digital aesthetic",
    "history": "anime girl reading ancient japanese scroll golden light sakura temple serene peaceful watercolor",
    "refer":   "two anime girls hand in hand cherry blossom avenue pink magical sparkle glow soft light",
    "ban":     "anime judge girl dark courtroom gavel lightning dramatic atmosphere purple black",
    "success": "anime girl victorious fist pump sakura petals swirling sparkle golden light celebration",
    "fail":    "anime girl sad rain window drops dark room dim lamp soft melancholic",
    "cookie":  "anime girl magical cookie jar glowing runes enchanted kitchen cozy aesthetic",
    "welcome": "anime girl standing gate to magical japanese garden night fireflies lanterns bokeh cinematic",
}

# Pillow font — use default since no custom font guaranteed on Render
_PIL_FONT_LARGE  = None
_PIL_FONT_MEDIUM = None
_PIL_FONT_SMALL  = None

def _load_pil_fonts():
    global _PIL_FONT_LARGE, _PIL_FONT_MEDIUM, _PIL_FONT_SMALL
    try:
        from PIL import ImageFont
        # Try to load a nice font if available
        for font_path in [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ]:
            if os.path.exists(font_path):
                _PIL_FONT_LARGE  = ImageFont.truetype(font_path, 52)
                _PIL_FONT_MEDIUM = ImageFont.truetype(font_path, 34)
                _PIL_FONT_SMALL  = ImageFont.truetype(font_path, 24)
                break
        if not _PIL_FONT_LARGE:
            _PIL_FONT_LARGE  = ImageFont.load_default()
            _PIL_FONT_MEDIUM = ImageFont.load_default()
            _PIL_FONT_SMALL  = ImageFont.load_default()
    except Exception:
        pass

async def get_anime_image(
    key: str = "main",
    overlay_title: str = "",
    overlay_sub: str = "",
    overlay_stat: str = "",
) -> Optional[bytes]:
    """
    Fetch anime image from Pollinations, then apply Pillow overlays:
    - Gradient vignette bottom
    - Title text (big, white, shadow)
    - Subtitle / stat line
    Returns PNG bytes.
    """
    prompt = ANIME_PROMPTS.get(key, ANIME_PROMPTS["main"])
    seed   = random.randint(1, 999999)
    url    = POLLINATIONS_BASE.format(
        prompt=urllib.parse.quote(prompt), seed=seed)
    try:
        async with aiohttp.ClientSession() as sess:
            async with sess.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status != 200:
                    return None
                raw = await resp.read()
    except Exception as ex:
        logger.warning("Pollinations fetch error: %s", ex)
        return None

    try:
        raw = await asyncio.to_thread(_apply_pillow_overlay, raw, overlay_title, overlay_sub, overlay_stat)
    except Exception as ex:
        logger.warning("Pillow overlay error: %s", ex)

    return raw


def _apply_pillow_overlay(
    raw: bytes,
    title: str,
    sub: str,
    stat: str,
) -> bytes:
    """Sync Pillow work — run via asyncio.to_thread."""
    img = Image.open(io.BytesIO(raw)).convert("RGBA")
    W, H = img.size

    # ── Dark gradient at bottom ───────────────────────────────
    gradient = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_g   = ImageDraw.Draw(gradient)
    grad_h   = int(H * 0.55)
    for y in range(grad_h):
        alpha = int(210 * (y / grad_h) ** 1.6)
        draw_g.line([(0, H - grad_h + y), (W, H - grad_h + y)],
                    fill=(10, 5, 20, alpha))
    img = Image.alpha_composite(img, gradient)

    # ── Soft purple tint overlay (top-right corner glow) ─────
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_glow = ImageDraw.Draw(glow)
    draw_glow.ellipse(
        [W - int(W*0.45), -int(H*0.2), W + int(W*0.1), int(H*0.5)],
        fill=(120, 40, 200, 28)
    )
    img = Image.alpha_composite(img, glow)

    draw = ImageDraw.Draw(img)
    font_l = _PIL_FONT_LARGE  or ImageFont.load_default()
    font_m = _PIL_FONT_MEDIUM or ImageFont.load_default()
    font_s = _PIL_FONT_SMALL  or ImageFont.load_default()

    pad = 38

    def draw_text_shadow(d, text, pos, font, color, shadow_color=(0,0,0,180), offset=3):
        x, y = pos
        d.text((x+offset, y+offset), text, font=font, fill=shadow_color)
        d.text((x, y), text, font=font, fill=color)

    if title:
        draw_text_shadow(draw, title, (pad, H - 180), font_l,
                         (255, 255, 255, 255))
    if sub:
        draw_text_shadow(draw, sub, (pad, H - 115), font_m,
                         (210, 180, 255, 240))
    if stat:
        draw_text_shadow(draw, stat, (pad, H - 68), font_s,
                         (180, 220, 255, 220))

    # ── Thin pink/purple bottom border ────────────────────────
    draw.rectangle([0, H-4, W, H], fill=(180, 80, 255, 200))
    draw.rectangle([0, H-8, W, H-4], fill=(255, 120, 200, 120))

    out = io.BytesIO()
    img.convert("RGB").save(out, format="JPEG", quality=92)
    return out.getvalue()


# ═══════════════════════════════════════════════════════════════
#  RICH MESSAGE HELPERS  — Bot API 10.3
# ═══════════════════════════════════════════════════════════════

def rt(text: str):
    """Plain rich text."""
    return tg_types.RichTextPlain(text=text)

def rt_bold(text: str):
    return RichTextBold(text=rt(text))

def rt_italic(text: str):
    return RichTextItalic(text=rt(text))

def rt_code(text: str):
    return RichTextCode(text=rt(text))

def rt_marked(text: str):
    """Highlighted/marked text."""
    return RichTextMarked(text=rt(text))

def rt_concat(*parts) -> list:
    """Concatenate rich text parts."""
    return list(parts)

def rich_divider() -> InputRichBlockDivider:
    return InputRichBlockDivider()

def rich_heading(text: str, emoji_key: str = "star") -> InputRichBlockSectionHeading:
    return InputRichBlockSectionHeading(
        header=rt_bold(text),
        subheader=rt_italic(f"𝐏 ʜ ᴀ ɴ ᴛ ᴏ ᴍ"),
    )

def rich_para(text: str) -> InputRichBlockParagraph:
    return InputRichBlockParagraph(text=rt(text))

def rich_table(headers: list[str], rows: list[list[str]]) -> InputRichBlockTable:
    """Build a native Telegram table block."""
    header_cells = [RichBlockTableCell(text=rt_bold(h)) for h in headers]
    data_rows = []
    for row in rows:
        data_rows.append([RichBlockTableCell(text=rt(cell)) for cell in row])
    return InputRichBlockTable(
        cells=[[header_cells]] + [data_rows[i:i+1] for i in range(len(data_rows))],
        is_compact=False,
    )

def rich_list(items: list[str], ordered: bool = False) -> InputRichBlockList:
    li = [InputRichBlockListItem(label=rt_bold("·"), body=rt(item)) for item in items]
    return InputRichBlockList(items=li, is_ordered=ordered)

def rich_quote(text: str, expandable: bool = True) -> InputRichBlockBlockQuotation | InputRichBlockExpandableBlockQuotation:
    if expandable:
        return InputRichBlockExpandableBlockQuotation(
            text=rt(text),
            credit=rt_italic("𝐏 ʜ ᴀ ɴ ᴛ ᴏ ᴍ"),
        )
    return InputRichBlockBlockQuotation(
        text=rt(text),
        credit=rt_italic("𝐏 ʜ ᴀ ɴ ᴛ ᴏ ᴍ"),
    )

def rich_pre(text: str) -> InputRichBlockPreformatted:
    return InputRichBlockPreformatted(text=rt(text), language="")

def rich_footer(text: str) -> InputRichBlockFooter:
    return InputRichBlockFooter(text=rt_italic(text))


# ═══════════════════════════════════════════════════════════════
#  KEYBOARD BUILDER HELPERS
# ═══════════════════════════════════════════════════════════════

def btn(
    text: str,
    cb: str | None = None,
    url: str | None = None,
    style: str | None = None,
    copy: str | None = None,
    emoji_key: str | None = None,
) -> InlineKeyboardButton:
    eid = M_EMOJI.get(emoji_key, rb()) if emoji_key else rb()
    kwargs: dict[str, Any] = {
        "text": text,
        "icon_custom_emoji_id": eid,
    }
    if style:
        kwargs["style"] = style
    if copy is not None:
        kwargs["copy_text"] = CopyTextButton(text=copy)
    elif url:
        kwargs["url"] = url
    else:
        kwargs["callback_data"] = cb or "noop"
    return InlineKeyboardButton(**kwargs)


def kb(*rows: list[InlineKeyboardButton]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=list(rows))


def kb_back(cb: str = "m_main") -> InlineKeyboardMarkup:
    return kb([btn("« ʙᴀᴄᴋ", cb=cb, style="primary", emoji_key="back")])


# ── Main Menu ──────────────────────────────────────────────────
def kb_main_menu() -> InlineKeyboardMarkup:
    return kb(
        [btn("𝐍ᴇᴛꜰʟɪx", cb="m_nf_menu",   style="danger",  emoji_key="netflix"),
         btn("ᴄʀᴜɴᴄʜʏʀᴏʟʟ", cb="m_cr_menu", style="primary", emoji_key="cr")],
        [btn("ᴍʏ ᴩʀᴏꜰɪʟᴇ",  cb="m_me",    style="primary", emoji_key="user"),
         btn("ᴩʟᴀɴꜱ",       cb="m_plans", style="success", emoji_key="crown")],
        [btn("ʀᴇᴅᴇᴇᴍ ᴋᴇʏ",  cb="m_redeem",  style="primary", emoji_key="key"),
         btn("ʀᴇꜰᴇʀ",       cb="m_refer",   style="success", emoji_key="refer")],
        [btn("ᴛʀɪᴀʟ",       cb="m_trial",  style="primary", emoji_key="trial"),
         btn("ʜɪꜱᴛᴏʀʏ",     cb="m_history", style="primary", emoji_key="history")],
        [btn("ꜱᴛᴀᴛꜱ",       cb="m_stats",   style="primary", emoji_key="chart"),
         btn("ʜᴇʟᴩ",        cb="m_help",    style="primary", emoji_key="info")],
    )


# ── Netflix Methods ────────────────────────────────────────────
def kb_nf_menu() -> InlineKeyboardMarkup:
    return kb(
        [btn("ᴛᴠ ʟᴏɢɪɴ",    cb="prompt_tv",    style="danger",  emoji_key="tv")],
        [btn("ᴅɪʀᴇᴄᴛ ʟᴏɢɪɴ", cb="prompt_login", style="primary", emoji_key="login")],
        [btn("ᴩʜᴏɴᴇ ᴍᴇᴛʜᴏᴅ", cb="prompt_phone", style="primary", emoji_key="phone")],
        [btn("ᴩᴄ ᴍᴇᴛʜᴏᴅ",    cb="prompt_pc",    style="primary", emoji_key="pc")],
        [btn("« ʙᴀᴄᴋ",       cb="m_main",       style="primary", emoji_key="back")],
    )


# ── CR Menu ────────────────────────────────────────────────────
def kb_cr_menu() -> InlineKeyboardMarkup:
    return kb(
        [btn("ᴛᴠ ᴀᴄᴛɪᴠᴀᴛɪᴏɴ", cb="prompt_crtv", style="primary", emoji_key="cr")],
        [btn("« ʙᴀᴄᴋ",         cb="m_main",       style="primary", emoji_key="back")],
    )


# ── Plan upgrade ───────────────────────────────────────────────
def kb_plan_upgrade() -> InlineKeyboardMarkup:
    return kb(
        [btn("ᴄᴏʀᴇ  —  ɪɴꜰᴏ",  cb="plan_info_core",  style="primary", emoji_key="bolt")],
        [btn("ᴇʟɪᴛᴇ —  ɪɴꜰᴏ",  cb="plan_info_elite", style="primary", emoji_key="gem")],
        [btn("ʀᴏᴏᴛ  —  ɪɴꜰᴏ",  cb="plan_info_root",  style="danger",  emoji_key="crown")],
        [btn("« ʙᴀᴄᴋ",          cb="m_main",          style="primary", emoji_key="back")],
    )


# ── Admin panel ────────────────────────────────────────────────
def kb_admin_main() -> InlineKeyboardMarkup:
    return kb(
        [btn("ᴄᴏᴏᴋɪᴇꜱ",   cb="adm_nf",        style="danger",  emoji_key="cookie"),
         btn("ᴄʀ ᴀᴄᴄꜱ",   cb="adm_cr",        style="primary", emoji_key="cr")],
        [btn("ᴜꜱᴇʀꜱ",      cb="adm_users",     style="primary", emoji_key="users"),
         btn("ᴋᴇʏꜱ",       cb="adm_keys",      style="success", emoji_key="key")],
        [btn("ʙʀᴏᴀᴅᴄᴀꜱᴛ",  cb="adm_broadcast", style="primary", emoji_key="broadcast"),
         btn("ᴩʀᴏxɪᴇꜱ",   cb="adm_proxies",   style="primary", emoji_key="proxy")],
        [btn("ᴍᴇᴅɪᴀ",      cb="adm_media",     style="primary", emoji_key="media"),
         btn("ᴄᴏɴꜰɪɢ",    cb="adm_config",    style="primary", emoji_key="settings")],
        [btn("ꜱᴛᴀᴛꜱ",      cb="adm_stats",     style="primary", emoji_key="stats"),
         btn("ᴀᴜᴅɪᴛ",      cb="adm_auditlog",  style="primary", emoji_key="audit")],
        [btn("ᴩʟᴀɴꜱ",      cb="adm_plans",     style="primary", emoji_key="plan"),
         btn("ᴛʀɪᴀʟꜱ",     cb="adm_trials",    style="primary", emoji_key="trial")],
        [btn("ʀᴇꜰꜱ",       cb="adm_refs",      style="primary", emoji_key="refer"),
         btn("ᴀᴅᴍɪɴꜱ",    cb="adm_admins",    style="primary", emoji_key="admin")],
        [btn("ᴄʟᴇᴀɴᴜᴩ",   cb="adm_cleanup",   style="danger",  emoji_key="cleanup"),
         btn("ʙᴀᴄᴋᴜᴩ",    cb="adm_backup",    style="primary", emoji_key="backup")],
        [btn("ᴍᴀɪɴᴛ",      cb="adm_maint",     style="danger",  emoji_key="wrench"),
         btn("ᴀʟᴇʀᴛꜱ",    cb="adm_alerts",    style="primary", emoji_key="alert")],
        [btn("✕ ᴄʟᴏꜱᴇ",   cb="adm_close",     style="danger",  emoji_key="cross")],
    )


def kb_verify(missing: list[str]) -> InlineKeyboardMarkup:
    rows = []
    for ch in missing:
        link = f"https://t.me/{ch.lstrip('@')}"
        rows.append([btn(f"ᴊᴏɪɴ  {ch}", url=link, style="primary", emoji_key="bolt")])
    rows.append([btn("ᴠᴇʀɪꜰʏ", cb="verify_check", style="success", emoji_key="check")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ═══════════════════════════════════════════════════════════════
#  FSM STATES
# ═══════════════════════════════════════════════════════════════
class AdminUpload(StatesGroup):
    waiting_nf_cookies  = State()
    waiting_cr_accounts = State()
    waiting_broadcast   = State()
    waiting_setvideo    = State()
    waiting_setgif      = State()
    waiting_setphoto    = State()
    waiting_setphoto_key= State()

class UserInput(StatesGroup):
    waiting_redeem_key = State()


# ═══════════════════════════════════════════════════════════════
#  DATABASE
# ═══════════════════════════════════════════════════════════════
_mongo_client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None

def get_db():
    return _mongo_client[DB_NAME]


async def init_db():
    db = get_db()
    # Indexes
    await db.users.create_index("ref_code", unique=True, sparse=True)
    await db.users.create_index("ref_by")
    await db.nf_cookies.create_index("status")
    await db.nf_cookies.create_index([("last_used", 1)])
    await db.cr_accounts.create_index("status")
    await db.cr_accounts.create_index([("last_used", 1)])
    await db.keys.create_index("key", unique=True)
    await db.login_logs.create_index([("uid", 1), ("ts", -1)])
    await db.login_logs.create_index("ts")
    await db.rate_limits.create_index("uid", unique=True)
    await db.admin_logs.create_index([("ts", -1)])
    await db.config.create_index("key", unique=True)

    # Seed defaults
    defaults = {
        "maintenance_mode":  False,
        "required_channels": [],
        "start_video":       None,
        "start_gif":         None,
        "welcome_text":      None,
        "default_proxy":     None,
        "trial_days":        1,
        "ref_bonus_days":    3,
        "free_daily":        2,
        "core_daily":        10,
        "elite_daily":       20,
        "root_daily":        30,
        "alert_low_cookies": 5,
        "alert_low_cr":      3,
        "admin_photo_main":  None,
        "admin_photo_nf":    None,
        "admin_photo_cr":    None,
        "admin_photo_plans": None,
        "admin_photo_admin": None,
    }
    for k, v in defaults.items():
        await db.config.update_one(
            {"key": k},
            {"$setOnInsert": {"key": k, "value": v}},
            upsert=True,
        )
    logger.info("DB initialized")


async def get_cfg(key: str, default=None):
    doc = await get_db().config.find_one({"key": key})
    return doc["value"] if doc else default


async def set_cfg(key: str, value):
    await get_db().config.update_one(
        {"key": key}, {"$set": {"value": value}}, upsert=True)


async def get_user(uid: int) -> dict:
    doc = await get_db().users.find_one({"_id": uid})
    if not doc:
        code = secrets.token_hex(5).upper()
        doc  = {
            "_id": uid, "plan": "free", "plan_expiry": None,
            "plan_source": None, "daily_count": 0,
            "daily_reset": int(time.time()),
            "ref_code": code, "ref_by": None, "ref_count": 0,
            "trial_used": False, "banned": False, "ban_reason": None,
            "notifications": True, "joined_at": int(time.time()),
            "last_active": int(time.time()),
        }
        await get_db().users.insert_one(doc)
    return doc


async def upsert_user(uid: int, update: dict):
    await get_db().users.update_one({"_id": uid}, update, upsert=True)


async def reset_daily_if_needed(uid: int) -> None:
    user = await get_user(uid)
    now  = int(time.time())
    last = user.get("daily_reset", 0)
    if now - last >= 86400:
        await upsert_user(uid, {"$set": {"daily_count": 0, "daily_reset": now}})


async def check_rate_limit(uid: int, cost: int = 1) -> bool:
    db  = get_db()
    now = time.time()
    doc = await db.rate_limits.find_one_and_update(
        {"uid": uid},
        {"$setOnInsert": {"uid": uid, "tokens": 10.0, "last_refill": now}},
        upsert=True, return_document=True,
    )
    tokens     = doc.get("tokens", 10.0)
    last_refill = doc.get("last_refill", now)
    elapsed    = now - last_refill
    tokens     = min(10.0, tokens + elapsed * (10.0 / 60.0))
    if tokens < cost:
        await db.rate_limits.update_one(
            {"uid": uid}, {"$set": {"tokens": tokens, "last_refill": now}})
        return False
    await db.rate_limits.update_one(
        {"uid": uid}, {"$set": {"tokens": tokens - cost, "last_refill": now}})
    return True


async def log_login(uid: int, service: str, method: str, code: str, success: bool, detail: str = ""):
    await get_db().login_logs.insert_one({
        "uid": uid, "service": service, "method": method,
        "code": code, "success": success, "detail": detail,
        "ts": int(time.time()),
    })


async def log_admin(admin_id: int, action: str, target, details: dict):
    await get_db().admin_logs.insert_one({
        "admin_id": admin_id, "action": action,
        "target": str(target), "details": details,
        "ts": int(time.time()),
    })


async def check_membership(bot: Bot, uid: int) -> list[str]:
    channels = await get_cfg("required_channels", [])
    missing  = []
    for ch in channels:
        try:
            member = await bot.get_chat_member(ch, uid)
            if member.status in ("left", "kicked"):
                missing.append(ch)
        except Exception:
            missing.append(ch)
    return missing


# ═══════════════════════════════════════════════════════════════
#  NETFLIX ENGINE
# ═══════════════════════════════════════════════════════════════

# ── Cookie parsing ─────────────────────────────────────────────
def parse_cookie_string(raw: str) -> Optional[dict]:
    raw = raw.strip()
    if not raw:
        return None
    # JSON format
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return {c["name"]: c["value"] for c in data if "name" in c and "value" in c}
        if isinstance(data, dict):
            if all(isinstance(v, str) for v in data.values()):
                return data
            if "name" in data:
                return {data["name"]: data["value"]}
    except Exception:
        pass
    # Netscape format
    cookies: dict[str, str] = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) >= 7:
            cookies[parts[5]] = parts[6]
    if cookies:
        return cookies
    # key=value inline
    for sep in (";", ",", "\n"):
        if sep in raw:
            d = {}
            for part in raw.split(sep):
                part = part.strip()
                if "=" in part:
                    k, _, v = part.partition("=")
                    d[k.strip()] = v.strip()
            if d:
                return d
    return None


def parse_cookie_file_bulk(text: str) -> list[dict]:
    results = []
    # Try splitting by blank lines (multiple cookies)
    blocks = re.split(r"\n{2,}", text.strip())
    for block in blocks:
        c = parse_cookie_string(block.strip())
        if c:
            results.append(c)
    if not results:
        c = parse_cookie_string(text)
        if c:
            results.append(c)
    return results


# ── Cookie vault ───────────────────────────────────────────────
async def get_live_cookie(priority: int = 0) -> Optional[dict]:
    db  = get_db()
    doc = await db.nf_cookies.find_one_and_update(
        {"status": "live", "in_use": {"$ne": True}},
        {"$set": {"in_use": True, "last_used": int(time.time())}},
        sort=[("last_used", 1)],
        return_document=True,
    )
    if not doc:
        return None
    return {"_id": doc["_id"], "cookies": json.loads(_decrypt(doc["data_enc"]))}


async def release_cookie(doc_id, success: bool):
    update = {"$set": {"in_use": False}}
    if not success:
        update["$inc"] = {"fail_count": 1}
    await get_db().nf_cookies.update_one({"_id": doc_id}, update)
    if not success:
        doc = await get_db().nf_cookies.find_one({"_id": doc_id})
        if doc and doc.get("fail_count", 0) >= 3:
            await get_db().nf_cookies.update_one(
                {"_id": doc_id}, {"$set": {"status": "dead"}})


# ── Netflix sync workers ───────────────────────────────────────
NF_TV_URL    = "https://www.netflix.com/activate"
NF_TV2_URL   = "https://www.netflix.com/activate"
NF_PHONE_URL = "https://www.netflix.com/activate"
NF_PC_URL    = "https://www.netflix.com/login"

NF_HEADERS_BASE = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/126.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "X-Netflix.browserName": "Chrome",
    "X-Netflix.browserVersion": "126",
    "X-Netflix.osName": "Windows",
    "X-Netflix.osVersion": "10.0",
    "Origin": "https://www.netflix.com",
    "Referer": "https://www.netflix.com/",
}

def _nf_session(proxy: Optional[str] = None) -> cloudscraper.CloudScraper:
    sess = cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "windows", "mobile": False},
        delay=2,
    )
    if proxy:
        sess.proxies = {"http": proxy, "https": proxy}
    return sess


def _extract_auth_url(html: str) -> Optional[str]:
    patterns = [
        r'"authURL"\s*:\s*"([^"]+)"',
        r'authURL\s*=\s*["\']([^"\']+)["\']',
        r'"authURL":"([^"]+)"',
        r"netflix\.reactContext\.models\..*?authURL['\"]:\s*['\"]([^'\"]+)",
    ]
    for p in patterns:
        m = re.search(p, html)
        if m:
            return m.group(1)
    return None


def _parse_country(html: str) -> str:
    m = re.search(r'"countryCode"\s*:\s*"([A-Z]+)"', html)
    return m.group(1) if m else "??"


def _parse_plan(html: str) -> str:
    for kw in ("Premium","Standard","Basic","Standard with ads"):
        if kw.lower() in html.lower():
            return kw
    return "Unknown"


def _is_code_error(text: str) -> bool:
    err_phrases = [
        "code is invalid", "code has expired", "try again",
        "Unable to activate", "activation code", "incorrect code",
        "Code incorrect", "code is not valid",
    ]
    tl = text.lower()
    return any(p.lower() in tl for p in err_phrases)


def _sync_nf_tv(cookie_dict: dict, tv_code: str, proxy: Optional[str]) -> dict:
    """TV method — POST to shakti activate endpoint."""
    sess = _nf_session(proxy)
    try:
        # Step 1: get home page for authURL
        r = sess.get("https://www.netflix.com/", headers=NF_HEADERS_BASE, timeout=20)
        auth_url = _extract_auth_url(r.text)
        if not auth_url:
            return {"ok": False, "reason": "auth_url_missing"}

        cookies_jar = {k: v for k, v in cookie_dict.items()}
        sess.cookies.update(cookies_jar)

        # Step 2: activate
        data = {"userInput": tv_code, "authURL": auth_url}
        headers = {**NF_HEADERS_BASE,
                   "Content-Type": "application/x-www-form-urlencoded",
                   "X-Netflix.request.client.user.guid": ""}
        r2 = sess.post(NF_TV_URL, data=data, headers=headers,
                       cookies=cookies_jar, timeout=20)
        body = r2.text

        if _is_code_error(body):
            return {"ok": False, "reason": "invalid_code"}
        if r2.status_code in (200, 302) or "success" in body.lower():
            country = _parse_country(body)
            plan    = _parse_plan(body)
            return {"ok": True, "country": country, "plan": plan, "method": "tv"}

        return {"ok": False, "reason": f"http_{r2.status_code}"}
    except Exception as ex:
        return {"ok": False, "reason": str(ex)}
    finally:
        sess.close()
        gc.collect()


def _sync_nf_login(cookie_dict: dict, tv_code: str, proxy: Optional[str]) -> dict:
    """Direct login/link code method."""
    sess = _nf_session(proxy)
    try:
        sess.cookies.update(cookie_dict)
        r = sess.get(
            f"https://www.netflix.com/activate?code={tv_code}",
            headers=NF_HEADERS_BASE, timeout=20,
            allow_redirects=True,
        )
        body = r.text
        if _is_code_error(body):
            return {"ok": False, "reason": "invalid_code"}
        if r.status_code in (200,) and ("activated" in body.lower() or "success" in body.lower()):
            return {"ok": True, "country": _parse_country(body),
                    "plan": _parse_plan(body), "method": "login"}
        # Fallback: if we got the activate page without error it likely worked
        if r.status_code == 200 and "netflix.com" in r.url:
            return {"ok": True, "country": _parse_country(body),
                    "plan": _parse_plan(body), "method": "login"}
        return {"ok": False, "reason": f"http_{r.status_code}"}
    except Exception as ex:
        return {"ok": False, "reason": str(ex)}
    finally:
        sess.close()
        gc.collect()


def _sync_nf_phone(cookie_dict: dict, tv_code: str, proxy: Optional[str]) -> dict:
    """Phone / mobile method — mobile user agent."""
    sess = cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "android", "mobile": True},
        delay=2,
    )
    if proxy:
        sess.proxies = {"http": proxy, "https": proxy}
    try:
        sess.cookies.update(cookie_dict)
        ua = ("Mozilla/5.0 (Linux; Android 14; Pixel 8) "
              "AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/126.0.6478.71 Mobile Safari/537.36")
        headers = {**NF_HEADERS_BASE, "User-Agent": ua,
                   "X-Netflix.osName": "Android",
                   "X-Netflix.osVersion": "14"}
        r = sess.get(f"https://www.netflix.com/activate?code={tv_code}",
                     headers=headers, timeout=20)
        body = r.text
        if _is_code_error(body):
            return {"ok": False, "reason": "invalid_code"}
        if r.status_code == 200:
            return {"ok": True, "country": _parse_country(body),
                    "plan": _parse_plan(body), "method": "phone"}
        return {"ok": False, "reason": f"http_{r.status_code}"}
    except Exception as ex:
        return {"ok": False, "reason": str(ex)}
    finally:
        sess.close()
        gc.collect()


def _sync_nf_pc(cookie_dict: dict, tv_code: str, proxy: Optional[str]) -> dict:
    """PC / browser method — full page simulate."""
    sess = _nf_session(proxy)
    try:
        sess.cookies.update(cookie_dict)
        r = sess.get("https://www.netflix.com/login",
                     headers=NF_HEADERS_BASE, timeout=20)
        auth_url = _extract_auth_url(r.text)
        if not auth_url:
            return {"ok": False, "reason": "auth_url_missing"}
        data = {"userInput": tv_code, "authURL": auth_url,
                "flow": "websiteSignUp", "mode": "activateDevice"}
        headers = {**NF_HEADERS_BASE,
                   "Content-Type": "application/x-www-form-urlencoded"}
        r2 = sess.post(NF_TV_URL, data=data,
                       headers=headers, timeout=20)
        body = r2.text
        if _is_code_error(body):
            return {"ok": False, "reason": "invalid_code"}
        if r2.status_code in (200, 302):
            return {"ok": True, "country": _parse_country(body),
                    "plan": _parse_plan(body), "method": "pc"}
        return {"ok": False, "reason": f"http_{r2.status_code}"}
    except Exception as ex:
        return {"ok": False, "reason": str(ex)}
    finally:
        sess.close()
        gc.collect()


def _sync_validate_cookie(cookie_dict: dict, proxy: Optional[str] = None) -> bool:
    sess = _nf_session(proxy)
    try:
        sess.cookies.update(cookie_dict)
        r = sess.get("https://www.netflix.com/YourAccount",
                     headers=NF_HEADERS_BASE, timeout=15,
                     allow_redirects=False)
        return r.status_code == 200
    except Exception:
        return False
    finally:
        sess.close()
        gc.collect()


# ── NF Orchestrator ────────────────────────────────────────────
_NF_WORKERS = {
    "tv":    _sync_nf_tv,
    "login": _sync_nf_login,
    "phone": _sync_nf_phone,
    "pc":    _sync_nf_pc,
}

async def _run_nf_login(
    message_or_cq,
    bot: Bot,
    tv_code: str,
    method: str,
) -> None:
    uid  = message_or_cq.from_user.id
    user = await get_user(uid)

    # Ban check
    if user.get("banned"):
        await _reply(message_or_cq, bot,
            f"{e('ban','·')} ʏᴏᴜ ᴀʀᴇ ʙᴀɴɴᴇᴅ·")
        return

    # Maintenance
    if await get_cfg("maintenance_mode", False) and uid not in ADMIN_IDS:
        await _reply(message_or_cq, bot,
            f"{e('wrench','·')} ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ ᴍᴏᴅᴇ·")
        return

    # Membership
    missing = await check_membership(bot, uid)
    if missing:
        await _reply(message_or_cq, bot,
            f"{e('lock','·')} ᴊᴏɪɴ ʀᴇQᴜɪʀᴇᴅ ᴄʜᴀɴɴᴇʟꜱ ꜰɪʀꜱᴛ·",
            kb_verify(missing))
        return

    # Plan check
    if method not in PLANS[user.get("plan","free")]["methods"]:
        await _reply(message_or_cq, bot,
            f"{e('lock','·')} {method.upper()} ʀᴇQᴜɪʀᴇꜱ ᴜᴩɢʀᴀᴅᴇ·",
            kb_plan_upgrade())
        return

    # Rate limit
    if not await check_rate_limit(uid):
        await _reply(message_or_cq, bot,
            f"{e('warn','·')} ʀᴀᴛᴇ ʟɪᴍɪᴛ — ᴡᴀɪᴛ 1 ᴍɪɴ·")
        return

    # Daily limit
    await reset_daily_if_needed(uid)
    user = await get_user(uid)
    plan = user.get("plan","free")
    daily_max = PLANS[plan]["daily"]
    if user.get("daily_count", 0) >= daily_max:
        await _reply(message_or_cq, bot,
            f"{e('warn','·')} ᴅᴀɪʟʏ ʟɪᴍɪᴛ ({daily_max}) ʀᴇᴀᴄʜᴇᴅ·",
            kb_plan_upgrade())
        return

    # Code validate
    if not TV_CODE_RE.match(tv_code):
        await _reply(message_or_cq, bot,
            f"{e('cross','·')} ɪɴᴠᴀʟɪᴅ ᴄᴏᴅᴇ ꜰᴏʀᴍᴀᴛ·")
        return

    # Working indicator
    wait_msg = await _reply(message_or_cq, bot,
        f"{e('bolt','·')} ᴡᴏʀᴋɪɴɢ… [{method.upper()}] <code>{tv_code}</code>")

    sem = NF_SEM if method in ("tv","login") else PHONE_SEM if method == "phone" else NF_SEM
    async with sem:
        cookie_doc = await get_live_cookie(PLANS[plan]["priority"])
        if not cookie_doc:
            await _edit_or_reply(wait_msg, message_or_cq, bot,
                f"{e('cross','·')} ɴᴏ ᴄᴏᴏᴋɪᴇꜱ ᴀᴠᴀɪʟᴀʙʟᴇ·",
                kb_back("m_nf_menu"))
            return

        proxy   = await get_cfg("default_proxy")
        worker  = _NF_WORKERS[method]
        result  = await asyncio.to_thread(
            worker, cookie_doc["cookies"], tv_code, proxy)
        success = result.get("ok", False)
        await release_cookie(cookie_doc["_id"], success)

    await upsert_user(uid, {"$inc": {"daily_count": 1},
                             "$set": {"last_active": int(time.time())}})
    await log_login(uid, "netflix", method, tv_code, success,
                    result.get("reason","") if not success else "")

    if success:
        country = result.get("country","??")
        plan_   = result.get("plan","Unknown")
        img     = await get_anime_image(
            "success",
            overlay_title="𝐋 ᴏ ɢ ɪ ɴ  ꜱ ᴜ ᴄ ᴄ ᴇ ꜱ ꜱ",
            overlay_sub=f"Netflix · {method.upper()} · {country}",
            overlay_stat=f"Plan: {plan_}",
        )
        # Rich Message for success
        blocks = [
            rich_heading("ɴᴇᴛꜰʟɪx ᴀᴄᴛɪᴠᴀᴛᴇᴅ", "check"),
            rich_divider(),
            rich_table(
                ["ꜰɪᴇʟᴅ", "ᴠᴀʟᴜᴇ"],
                [
                    ["ᴍᴇᴛʜᴏᴅ",  method.upper()],
                    ["ᴄᴏᴅᴇ",    tv_code],
                    ["ᴄᴏᴜɴᴛʀʏ", country],
                    ["ᴩʟᴀɴ",    plan_],
                    ["ꜱᴛᴀᴛᴜꜱ", "ꜱᴜᴄᴄᴇꜱꜱ"],
                ]
            ),
            rich_footer("𝐏 ʜ ᴀ ɴ ᴛ ᴏ ᴍ  · ʜᴀᴩᴩʏ ꜱᴛʀᴇᴀᴍɪɴɢ"),
        ]
        retry_kb = kb(
            [btn("ᴛʀʏ ᴀɴᴏᴛʜᴇʀ ᴄᴏᴅᴇ", cb=f"prompt_{method}", style="primary", emoji_key="refresh")],
            [btn("« ᴍᴀɪɴ ᴍᴇɴᴜ",       cb="m_main",           style="primary", emoji_key="back")],
        )
        if img:
            await bot.send_photo(
                chat_id=uid,
                photo=BufferedInputFile(img, "success.jpg"),
                caption=f"{e('check','·')} <b>ɴᴇᴛꜰʟɪx {method.upper()} ᴀᴄᴛɪᴠᴀᴛᴇᴅ</b>\n"
                        f"{BDIV}\n"
                        f"{e('arrow','·')} ᴄᴏᴅᴇ: <code>{tv_code}</code>\n"
                        f"{e('arrow','·')} ᴄᴏᴜɴᴛʀʏ: <b>{country}</b>\n"
                        f"{e('arrow','·')} ᴩʟᴀɴ: <b>{plan_}</b>",
                parse_mode=ParseMode.HTML,
                reply_markup=retry_kb,
            )
        try:
            await bot.send_rich_message(
                chat_id=uid,
                rich_message=InputRichMessage(blocks=blocks),
                reply_markup=retry_kb,
            )
        except Exception:
            pass  # Rich message optional — photo already sent
    else:
        reason = result.get("reason","unknown")
        img    = await get_anime_image(
            "fail",
            overlay_title="𝐋 ᴏ ɢ ɪ ɴ  ꜰ ᴀ ɪ ʟ ᴇ ᴅ",
            overlay_sub=f"Netflix · {method.upper()}",
            overlay_stat=f"Reason: {reason}",
        )
        retry_kb = kb(
            [btn("ʀᴇᴛʀʏ", cb=f"retry_nf_{method}_{tv_code}", style="danger",  emoji_key="refresh")],
            [btn("« ʙᴀᴄᴋ", cb="m_nf_menu",                   style="primary", emoji_key="back")],
        )
        if img:
            await bot.send_photo(
                chat_id=uid,
                photo=BufferedInputFile(img, "fail.jpg"),
                caption=f"{e('cross','·')} <b>ꜰᴀɪʟᴇᴅ</b>\n"
                        f"{BDIV}\n"
                        f"{e('info','·')} ʀᴇᴀꜱᴏɴ: <code>{reason}</code>",
                parse_mode=ParseMode.HTML,
                reply_markup=retry_kb,
            )
        else:
            await _edit_or_reply(wait_msg, message_or_cq, bot,
                f"{e('cross','·')} <b>ꜰᴀɪʟᴇᴅ</b> — <code>{reason}</code>",
                retry_kb)

    # Delete wait msg if it's a message object
    try:
        if wait_msg:
            await wait_msg.delete()
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════
#  CRUNCHYROLL ENGINE
# ═══════════════════════════════════════════════════════════════

CR_SSO_BASE   = "https://sso.crunchyroll.com"
CR_API_BASE   = "https://api.crunchyroll.com"
CR_DEVICE_URL = "https://api.crunchyroll.com/device/v1/auth/link"
CR_CLIENT_ID  = "noaihdevm_6iyg0a8l0q"  # public CR web client id
CR_CLIENT_SEC = "cr_pkg!XqCYSRepF"       # public CR web client secret

CR_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/126.0.0.0 Safari/537.36",
    "Origin":  "https://www.crunchyroll.com",
    "Referer": "https://www.crunchyroll.com/",
}


async def get_live_cr_account() -> Optional[dict]:
    doc = await get_db().cr_accounts.find_one_and_update(
        {"status": "live", "in_use": {"$ne": True}},
        {"$set": {"in_use": True, "last_used": int(time.time())}},
        sort=[("last_used", 1)],
        return_document=True,
    )
    if not doc:
        return None
    creds = _decrypt(doc["data_enc"])
    email, _, password = creds.partition(":")
    return {"_id": doc["_id"], "email": email, "password": password}


async def release_cr_account(doc_id, success: bool):
    update = {"$set": {"in_use": False}}
    if not success:
        update["$inc"] = {"fail_count": 1}
    await get_db().cr_accounts.update_one({"_id": doc_id}, update)
    if not success:
        doc = await get_db().cr_accounts.find_one({"_id": doc_id})
        if doc and doc.get("fail_count", 0) >= 3:
            await get_db().cr_accounts.update_one(
                {"_id": doc_id}, {"$set": {"status": "dead"}})


def _sync_cr_activate(email: str, password: str, tv_code: str, proxy: Optional[str]) -> dict:
    """
    Full Crunchyroll SSO + device link flow:
    1. POST /oauth2/token → get access_token
    2. POST /device/v1/auth/link with tv_code
    """
    import base64
    sess = requests.Session()
    if proxy:
        sess.proxies = {"http": proxy, "https": proxy}
    sess.headers.update(CR_HEADERS)

    try:
        # Step 1: OAuth token
        auth = base64.b64encode(
            f"{CR_CLIENT_ID}:{CR_CLIENT_SEC}".encode()).decode()
        token_resp = sess.post(
            f"{CR_SSO_BASE}/oauth2/token",
            data={
                "grant_type":    "password",
                "username":       email,
                "password":       password,
                "scope":          "offline_access",
            },
            headers={
                **CR_HEADERS,
                "Authorization": f"Basic {auth}",
                "Content-Type":  "application/x-www-form-urlencoded",
            },
            timeout=20,
        )
        token_data = token_resp.json()
        if "access_token" not in token_data:
            err = token_data.get("error", token_data.get("message","auth_failed"))
            return {"ok": False, "reason": str(err)}

        access_token = token_data["access_token"]

        # Step 2: Link device with TV code
        link_resp = sess.post(
            CR_DEVICE_URL,
            json={"registration_code": tv_code},
            headers={
                **CR_HEADERS,
                "Authorization": f"Bearer {access_token}",
                "Content-Type":  "application/json",
            },
            timeout=20,
        )
        if link_resp.status_code in (200, 201, 204):
            return {"ok": True, "email": email}
        body = link_resp.json()
        err  = body.get("error", body.get("message", f"http_{link_resp.status_code}"))
        if "expired" in str(err).lower() or "invalid" in str(err).lower():
            return {"ok": False, "reason": "invalid_code"}
        return {"ok": False, "reason": str(err)}

    except Exception as ex:
        return {"ok": False, "reason": str(ex)}
    finally:
        sess.close()
        gc.collect()


def _sync_cr_validate(email: str, password: str, proxy: Optional[str]) -> bool:
    import base64
    sess = requests.Session()
    if proxy:
        sess.proxies = {"http": proxy, "https": proxy}
    try:
        auth = base64.b64encode(
            f"{CR_CLIENT_ID}:{CR_CLIENT_SEC}".encode()).decode()
        r = sess.post(
            f"{CR_SSO_BASE}/oauth2/token",
            data={"grant_type": "password", "username": email,
                  "password": password, "scope": "offline_access"},
            headers={**CR_HEADERS, "Authorization": f"Basic {auth}",
                     "Content-Type": "application/x-www-form-urlencoded"},
            timeout=15,
        )
        return "access_token" in r.json()
    except Exception:
        return False
    finally:
        sess.close()
        gc.collect()


async def _run_cr_login(message_or_cq, bot: Bot, tv_code: str) -> None:
    uid  = message_or_cq.from_user.id
    user = await get_user(uid)

    if user.get("banned"):
        await _reply(message_or_cq, bot, f"{e('ban','·')} ʙᴀɴɴᴇᴅ·")
        return
    if await get_cfg("maintenance_mode", False) and uid not in ADMIN_IDS:
        await _reply(message_or_cq, bot, f"{e('wrench','·')} ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ·")
        return
    missing = await check_membership(bot, uid)
    if missing:
        await _reply(message_or_cq, bot,
            f"{e('lock','·')} ᴊᴏɪɴ ʀᴇQᴜɪʀᴇᴅ ᴄʜᴀɴɴᴇʟꜱ·", kb_verify(missing))
        return
    if not await check_rate_limit(uid):
        await _reply(message_or_cq, bot, f"{e('warn','·')} ʀᴀᴛᴇ ʟɪᴍɪᴛ·")
        return
    await reset_daily_if_needed(uid)
    user = await get_user(uid)
    plan = user.get("plan","free")
    if user.get("daily_count",0) >= PLANS[plan]["daily"]:
        await _reply(message_or_cq, bot,
            f"{e('warn','·')} ᴅᴀɪʟʏ ʟɪᴍɪᴛ ʀᴇᴀᴄʜᴇᴅ·", kb_plan_upgrade())
        return
    if not TV_CODE_RE.match(tv_code):
        await _reply(message_or_cq, bot, f"{e('cross','·')} ɪɴᴠᴀʟɪᴅ ᴄᴏᴅᴇ·")
        return

    wait_msg = await _reply(message_or_cq, bot,
        f"{e('bolt','·')} ᴡᴏʀᴋɪɴɢ… [ᴄʀ ᴛᴠ] <code>{tv_code}</code>")

    async with CR_SEM:
        acc_doc = await get_live_cr_account()
        if not acc_doc:
            await _edit_or_reply(wait_msg, message_or_cq, bot,
                f"{e('cross','·')} ɴᴏ ᴄʀ ᴀᴄᴄᴏᴜɴᴛꜱ ᴀᴠᴀɪʟᴀʙʟᴇ·", kb_back("m_cr_menu"))
            return
        proxy  = await get_cfg("default_proxy")
        result = await asyncio.to_thread(
            _sync_cr_activate, acc_doc["email"], acc_doc["password"], tv_code, proxy)
        success = result.get("ok", False)
        await release_cr_account(acc_doc["_id"], success)

    await upsert_user(uid, {"$inc": {"daily_count": 1},
                             "$set": {"last_active": int(time.time())}})
    await log_login(uid, "crunchyroll", "tv", tv_code, success,
                    result.get("reason","") if not success else "")

    if success:
        img = await get_anime_image(
            "cr",
            overlay_title="ᴄʀᴜɴᴄʜʏʀᴏʟʟ ᴀᴄᴛɪᴠᴀᴛᴇᴅ",
            overlay_sub=f"TV Code: {tv_code}",
            overlay_stat="ʜᴀᴩᴩʏ ᴡᴀᴛᴄʜɪɴɢ!",
        )
        blocks = [
            rich_heading("ᴄʀᴜɴᴄʜʏʀᴏʟʟ ᴀᴄᴛɪᴠᴀᴛᴇᴅ", "cr"),
            rich_divider(),
            rich_table(
                ["ꜰɪᴇʟᴅ","ᴠᴀʟᴜᴇ"],
                [["ᴄᴏᴅᴇ", tv_code],["ꜱᴛᴀᴛᴜꜱ","ꜱᴜᴄᴄᴇꜱꜱ"]]
            ),
            rich_footer("𝐏 ʜ ᴀ ɴ ᴛ ᴏ ᴍ · ᴇɴᴊᴏʏ ᴀɴɪᴍᴇ!"),
        ]
        retry_kb = kb(
            [btn("ᴛʀʏ ᴀɴᴏᴛʜᴇʀ", cb="prompt_crtv", style="primary", emoji_key="refresh")],
            [btn("« ᴍᴀɪɴ",       cb="m_main",      style="primary", emoji_key="back")],
        )
        if img:
            await bot.send_photo(
                chat_id=uid,
                photo=BufferedInputFile(img, "cr.jpg"),
                caption=f"{e('check','·')} <b>ᴄʀᴜɴᴄʜʏʀᴏʟʟ ᴀᴄᴛɪᴠᴀᴛᴇᴅ</b>\n"
                        f"{BDIV}\n"
                        f"{e('arrow','·')} ᴄᴏᴅᴇ: <code>{tv_code}</code>",
                parse_mode=ParseMode.HTML,
                reply_markup=retry_kb,
            )
        try:
            await bot.send_rich_message(
                chat_id=uid,
                rich_message=InputRichMessage(blocks=blocks),
                reply_markup=retry_kb,
            )
        except Exception:
            pass
    else:
        reason   = result.get("reason","unknown")
        retry_kb = kb(
            [btn("ʀᴇᴛʀʏ", cb=f"retry_cr_{tv_code}", style="danger",  emoji_key="refresh")],
            [btn("« ʙᴀᴄᴋ", cb="m_cr_menu",          style="primary", emoji_key="back")],
        )
        img = await get_anime_image("fail",
            overlay_title="ᴄʀ ꜰᴀɪʟᴇᴅ", overlay_sub=reason)
        if img:
            await bot.send_photo(
                chat_id=uid,
                photo=BufferedInputFile(img,"fail.jpg"),
                caption=f"{e('cross','·')} <b>ᴄʀ ꜰᴀɪʟᴇᴅ</b> — <code>{reason}</code>",
                parse_mode=ParseMode.HTML,
                reply_markup=retry_kb,
            )
        else:
            await _edit_or_reply(wait_msg, message_or_cq, bot,
                f"{e('cross','·')} ᴄʀ ꜰᴀɪʟᴇᴅ — <code>{reason}</code>", retry_kb)
    try:
        if wait_msg:
            await wait_msg.delete()
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════
#  UTILITIES
# ═══════════════════════════════════════════════════════════════

async def _reply(source, bot: Bot, text: str, markup=None) -> Optional[Message]:
    kwargs = {"parse_mode": ParseMode.HTML}
    if markup:
        kwargs["reply_markup"] = markup
    if isinstance(source, Message):
        return await source.answer(text, **kwargs)
    elif isinstance(source, CallbackQuery):
        return await source.message.answer(text, **kwargs)
    return None


async def _edit_or_reply(wait_msg, source, bot: Bot, text: str, markup=None):
    kwargs = {"parse_mode": ParseMode.HTML}
    if markup:
        kwargs["reply_markup"] = markup
    if wait_msg:
        try:
            await wait_msg.edit_text(text, **kwargs)
            return
        except Exception:
            pass
    await _reply(source, bot, text, markup)


async def _safe_edit_photo(
    cq: CallbackQuery,
    bot: Bot,
    img: Optional[bytes],
    caption: str,
    markup: InlineKeyboardMarkup,
    filename: str = "phantom.jpg",
):
    """Edit message media (photo) or fall back to caption edit / new message."""
    if img:
        media = tg_types.InputMediaPhoto(
            media=BufferedInputFile(img, filename),
            caption=caption,
            parse_mode=ParseMode.HTML,
        )
        try:
            await cq.message.edit_media(media=media, reply_markup=markup)
            return
        except Exception:
            pass
        try:
            await bot.send_photo(
                chat_id=cq.from_user.id,
                photo=BufferedInputFile(img, filename),
                caption=caption,
                parse_mode=ParseMode.HTML,
                reply_markup=markup,
            )
        except Exception:
            pass
    else:
        try:
            if cq.message.photo:
                await cq.message.edit_caption(
                    caption=caption, parse_mode=ParseMode.HTML, reply_markup=markup)
            else:
                await cq.message.edit_text(
                    text=caption, parse_mode=ParseMode.HTML, reply_markup=markup)
        except Exception:
            await cq.message.answer(caption, parse_mode=ParseMode.HTML, reply_markup=markup)


# ═══════════════════════════════════════════════════════════════
#  MIDDLEWARE  — ban / maintenance / rate
# ═══════════════════════════════════════════════════════════════
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from typing import Callable, Awaitable


class GlobalMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict], Awaitable[Any]],
        event: TelegramObject,
        data: dict,
    ) -> Any:
        # Attach bot for convenience
        bot: Bot = data.get("bot")
        user = None
        uid  = None

        if hasattr(event, "from_user") and event.from_user:
            uid  = event.from_user.id
            user = await get_user(uid)

        if user and user.get("banned"):
            if isinstance(event, (Message, CallbackQuery)):
                txt = f"{e('ban','·')} ʏᴏᴜ ᴀʀᴇ ʙᴀɴɴᴇᴅ·"
                if isinstance(event, Message):
                    await event.answer(txt, parse_mode=ParseMode.HTML)
                else:
                    await event.answer(txt, show_alert=True)
            return

        # Update last_active
        if uid:
            await get_db().users.update_one(
                {"_id": uid}, {"$set": {"last_active": int(time.time())}})

        return await handler(event, data)


# ═══════════════════════════════════════════════════════════════
#  ROUTER + HANDLERS
# ═══════════════════════════════════════════════════════════════
router = Router()


# ── /start ────────────────────────────────────────────────────
@router.message(CommandStart())
async def cmd_start(msg: Message, bot: Bot, state: FSMContext):
    await state.clear()
    uid  = msg.from_user.id
    args = msg.text.split(None, 1)
    ref  = args[1].strip() if len(args) > 1 else ""

    # Referral
    if ref.startswith("ref_"):
        ref_code = ref[4:]
        user     = await get_user(uid)
        if not user.get("ref_by") and ref_code != user.get("ref_code"):
            ref_owner = await get_db().users.find_one({"ref_code": ref_code})
            if ref_owner:
                bonus = int(await get_cfg("ref_bonus_days", 3))
                await upsert_user(uid, {"$set": {"ref_by": ref_owner["_id"]}})
                # Give bonus to referrer
                exp = ref_owner.get("plan_expiry") or int(time.time())
                await upsert_user(ref_owner["_id"], {
                    "$inc": {"ref_count": 1},
                    "$set": {"plan_expiry": max(exp, int(time.time())) + bonus * 86400},
                })

    # Membership check
    missing = await check_membership(bot, uid)
    if missing:
        img = await get_anime_image("welcome",
            overlay_title="𝐏 ʜ ᴀ ɴ ᴛ ᴏ ᴍ",
            overlay_sub="ᴊᴏɪɴ ʀᴇQᴜɪʀᴇᴅ ᴄʜᴀɴɴᴇʟꜱ ᴛᴏ ᴄᴏɴᴛɪɴᴜᴇ",
        )
        caption = (
            f"{e('lock','·')} <b>𝐏 ʜ ᴀ ɴ ᴛ ᴏ ᴍ</b>\n"
            f"{BDIV}\n"
            f"{e('info','·')} <i>ᴩʟᴇᴀꜱᴇ ᴊᴏɪɴ ᴀʟʟ ᴄʜᴀɴɴᴇʟꜱ ᴛᴏ ᴜꜱᴇ ᴛʜᴇ ʙᴏᴛ·</i>"
        )
        if img:
            await msg.answer_photo(
                photo=BufferedInputFile(img,"welcome.jpg"),
                caption=caption, parse_mode=ParseMode.HTML,
                reply_markup=kb_verify(missing))
        else:
            await msg.answer(caption, parse_mode=ParseMode.HTML,
                             reply_markup=kb_verify(missing))
        return

    welcome_text = await get_cfg("welcome_text") or (
        f"{e('star','·')} <b>𝐏 ʜ ᴀ ɴ ᴛ ᴏ ᴍ</b>\n"
        f"{BDIV}\n"
        f"<blockquote expandable>"
        f"{e('netflix','·')} ɴᴇᴛꜰʟɪx TV · Login · Phone · PC\n"
        f"{e('cr','·')} ᴄʀᴜɴᴄʜʏʀᴏʟʟ TV ᴀᴄᴛɪᴠᴀᴛɪᴏɴ\n"
        f"{e('bolt','·')} ꜰᴀꜱᴛ · ꜱᴇᴄᴜʀᴇ · ᴀᴜᴛᴏᴍᴀᴛᴇᴅ\n"
        f"</blockquote>\n"
        f"{SDIV}\n"
        f"{e('info','·')} <i>ꜱᴇʟᴇᴄᴛ ᴀ ꜱᴇʀᴠɪᴄᴇ ʙᴇʟᴏᴡ·</i>"
    )

    user     = await get_user(uid)
    start_v  = await get_cfg("start_video")
    start_g  = await get_cfg("start_gif")

    img = await get_anime_image("welcome",
        overlay_title="𝐏 ʜ ᴀ ɴ ᴛ ᴏ ᴍ",
        overlay_sub="ɴᴇᴛꜰʟɪx  ·  ᴄʀᴜɴᴄʜʏʀᴏʟʟ",
        overlay_stat=f"ᴩʟᴀɴ: {PLANS[user.get('plan','free')]['badge']}",
    )

    if start_v:
        await msg.answer_video(video=start_v,
            caption=welcome_text, parse_mode=ParseMode.HTML,
            reply_markup=kb_main_menu())
    elif start_g:
        await msg.answer_animation(animation=start_g,
            caption=welcome_text, parse_mode=ParseMode.HTML,
            reply_markup=kb_main_menu())
    elif img:
        await msg.answer_photo(
            photo=BufferedInputFile(img, "phantom.jpg"),
            caption=welcome_text, parse_mode=ParseMode.HTML,
            reply_markup=kb_main_menu())
    else:
        await msg.answer(welcome_text, parse_mode=ParseMode.HTML,
                         reply_markup=kb_main_menu())

    # Trial offer for new users
    if not user.get("trial_used") and user.get("plan","free") == "free":
        trial_days = int(await get_cfg("trial_days", 1))
        await msg.answer(
            f"{e('gift','·')} <b>ꜰʀᴇᴇ ᴛʀɪᴀʟ ᴀᴠᴀɪʟᴀʙʟᴇ!</b>\n"
            f"{e('arrow','·')} ɢᴇᴛ <b>{trial_days} ᴅᴀʏ(ꜱ)</b> ᴄᴏʀᴇ ᴩʟᴀɴ ꜰʀᴇᴇ·",
            parse_mode=ParseMode.HTML,
            reply_markup=kb(
                [btn("ᴄʟᴀɪᴍ ᴛʀɪᴀʟ", cb="m_trial", style="success", emoji_key="gift")],
            ))


# ── /tv /login /phone /pc /crtv ──────────────────────────────
@router.message(Command("tv"))
async def cmd_tv(msg: Message, bot: Bot):
    args = msg.text.split(None, 1)
    if len(args) < 2 or not args[1].strip():
        await msg.answer(
            f"{e('info','·')} ᴜꜱᴀɢᴇ: <code>/tv CODE</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=kb([btn("« ʙᴀᴄᴋ", cb="m_nf_menu", style="primary", emoji_key="back")]))
        return
    await _run_nf_login(msg, bot, args[1].strip().upper(), "tv")


@router.message(Command("login"))
async def cmd_login(msg: Message, bot: Bot):
    args = msg.text.split(None, 1)
    if len(args) < 2:
        await msg.answer(f"{e('info','·')} ᴜꜱᴀɢᴇ: <code>/login CODE</code>",
                         parse_mode=ParseMode.HTML)
        return
    await _run_nf_login(msg, bot, args[1].strip().upper(), "login")


@router.message(Command("phone"))
async def cmd_phone(msg: Message, bot: Bot):
    args = msg.text.split(None, 1)
    if len(args) < 2:
        await msg.answer(f"{e('info','·')} ᴜꜱᴀɢᴇ: <code>/phone CODE</code>",
                         parse_mode=ParseMode.HTML)
        return
    await _run_nf_login(msg, bot, args[1].strip().upper(), "phone")


@router.message(Command("pc"))
async def cmd_pc(msg: Message, bot: Bot):
    args = msg.text.split(None, 1)
    if len(args) < 2:
        await msg.answer(f"{e('info','·')} ᴜꜱᴀɢᴇ: <code>/pc CODE</code>",
                         parse_mode=ParseMode.HTML)
        return
    await _run_nf_login(msg, bot, args[1].strip().upper(), "pc")


@router.message(Command("crtv"))
async def cmd_crtv(msg: Message, bot: Bot):
    args = msg.text.split(None, 1)
    if len(args) < 2:
        await msg.answer(f"{e('info','·')} ᴜꜱᴀɢᴇ: <code>/crtv CODE</code>",
                         parse_mode=ParseMode.HTML)
        return
    await _run_cr_login(msg, bot, args[1].strip().upper())


# ── /me ───────────────────────────────────────────────────────
@router.message(Command("me"))
async def cmd_me(msg: Message, bot: Bot):
    uid  = msg.from_user.id
    user = await get_user(uid)
    plan = user.get("plan","free")
    exp  = user.get("plan_expiry")
    exp_s = time.strftime("%Y-%m-%d", time.gmtime(exp)) if exp else "∞"
    daily = PLANS[plan]["daily"]
    used  = user.get("daily_count", 0)
    refs  = user.get("ref_count", 0)
    joined = time.strftime("%Y-%m-%d", time.gmtime(user.get("joined_at", 0)))

    img = await get_anime_image("stats",
        overlay_title="𝐌 ʏ  ᴩ ʀ ᴏ ꜰ ɪ ʟ ᴇ",
        overlay_sub=f"ᴩʟᴀɴ: {PLANS[plan]['badge']}",
        overlay_stat=f"ᴜꜱᴇᴅ: {used}/{daily}  ·  ʀᴇꜰꜱ: {refs}",
    )

    # Rich Message profile
    try:
        blocks = [
            rich_heading("𝐌 ʏ  ᴩ ʀ ᴏ ꜰ ɪ ʟ ᴇ", "user"),
            rich_divider(),
            rich_table(
                ["ꜰɪᴇʟᴅ","ᴠᴀʟᴜᴇ"],
                [
                    ["ɪᴅ",      str(uid)],
                    ["ᴩʟᴀɴ",    PLANS[plan]["badge"]],
                    ["ᴇxᴩɪʀʏ",  exp_s],
                    ["ᴜꜱᴇᴅ",    f"{used}/{daily}"],
                    ["ʀᴇꜰꜱ",    str(refs)],
                    ["ᴊᴏɪɴᴇᴅ",  joined],
                ]
            ),
            rich_footer("𝐏 ʜ ᴀ ɴ ᴛ ᴏ ᴍ"),
        ]
        await bot.send_rich_message(
            chat_id=uid,
            rich_message=InputRichMessage(blocks=blocks),
            reply_markup=kb_back(),
        )
    except Exception:
        caption = (
            f"{e('user','·')} <b>𝐌 ʏ  ᴩ ʀ ᴏ ꜰ ɪ ʟ ᴇ</b>\n"
            f"{BDIV}\n"
            f"<blockquote expandable>"
            f"{e('id','·')} ɪᴅ: <code>{uid}</code>\n"
            f"{e('bolt','·')} ᴩʟᴀɴ: <b>{PLANS[plan]['badge']}</b>\n"
            f"{e('time','·')} ᴇxᴩɪʀʏ: <b>{exp_s}</b>\n"
            f"{e('chart','·')} ᴜꜱᴇᴅ: <b>{used}/{daily}</b>\n"
            f"{e('refer','·')} ʀᴇꜰꜱ: <b>{refs}</b>\n"
            f"{e('history','·')} ᴊᴏɪɴᴇᴅ: <b>{joined}</b>\n"
            f"</blockquote>"
        )
        if img:
            await msg.answer_photo(
                photo=BufferedInputFile(img,"me.jpg"),
                caption=caption, parse_mode=ParseMode.HTML, reply_markup=kb_back())
        else:
            await msg.answer(caption, parse_mode=ParseMode.HTML, reply_markup=kb_back())


# ── /plans ────────────────────────────────────────────────────
@router.message(Command("plans"))
async def cmd_plans(msg: Message, bot: Bot):
    uid  = msg.from_user.id
    user = await get_user(uid)
    cur  = user.get("plan","free")

    img = await get_anime_image("plans",
        overlay_title="𝐏 ʜ ᴀ ɴ ᴛ ᴏ ᴍ  ᴩʟᴀɴꜱ",
        overlay_sub="ᴄʜᴏᴏꜱᴇ ʏᴏᴜʀ ᴛɪᴇʀ",
    )

    try:
        blocks = [
            rich_heading("ᴩʟᴀɴ ᴄᴏᴍᴩᴀʀɪꜱᴏɴ", "crown"),
            rich_divider(),
            rich_table(
                ["ᴩʟᴀɴ","ᴅᴀɪʟʏ","ᴛᴠ","ʟᴏɢɪɴ","ᴩʜᴏɴᴇ","ᴩᴄ"],
                [
                    ["ꜰʀᴇᴇ",  "2",  "✓","✓","✗","✗"],
                    ["ᴄᴏʀᴇ",  "10", "✓","✓","✓","✗"],
                    ["ᴇʟɪᴛᴇ", "20", "✓","✓","✓","✓"],
                    ["ʀᴏᴏᴛ",  "30", "✓","✓","✓","✓"],
                ]
            ),
            rich_divider(),
            rich_para(f"ᴄᴜʀʀᴇɴᴛ: {PLANS[cur]['badge']}"),
            rich_footer("ᴜꜱᴇ /redeem ᴋᴇʏ ᴛᴏ ᴜᴩɢʀᴀᴅᴇ"),
        ]
        await bot.send_rich_message(
            chat_id=uid,
            rich_message=InputRichMessage(blocks=blocks),
            reply_markup=kb_plan_upgrade(),
        )
    except Exception:
        caption = (
            f"{e('crown','·')} <b>ᴩʟᴀɴꜱ</b>\n"
            f"{BDIV}\n"
            f"<blockquote expandable>"
            f"ꜰʀᴇᴇ  — 2/ᴅ · ᴛᴠ · ʟᴏɢɪɴ\n"
            f"ᴄᴏʀᴇ  — 10/ᴅ · + ᴩʜᴏɴᴇ\n"
            f"ᴇʟɪᴛᴇ — 20/ᴅ · + ᴩᴄ\n"
            f"ʀᴏᴏᴛ  — 30/ᴅ · ᴀʟʟ ᴍᴇᴛʜᴏᴅꜱ\n"
            f"</blockquote>\n"
            f"{e('bolt','·')} ᴄᴜʀʀᴇɴᴛ: <b>{PLANS[cur]['badge']}</b>"
        )
        if img:
            await msg.answer_photo(
                photo=BufferedInputFile(img,"plans.jpg"),
                caption=caption, parse_mode=ParseMode.HTML,
                reply_markup=kb_plan_upgrade())
        else:
            await msg.answer(caption, parse_mode=ParseMode.HTML,
                             reply_markup=kb_plan_upgrade())


# ── /redeem ───────────────────────────────────────────────────
@router.message(Command("redeem"))
async def cmd_redeem(msg: Message, bot: Bot, state: FSMContext):
    args = msg.text.split(None, 1)
    if len(args) < 2:
        await msg.answer(
            f"{e('key','·')} <b>ʀᴇᴅᴇᴇᴍ ᴋᴇʏ</b>\n"
            f"{e('info','·')} ꜱᴇɴᴅ: <code>/redeem YOUR-KEY</code>\n"
            f"{e('arrow','·')} ꜰᴏʀᴍᴀᴛ: <code>PHM-XXXXXXXX</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=kb_back())
        return
    key_str = args[1].strip().upper()
    await _process_redeem(msg, bot, key_str)


async def _process_redeem(msg: Message, bot: Bot, key_str: str):
    uid = msg.from_user.id
    doc = await get_db().keys.find_one({"key": key_str, "used": False})
    if not doc:
        await msg.answer(
            f"{e('cross','·')} ɪɴᴠᴀʟɪᴅ ᴏʀ ᴀʟʀᴇᴀᴅʏ ᴜꜱᴇᴅ ᴋᴇʏ·",
            parse_mode=ParseMode.HTML,
            reply_markup=kb_back())
        return
    plan   = doc["plan"]
    days   = doc.get("days", 30)
    expiry = int(time.time()) + days * 86400
    await get_db().keys.update_one(
        {"_id": doc["_id"]},
        {"$set": {"used": True, "used_by": uid, "used_at": int(time.time())}})
    await upsert_user(uid, {"$set": {
        "plan": plan, "plan_expiry": expiry, "plan_source": f"key:{key_str}"}})
    exp_s = time.strftime("%Y-%m-%d", time.gmtime(expiry))
    await msg.answer(
        f"{e('check','·')} <b>ᴋᴇʏ ʀᴇᴅᴇᴇᴍᴇᴅ</b>\n"
        f"{BDIV}\n"
        f"{e('bolt','·')} ᴩʟᴀɴ: <b>{PLANS[plan]['badge']}</b>\n"
        f"{e('time','·')} ᴇxᴩɪʀʏ: <b>{exp_s}</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=kb_back())


# ── /refer ────────────────────────────────────────────────────
@router.message(Command("refer"))
async def cmd_refer(msg: Message, bot: Bot):
    uid      = msg.from_user.id
    user     = await get_user(uid)
    ref_code = user.get("ref_code","")
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{ref_code}"
    bonus    = int(await get_cfg("ref_bonus_days", 3))
    refs     = user.get("ref_count", 0)

    img = await get_anime_image("refer",
        overlay_title="ʀᴇꜰᴇʀ & ᴇᴀʀɴ",
        overlay_sub=f"ʙᴏɴᴜꜱ: +{bonus} ᴅᴀʏꜱ ᴩᴇʀ ʀᴇꜰ",
        overlay_stat=f"ʏᴏᴜʀ ʀᴇꜰꜱ: {refs}",
    )
    caption = (
        f"{e('refer','·')} <b>ʀᴇꜰᴇʀʀᴀʟ</b>\n"
        f"{BDIV}\n"
        f"{e('bolt','·')} ʙᴏɴᴜꜱ: <b>+{bonus} ᴅᴀʏꜱ</b> ᴩᴇʀ ʀᴇꜰ\n"
        f"{e('users','·')} ʀᴇꜰꜱ: <b>{refs}</b>\n"
        f"{SDIV}\n"
        f"{e('link','·')} <code>{ref_link}</code>"
    )
    markup = kb(
        [btn("ᴄᴏᴩʏ ʟɪɴᴋ", copy=ref_link, style="success", emoji_key="copy")],
        [btn("« ʙᴀᴄᴋ",     cb="m_main",   style="primary", emoji_key="back")],
    )
    if img:
        await msg.answer_photo(
            photo=BufferedInputFile(img,"refer.jpg"),
            caption=caption, parse_mode=ParseMode.HTML, reply_markup=markup)
    else:
        await msg.answer(caption, parse_mode=ParseMode.HTML, reply_markup=markup)


# ── /trial ────────────────────────────────────────────────────
@router.message(Command("trial"))
async def cmd_trial(msg: Message, bot: Bot):
    uid  = msg.from_user.id
    user = await get_user(uid)
    if user.get("plan","free") != "free":
        await msg.answer(
            f"{e('info','·')} ʏᴏᴜ ᴀʟʀᴇᴀᴅʏ ʜᴀᴠᴇ ᴀ ᴩᴀɪᴅ ᴩʟᴀɴ·",
            parse_mode=ParseMode.HTML)
        return
    if user.get("trial_used"):
        await msg.answer(
            f"{e('cross','·')} ᴛʀɪᴀʟ ᴀʟʀᴇᴀᴅʏ ᴜꜱᴇᴅ·",
            parse_mode=ParseMode.HTML)
        return
    trial_days = int(await get_cfg("trial_days", 1))
    expiry     = int(time.time()) + trial_days * 86400
    await upsert_user(uid, {"$set": {
        "plan": "core", "plan_expiry": expiry,
        "trial_used": True, "plan_source": "trial",
    }})
    exp_s = time.strftime("%Y-%m-%d", time.gmtime(expiry))
    await msg.answer(
        f"{e('gift','·')} <b>ᴛʀɪᴀʟ ᴀᴄᴛɪᴠᴀᴛᴇᴅ</b>\n"
        f"{BDIV}\n"
        f"{e('bolt','·')} ᴩʟᴀɴ: <b>ᴄᴏʀᴇ</b>\n"
        f"{e('time','·')} ᴇxᴩɪʀʏ: <b>{exp_s}</b>",
        parse_mode=ParseMode.HTML, reply_markup=kb_back())


# ── /history ──────────────────────────────────────────────────
@router.message(Command("history"))
async def cmd_history(msg: Message, bot: Bot):
    uid  = msg.from_user.id
    logs = await get_db().login_logs.find(
        {"uid": uid}, sort=[("ts",-1)], limit=10).to_list(10)
    if not logs:
        await msg.answer(
            f"{e('history','·')} ɴᴏ ʜɪꜱᴛᴏʀʏ ʏᴇᴛ·",
            parse_mode=ParseMode.HTML, reply_markup=kb_back())
        return

    try:
        rows = []
        for lg in logs:
            ts  = time.strftime("%m/%d %H:%M", time.gmtime(lg.get("ts",0)))
            svc = lg.get("service","?").upper()
            ok  = "✓" if lg.get("success") else "✗"
            mth = lg.get("method","?")
            rows.append([ts, svc, mth, ok])
        blocks = [
            rich_heading("ʟᴏɢɪɴ ʜɪꜱᴛᴏʀʏ","history"),
            rich_divider(),
            rich_table(["ᴛɪᴍᴇ","ꜱᴠᴄ","ᴍᴇᴛʜ","ꜱᴛᴀᴛ"], rows),
            rich_footer("ʟᴀꜱᴛ 10 ʟᴏɢɪɴꜱ"),
        ]
        await bot.send_rich_message(
            chat_id=uid,
            rich_message=InputRichMessage(blocks=blocks),
            reply_markup=kb_back(),
        )
    except Exception:
        lines = []
        for lg in logs:
            ts  = time.strftime("%m/%d %H:%M", time.gmtime(lg.get("ts",0)))
            svc = lg.get("service","?").upper()
            ok  = e("check","·") if lg.get("success") else e("cross","·")
            lines.append(f"{ok} [{ts}] {svc} · {lg.get('method','?')}")
        text = (
            f"{e('history','·')} <b>ʜɪꜱᴛᴏʀʏ</b>\n"
            f"{BDIV}\n"
            f"<blockquote expandable>{'·'.join(lines)}</blockquote>"
        )
        await msg.answer(text, parse_mode=ParseMode.HTML, reply_markup=kb_back())


# ── /stats ────────────────────────────────────────────────────
@router.message(Command("stats"))
async def cmd_stats(msg: Message, bot: Bot):
    uid  = msg.from_user.id
    db   = get_db()
    total  = await db.users.count_documents({})
    active = await db.users.count_documents(
        {"last_active": {"$gte": int(time.time()) - 86400}})
    nf  = await db.nf_cookies.count_documents({"status": "live"})
    cr  = await db.cr_accounts.count_documents({"status": "live"})
    tot_l = await db.login_logs.count_documents({})
    plan_c = {p: await db.users.count_documents({"plan": p}) for p in PLANS}

    img = await get_anime_image("stats",
        overlay_title="ʙᴏᴛ ꜱᴛᴀᴛɪꜱᴛɪᴄꜱ",
        overlay_sub=f"ᴜꜱᴇʀꜱ: {total:,}  ·  ᴀᴄᴛɪᴠᴇ: {active:,}",
        overlay_stat=f"ᴄᴏᴏᴋɪᴇꜱ: {nf}  ·  ᴄʀ: {cr}",
    )

    try:
        blocks = [
            rich_heading("ʙᴏᴛ ꜱᴛᴀᴛꜱ","stats"),
            rich_divider(),
            rich_table(
                ["ᴍᴇᴛʀɪᴄ","ᴠᴀʟᴜᴇ"],
                [
                    ["ᴛᴏᴛᴀʟ ᴜꜱᴇʀꜱ",   f"{total:,}"],
                    ["ᴀᴄᴛɪᴠᴇ 24ʜ",    f"{active:,}"],
                    ["ɴꜰ ᴄᴏᴏᴋɪᴇꜱ",   str(nf)],
                    ["ᴄʀ ᴀᴄᴄᴏᴜɴᴛꜱ",  str(cr)],
                    ["ᴛᴏᴛᴀʟ ʟᴏɢɪɴꜱ", f"{tot_l:,}"],
                ]
            ),
            rich_divider(),
            rich_table(
                ["ᴩʟᴀɴ","ᴄᴏᴜɴᴛ"],
                [[p.upper(), str(plan_c[p])] for p in PLANS]
            ),
            rich_footer("𝐏 ʜ ᴀ ɴ ᴛ ᴏ ᴍ"),
        ]
        await bot.send_rich_message(
            chat_id=uid,
            rich_message=InputRichMessage(blocks=blocks),
            reply_markup=kb_back(),
        )
    except Exception:
        caption = (
            f"{e('chart','·')} <b>ꜱᴛᴀᴛꜱ</b>\n"
            f"{BDIV}\n"
            f"<blockquote expandable>"
            f"{e('users','·')} ᴜꜱᴇʀꜱ: <b>{total:,}</b>\n"
            f"{e('bolt','·')} ᴀᴄᴛɪᴠᴇ 24ʜ: <b>{active:,}</b>\n"
            f"{e('netflix','·')} ɴꜰ ᴄᴏᴏᴋɪᴇꜱ: <b>{nf}</b>\n"
            f"{e('cr','·')} ᴄʀ ᴀᴄᴄꜱ: <b>{cr}</b>\n"
            f"{e('history','·')} ᴛᴏᴛᴀʟ ʟᴏɢɪɴꜱ: <b>{tot_l:,}</b>\n"
            f"</blockquote>"
        )
        if img:
            await msg.answer_photo(
                photo=BufferedInputFile(img,"stats.jpg"),
                caption=caption, parse_mode=ParseMode.HTML, reply_markup=kb_back())
        else:
            await msg.answer(caption, parse_mode=ParseMode.HTML, reply_markup=kb_back())


# ── /help ─────────────────────────────────────────────────────
@router.message(Command("help"))
async def cmd_help(msg: Message, bot: Bot):
    uid = msg.from_user.id
    try:
        blocks = [
            rich_heading("𝐏 ʜ ᴀ ɴ ᴛ ᴏ ᴍ  ʜᴇʟᴩ","info"),
            rich_divider(),
            InputRichBlockDetails(
                header=rt_bold("ɴᴇᴛꜰʟɪx"),
                blocks=[
                    rich_list([
                        "/tv CODE — ᴛᴠ ᴀᴄᴛɪᴠᴀᴛɪᴏɴ (ꜰʀᴇᴇ+)",
                        "/login CODE — ᴅɪʀᴇᴄᴛ (ꜰʀᴇᴇ+)",
                        "/phone CODE — ᴩʜᴏɴᴇ (ᴄᴏʀᴇ+)",
                        "/pc CODE — ᴩᴄ (ᴇʟɪᴛᴇ+)",
                    ])
                ]
            ),
            InputRichBlockDetails(
                header=rt_bold("ᴄʀᴜɴᴄʜʏʀᴏʟʟ"),
                blocks=[rich_list(["/crtv CODE — ᴛᴠ ᴀᴄᴛɪᴠᴀᴛɪᴏɴ (ꜰʀᴇᴇ+)"])]
            ),
            # ── continued from cut ─────────────────────────────────────────────────────
            InputRichBlockDetails(
                header=rt_bold("ᴀᴄᴄᴏᴜɴᴛ"),
                blocks=[rich_list([
                    "/me — ᴩʀᴏꜰɪʟᴇ",
                    "/plans — ᴩʟᴀɴ ᴄᴏᴍᴩᴀʀɪꜱᴏɴ",
                    "/redeem KEY — ᴀᴄᴛɪᴠᴀᴛᴇ ᴩʟᴀɴ",
                    "/refer — ᴩᴀʀᴛɴᴇʀ ʟɪɴᴋ",
                    "/trial — ꜰʀᴇᴇ 12ʜ ᴛʀɪᴀʟ",
                    "/history — ʟᴏɢɪɴ ʜɪꜱᴛᴏʀʏ",
                    "/stats — ʙᴏᴛ ꜱᴛᴀᴛɪꜱᴛɪᴄꜱ",
                ])]
            ),
            rich_divider(),
            rich_quote("ᴘᴡᴅ ʙʏ ᴘʜᴀɴᴛᴏᴍ • ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴜꜱᴇ ᴏɴʟʏ", expandable=False),
        ]
        img = await get_anime_image(
            "help",
            overlay_title="ᴩ ʜ ᴀ ɴ ᴛ ᴏ ᴍ",
            overlay_sub="ᴄᴏᴍᴍᴀɴᴅ ᴄᴇɴᴛʀᴇ",
            overlay_stat="ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅꜱ",
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [btn("ɴᴇᴛꜰʟɪx ᴍᴇɴᴜ","m_nf_menu",style="primary"),
             btn("ᴄʀᴜɴᴄʜʏʀᴏʟʟ","m_cr_menu",style="primary")],
            [btn("ᴍʏ ᴩʀᴏꜰɪʟᴇ","m_me",style="success"),
             btn("ᴩʟᴀɴꜱ","m_plans",style="success")],
            [btn("« ᴍᴀɪɴ ᴍᴇɴᴜ","m_main")],
        ])
        if img:
            await bot.send_photo(uid, BufferedInputFile(img,"help.jpg"),
                caption=f'{e("info")} ᴩʜᴀɴᴛᴏᴍ ʜᴇʟᴩ', reply_markup=kb)
        await bot.send_rich_message(
            chat_id=uid,
            rich_message=InputRichMessage(blocks=blocks),
            reply_markup=kb,
        )
    except Exception as ex:
        log.exception("cmd_help %s", ex)
        await msg.answer(
            f'{e("info")} <b>ᴩʜᴀɴᴛᴏᴍ ʜᴇʟᴩ</b>\n\n'
            f'{e("spark")} <b>ɴᴇᴛꜰʟɪx</b>\n'
            f'  /tv /login /phone /pc\n\n'
            f'{e("spark")} <b>ᴄʀᴜɴᴄʜʏʀᴏʟʟ</b>\n'
            f'  /crtv\n\n'
            f'{e("spark")} <b>ᴀᴄᴄᴏᴜɴᴛ</b>\n'
            f'  /me /plans /redeem /refer /trial /history /stats',
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [btn("ᴍᴀɪɴ ᴍᴇɴᴜ","m_main",style="primary")],
            ]),
            parse_mode="HTML",
        )


# ═══════════════════════════════════════════════════════════════════════════════
# §  P R O M P T   C A L L B A C K S
# ═══════════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data == "prompt_tv")
async def prompt_tv(cq: CallbackQuery):
    await cq.answer()
    await cq.message.answer(
        f'{e("nf")} <b>ɴᴇᴛꜰʟɪx ᴛᴠ ᴀᴄᴛɪᴠᴀᴛɪᴏɴ</b>\n\n'
        f'ꜱᴇɴᴅ ʏᴏᴜʀ <b>8-ᴅɪɢɪᴛ ᴛᴠ ᴄᴏᴅᴇ</b>:\n'
        f'<code>/tv XXXXXXXX</code>\n\n'
        f'{e("info")} ꜰᴏᴜɴᴅ ᴀᴛ netflix.com/activate',
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [btn("« ɴᴇᴛꜰʟɪx ᴍᴇɴᴜ","m_nf_menu")],
        ]),
    )

@router.callback_query(F.data == "prompt_login")
async def prompt_login(cq: CallbackQuery):
    await cq.answer()
    await cq.message.answer(
        f'{e("nf")} <b>ɴᴇᴛꜰʟɪx ᴅɪʀᴇᴄᴛ ʟᴏɢɪɴ</b>\n\n'
        f'ꜱᴇɴᴅ ʏᴏᴜʀ ᴛᴠ ᴄᴏᴅᴇ:\n'
        f'<code>/login XXXXXXXX</code>',
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [btn("« ɴᴇᴛꜰʟɪx ᴍᴇɴᴜ","m_nf_menu")],
        ]),
    )

@router.callback_query(F.data == "prompt_phone")
async def prompt_phone(cq: CallbackQuery):
    await cq.answer()
    await cq.message.answer(
        f'{e("nf")} <b>ɴᴇᴛꜰʟɪx ᴩʜᴏɴᴇ ᴍᴇᴛʜᴏᴅ</b>\n\n'
        f'{e("warn")} ʀᴇǫᴜɪʀᴇꜱ <b>ᴄᴏʀᴇ+</b> ᴩʟᴀɴ\n\n'
        f'<code>/phone XXXXXXXX</code>',
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [btn("ᴜᴩɢʀᴀᴅᴇ ᴩʟᴀɴ","m_plans",style="primary"),
             btn("« ʙᴀᴄᴋ","m_nf_menu")],
        ]),
    )

@router.callback_query(F.data == "prompt_pc")
async def prompt_pc(cq: CallbackQuery):
    await cq.answer()
    await cq.message.answer(
        f'{e("nf")} <b>ɴᴇᴛꜰʟɪx ᴩᴄ ᴍᴇᴛʜᴏᴅ</b>\n\n'
        f'{e("warn")} ʀᴇǫᴜɪʀᴇꜱ <b>ᴇʟɪᴛᴇ+</b> ᴩʟᴀɴ\n\n'
        f'<code>/pc XXXXXXXX</code>',
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [btn("ᴜᴩɢʀᴀᴅᴇ ᴩʟᴀɴ","m_plans",style="primary"),
             btn("« ʙᴀᴄᴋ","m_nf_menu")],
        ]),
    )

@router.callback_query(F.data == "prompt_crtv")
async def prompt_crtv(cq: CallbackQuery):
    await cq.answer()
    await cq.message.answer(
        f'{e("cr")} <b>ᴄʀᴜɴᴄʜʏʀᴏʟʟ ᴛᴠ ᴀᴄᴛɪᴠᴀᴛɪᴏɴ</b>\n\n'
        f'ᴄᴏᴅᴇ ꜰʀᴏᴍ <b>crunchyroll.com/activate</b>\n\n'
        f'<code>/crtv XXXXXXXX</code>',
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [btn("« ᴄʀᴜɴᴄʜʏʀᴏʟʟ ᴍᴇɴᴜ","m_cr_menu")],
        ]),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# §  C A L L B A C K   R O U T E R
# ═══════════════════════════════════════════════════════════════════════════════

async def _edit_or_send(cq: CallbackQuery, bot: Bot,
                        blocks, kb, photo_key: str,
                        photo_title="", photo_sub="", photo_stat=""):
    """Edit current message if possible, else send new."""
    img = await get_anime_image(photo_key, photo_title, photo_sub, photo_stat)
    try:
        if img:
            media = InputMediaPhoto(media=BufferedInputFile(img, f"{photo_key}.jpg"))
            await cq.message.edit_media(media=media, reply_markup=kb)
        else:
            await cq.message.edit_reply_markup(reply_markup=kb)
        await bot.send_rich_message(
            chat_id=cq.from_user.id,
            rich_message=InputRichMessage(blocks=blocks),
            reply_markup=kb,
        )
    except Exception:
        if img:
            await bot.send_photo(cq.from_user.id,
                BufferedInputFile(img, f"{photo_key}.jpg"), reply_markup=kb)
        await bot.send_rich_message(
            chat_id=cq.from_user.id,
            rich_message=InputRichMessage(blocks=blocks),
            reply_markup=kb,
        )


@router.callback_query(F.data == "m_main")
async def cb_main(cq: CallbackQuery, bot: Bot):
    await cq.answer()
    uid = cq.from_user.id
    user = await get_user(uid)
    plan = user.get("plan","free").upper()
    daily = user.get("daily_used",0)
    daily_max = PLAN_DAILY.get(user.get("plan","free"),2)
    blocks = [
        rich_heading("ᴩ ʜ ᴀ ɴ ᴛ ᴏ ᴍ","spark"),
        rich_divider(),
        InputRichBlockParagraph(text=RichText(texts=[
            rt_bold("ᴡᴇʟᴄᴏᴍᴇ ʙᴀᴄᴋ"),
            rt(" — "),
            rt_italic(cq.from_user.first_name or "ᴜꜱᴇʀ"),
        ])),
        rich_table(
            ["ᴩʟᴀɴ","ᴅᴀɪʟʏ","ᴜꜱᴇᴅ"],
            [[plan, str(daily_max), str(daily)]],
        ),
        rich_divider(),
        rich_quote("ꜱᴇʟᴇᴄᴛ ᴀ ꜱᴇʀᴠɪᴄᴇ ᴛᴏ ᴀᴄᴛɪᴠᴀᴛᴇ", expandable=False),
    ]
    await _edit_or_send(cq, bot, blocks, kb_main_menu(),
        "main","ᴩʜᴀɴᴛᴏᴍ","ᴜʟᴛɪᴍᴀᴛᴇ ᴀᴄᴛɪᴠᴀᴛᴏʀ",f"ᴩʟᴀɴ: {plan}")


@router.callback_query(F.data == "m_nf_menu")
async def cb_nf_menu(cq: CallbackQuery, bot: Bot):
    await cq.answer()
    uid = cq.from_user.id
    user = await get_user(uid)
    plan = user.get("plan","free")
    nf_stock = await db.cookies.count_documents({"service":"nf","used":False,"valid":True})
    blocks = [
        rich_heading("ɴᴇᴛꜰʟɪx ᴀᴄᴛɪᴠᴀᴛᴏʀ","nf"),
        rich_divider(),
        rich_table(
            ["ᴍᴇᴛʜᴏᴅ","ᴩʟᴀɴ","ꜱᴛᴀᴛᴜꜱ"],
            [
                ["TV","FREE+","✓ ACTIVE"],
                ["LOGIN","FREE+","✓ ACTIVE"],
                ["PHONE","CORE+","✓ ACTIVE" if plan in ("core","elite","root") else "✗ LOCKED"],
                ["PC","ELITE+","✓ ACTIVE" if plan in ("elite","root") else "✗ LOCKED"],
            ],
            is_compact=True,
        ),
        rich_divider(),
        rich_quote(f"ᴄᴏᴏᴋɪᴇ ꜱᴛᴏᴄᴋ: {nf_stock}", expandable=False),
    ]
    await _edit_or_send(cq, bot, blocks, kb_nf_menu(),
        "nf_menu","ɴᴇᴛꜰʟɪx","ᴀᴄᴛɪᴠᴀᴛɪᴏɴ ʜᴜʙ",f"ꜱᴛᴏᴄᴋ: {nf_stock}")


@router.callback_query(F.data == "m_cr_menu")
async def cb_cr_menu(cq: CallbackQuery, bot: Bot):
    await cq.answer()
    cr_stock = await db.cr_accounts.count_documents({"used":False,"valid":True})
    blocks = [
        rich_heading("ᴄʀᴜɴᴄʜʏʀᴏʟʟ ᴀᴄᴛɪᴠᴀᴛᴏʀ","cr"),
        rich_divider(),
        rich_table(
            ["ᴍᴇᴛʜᴏᴅ","ᴩʟᴀɴ","ꜱᴛᴀᴛᴜꜱ"],
            [["TV SSO","FREE+","✓ ACTIVE"]],
            is_compact=True,
        ),
        rich_divider(),
        rich_quote(f"ᴀᴄᴄᴏᴜɴᴛ ꜱᴛᴏᴄᴋ: {cr_stock}", expandable=False),
    ]
    await _edit_or_send(cq, bot, blocks, kb_cr_menu(),
        "cr_menu","ᴄʀᴜɴᴄʜʏʀᴏʟʟ","ᴀɴɪᴍᴇ ᴀᴄᴛɪᴠᴀᴛɪᴏɴ",f"ꜱᴛᴏᴄᴋ: {cr_stock}")


@router.callback_query(F.data == "m_me")
async def cb_me(cq: CallbackQuery, bot: Bot):
    await cq.answer()
    await cmd_me.__wrapped__(cq.message, bot) if hasattr(cmd_me,"__wrapped__") \
        else await bot.send_message(cq.from_user.id,"/me")


@router.callback_query(F.data == "m_plans")
async def cb_plans(cq: CallbackQuery, bot: Bot):
    await cq.answer()
    uid = cq.from_user.id
    blocks = [
        rich_heading("ᴩʜᴀɴᴛᴏᴍ ᴩʟᴀɴꜱ","crown"),
        rich_divider(),
        rich_table(
            ["ᴩʟᴀɴ","ᴅᴀɪʟʏ","ᴩʀɪᴄᴇ","ʙᴇɴᴇꜰɪᴛꜱ"],
            [
                ["FREE","2","₹0","TV+LOGIN"],
                ["CORE","10","₹49","PHONE"],
                ["ELITE","25","₹99","PC+PHONE"],
                ["ROOT","∞","₹199","ALL+PRIO"],
            ],
        ),
        rich_divider(),
        InputRichBlockDetails(
            header=rt_bold("ᴄᴏʀᴇ — ᴅᴇᴛᴀɪʟꜱ"),
            blocks=[rich_list(["10 ʟᴏɢɪɴꜱ/ᴅᴀʏ","ɴᴇᴛꜰʟɪx ᴩʜᴏɴᴇ ᴍᴇᴛʜᴏᴅ",
                               "ᴄʀᴜɴᴄʜʏʀᴏʟʟ ꜱꜱᴏ","ᴩʀɪᴏʀɪᴛʏ ꜱᴜᴩᴩᴏʀᴛ"])]
        ),
        InputRichBlockDetails(
            header=rt_bold("ᴇʟɪᴛᴇ — ᴅᴇᴛᴀɪʟꜱ"),
            blocks=[rich_list(["25 ʟᴏɢɪɴꜱ/ᴅᴀʏ","ᴀʟʟ ɴᴇᴛꜰʟɪx ᴍᴇᴛʜᴏᴅꜱ",
                               "ꜰᴀꜱᴛᴇʀ ᴄᴏᴏᴋɪᴇ ǫᴜᴇᴜᴇ","ᴅᴇᴅɪᴄᴀᴛᴇᴅ ꜱʟᴏᴛꜱ"])]
        ),
        InputRichBlockDetails(
            header=rt_bold("ʀᴏᴏᴛ — ᴅᴇᴛᴀɪʟꜱ"),
            blocks=[rich_list(["ᴜɴʟɪᴍɪᴛᴇᴅ ʟᴏɢɪɴꜱ","ᴢᴇʀᴏ ǫᴜᴇᴜᴇ ᴡᴀɪᴛ",
                               "ᴀᴅᴍɪɴ ᴠɪꜱɪʙɪʟɪᴛʏ ᴘᴀɴᴇʟ","ʟɪꜰᴇᴛɪᴍᴇ ᴀᴠᴀɪʟᴀʙʟᴇ"])]
        ),
    ]
    img = await get_anime_image("plans","ᴩʜᴀɴᴛᴏᴍ ᴩʟᴀɴꜱ","ᴄʜᴏᴏꜱᴇ ʏᴏᴜʀ ᴩᴀᴛʜ","ꜰʀᴏᴍ ₹0")
    kb = kb_plan_upgrade()
    try:
        if img:
            await bot.send_photo(uid, BufferedInputFile(img,"plans.jpg"), reply_markup=kb)
        await bot.send_rich_message(
            chat_id=uid,
            rich_message=InputRichMessage(blocks=blocks),
            reply_markup=kb,
        )
    except Exception:
        await bot.send_message(uid, f'{e("crown")} <b>ᴩʜᴀɴᴛᴏᴍ ᴩʟᴀɴꜱ</b>',
            parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data == "m_refer")
async def cb_refer(cq: CallbackQuery, bot: Bot):
    await cq.answer()
    uid = cq.from_user.id
    user = await get_user(uid)
    refs = user.get("refer_count", 0)
    link = f"https://t.me/{(await bot.get_me()).username}?start=ref_{uid}"
    blocks = [
        rich_heading("ʀᴇꜰᴇʀʀᴀʟ ᴩʀᴏɢʀᴀᴍ","refer"),
        rich_divider(),
        rich_table(
            ["ʏᴏᴜʀ ʀᴇꜰꜱ","ʙᴏɴᴜꜱ ᴇᴀᴄʜ"],
            [[str(refs),"ᴇxᴛʀᴀ ᴜꜱᴇ/ᴅᴀʏ"]],
        ),
        rich_divider(),
        InputRichBlockParagraph(text=RichText(texts=[
            rt("ꜱʜᴀʀᴇ ʏᴏᴜʀ ʟɪɴᴋ ᴀɴᴅ ᴇᴀʀɴ ʙᴏɴᴜꜱ ᴜꜱᴇꜱ!"),
        ])),
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [btn("ᴄᴏᴩʏ ʀᴇꜰᴇʀʀᴀʟ ʟɪɴᴋ", copy=link, style="primary")],
        [btn("« ʙᴀᴄᴋ","m_main")],
    ])
    img = await get_anime_image("refer","ʀᴇꜰᴇʀ & ᴇᴀʀɴ","ɪɴᴠɪᴛᴇ ꜰʀɪᴇɴᴅꜱ",f"{refs} ʀᴇꜰꜱ")
    try:
        if img:
            await bot.send_photo(uid, BufferedInputFile(img,"refer.jpg"), reply_markup=kb)
        await bot.send_rich_message(
            chat_id=uid, rich_message=InputRichMessage(blocks=blocks), reply_markup=kb)
    except Exception:
        await bot.send_message(uid,
            f'{e("refer")} <b>ʀᴇꜰᴇʀʀᴀʟ ʟɪɴᴋ</b>\n<code>{link}</code>',
            parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data == "m_history")
async def cb_history(cq: CallbackQuery, bot: Bot):
    await cq.answer()
    uid = cq.from_user.id
    logs = await db.login_logs.find({"uid":uid}).sort("ts",-1).limit(8).to_list(8)
    blocks = [
        rich_heading("ʟᴏɢɪɴ ʜɪꜱᴛᴏʀʏ","history"),
        rich_divider(),
    ]
    if logs:
        rows = []
        for l in logs:
            ts = l["ts"].strftime("%m/%d %H:%M") if hasattr(l["ts"],"strftime") else str(l["ts"])[:11]
            rows.append([l.get("service","?").upper(), l.get("method","?").upper(),
                         "✓" if l.get("success") else "✗", ts])
        blocks.append(rich_table(["ꜱᴠᴄ","ᴍᴇᴛʜᴏᴅ","ꜱᴛᴀᴛ","ᴛɪᴍᴇ"], rows))
    else:
        blocks.append(InputRichBlockParagraph(text=RichText(texts=[rt("ɴᴏ ʜɪꜱᴛᴏʀʏ ʏᴇᴛ")])))
    kb = InlineKeyboardMarkup(inline_keyboard=[[btn("« ʙᴀᴄᴋ","m_main")]])
    try:
        await bot.send_rich_message(
            chat_id=uid, rich_message=InputRichMessage(blocks=blocks), reply_markup=kb)
    except Exception:
        await bot.send_message(uid, f'{e("history")} <b>ʜɪꜱᴛᴏʀʏ</b>',
            parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data == "m_redeem")
async def cb_redeem(cq: CallbackQuery, state: FSMContext):
    await cq.answer()
    await state.set_state(UserInput.waiting_redeem_key)
    await cq.message.answer(
        f'{e("key")} <b>ᴇɴᴛᴇʀ ʀᴇᴅᴇᴍᴩᴛɪᴏɴ ᴋᴇʏ</b>\n\n'
        f'ꜱᴇɴᴅ ʏᴏᴜʀ ᴋᴇʏ ᴏʀ ᴜꜱᴇ:\n<code>/redeem YOUR-KEY</code>',
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [btn("ᴄᴀɴᴄᴇʟ","m_main",style="danger")],
        ]),
    )


@router.callback_query(F.data == "m_help")
async def cb_help(cq: CallbackQuery, bot: Bot):
    await cq.answer()
    # Reuse the message handler
    class _FakeMsg:
        from_user = cq.from_user
        async def answer(self, *a, **kw): pass
    await cmd_help(_FakeMsg(), bot)


@router.callback_query(F.data == "m_trial")
async def cb_trial(cq: CallbackQuery, bot: Bot):
    await cq.answer()
    uid = cq.from_user.id
    user = await get_user(uid)
    if user.get("trial_used"):
        await cq.answer("ʏᴏᴜ ʜᴀᴠᴇ ᴀʟʀᴇᴀᴅʏ ᴜꜱᴇᴅ ʏᴏᴜʀ ᴛʀɪᴀʟ!", show_alert=True)
        return
    if user.get("plan","free") != "free":
        await cq.answer("ᴛʀɪᴀʟ ɪꜱ ᴏɴʟʏ ꜰᴏʀ ꜰʀᴇᴇ ᴜꜱᴇʀꜱ!", show_alert=True)
        return
    expiry = datetime.utcnow() + timedelta(hours=12)
    await db.users.update_one({"uid":uid},{
        "$set":{"plan":"core","plan_expiry":expiry,"trial_used":True}})
    blocks = [
        rich_heading("ᴛʀɪᴀʟ ᴀᴄᴛɪᴠᴀᴛᴇᴅ","check"),
        rich_divider(),
        rich_table(
            ["ᴩʟᴀɴ","ᴅᴜʀᴀᴛɪᴏɴ","ᴇxᴩɪʀʏ"],
            [["CORE (TRIAL)","12ʜ", expiry.strftime("%H:%M UTC")]],
        ),
        rich_quote("ᴇɴᴊᴏʏ ʏᴏᴜʀ ᴛʀɪᴀʟ — ᴜᴩɢʀᴀᴅᴇ ʙᴇꜰᴏʀᴇ ɪᴛ ᴇxᴩɪʀᴇꜱ!", expandable=False),
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [btn("ᴜꜱᴇ ɴᴏᴡ","m_nf_menu",style="success"),
         btn("ᴜᴩɢʀᴀᴅᴇ","m_plans",style="primary")],
    ])
    try:
        await bot.send_rich_message(
            chat_id=uid, rich_message=InputRichMessage(blocks=blocks), reply_markup=kb)
    except Exception:
        await bot.send_message(uid,
            f'{e("check")} <b>ᴛʀɪᴀʟ ᴀᴄᴛɪᴠᴀᴛᴇᴅ</b> — 12ʜ ᴄᴏʀᴇ ᴩʟᴀɴ',
            parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data == "m_stats")
async def cb_stats(cq: CallbackQuery, bot: Bot):
    await cq.answer()
    await cmd_stats.__wrapped__(cq.message, bot) if hasattr(cmd_stats,"__wrapped__") \
        else None


@router.callback_query(F.data == "verify_check")
async def cb_verify(cq: CallbackQuery, bot: Bot):
    await cq.answer()
    uid = cq.from_user.id
    cfg = await get_cfg()
    channel = cfg.get("verify_channel")
    if not channel:
        await db.users.update_one({"uid":uid},{"$set":{"verified":True}},upsert=True)
        await cq.answer("✓ ᴠᴇʀɪꜰɪᴇᴅ", show_alert=True)
        return
    try:
        member = await bot.get_chat_member(channel, uid)
        if member.status in ("member","administrator","creator"):
            await db.users.update_one({"uid":uid},{"$set":{"verified":True}},upsert=True)
            await cq.answer("✓ ᴠᴇʀɪꜰɪᴇᴅ! ᴀᴄᴄᴇꜱꜱ ɢʀᴀɴᴛᴇᴅ", show_alert=True)
            await cq.message.delete()
            # resend start
            class _FM: from_user=cq.from_user; text="/start"
            await cmd_start(_FM(), bot, FSMContext(storage=dp.storage,
                key=StorageKey(bot_id=bot.id,chat_id=uid,user_id=uid)))
        else:
            await cq.answer("ɴᴏᴛ ᴊᴏɪɴᴇᴅ ʏᴇᴛ!", show_alert=True)
    except Exception:
        await cq.answer("ᴄᴀɴɴᴏᴛ ᴠᴇʀɪꜰʏ — ᴩʟᴇᴀꜱᴇ ᴛʀʏ ᴀɢᴀɪɴ", show_alert=True)


@router.callback_query(F.data.startswith("plan_info_"))
async def cb_plan_info(cq: CallbackQuery):
    plan = cq.data.replace("plan_info_","").upper()
    info = {
        "CORE":  "10 ᴅᴀɪʟʏ ᴜꜱᴇꜱ • ɴᴇᴛꜰʟɪx ᴩʜᴏɴᴇ • ᴄʀᴜɴᴄʜʏʀᴏʟʟ ꜱꜱᴏ • ₹49/ᴍᴏ",
        "ELITE": "25 ᴅᴀɪʟʏ • ᴀʟʟ ɴᴇᴛꜰʟɪx ᴍᴇᴛʜᴏᴅꜱ • ꜰᴀꜱᴛ ǫᴜᴇᴜᴇ • ₹99/ᴍᴏ",
        "ROOT":  "∞ ᴜꜱᴇꜱ • ᴢᴇʀᴏ ᴡᴀɪᴛ • ᴀʟʟ ꜰᴇᴀᴛᴜʀᴇꜱ • ₹199/ᴍᴏ",
    }
    await cq.answer(info.get(plan, "ɴᴏ ɪɴꜰᴏ"), show_alert=True)


@router.callback_query(F.data.startswith("retry_nf_"))
async def cb_retry_nf(cq: CallbackQuery, bot: Bot):
    await cq.answer()
    parts = cq.data.split("_")  # retry_nf_tv_ABCDE
    method = parts[2] if len(parts) > 2 else "tv"
    code   = parts[3] if len(parts) > 3 else ""
    if not code:
        await cq.answer("ᴄᴏᴅᴇ ᴍɪꜱꜱɪɴɢ", show_alert=True)
        return
    await cq.message.answer(f'{e("wait")} ʀᴇᴛʀʏɪɴɢ...', parse_mode="HTML")
    await _run_nf_login(cq, bot, code, method)


@router.callback_query(F.data.startswith("retry_cr_"))
async def cb_retry_cr(cq: CallbackQuery, bot: Bot):
    await cq.answer()
    code = cq.data.replace("retry_cr_","")
    if not code:
        await cq.answer("ᴄᴏᴅᴇ ᴍɪꜱꜱɪɴɢ", show_alert=True)
        return
    await cq.message.answer(f'{e("wait")} ʀᴇᴛʀʏɪɴɢ...', parse_mode="HTML")
    await _run_cr_login(cq, bot, code)


# ─── settings ───────────────────────────────────────────────────────────────

@router.callback_query(F.data.in_({"set_notif_on","set_notif_off"}))
async def cb_notif(cq: CallbackQuery):
    uid = cq.from_user.id
    val = cq.data == "set_notif_on"
    await db.users.update_one({"uid":uid},{"$set":{"notif":val}},upsert=True)
    await cq.answer("ɴᴏᴛɪꜰɪᴄᴀᴛɪᴏɴꜱ " + ("ᴏɴ ✓" if val else "ᴏꜰꜰ ✗"), show_alert=True)


# ═══════════════════════════════════════════════════════════════════════════════
# §  A D M I N   C O M M A N D S
# ═══════════════════════════════════════════════════════════════════════════════

def is_admin(uid: int) -> bool:
    return uid in ADMIN_IDS

def admin_only(fn):
    @wraps(fn)
    async def wrapper(msg: Message, *args, **kwargs):
        if not is_admin(msg.from_user.id):
            await msg.answer(f'{e("cross")} <b>ᴜɴᴀᴜᴛʜᴏʀɪꜱᴇᴅ</b>', parse_mode="HTML")
            return
        return await fn(msg, *args, **kwargs)
    return wrapper


@router.message(Command("admin"))
@admin_only
async def cmd_admin(msg: Message, bot: Bot):
    uid = msg.from_user.id
    total_users  = await db.users.count_documents({})
    nf_cookies   = await db.cookies.count_documents({"service":"nf","used":False,"valid":True})
    cr_accs      = await db.cr_accounts.count_documents({"used":False,"valid":True})
    today = datetime.utcnow().replace(hour=0,minute=0,second=0,microsecond=0)
    today_logins = await db.login_logs.count_documents({"ts":{"$gte":today}})
    success_rate_docs = await db.login_logs.find({"ts":{"$gte":today}},
        {"success":1}).to_list(None)
    ok = sum(1 for x in success_rate_docs if x.get("success"))
    rate = f"{ok*100//max(len(success_rate_docs),1)}%"
    plan_free  = await db.users.count_documents({"plan":"free"})
    plan_core  = await db.users.count_documents({"plan":"core"})
    plan_elite = await db.users.count_documents({"plan":"elite"})
    plan_root  = await db.users.count_documents({"plan":"root"})
    blocks = [
        rich_heading("ᴩʜᴀɴᴛᴏᴍ ᴀᴅᴍɪɴ","crown"),
        rich_divider(),
        rich_table(
            ["ᴍᴇᴛʀɪᴄ","ᴠᴀʟᴜᴇ"],
            [
                ["ᴛᴏᴛᴀʟ ᴜꜱᴇʀꜱ", str(total_users)],
                ["ɴꜰ ᴄᴏᴏᴋɪᴇꜱ",   str(nf_cookies)],
                ["ᴄʀ ᴀᴄᴄᴏᴜɴᴛꜱ",  str(cr_accs)],
                ["ᴛᴏᴅᴀʏ ʟᴏɢɪɴꜱ",  str(today_logins)],
                ["ꜱᴜᴄᴄᴇꜱꜱ ʀᴀᴛᴇ",  rate],
            ],
        ),
        rich_divider(),
        rich_table(
            ["ᴩʟᴀɴ","ᴄᴏᴜɴᴛ"],
            [["FREE",str(plan_free)],["CORE",str(plan_core)],
             ["ELITE",str(plan_elite)],["ROOT",str(plan_root)]],
            is_compact=True,
        ),
        rich_divider(),
        rich_quote("ᴀᴅᴍɪɴ ᴄᴏɴᴛʀᴏʟ ᴩᴀɴᴇʟ", expandable=False),
    ]
    img = await get_anime_image("admin","ᴀᴅᴍɪɴ ᴩᴀɴᴇʟ","ᴩʜᴀɴᴛᴏᴍ ᴏᴩꜱ",f"{total_users} ᴜꜱᴇʀꜱ")
    if img:
        await bot.send_photo(uid, BufferedInputFile(img,"admin.jpg"),
            reply_markup=kb_admin_main())
    try:
        await bot.send_rich_message(
            chat_id=uid, rich_message=InputRichMessage(blocks=blocks),
            reply_markup=kb_admin_main())
    except Exception:
        await msg.answer(f'{e("crown")} <b>ᴀᴅᴍɪɴ</b> — {total_users} ᴜꜱᴇʀꜱ',
            parse_mode="HTML", reply_markup=kb_admin_main())
    await log_admin(uid, "admin_panel", {})


@router.message(Command("addcookie"))
@admin_only
async def cmd_addcookie(msg: Message, state: FSMContext):
    await state.set_state(AdminUpload.waiting_nf_cookies)
    await msg.answer(
        f'{e("nf")} <b>ᴜᴩʟᴏᴀᴅ ɴᴇᴛꜰʟɪx ᴄᴏᴏᴋɪᴇꜱ</b>\n\n'
        f'ꜱᴇɴᴅ ɴᴇᴛꜱᴄᴀᴩᴇ ᴄᴏᴏᴋɪᴇ ꜰɪʟᴇ ᴏʀ ᴩᴀꜱᴛᴇ ᴊꜱᴏɴ ᴀʀʀᴀʏ.\n'
        f'ᴏɴᴇ ᴄᴏᴏᴋɪᴇ = ᴏɴᴇ ʟɪɴᴇ ᴏʀ ᴊꜱᴏɴ ᴏʙᴊᴇᴄᴛ.\n\n'
        f'ꜱᴇɴᴅ /cancel ᴛᴏ ᴀʙᴏʀᴛ.',
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [btn("ᴄᴀɴᴄᴇʟ","adm_close",style="danger")],
        ]),
    )


@router.message(Command("addcr"))
@admin_only
async def cmd_addcr(msg: Message, state: FSMContext):
    await state.set_state(AdminUpload.waiting_cr_accounts)
    await msg.answer(
        f'{e("cr")} <b>ᴜᴩʟᴏᴀᴅ ᴄʀᴜɴᴄʜʏʀᴏʟʟ ᴀᴄᴄᴏᴜɴᴛꜱ</b>\n\n'
        f'ꜰᴏʀᴍᴀᴛ: <code>email:password</code> (ᴏɴᴇ ᴩᴇʀ ʟɪɴᴇ)\n\n'
        f'ꜱᴇɴᴅ /cancel ᴛᴏ ᴀʙᴏʀᴛ.',
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [btn("ᴄᴀɴᴄᴇʟ","adm_close",style="danger")],
        ]),
    )


@router.message(Command("broadcast"))
@admin_only
async def cmd_broadcast(msg: Message, state: FSMContext):
    await state.set_state(AdminUpload.waiting_broadcast)
    await msg.answer(
        f'{e("spark")} <b>ʙʀᴏᴀᴅᴄᴀꜱᴛ ᴍᴏᴅᴇ</b>\n\n'
        f'ꜱᴇɴᴅ ᴍᴇꜱꜱᴀɢᴇ, ᴩʜᴏᴛᴏ, ᴏʀ ᴠɪᴅᴇᴏ ᴛᴏ ʙʀᴏᴀᴅᴄᴀꜱᴛ.\n\n'
        f'/cancel ᴛᴏ ᴀʙᴏʀᴛ.',
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [btn("ᴄᴀɴᴄᴇʟ","adm_close",style="danger")],
        ]),
    )


@router.message(Command("genkeys"))
@admin_only
async def cmd_genkeys(msg: Message, bot: Bot):
    args = msg.text.split()
    # /genkeys COUNT PLAN DAYS
    count = int(args[1]) if len(args)>1 and args[1].isdigit() else 5
    plan  = args[2] if len(args)>2 else "core"
    days  = int(args[3]) if len(args)>3 and args[3].isdigit() else 30
    count = min(count, 50)
    keys = []
    for _ in range(count):
        k = f"PHTM-{secrets.token_hex(4).upper()}-{secrets.token_hex(4).upper()}"
        await db.keys.insert_one({
            "key":k,"plan":plan,"days":days,"used":False,
            "created":datetime.utcnow(),"created_by":msg.from_user.id
        })
        keys.append(k)
    key_text = "\n".join(f"<code>{k}</code>" for k in keys)
    blocks = [
        rich_heading("ᴋᴇʏꜱ ɢᴇɴᴇʀᴀᴛᴇᴅ","key"),
        rich_divider(),
        rich_table(
            ["ᴄᴏᴜɴᴛ","ᴩʟᴀɴ","ᴅᴀʏꜱ"],
            [[str(count),plan.upper(),str(days)]],
        ),
        rich_divider(),
        InputRichBlockPreformatted(text=RichText(texts=[rt("\n".join(keys))])),
    ]
    try:
        await bot.send_rich_message(
            chat_id=msg.from_user.id,
            rich_message=InputRichMessage(blocks=blocks))
    except Exception:
        await msg.answer(
            f'{e("key")} <b>{count} ᴋᴇʏꜱ ɢᴇɴᴇʀᴀᴛᴇᴅ</b> ({plan}, {days}d)\n\n{key_text}',
            parse_mode="HTML")
    await log_admin(msg.from_user.id,"genkeys",{"count":count,"plan":plan,"days":days})


@router.message(Command("ban"))
@admin_only
async def cmd_ban(msg: Message, bot: Bot):
    args = msg.text.split()
    if len(args) < 2:
        await msg.answer(f'{e("cross")} ᴜꜱᴀɢᴇ: /ban USER_ID', parse_mode="HTML")
        return
    try:
        target = int(args[1])
    except ValueError:
        await msg.answer(f'{e("cross")} ɪɴᴠᴀʟɪᴅ ᴜꜱᴇʀ ɪᴅ', parse_mode="HTML")
        return
    reason = " ".join(args[2:]) if len(args)>2 else "ᴀᴅᴍɪɴ ʙᴀɴ"
    await db.users.update_one({"uid":target},
        {"$set":{"banned":True,"ban_reason":reason}}, upsert=True)
    try:
        await bot.send_message(target,
            f'{e("cross")} <b>ʏᴏᴜ ʜᴀᴠᴇ ʙᴇᴇɴ ʙᴀɴɴᴇᴅ</b>\n{reason}', parse_mode="HTML")
    except Exception:
        pass
    await msg.answer(f'{e("check")} ᴜꜱᴇʀ {target} ʙᴀɴɴᴇᴅ', parse_mode="HTML")
    await log_admin(msg.from_user.id,"ban",{"target":target,"reason":reason})


@router.message(Command("unban"))
@admin_only
async def cmd_unban(msg: Message):
    args = msg.text.split()
    if len(args) < 2:
        await msg.answer(f'{e("cross")} ᴜꜱᴀɢᴇ: /unban USER_ID', parse_mode="HTML")
        return
    try:
        target = int(args[1])
    except ValueError:
        await msg.answer(f'{e("cross")} ɪɴᴠᴀʟɪᴅ ɪᴅ', parse_mode="HTML")
        return
    await db.users.update_one({"uid":target},
        {"$set":{"banned":False,"ban_reason":""}}, upsert=True)
    await msg.answer(f'{e("check")} ᴜꜱᴇʀ {target} ᴜɴʙᴀɴɴᴇᴅ', parse_mode="HTML")
    await log_admin(msg.from_user.id,"unban",{"target":target})


@router.message(Command("give"))
@admin_only
async def cmd_give(msg: Message, bot: Bot):
    """Give a plan to a user: /give USER_ID PLAN DAYS"""
    args = msg.text.split()
    if len(args) < 4:
        await msg.answer(
            f'{e("cross")} ᴜꜱᴀɢᴇ: /give USER_ID PLAN DAYS', parse_mode="HTML")
        return
    try:
        target = int(args[1])
        plan   = args[2].lower()
        days   = int(args[3])
    except (ValueError, IndexError):
        await msg.answer(f'{e("cross")} ɪɴᴠᴀʟɪᴅ ᴀʀɢᴜᴍᴇɴᴛꜱ', parse_mode="HTML")
        return
    if plan not in ("free","core","elite","root"):
        await msg.answer(f'{e("cross")} ɪɴᴠᴀʟɪᴅ ᴩʟᴀɴ', parse_mode="HTML")
        return
    expiry = datetime.utcnow() + timedelta(days=days)
    await db.users.update_one({"uid":target},
        {"$set":{"plan":plan,"plan_expiry":expiry}}, upsert=True)
    try:
        await bot.send_message(target,
            f'{e("check")} <b>ᴩʟᴀɴ ᴜᴩᴅᴀᴛᴇᴅ</b>\n'
            f'ᴩʟᴀɴ: <b>{plan.upper()}</b> ꜰᴏʀ {days} ᴅᴀʏꜱ', parse_mode="HTML")
    except Exception:
        pass
    await msg.answer(
        f'{e("check")} ɢᴀᴠᴇ {plan.upper()} ᴛᴏ {target} ꜰᴏʀ {days}ᴅ', parse_mode="HTML")
    await log_admin(msg.from_user.id,"give",
        {"target":target,"plan":plan,"days":days})


@router.message(Command("setcfg"))
@admin_only
async def cmd_setcfg(msg: Message):
    """Set a config key: /setcfg key value"""
    args = msg.text.split(maxsplit=2)
    if len(args) < 3:
        await msg.answer(f'{e("info")} ᴜꜱᴀɢᴇ: /setcfg KEY VALUE', parse_mode="HTML")
        return
    key, val = args[1], args[2]
    # try to coerce booleans / ints
    if val.lower() in ("true","1","yes"):  val = True
    elif val.lower() in ("false","0","no"): val = False
    else:
        try: val = int(val)
        except ValueError: pass
    await set_cfg(key, val)
    await msg.answer(f'{e("check")} <code>{key}</code> = <code>{val}</code>',
        parse_mode="HTML")


@router.message(Command("setvideo"))
@admin_only
async def cmd_setvideo(msg: Message, state: FSMContext):
    await state.set_state(AdminUpload.waiting_setvideo)
    await msg.answer(
        f'{e("info")} ꜱᴇɴᴅ ᴛʜᴇ ᴠɪᴅᴇᴏ ᴛᴏ ꜱᴇᴛ ᴀꜱ ꜱᴛᴀʀᴛ ᴠɪᴅᴇᴏ.',
        parse_mode="HTML")


@router.message(Command("setgif"))
@admin_only
async def cmd_setgif(msg: Message, state: FSMContext):
    await state.set_state(AdminUpload.waiting_setgif)
    await msg.answer(
        f'{e("info")} ꜱᴇɴᴅ ᴛʜᴇ ɢɪꜰ/ᴀɴɪᴍᴀᴛɪᴏɴ.',
        parse_mode="HTML")


@router.message(Command("setphoto"))
@admin_only
async def cmd_setphoto(msg: Message, state: FSMContext):
    await state.set_state(AdminUpload.waiting_setphoto_key)
    await msg.answer(
        f'{e("info")} ꜱᴇɴᴅ ᴛʜᴇ <b>ᴋᴇʏ ɴᴀᴍᴇ</b> ꜰᴏʀ ᴛʜɪꜱ ᴩʜᴏᴛᴏ\n'
        f'(ᴇɢ: <code>main</code>, <code>nf_menu</code>)',
        parse_mode="HTML")


@router.message(Command("cancel"))
async def cmd_cancel(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer(f'{e("check")} ᴄᴀɴᴄᴇʟʟᴇᴅ', parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [btn("ᴍᴀɪɴ ᴍᴇɴᴜ","m_main",style="primary")],
        ]))


# ═══════════════════════════════════════════════════════════════════════════════
# §  F S M   M E S S A G E   H A N D L E R S
# ═══════════════════════════════════════════════════════════════════════════════

@router.message(AdminUpload.waiting_nf_cookies)
async def fsm_nf_cookies(msg: Message, state: FSMContext, bot: Bot):
    if not is_admin(msg.from_user.id):
        return
    await state.clear()
    text = msg.text or ""
    cookies_raw: list[dict] = []

    # Support file upload
    if msg.document:
        file = await bot.get_file(msg.document.file_id)
        buf = BytesIO()
        await bot.download_file(file.file_path, buf)
        text = buf.getvalue().decode("utf-8", errors="ignore")

    # Try JSON array
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            cookies_raw = parsed
        elif isinstance(parsed, dict):
            cookies_raw = [parsed]
    except Exception:
        pass

    # Try Netscape format (one cookie per line / tab-separated)
    if not cookies_raw:
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) >= 7:
                cookies_raw.append({
                    "domain":parts[0],"flag":parts[1],"path":parts[2],
                    "secure":parts[3],"expiry":parts[4],
                    "name":parts[5],"value":parts[6],
                })

    if not cookies_raw:
        await msg.answer(f'{e("cross")} ᴄᴀɴɴᴏᴛ ᴩᴀʀꜱᴇ ᴄᴏᴏᴋɪᴇꜱ', parse_mode="HTML")
        return

    prog = await msg.answer(
        f'{e("wait")} ᴠᴀʟɪᴅᴀᴛɪɴɢ {len(cookies_raw)} ᴄᴏᴏᴋɪᴇꜱ…',
        parse_mode="HTML")

    valid_count = 0
    invalid_count = 0
    semaphore = asyncio.Semaphore(4)

    async def _validate_one(raw_cookie):
        nonlocal valid_count, invalid_count
        cookie_dict = {}
        if isinstance(raw_cookie, list):
            for item in raw_cookie:
                cookie_dict[item.get("name","")] = item.get("value","")
        elif isinstance(raw_cookie, dict):
            # might be flat {name:value} or array-of-dicts
            if "name" in raw_cookie and "value" in raw_cookie:
                cookie_dict[raw_cookie["name"]] = raw_cookie["value"]
            else:
                cookie_dict = raw_cookie
        async with semaphore:
            ok = await asyncio.to_thread(_sync_validate_cookie, cookie_dict, None)
        if ok:
            valid_count += 1
            # encrypt & store
            cookie_json = json.dumps(cookie_dict)
            encrypted = _encrypt(cookie_json.encode())
            await db.cookies.insert_one({
                "service":"nf","data":encrypted,
                "valid":True,"used":False,
                "added":datetime.utcnow(),
                "added_by":msg.from_user.id,
            })
        else:
            invalid_count += 1

    await asyncio.gather(*[_validate_one(c) for c in cookies_raw])
    await prog.delete()
    await msg.answer(
        f'{e("check")} <b>ᴄᴏᴏᴋɪᴇ ᴜᴩʟᴏᴀᴅ ᴄᴏᴍᴩʟᴇᴛᴇ</b>\n\n'
        f'{e("check")} ᴠᴀʟɪᴅ: <b>{valid_count}</b>\n'
        f'{e("cross")} ɪɴᴠᴀʟɪᴅ: <b>{invalid_count}</b>',
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [btn("ᴀᴅᴅ ᴍᴏʀᴇ","adm_nf",style="primary"),
             btn("ᴀᴅᴍɪɴ ᴩᴀɴᴇʟ","adm_close")],
        ]),
    )
    await log_admin(msg.from_user.id,"add_cookies",
        {"valid":valid_count,"invalid":invalid_count})


@router.message(AdminUpload.waiting_cr_accounts)
async def fsm_cr_accounts(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    await state.clear()
    text = msg.text or ""
    lines = [l.strip() for l in text.splitlines() if ":" in l.strip()]
    if not lines:
        await msg.answer(f'{e("cross")} ɴᴏ ᴠᴀʟɪᴅ ᴇɴᴛʀɪᴇꜱ ꜰᴏᴜɴᴅ', parse_mode="HTML")
        return
    added = 0
    for line in lines:
        parts = line.split(":",1)
        if len(parts) == 2:
            email, password = parts[0].strip(), parts[1].strip()
            if "@" in email and len(password) >= 6:
                encrypted = _encrypt(json.dumps({"email":email,"password":password}).encode())
                await db.cr_accounts.insert_one({
                    "data":encrypted,"valid":True,"used":False,
                    "added":datetime.utcnow(),"added_by":msg.from_user.id,
                })
                added += 1
    await msg.answer(
        f'{e("check")} ᴀᴅᴅᴇᴅ <b>{added}</b> ᴄʀᴜɴᴄʜʏʀᴏʟʟ ᴀᴄᴄᴏᴜɴᴛꜱ',
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [btn("ᴀᴅᴍɪɴ ᴩᴀɴᴇʟ","adm_close")],
        ]),
    )
    await log_admin(msg.from_user.id,"add_cr",{"count":added})


@router.message(AdminUpload.waiting_broadcast)
async def fsm_broadcast(msg: Message, state: FSMContext, bot: Bot):
    if not is_admin(msg.from_user.id):
        return
    await state.clear()
    prog = await msg.answer(f'{e("wait")} ʙʀᴏᴀᴅᴄᴀꜱᴛɪɴɢ…', parse_mode="HTML")
    users = await db.users.find({"banned":{"$ne":True}},{"uid":1}).to_list(None)
    ok = fail = 0
    for u in users:
        try:
            if msg.text:
                await bot.send_message(u["uid"], msg.text, parse_mode="HTML")
            elif msg.photo:
                await bot.send_photo(u["uid"], msg.photo[-1].file_id,
                    caption=msg.caption or "")
            elif msg.video:
                await bot.send_video(u["uid"], msg.video.file_id,
                    caption=msg.caption or "")
            elif msg.animation:
                await bot.send_animation(u["uid"], msg.animation.file_id,
                    caption=msg.caption or "")
            ok += 1
            await asyncio.sleep(0.04)  # flood control
        except Exception:
            fail += 1
    await prog.delete()
    await msg.answer(
        f'{e("check")} <b>ʙʀᴏᴀᴅᴄᴀꜱᴛ ᴄᴏᴍᴩʟᴇᴛᴇ</b>\n\n'
        f'✓ {ok} ꜱᴜᴄᴄᴇꜱꜱ  ✗ {fail} ꜰᴀɪʟ',
        parse_mode="HTML",
    )
    await log_admin(msg.from_user.id,"broadcast",{"ok":ok,"fail":fail})


@router.message(AdminUpload.waiting_setvideo)
async def fsm_setvideo(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    await state.clear()
    fid = None
    if msg.video:
        fid = msg.video.file_id
    elif msg.animation:
        fid = msg.animation.file_id
    if not fid:
        await msg.answer(f'{e("cross")} ꜱᴇɴᴅ ᴀ ᴠɪᴅᴇᴏ ꜰɪʟᴇ', parse_mode="HTML")
        return
    await set_cfg("start_video", fid)
    await msg.answer(f'{e("check")} ꜱᴛᴀʀᴛ ᴠɪᴅᴇᴏ ᴜᴩᴅᴀᴛᴇᴅ', parse_mode="HTML")


@router.message(AdminUpload.waiting_setgif)
async def fsm_setgif(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    await state.clear()
    fid = None
    if msg.animation:
        fid = msg.animation.file_id
    elif msg.video:
        fid = msg.video.file_id
    if not fid:
        await msg.answer(f'{e("cross")} ꜱᴇɴᴅ ᴀ ɢɪꜰ', parse_mode="HTML")
        return
    await set_cfg("start_gif", fid)
    await msg.answer(f'{e("check")} ꜱᴛᴀʀᴛ ɢɪꜰ ᴜᴩᴅᴀᴛᴇᴅ', parse_mode="HTML")


@router.message(AdminUpload.waiting_setphoto_key)
async def fsm_setphoto_key(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    key = (msg.text or "").strip().lower()
    if not key:
        await msg.answer(f'{e("cross")} ꜱᴇɴᴅ ᴀ ᴋᴇʏ ɴᴀᴍᴇ', parse_mode="HTML")
        return
    await state.update_data(photo_key=key)
    await state.set_state(AdminUpload.waiting_setphoto)
    await msg.answer(
        f'{e("info")} ɴᴏᴡ ꜱᴇɴᴅ ᴛʜᴇ ᴩʜᴏᴛᴏ ꜰᴏʀ ᴋᴇʏ: <code>{key}</code>',
        parse_mode="HTML")


@router.message(AdminUpload.waiting_setphoto)
async def fsm_setphoto(msg: Message, state: FSMContext):
    if not is_admin(msg.from_user.id):
        return
    data = await state.get_data()
    key = data.get("photo_key","default")
    await state.clear()
    if not msg.photo:
        await msg.answer(f'{e("cross")} ꜱᴇɴᴅ ᴀ ᴩʜᴏᴛᴏ', parse_mode="HTML")
        return
    fid = msg.photo[-1].file_id
    await set_cfg(f"photo_{key}", fid)
    await msg.answer(f'{e("check")} ᴩʜᴏᴛᴏ <code>{key}</code> ꜱᴀᴠᴇᴅ', parse_mode="HTML")


@router.message(UserInput.waiting_redeem_key)
async def fsm_redeem_key(msg: Message, state: FSMContext, bot: Bot):
    await state.clear()
    key_str = (msg.text or "").strip().upper()
    await _process_redeem(msg, bot, key_str)


# ─── admin callback close / other ────────────────────────────────────────────

@router.callback_query(F.data == "adm_close")
async def cb_adm_close(cq: CallbackQuery, state: FSMContext):
    await state.clear()
    await cq.answer("ᴄᴀɴᴄᴇʟʟᴇᴅ")
    try:
        await cq.message.delete()
    except Exception:
        pass


@router.callback_query(F.data.startswith("adm_"))
async def cb_adm_dispatch(cq: CallbackQuery, bot: Bot):
    if not is_admin(cq.from_user.id):
        await cq.answer("ᴜɴᴀᴜᴛʜᴏʀɪꜱᴇᴅ", show_alert=True)
        return
    action = cq.data  # adm_nf, adm_cr, adm_users, etc.
    await cq.answer()

    uid = cq.from_user.id

    if action == "adm_nf":
        count = await db.cookies.count_documents({"service":"nf","valid":True,"used":False})
        used  = await db.cookies.count_documents({"service":"nf","used":True})
        await cq.message.answer(
            f'{e("nf")} <b>ɴᴇᴛꜰʟɪx ᴄᴏᴏᴋɪᴇꜱ</b>\n\n'
            f'✓ ᴠᴀʟɪᴅ: <b>{count}</b>\n'
            f'✗ ᴜꜱᴇᴅ: <b>{used}</b>\n\n'
            f'ᴜꜱᴇ /addcookie ᴛᴏ ᴀᴅᴅ ᴍᴏʀᴇ',
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [btn("ᴀᴅᴅ ᴄᴏᴏᴋɪᴇꜱ","adm_addcookie_prompt",style="primary"),
                 btn("ᴄʟᴇᴀʀ ᴜꜱᴇᴅ","adm_clear_used_nf",style="danger")],
                [btn("« ʙᴀᴄᴋ","adm_main")],
            ]),
        )

    elif action == "adm_addcookie_prompt":
        class _FM:
            text="/addcookie"; from_user=cq.from_user
        from aiogram.fsm.context import FSMContext as _FSM
        # We need state — use a workaround: send message
        await cq.message.answer(
            f'{e("nf")} ꜱᴇɴᴅ /addcookie ᴛᴏ ᴜᴩʟᴏᴀᴅ ᴄᴏᴏᴋɪᴇꜱ',
            parse_mode="HTML")

    elif action == "adm_clear_used_nf":
        res = await db.cookies.delete_many({"service":"nf","used":True})
        await cq.answer(f"ᴅᴇʟᴇᴛᴇᴅ {res.deleted_count}", show_alert=True)

    elif action == "adm_cr":
        count = await db.cr_accounts.count_documents({"valid":True,"used":False})
        await cq.message.answer(
            f'{e("cr")} <b>ᴄʀᴜɴᴄʜʏʀᴏʟʟ ᴀᴄᴄᴏᴜɴᴛꜱ</b>\n\n'
            f'✓ ᴠᴀʟɪᴅ: <b>{count}</b>\n\n'
            f'ᴜꜱᴇ /addcr ᴛᴏ ᴀᴅᴅ ᴍᴏʀᴇ',
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [btn("« ʙᴀᴄᴋ","adm_main")],
            ]),
        )

    elif action == "adm_users":
        total = await db.users.count_documents({})
        banned= await db.users.count_documents({"banned":True})
        today_start = datetime.utcnow().replace(hour=0,minute=0,second=0,microsecond=0)
        active_today= await db.users.count_documents(
            {"last_active":{"$gte":today_start}})
        await cq.message.answer(
            f'{e("info")} <b>ᴜꜱᴇʀ ꜱᴛᴀᴛꜱ</b>\n\n'
            f'ᴛᴏᴛᴀʟ: <b>{total}</b>\n'
            f'ʙᴀɴɴᴇᴅ: <b>{banned}</b>\n'
            f'ᴀᴄᴛɪᴠᴇ ᴛᴏᴅᴀʏ: <b>{active_today}</b>',
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [btn("« ʙᴀᴄᴋ","adm_main")],
            ]),
        )

    elif action == "adm_broadcast":
        class _FM:
            text="/broadcast"; from_user=cq.from_user
        await cq.message.answer(
            f'{e("spark")} ꜱᴇɴᴅ /broadcast ᴛᴏ ꜱᴛᴀʀᴛ ʙʀᴏᴀᴅᴄᴀꜱᴛ',
            parse_mode="HTML")

    elif action == "adm_keys":
        count = await db.keys.count_documents({"used":False})
        await cq.message.answer(
            f'{e("key")} <b>ᴀᴠᴀɪʟᴀʙʟᴇ ᴋᴇʏꜱ: {count}</b>\n\n'
            f'/genkeys COUNT PLAN DAYS',
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [btn("« ʙᴀᴄᴋ","adm_main")],
            ]),
        )

    elif action == "adm_maint":
        cfg = await get_cfg()
        current = cfg.get("maintenance", False)
        new_val = not current
        await set_cfg("maintenance", new_val)
        await cq.answer(
            f'ᴍᴀɪɴᴛᴇɴᴀɴᴄᴇ {"ᴏɴ" if new_val else "ᴏꜰꜰ"}', show_alert=True)

    elif action == "adm_cleanup":
        # Clean up expired plans
        now = datetime.utcnow()
        res = await db.users.update_many(
            {"plan":{"$ne":"free"},
             "plan_expiry":{"$lt":now}},
            {"$set":{"plan":"free","plan_expiry":None}},
        )
        await cq.answer(f"ᴅᴏᴡɴɢʀᴀᴅᴇᴅ {res.modified_count} ᴜꜱᴇʀꜱ", show_alert=True)

    elif action == "adm_proxies":
        proxies = await db.config.find_one({"key":"proxies"})
        plist = proxies.get("value",[]) if proxies else []
        await cq.message.answer(
            f'{e("info")} <b>ᴩʀᴏxɪᴇꜱ: {len(plist)}</b>\n\n'
            f'ꜰᴏʀᴍᴀᴛ: <code>http://user:pass@ip:port</code>\n'
            f'/setcfg proxies ["http://...","http://..."]',
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [btn("« ʙᴀᴄᴋ","adm_main")],
            ]),
        )

    elif action in ("adm_stats","adm_main"):
        # Redirect back to admin panel
        class _FM:
            text="/admin"; from_user=cq.from_user
            async def answer(self, *a, **kw): pass
        await cmd_admin(_FM(), bot)

    elif action == "adm_auditlog":
        logs = await db.admin_logs.find().sort("ts",-1).limit(10).to_list(10)
        lines = []
        for l in logs:
            ts = l["ts"].strftime("%m/%d %H:%M") if hasattr(l.get("ts"),"strftime") else ""
            lines.append(f'{ts} — {l.get("action","?")} by {l.get("admin_id","?")}')
        text = "\n".join(lines) or "ɴᴏ ʟᴏɢꜱ"
        await cq.message.answer(
            f'{e("history")} <b>ᴀᴜᴅɪᴛ ʟᴏɢ</b>\n\n<code>{text}</code>',
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [btn("« ʙᴀᴄᴋ","adm_main")],
            ]),
        )

    elif action == "adm_alerts":
        await cq.message.answer(
            f'{e("warn")} <b>ᴀʟᴇʀᴛꜱ</b>\n\n'
            f'ᴀʟᴇʀᴛꜱ ᴀʀᴇ ꜱᴇɴᴛ ᴛᴏ ᴀᴅᴍɪɴ ᴅᴍ ᴡʜᴇɴ:\n'
            f'• ᴄᴏᴏᴋɪᴇ ꜱᴛᴏᴄᴋ < 10\n'
            f'• ᴄʀ ᴀᴄᴄᴏᴜɴᴛ ꜱᴛᴏᴄᴋ < 5\n'
            f'• ᴇʀʀᴏʀ ʀᴀᴛᴇ > 50%',
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [btn("« ʙᴀᴄᴋ","adm_main")],
            ]),
        )

    elif action == "adm_backup":
        # Export a small JSON backup of config
        cfg_doc = await db.config.find().to_list(None)
        export = json.dumps(cfg_doc, default=str, indent=2)
        buf = BufferedInputFile(export.encode(), "phantom_backup.json")
        await bot.send_document(uid, buf, caption=f'{e("info")} ᴄᴏɴꜰɪɢ ʙᴀᴄᴋᴜᴩ')

    elif action == "adm_plans":
        await cq.message.answer(
            f'{e("crown")} <b>ᴩʟᴀɴ ᴄᴏɴꜰɪɢ</b>\n\n'
            f'ꜱᴇᴛ ᴅᴀɪʟʏ ʟɪᴍɪᴛꜱ:\n'
            f'/setcfg plan_free_daily 2\n'
            f'/setcfg plan_core_daily 10\n'
            f'/setcfg plan_elite_daily 25\n'
            f'/setcfg plan_root_daily 999',
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [btn("« ʙᴀᴄᴋ","adm_main")],
            ]),
        )

    elif action == "adm_refs":
        top = await db.users.find({}).sort("refer_count",-1).limit(5).to_list(5)
        lines = [f'{i+1}. {u.get("uid")} — {u.get("refer_count",0)} ʀᴇꜰꜱ'
                 for i,u in enumerate(top)]
        await cq.message.answer(
            f'{e("refer")} <b>ᴛᴏᴩ ʀᴇꜰᴇʀʀᴀʟꜱ</b>\n\n' + "\n".join(lines),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [btn("« ʙᴀᴄᴋ","adm_main")],
            ]),
        )

    elif action == "adm_trials":
        count = await db.users.count_documents({"trial_used":True})
        await cq.answer(f"ᴛʀɪᴀʟꜱ ᴜꜱᴇᴅ: {count}", show_alert=True)

    elif action == "adm_admins":
        await cq.message.answer(
            f'{e("crown")} <b>ᴀᴅᴍɪɴ ɪᴅꜱ</b>\n\n'
            f'<code>{", ".join(str(a) for a in ADMIN_IDS)}</code>\n\n'
            f'ꜱᴇᴛ ɪɴ ᴇɴᴠ: <code>ADMIN_IDS</code>',
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [btn("« ʙᴀᴄᴋ","adm_main")],
            ]),
        )

    elif action == "adm_config":
        cfg = await get_cfg()
        lines = [f'{k}: {v}' for k,v in list(cfg.items())[:15]]
        await cq.message.answer(
            f'{e("info")} <b>ᴄᴏɴꜰɪɢ</b>\n\n<code>' + "\n".join(lines) + '</code>',
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [btn("« ʙᴀᴄᴋ","adm_main")],
            ]),
        )

    elif action == "adm_media":
        cfg = await get_cfg()
        vid  = cfg.get("start_video","ɴᴏᴛ ꜱᴇᴛ")
        gif  = cfg.get("start_gif","ɴᴏᴛ ꜱᴇᴛ")
        await cq.message.answer(
            f'{e("info")} <b>ᴍᴇᴅɪᴀ</b>\n\n'
            f'ᴠɪᴅᴇᴏ: <code>{vid[:20] if vid!="ɴᴏᴛ ꜱᴇᴛ" else vid}</code>\n'
            f'ɢɪꜰ:   <code>{gif[:20] if gif!="ɴᴏᴛ ꜱᴇᴛ" else gif}</code>\n\n'
            f'/setvideo  /setgif  /setphoto KEY',
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [btn("« ʙᴀᴄᴋ","adm_main")],
            ]),
        )


# ═══════════════════════════════════════════════════════════════════════════════
# §  S C H E D U L E D   J O B S
# ═══════════════════════════════════════════════════════════════════════════════

async def job_cookie_health():
    """Revalidate all NF cookies; mark invalid."""
    log.info("[scheduler] cookie_health start")
    cursor = db.cookies.find({"service":"nf","used":False,"valid":True})
    invalid = 0
    async for doc in cursor:
        try:
            raw = _decrypt(doc["data"])
            cookie_dict = json.loads(raw)
            ok = await asyncio.to_thread(_sync_validate_cookie, cookie_dict, None)
            if not ok:
                await db.cookies.update_one(
                    {"_id":doc["_id"]},{"$set":{"valid":False}})
                invalid += 1
        except Exception as ex:
            log.warning("cookie_health skip: %s", ex)
    log.info("[scheduler] cookie_health done — invalid=%d", invalid)
    # Alert admins if low
    remain = await db.cookies.count_documents({"service":"nf","used":False,"valid":True})
    if remain < 10:
        for aid in ADMIN_IDS:
            try:
                await _bot_ref.send_message(aid,
                    f'{e("warn")} <b>ʟᴏᴡ ᴄᴏᴏᴋɪᴇ ꜱᴛᴏᴄᴋ!</b> ᴏɴʟʏ {remain} ʟᴇꜰᴛ',
                    parse_mode="HTML")
            except Exception:
                pass


async def job_cr_health():
    """Verify CR accounts still have valid tokens by doing a token refresh check."""
    log.info("[scheduler] cr_health start")
    cursor = db.cr_accounts.find({"used":False,"valid":True})
    invalid = 0
    async for doc in cursor:
        try:
            raw = _decrypt(doc["data"])
            cred = json.loads(raw)
            # Quick OAuth ping — if token refresh fails, mark invalid
            def _check():
                try:
                    import requests
                    r = requests.post(
                        "https://sso.crunchyroll.com/oauth2/token",
                        headers={"Authorization":f"Basic {CR_BASIC_AUTH}",
                                 "Content-Type":"application/x-www-form-urlencoded"},
                        data={"grant_type":"password",
                              "username":cred["email"],
                              "password":cred["password"],
                              "scope":"offline_access"},
                        timeout=10,
                    )
                    return r.status_code == 200
                except Exception:
                    return False
            ok = await asyncio.to_thread(_check)
            if not ok:
                await db.cr_accounts.update_one(
                    {"_id":doc["_id"]},{"$set":{"valid":False}})
                invalid += 1
            await asyncio.sleep(0.5)
        except Exception as ex:
            log.warning("cr_health skip: %s", ex)
    log.info("[scheduler] cr_health done — invalid=%d", invalid)
    remain = await db.cr_accounts.count_documents({"used":False,"valid":True})
    if remain < 5:
        for aid in ADMIN_IDS:
            try:
                await _bot_ref.send_message(aid,
                    f'{e("warn")} <b>ʟᴏᴡ ᴄʀ ꜱᴛᴏᴄᴋ!</b> ᴏɴʟʏ {remain} ʟᴇꜰᴛ',
                    parse_mode="HTML")
            except Exception:
                pass


async def job_daily_reset():
    """Reset daily usage counters for all users at midnight UTC."""
    log.info("[scheduler] daily_reset")
    today = datetime.utcnow().replace(hour=0,minute=0,second=0,microsecond=0)
    await db.users.update_many(
        {"daily_reset":{"$lt":today}},
        {"$set":{"daily_used":0,"daily_reset":today}},
    )


async def job_plan_expiry():
    """Downgrade users whose paid plan has expired."""
    log.info("[scheduler] plan_expiry")
    now = datetime.utcnow()
    expired = await db.users.find(
        {"plan":{"$ne":"free"},"plan_expiry":{"$lt":now}},
        {"uid":1}
    ).to_list(None)
    for u in expired:
        await db.users.update_one(
            {"uid":u["uid"]},
            {"$set":{"plan":"free","plan_expiry":None}},
        )
        try:
            await _bot_ref.send_message(u["uid"],
                f'{e("warn")} <b>ʏᴏᴜʀ ᴩʟᴀɴ ʜᴀꜱ ᴇxᴩɪʀᴇᴅ</b>\n'
                f'ᴜᴩɢʀᴀᴅᴇ ᴛᴏ ᴄᴏɴᴛɪɴᴜᴇ ᴜꜱɪɴɢ ᴩʀᴇᴍɪᴜᴍ ᴍᴇᴛʜᴏᴅꜱ.',
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [btn("ᴜᴩɢʀᴀᴅᴇ ɴᴏᴡ","m_plans",style="primary")],
                ]),
            )
        except Exception:
            pass
    log.info("[scheduler] plan_expiry done — expired=%d", len(expired))


async def job_cleanup_ratelimits():
    """Remove stale rate limit docs older than 24h."""
    log.info("[scheduler] cleanup_ratelimits")
    cutoff = datetime.utcnow() - timedelta(hours=24)
    res = await db.rate_limits.delete_many({"last_refill":{"$lt":cutoff}})
    log.info("[scheduler] cleanup done — removed=%d", res.deleted_count)


# ═══════════════════════════════════════════════════════════════════════════════
# §  R E G I S T E R   &   M A I N
# ═══════════════════════════════════════════════════════════════════════════════

# Global bot reference for jobs
_bot_ref: Optional[Bot] = None


async def on_startup(bot: Bot):
    global _bot_ref
    _bot_ref = bot
    await init_db()
    log.info("DB initialised")
    # Set webhook
    webhook_url = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
    await bot.set_webhook(
        url=webhook_url,
        secret_token=WEBHOOK_SECRET,
        drop_pending_updates=True,
        allowed_updates=["message","callback_query","my_chat_member"],
    )
    log.info("Webhook set: %s", webhook_url)

    # Start APScheduler
    scheduler.add_job(job_cookie_health,  "interval", hours=2,   id="cookie_health")
    scheduler.add_job(job_cr_health,      "interval", hours=3,   id="cr_health")
    scheduler.add_job(job_daily_reset,    "cron",     hour=0, minute=1, id="daily_reset")
    scheduler.add_job(job_plan_expiry,    "interval", minutes=30, id="plan_expiry")
    scheduler.add_job(job_cleanup_ratelimits,"cron",  hour=3, minute=0, id="cleanup_rl")
    scheduler.start()
    log.info("Scheduler started")


async def on_shutdown(bot: Bot):
    scheduler.shutdown(wait=False)
    await bot.delete_webhook()
    log.info("Shutdown complete")


async def health_handler(request: web.Request) -> web.Response:
    return web.json_response({
        "status": "ok",
        "bot": BOT_USERNAME,
        "uptime": str(datetime.utcnow()),
    })


async def webhook_handler(request: web.Request) -> web.Response:
    # Verify secret
    secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token","")
    if WEBHOOK_SECRET and secret != WEBHOOK_SECRET:
        return web.Response(status=403)
    try:
        data = await request.json()
        update = Update.model_validate(data)
        await dp.feed_update(bot=_bot_ref, update=update)
    except Exception as ex:
        log.exception("webhook_handler error: %s", ex)
    return web.Response(status=200)


async def main():
    global dp, _bot_ref

    # ── Bot & Storage ──────────────────────────────────────────────────────
    mongo_client = AsyncIOMotorClient(MONGO_URI)
    storage      = MongoStorage(client=mongo_client, db_name=MONGO_DB,
                                 collection_name="fsm_states")

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    _bot_ref = bot

    dp = Dispatcher(storage=storage)
    dp.update.middleware(GlobalMiddleware())

    # Include router
    dp.include_router(router)

    # ── aiohttp app ────────────────────────────────────────────────────────
    app = web.Application()
    app.router.add_get("/health", health_handler)
    app.router.add_post(WEBHOOK_PATH, webhook_handler)

    # ── lifecycle ──────────────────────────────────────────────────────────
    await on_startup(bot)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=PORT)
    await site.start()

    log.info("ᴩʜᴀɴᴛᴏᴍ ʟɪꜱᴛᴇɴɪɴɢ ᴏɴ ᴩᴏʀᴛ %d", PORT)

    try:
        await asyncio.Event().wait()   # run forever
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        await on_shutdown(bot)
        await runner.cleanup()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
