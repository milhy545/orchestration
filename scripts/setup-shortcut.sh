#!/bin/bash
# 🎹 Skript pro nastavení klávesové zkratky Alt+S pro /speak

# Cesta k projektu
PROJECT_DIR="/media/milhy777/Develop/orchestration"

echo "🔧 Nastavuji klávesovou zkratku Alt+S pro tvůj shell..."

# Definice funkce pro ZSH
ZSH_CONFIG="
# Gemini Speak Shortcut (Alt+S)
speak_last_reply() {
    # Vytáhneme poslední odpověď z historie Gemini (pokud ji Gemini CLI ukládá do logu)
    # Nebo jednoduše zavoláme náš skript na pozadí
    (python3 $PROJECT_DIR/scripts/speak.py \"\$(gemini history --last 1)\" &)
    zle redisplay
}
zle -N speak_last_reply
bindkey '^[s' speak_last_reply
"

if [ -f ~/.zshrc ]; then
    if ! grep -q "speak_last_reply" ~/.zshrc; then
        echo "$ZSH_CONFIG" >> ~/.zshrc
        echo "✅ Zkratka Alt+S byla přidána do tvého ~/.zshrc"
        echo "👉 Spusť: 'source ~/.zshrc' pro aktivaci."
    else
        echo "ℹ️ Zkratka už v ~/.zshrc existuje."
    fi
else
    echo "❌ ~/.zshrc nenalezen. Pokud používáš Bash, budeme muset použít jinou metodu."
fi
