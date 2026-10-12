"""Простой переключатель языка (RU/EN) для портфолио-хаба.

Использование на каждой странице:
    from i18n import lang_switcher
    lang = lang_switcher()          # рисует переключатель в сайдбаре
    T = TEXTS[lang]                 # словарь строк страницы
"""

import streamlit as st

LANGS = ("ru", "en")
FLAGS = {"ru": "🇷🇺 Русский", "en": "🇬🇧 English"}


def lang_switcher() -> str:
    """Показывает переключатель в сайдбаре и возвращает 'ru' | 'en'."""
    lang = st.session_state.get("lang", "ru")
    labels = [FLAGS[l] for l in LANGS]
    idx = list(LANGS).index(lang) if lang in LANGS else 0
    choice = st.sidebar.radio("🌐", labels, index=idx, label_visibility="collapsed")
    new = LANGS[labels.index(choice)]
    st.session_state["lang"] = new
    return new
