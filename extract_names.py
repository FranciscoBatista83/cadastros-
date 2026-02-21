import re
import os

log_path = r"c:\Users\User\Documents\Repositorio_local\Python\Coisas da Laine\Projeto_apolices_antigravity\logs\bot_debug.log"

if os.path.exists(log_path):
    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
        # Lê apenas o final do arquivo para economizar memória
        f.seek(0, os.SEEK_END)
        size = f.tell()
        # Lê os últimos 1MB
        f.seek(max(0, size - 1024 * 1024))
        content = f.read()
        
    names = re.findall(r"Limpando nome: '(.*)'", content)
    for name in sorted(list(set(names))):
        print(name)
else:
    print("Log not found")
