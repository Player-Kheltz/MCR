"""MCR-DevIA — Utilitario: print SEM emoji, SEM crash cp1252"""
import re, sys

# Padrao de emojis para remover
_EMOJI_PATTERN = re.compile(
    "[" 
    "\U0001F600-\U0001F9FF" "\U0001FA00-\U0001FAFF"
    "\U00002702-\U000027B0" "\U000024C2-\U0001F251"
    "\U0001F300-\U0001F5FF" "\U0001F680-\U0001F6FF"
    "\U0000FE00-\U0000FE0F" "\U0000200D"
    "\U00002B50" "\U00002764" "\U00002B06" "\U00002B07"
    "\U00002757" "\U0000203C" "\U00002049" "\U000020E3"
    "\U00002934" "\U00002935" "\U000025AA" "\U000025AB"
    "\U000025B6" "\U000025C0" "\U000025FB" "\U000025FC"
    "\U000025FD" "\U000025FE" "\U00002615" "\U000026AA"
    "\U000026AB" "\U000026BD" "\U000026BE" "\U000025CE"
    "\U00002B55" "\U00002733" "\U00002734" "\U00002744"
    "\U00002747" "\U00002763" "\U00002764" "\U00002795"
    "\U00002796" "\U00002797" "\U000027A1" "\U00002B05"
    "\U00002B08" "\U00002B09" "\U00002B0A" "\U00002B0B"
    "\U00002B0C" "\U00002B0D" "\U0000FE0F"
    "\U0001F1E0-\U0001F1FF" "\U0000200D"
    "\U000020E3" "\U0000FE00" "\U0000FE01" "\U0000FE02"
    "\U0000FE03" "\U0000FE04" "\U0000FE05" "\U0000FE06"
    "\U0000FE07" "\U0000FE08" "\U0000FE09" "\U0000FE0A"
    "\U0000FE0B" "\U0000FE0C" "\U0000FE0D" "\U0000FE0E"
    "\U0000FE0F"
    "]+", re.UNICODE
)

def safe_print(*args, **kwargs):
    """Print que NUNCA quebra por encoding. Remove emojis, converte para ASCII."""
    saida = " ".join(str(a) for a in args)
    saida = _EMOJI_PATTERN.sub("", saida)
    saida = saida.encode("ascii", "replace").decode("ascii")
    kwargs.pop("file", None)
    print(saida, file=sys.stdout, **kwargs)

def limpar_emoji(texto):
    """Remove emojis de qualquer texto."""
    return _EMOJI_PATTERN.sub("", texto)

# Teste
if __name__ == "__main__":
    safe_print("Teste com emoji:", "✅⭐❤️⬆️📌 removidos")
    safe_print("[OK] Sistema de safe_print ativo!")
