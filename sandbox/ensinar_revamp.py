import json, subprocess, sys
cmd = {
    'cmd': 'ensinar',
    'args': [
        'Revamp de scripts legados concluido. 10 scripts movidos para _archive/. 3 funcoes uteis extraidas: validadores de codigo (crew_deepseek), fragmentador universal (super_fragmentador -> modulos/), gerador de licoes para KG (mcr_knowledge). 4 scripts externos atualizados para usar router padronizado.',
        'Revamp de scripts legados completo',
        'Arquivos arquivados: mcr_ultimate_upgrade, corrida_final_absoluta, mcr_supervisor, input_pipeline, mcr_learning_scan, mcr_scriptbuilder, mcr_auto_improve, crew_deepseek, super_fragmentador, mcr_knowledge. Funcoes uteis integradas em auto_revisor.py, kg.py, modulos/super_fragmentador.py. Scripts externos (mcr_agent, autobuild, observatory, crew_pattern) atualizados para router.',
        'arquitetura'
    ]
}
with open('E:/Projeto MCR/sandbox/.mcr_cmd.json', 'w') as f:
    json.dump(cmd, f, ensure_ascii=False)
subprocess.run([sys.executable, 'E:/Projeto MCR/scripts/mcr_devia/MCR_DevIA-Kernel.py', '--json', 'E:/Projeto MCR/sandbox/.mcr_cmd.json'],
    capture_output=True, text=True, timeout=60)
print('OK')
