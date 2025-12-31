# 🏰 Hogwarts Wizarding UI – Global Stylesheet
HOGWARTS_STYLE = """
/* 🪄 GLOBAL BASE */
QWidget {
    background-color: #0b0f1a;
    color: #f1f5ff;
    font-family: "Garamond", "Times New Roman", serif;
}

QLabel {
    color: #f6f1e7;
}

/* 📜 TITLE – Ancient Chapter Header */
QLabel#TitleLabel {
    color: #d4af37;
    font-size: 20px;
    font-weight: bold;
    letter-spacing: 1px;
    text-transform: none;
    margin-bottom: 15px;
    text-shadow:
        0 0 8px rgba(212,175,55,0.6);
    text-align: center;

    /* Background and border styling */
    background-color: #1a1d2a;
    border: 2px solid #d4af37;
    border-radius: 15px;
    padding: 12px 20px;
}

/* 📖 STORY PANEL – Parchment Scroll */
QLabel#StoryText {
    background-color: #1c1626;
    border: 2px solid #6b5a3a;
    border-radius: 22px;
    padding: 26px;

    font-size: 16px;
    line-height: 1.7;
    color: #f6f1e7;

    /* Ancient depth */
    box-shadow:
        inset 0 0 12px rgba(0,0,0,0.4),
        0 0 18px rgba(0,0,0,0.6);
}

/* 🪞 CAMERA – Magic Mirror / Pensieve */
QWidget#CameraMirror {
    background-color: #0a0c12;
    border: 3px solid #3a2f4f;
    border-radius: 26px;
}

/* ✨ Active Spell Glow (set dynamically) */
QWidget#CameraMirror[spellState="active"] {
    border: 3px solid #9b6fd3;
    box-shadow: 0 0 22px rgba(155,111,211,0.7);
}

/* 🦌 Patronus Glow */
QWidget#CameraMirror[spellState="patronus"] {
    border: 3px solid #ccefff;
    box-shadow: 0 0 35px rgba(204,239,255,0.85);
}

/* 🪄 STATUS BAR – Spell Aura */
QLabel#StatusBar {
    border-radius: 20px;
    padding: 18px;
    font-size: 16px;
    font-weight: bold;
    text-align: center;
}

/* Info / Scroll */
QLabel#StatusBar[statusStyle="info"] {
    background-color: #1c1626;
    border: 2px solid #d6b36a;
}

/* Listening / Wand Aura */
QLabel#StatusBar[statusStyle="listening"] {
    background-color: #221b2e;
    border: 2px solid #f0c75e;
    box-shadow: 0 0 14px rgba(240,199,94,0.5);
}

/* Validating / Arcane */
QLabel#StatusBar[statusStyle="validating"] {
    background-color: #2a1c3a;
    border: 2px solid #9b6fd3;
    box-shadow: 0 0 18px rgba(155,111,211,0.6);
}

/* Success / Patronus */
QLabel#StatusBar[statusStyle="success"] {
    background-color: #16251b;
    border: 2px solid #6fbf73;
    box-shadow: 0 0 22px rgba(111,191,115,0.7);
}

/* Error / Dark Curse */
QLabel#StatusBar[statusStyle="error"] {
    background-color: #2a1414;
    border: 2px solid #b14a4a;
    box-shadow: 0 0 14px rgba(177,74,74,0.6);
}

/* ⚡ MAGICAL ENERGY BAR (Progress) */
QProgressBar {
    background-color: #1a2035;
    border-radius: 6px;
    height: 8px;
}

QProgressBar::chunk {
    border-radius: 6px;
    background-color: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #9b6fd3,
        stop:0.5 #d6b36a,
        stop:1 #5dade2
    );
}

/* 🧙 BUTTONS – Wizard Controls */
QPushButton {
    background-color: #1c1626;
    color: #f6f1e7;

    border-radius: 20px;
    border: 2px solid #d6b36a;

    padding: 12px 28px;
    font-size: 15px;
    font-weight: bold;

    letter-spacing: 1px;
}

/* Hover – Golden Glow */
QPushButton:hover {
    background-color: #2a2138;
    box-shadow: 0 0 12px rgba(212,175,55,0.55);
}

/* Pressed – Dark Magic */
QPushButton:pressed {
    background-color: #120d18;
}

/* Disabled */
QPushButton:disabled {
    color: #777;
    border-color: #444;
}

/* 🎮 SPELL HUD – Status + Mana Control Zone */
QWidget#SpellHUD {
    background-color: #0f1322;
    border: 2px solid #3a2f4f;
    border-radius: 18px;
}

/* 🎬 EXPECTO PATRONUM – CINEMATIC MODE (Optional) */
QWidget#CinematicMode {
    background-color: #10182b;
}
"""

MAGIC_COLORS = {
    "bg": "#0a0c12",        # darker, less blue
    "panel": "#16121c",     # purple-brown
    "border": "#3a2f4f",

    "gold": "#d6b36a",      # aged gold
    "ink": "#f6f1e7",       # parchment text
    "danger": "#8b2e2e",

    "text_main": "#f1f5ff",
    "text_muted": "#9aa4c7",

    "blue": "#5dade2",        # Arcane energy
    "purple": "#9b59b6",      # Mystic
    "green": "#2ecc71",       # Success
    "red": "#e74c3c",         # Failure
}