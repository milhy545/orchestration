# RPi Mode Skill

Tento skill instruuje AI agenta, aby veškeré operace v příkazové řádce (bash/shell) prováděl vzdáleně na Raspberry Pi místo lokálního stroje. Tím se zamezí nechtěným změnám na pracovní stanici (např. Milhy-PC).

## Instrukce pro agenta:

1. **Aktivace:** Pokud uživatel zmíní "budeme pracovat na rpi" nebo použije příkaz `/rpi-on`, aktivuj tento režim.
2. **Tunelování:** Každý `run_shell_command` nebo volání `bash` nástroje musí být obaleno do SSH wrapperu:
   ```bash
   ssh RPi "tmux has-session -t pi 2>/dev/null || tmux new-session -d -s pi; tmux send-keys -t pi:0.0 '<příkaz>' C-m; ..."
   ```
3. **Zabezpečení:** Používej `base64` pro přenos příkazu, aby nedošlo k rozbití speciálních znaků.
4. **Persistence:** Veškerá práce probíhá v tmux session `pi`.

## Parametry připojení:
- **Host:** RPi (definováno v ~/.ssh/config)
- **Session:** pi
