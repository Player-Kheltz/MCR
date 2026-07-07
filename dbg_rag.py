import sys; sys.path.insert(0, r'E:\MCR')
from rag_mcr import MCRRAG
rag = MCRRAG()
c = rag.collection.count()
print(f'Chunks no ChromaDB: {c}')
if c > 0:
    r = rag.collection.peek()
    metas = r.get('metadatas', [])
    docs = r.get('documents', [])
    print(f'--- Ultimos {min(5,len(metas))} chunks ---')
    for i in range(len(metas)-min(5,len(metas)), len(metas)):
        fonte = metas[i].get('fonte', '?') if metas[i] else '?'
        txt = docs[i][:60] if i < len(docs) else '?'
        print(f'  [{fonte}] {txt}')
