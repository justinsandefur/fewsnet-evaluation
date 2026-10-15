import json
def walk(o,key,acc):
    if isinstance(o,dict):
        for k,v in o.items():
            if k==key: acc.append(v)
            walk(v,key,acc)
    elif isinstance(o,list):
        for v in o: walk(v,key,acc)
    return acc
def loads(t):
    if t and t[0].isdigit():
        parts=[];i=0
        while i<len(t):
            j=t.index(';',i); n=int(t[i:j]); parts.append(json.loads(t[j+1:j+1+n])); i=j+1+n
        return parts
    return [json.loads(t)]
class Pool:
    def __init__(s): s.seen=set(); s.pool={}
    def add(s,objs):
        segs={}
        for o in objs:
            for dd in walk(o,'dataSegments',[]):
                if not dd: continue
                for k,v in dd.items():
                    if v: segs[int(k)]=v
        if 0 in segs: s.seen=set(); s.pool={}
        for k in sorted(segs):
            if k in s.seen: continue
            s.seen.add(k)
            for col in segs[k]['dataColumns']:
                s.pool.setdefault(col['dataType'],[]).extend(col['dataValues'])
    def worksheets(s,objs):
        res={}
        def get(dt,x):
            if x<0: x=-x-1; dt='cstring'
            L=s.pool.get(dt,[])
            return L[x] if x<len(L) else None
        def find(o,ws=None):
            if isinstance(o,dict):
                if isinstance(o.get('worksheet'),str): ws=o['worksheet']
                if 'paneColumnsData' in o:
                    pcd=o['paneColumnsData']; cols={}
                    for vc in pcd['vizDataColumns']:
                        if 'fieldCaption' not in vc: continue
                        for idx,pi in enumerate(vc.get('paneIndices',[])):
                            pc=pcd['paneColumnsList'][pi]['vizPaneColumns'][vc['columnIndices'][idx]]
                            vi=pc.get('aliasIndices') or pc.get('valueIndices') or []
                            vi2=pc.get('valueIndices') or []
                            cols[vc['fieldCaption']+('' if idx==0 else f'#{idx}')]=[get(vc.get('dataType'),x) for x in vi]
                            if vi2 and vi2!=vi: cols[vc['fieldCaption']+'_raw'+('' if idx==0 else f'#{idx}')]=[get(vc.get('dataType'),x) for x in vi2]
                    res.setdefault(ws,[]).append(cols)
                for v in o.values(): find(v,ws)
            elif isinstance(o,list):
                for v in o: find(v,ws)
        for o in objs: find(o)
        return res
