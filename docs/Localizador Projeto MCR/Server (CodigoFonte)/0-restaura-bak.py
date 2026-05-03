import os, shutil
for root, dirs, files in os.walk("E:/Projeto MCR/Canary/src"):
    for f in files:
        if f.endswith(".bak"):
            orig = os.path.join(root, f[:-4])
            bak = os.path.join(root, f)
            shutil.copy2(bak, orig)
            print(f"Restaurado: {orig}")