import requests,sys,json,warnings,csv,os,re
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from tparse2 import Pool,loads
warnings.filterwarnings('ignore')
wb,dash,outcsv=sys.argv[1:4]; months=sys.argv[4].split(',')
sp='4'; mapws='MROS1 Response map '; donws=sys.argv[5]; pick=sys.argv[6]
view='ResponseDashboards'; base='https://analytics.wfp.org'
def session():
    S=requests.Session(); S.headers['User-Agent']='Mozilla/5.0'
    S.get(f'{base}/t/Public/views/{wb}/{view}',params={':embed':'y',':showVizHome':'no'})
    c=S.post(f'{base}/vizql/t/Public/w/{wb}/v/{view}/startSession/viewing',params={':embed':'y',':showVizHome':'no'},headers={'Accept':'application/json'}).json()
    sid=c['sessionid']; root=base+c['vizql_root']; P=Pool()
    r=S.post(f"{root}/bootstrapSession/sessions/{sid}",data={'sheet_id':c['sheetId'],'worksheetPortSize':'{"w":1600,"h":1200}','dashboardPortSize':'{"w":1600,"h":1200}','clientDimension':'{"w":1600,"h":1200}','renderMapsClientSide':'true','isBrowserRendering':'true','browserRenderingThreshold':'100000','formatDataValueLocally':'false','navType':'Nav','navSrc':'Boot','devicePixelRatio':'1','showParams':'{"checkpoint":false,"refresh":false,"refreshUnmodified":false}','filterTileSize':'200','locale':'en_US','language':'en','verboseMode':'false','keychain_version':'1'})
    P.add(loads(r.text))
    H={'X-Tsi-Active-Tab':c['sheetId'],'Accept':'text/javascript'}
    r=S.post(f"{root}/sessions/{sid}/commands/tabdoc/set-active-story-point",data={'storyboard':'Response Dashboards ','storyPointId':sp,'shouldAutoCapture':'false','shouldAutoRevert':'true'},headers=H)
    P.add(loads(r.text))
    fed=re.findall(r'(\[federated\.[a-z0-9]+\]\.\[mn:Month:ok\])',r.text)[0]
    return S,root,sid,H,P,fed
def vid(ws): return json.dumps({'worksheet':ws,'dashboard':dash,'storyboard':'Response Dashboards ','storyPointId':int(sp)})
def mapdf(W):
    mp=[x for x in W.get(mapws,[]) if 'Admin2 Pcode' in x]
    if not mp: return []
    x=max(mp,key=lambda d:len(d['Admin2 Pcode']))
    vk=[k for k in x if k.startswith('SUM(Number of reached') and '#' not in k]
    vk=[k for k in vk if '_raw' in k] or vk
    return [(x['Admin 11'][i],x['Admin 21'][i],x['Admin2 Pcode'][i],x[vk[0]][i]) for i in range(len(x['Admin2 Pcode']))]
rows=[]
for m in months:
    S,root,sid,H,P,fed=session()
    r=S.post(f"{root}/sessions/{sid}/commands/tabdoc/categorical-filter",data={'visualIdPresModel':vid(mapws),'globalFieldName':fed,'membershipTarget':'filter','filterValues':json.dumps([m]),'filterUpdateType':'filter-replace'},headers=H)
    o=loads(r.text); P.add(o); W=P.worksheets(o)
    don=[x for x in W.get(donws,[]) if x]
    donors=max(don,key=lambda d:len(list(d.values())[0]))[list(don[0].keys())[0]] if don else []
    print(m,"donors",len(donors),flush=True)
    for i,dn in enumerate(donors):
        if pick not in str(dn): continue
        r=S.post(f"{root}/sessions/{sid}/commands/tabdoc/select",data={'visualIdPresModel':vid(donws),'selection':json.dumps({'objectIds':[i+1],'selectionType':'tuples'}),'selectOptions':'select-options-simple'},headers=H)
        o=loads(r.text); P.add(o); W=P.worksheets(o)
        md=mapdf(W)
        tot=sum(float(str(v).replace(',','')) for *_,v in md if v is not None)
        print('  ',i+1,dn,len(md),tot)
        for a1,a2,pc,v in md: rows.append({'workbook':wb,'month':m,'donor':dn,'admin1':a1,'admin2':a2,'admin2_pcode':pc,'reached':v})
with open(outcsv,'w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['workbook','month','donor','admin1','admin2','admin2_pcode','reached']); w.writeheader(); w.writerows(rows)
