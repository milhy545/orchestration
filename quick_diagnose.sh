#!/bin/bash

# Rychlá diagnostika gemini-cli na serveru
# Tento skript zkontroluje aktuální stav a navrhne rychlé opravy

echo "🔍 Rychlá diagnostika gemini-cli"
echo "==============================="
echo ""

# Kontrola shellu
echo "1️⃣ Shell konfigurace:"
if [ -n "$BASH_VERSION" ]; then
    echo "   ✅ Bash: $BASH_VERSION"
else
    echo "   ❌ Bash není aktivní"
fi

if [ -n "$TMUX" ]; then
    echo "   ✅ Tmux: $TMUX"
else
    echo "   ❌ Tmux není aktivní"
fi

echo ""

# Kontrola bash dostupnosti
echo "2️⃣ Bash dostupnost:"
if command -v bash &> /dev/null; then
    echo "   ✅ Bash příkaz dostupný"
else
    echo "   ❌ Bash příkaz nedostupný"
    echo "   🔧 Instalace: apk add bash"
fi

echo ""

# Kontrola gemini-cli
echo "3️⃣ Gemini-cli stav:"
if command -v gemini &> /dev/null; then
    echo "   ✅ Gemini-cli nainstalován"
    VERSION=$(gemini --version 2>/dev/null | head -1)
    echo "   📋 Verze: $VERSION"
else
    echo "   ❌ Gemini-cli nenainstalován"
    echo "   🔧 Instalace: npm install -g @google/gemini-cli"
fi

echo ""

# Kontrola konfigurace
echo "4️⃣ Konfigurace:"
GEMINI_DIR="$HOME/.gemini"
if [ -d "$GEMINI_DIR" ]; then
    echo "   ✅ .gemini adresář existuje"

    if [ -f "$GEMINI_DIR/settings.json" ]; then
        echo "   ✅ settings.json nalezen"

        if grep -q '"sandbox".*false' "$GEMINI_DIR/settings.json"; then
            echo "   ✅ Sandboxing: VYPNUTÝ"
        else
            echo "   ❌ Sandboxing: ZAPNUTÝ nebo nenakonfigurovaný"
        fi

        if grep -q '"enableInteractiveShell".*true' "$GEMINI_DIR/settings.json"; then
            echo "   ✅ Interaktivní shell: ZAPNUTÝ"
        else
            echo "   ⚠️  Interaktivní shell: nenakonfigurovaný"
        fi
    else
        echo "   ❌ settings.json nenalezen"
    fi
else
    echo "   ❌ .gemini adresář nenalezen"
fi

echo ""

# Kontrola API klíče
echo "5️⃣ API klíč:"
if [ -f "$HOME/.gemini_api_key" ]; then
    echo "   ✅ API klíč nalezen"
else
    echo "   ❌ API klíč nenalezen"
    echo "   🔧 Vytvořte: echo 'váš-api-klíč' > ~/.gemini_api_key"
fi

echo ""

# Rychlý test
echo "6️⃣ Rychlý test:"
echo "   Testování základní funkčnosti..."
if command -v gemini &> /dev/null; then
    if timeout 5s bash -c "gemini --help" > /dev/null 2>&1; then
        echo "   ✅ Základní funkce: OK"
    else
        echo "   ❌ Základní funkce: CHYBA"
    fi

    if timeout 5s bash -c "gemini -p 'echo test'" > /dev/null 2>&1; then
        echo "   ✅ Shell příkazy: OK"
    else
        echo "   ❌ Shell příkazy: CHYBA"
    fi
fi

echo ""
echo "📋 Rychlé opravy:"
echo "================="
echo ""
echo "1. Aktivovat bash:"
echo "   export SHELL=/bin/bash"
echo "   source ~/.bashrc"
echo ""
echo "2. Opravit konfiguraci:"
echo "   cp /home/milhy777/orchestration/gemini_settings_fixed.json ~/.gemini/settings.json"
echo ""
echo "3. Restartovat tmux:"
echo "   tmux kill-session -t orchestration-main"
echo "   tmux new-session -s orchestration-main"
echo ""
echo "4. Přihlásit se:"
echo "   gemini auth login"
echo ""
echo "5. Otestovat:"
echo "   gemini -p 'echo funguje'"
echo ""
echo "🔧 Pro kompletní opravu spusťte:"
echo "   bash /home/milhy777/orchestration/server_gemini_fix.sh"
