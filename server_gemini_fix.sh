#!/bin/bash

# Komplexní oprava gemini-cli pro serverové prostředí
# Tento skript diagnostikuje a opravuje problémy s gemini-cli v SSH/tmux prostředí

echo "🚀 Komplexní oprava gemini-cli pro server"
echo "========================================"
echo ""

# Funkce pro logování
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a /tmp/gemini_fix.log
}

log "🔍 Začínám diagnostiku..."

# 1. Kontrola základního prostředí
log "1️⃣ Kontrola základního prostředí"
if [ -f /etc/alpine-release ]; then
    log "✅ Alpine Linux detekován"
    ALPINE=true
else
    log "ℹ️  Jiný OS než Alpine"
    ALPINE=false
fi

# Kontrola shellu
if [ -n "$BASH_VERSION" ]; then
    log "✅ Bash shell aktivní: $BASH_VERSION"
elif [ -n "$ZSH_VERSION" ]; then
    log "✅ Zsh shell aktivní: $ZSH_VERSION"
fi

# 2. Kontrola a instalace bash (pokud není)
log "2️⃣ Zajištění bash shellu"
if ! command -v bash &> /dev/null; then
    log "📦 Instalace bash..."
    if [ "$ALPINE" = true ]; then
        apk add --no-cache bash
    else
        apt update && apt install -y bash
    fi
    log "✅ Bash nainstalován"
else
    log "✅ Bash je dostupný"
fi

# 3. Kontrola tmux
log "3️⃣ Kontrola tmux"
if ! command -v tmux &> /dev/null; then
    log "📦 Instalace tmux..."
    if [ "$ALPINE" = true ]; then
        apk add --no-cache tmux
    else
        apt install -y tmux
    fi
    log "✅ Tmux nainstalován"
else
    log "✅ Tmux je dostupný"
fi

# 4. Vytvoření .bashrc pro správnou konfiguraci
log "4️⃣ Vytváření .bashrc konfigurace"
cat > ~/.bashrc << 'EOF'
#!/bin/bash
# .bashrc pro serverové prostředí s gemini-cli podporou

if [[ $- != *i* ]]; then
    return
fi

export TERM=xterm-256color
export LANG=C.UTF-8

# Kontrola oh-my-zsh
if [ -d "/root/.oh-my-zsh" ]; then
    export ZSH="/root/.oh-my-zsh"
    source $ZSH/oh-my-zsh.sh
elif [ -d "$HOME/.oh-my-zsh" ]; then
    export ZSH="$HOME/.oh-my-zsh"
    source $ZSH/oh-my-zsh.sh
else
    # Základní prompt bez oh-my-zsh
    PS1='\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '
fi

# Alias příkazy
alias ll='ls -la'
alias la='ls -A'
alias l='ls -CF'

# Funkce pro debug
debug_info() {
    echo "=== Debug Info ==="
    echo "Shell: $SHELL"
    echo "User: $(whoami)"
    echo "Home: $HOME"
    echo "PWD: $PWD"
    echo "PATH: $PATH"
    echo "TMUX: $TMUX"
    echo "=== End Debug ==="
}
export -f debug_info

# Zajistit správný SHELL pro gemini-cli
export SHELL=/bin/bash

log "✅ .bashrc vytvořen"
EOF

# 5. Kontrola a oprava gemini-cli konfigurace
log "5️⃣ Oprava gemini-cli konfigurace"

GEMINI_DIR="$HOME/.gemini"
if [ ! -d "$GEMINI_DIR" ]; then
    log "📁 Vytváření .gemini adresáře"
    mkdir -p "$GEMINI_DIR"
fi

# Zálohování stávající konfigurace
if [ -f "$GEMINI_DIR/settings.json" ]; then
    cp "$GEMINI_DIR/settings.json" "$GEMINI_DIR/settings.json.backup.$(date +%Y%m%d_%H%M%S)"
    log "💾 Stávající konfigurace zálohována"
fi

# Vytvoření opravené konfigurace
cat > "$GEMINI_DIR/settings.json" << 'EOF'
{
  "security": {
    "folderTrust": {
      "featureEnabled": true,
      "enabled": true
    },
    "auth": {
      "selectedType": "oauth-personal"
    }
  },
  "ui": {
    "showMemoryUsage": true,
    "showLineNumbers": false,
    "theme": "Shades Of Purple",
    "showCitations": true,
    "accessibility": {
      "screenReader": true
    }
  },
  "context": {
    "loadFromIncludeDirectories": true,
    "loadMemoryFromIncludeDirectories": true
  },
  "general": {
    "preferredEditor": "emacs",
    "debugKeystrokeLogging": true,
    "enablePromptCompletion": true
  },
  "output": {
    "format": "text"
  },
  "tools": {
    "shell": {
      "showColor": true,
      "enableInteractiveShell": true
    },
    "sandbox": false,
    "autoAccept": true
  },
  "hasSeenIdeIntegrationNudge": true,
  "ide": {
    "enabled": true
  },
  "advanced": {
    "excludedEnvVars": []
  }
}
EOF

log "✅ Opravená konfigurace vytvořena"

# 6. Kontrola API klíče
log "6️⃣ Kontrola API klíče"
if [ ! -f "$HOME/.gemini_api_key" ]; then
    log "⚠️  API klíč nenalezen"
    echo "Vytvořte soubor $HOME/.gemini_api_key s vaším API klíčem:"
    echo "echo 'váš-api-klíč-zde' > ~/.gemini_api_key"
    echo "chmod 600 ~/.gemini_api_key"
else
    log "✅ API klíč nalezen"
    chmod 600 ~/.gemini_api_key
fi

# 7. Testování oprav
log "7️⃣ Testování oprav"

echo ""
echo -e "\033[1;34m🧪 Spouštím testy...\033[0m"

# Test 1: Základní bash funkčnost
log "Test 1: Základní bash funkčnost"
if bash -c "echo 'Bash funguje správně'" > /tmp/bash_test.log 2>&1; then
    log "✅ Bash funguje"
else
    log "❌ Bash má problém"
fi

# Test 2: Gemini-cli základní funkce
log "Test 2: Gemini-cli základní funkce"
if command -v gemini &> /dev/null; then
    if timeout 10s bash -c "gemini --help" > /tmp/gemini_help.log 2>&1; then
        log "✅ Gemini-cli základní funkce fungují"
    else
        log "❌ Gemini-cli základní funkce mají problém"
        log "   Log: $(cat /tmp/gemini_help.log)"
    fi

    # Test 3: Shell příkaz
    log "Test 3: Shell příkaz"
    if timeout 10s bash -c "gemini -p 'echo test'" > /tmp/gemini_shell.log 2>&1; then
        log "✅ Shell příkazy fungují"
    else
        log "❌ Shell příkazy mají problém"
        log "   Log: $(cat /tmp/gemini_shell.log)"
    fi
else
    log "❌ Gemini-cli není nainstalován"
fi

# 8. Závěrečné instrukce
log "8️⃣ Závěrečné instrukce"
echo ""
echo -e "\033[1;32m✅ Oprava dokončena!\033[0m"
echo ""
echo -e "\033[1;33m📋 Pro dokončení proveďte tyto kroky:\033[0m"
echo ""
echo "1. Načtěte novou konfiguraci:"
echo "   source ~/.bashrc"
echo ""
echo "2. Restartujte tmux session:"
echo "   tmux kill-session -t orchestration-main"
echo "   tmux new-session -s orchestration-main"
echo ""
echo "3. Přihlaste se do gemini-cli:"
echo "   gemini auth login"
echo ""
echo "4. Otestujte funkčnost:"
echo "   gemini -p 'echo \"funguje!\"'"
echo ""
echo "5. Pokud stále nefunguje, zkontrolujte:"
echo "   - API klíč v ~/.gemini_api_key"
echo "   - Sandboxing v ~/.gemini/settings.json (měl by být false)"
echo ""
echo -e "\033[1;36m🔧 Log oprav: /tmp/gemini_fix.log\033[0m"

log "✅ Komplexní oprava dokončena"
