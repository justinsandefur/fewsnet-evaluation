import requests,sys,json,warnings,csv,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from tparse2 import Pool,loads
warnings.filterwarnings('ignore')
wb,sp,dash,mapws,outcsv=sys.argv[1:6]
view='ResponseDashboards'; base='https://analytics.wfp.org'
S=requests.Session(); S.headers['User-Agent']='Mozilla/5.0'
S.get(f'{base}/t/Public/views/{wb}/{view}',params={':embed':'y',':showVizHome':'no'})
c=S.post(f'{base}/vizql/t/Public/w/{wb}/v/{view}/startSession/viewing',params={':embed':'y',':showVizHome':'no'},headers={'Accept':'application/json'}).json()
sid=c['sessionid']; root=base+c['vizql_root']; P=Pool()
r=S.post(f"{root}/bootstrapSession/sessions/{sid}",data={'sheet_id':c['sheetId'],'worksheetPortSize':'{"w":1600,"h":1200}','dashboardPortSize':'{"w":1600,"h":1200}','clientDimension':'{"w":1600,"h":1200}','renderMapsClientSide':'true','isBrowserRendering':'true','browserRenderingThreshold':'100000','formatDataValueLocally':'false','navType':'Nav','navSrc':'Boot','devicePixelRatio':'1','showParams':'{"checkpoint":false,"refresh":false,"refreshUnmodified":false}','filterTileSize':'200','locale':'en_US','language':'en','verboseMode':'false','keychain_version':'1'})
P.add(loads(r.text))
H={'X-Tsi-Active-Tab':c['sheetId'],'Accept':'text/javascript'}
r=S.post(f"{root}/sessions/{sid}/commands/tabdoc/set-active-story-point",data={'storyboard':'Response Dashboards ','storyPointId':sp,'shouldAutoCapture':'false','shouldAutoRevert':'true'},headers=H)
P.add(loads(r.text))
import re
fed=re.findall(r'(\[federated\.[a-z0-9]+\]\.\[mn:Month:ok\])',r.text)[0]; print('field',fed)
vid=json.dumps({'worksheet':mapws,'dashboard':dash,'storyboard':'Response Dashboards ','storyPointId':int(sp)})
months=['January','February','March','April','May','June','July','August','September','October','November','December']
rows=[]
for m in months:
    r=S.post(f"{root}/sessions/{sid}/commands/tabdoc/categorical-filter",data={'visualIdPresModel':vid,'globalFieldName':fed,'membershipTarget':'filter','filterValues':json.dumps([m]),'filterUpdateType':'filter-replace'},headers=H)
    o=loads(r.text); P.add(o); W=P.worksheets(o)
    mp=[x for x in W.get(mapws,[]) if 'Admin2 Pcode' in x]
    tot=[x for k,v in W.items() if 'Beneficiaries Reached' in (k or '') for x in v]
    if not mp: print(m,'no map'); continue
    x=max(mp,key=lambda d:len(d['Admin2 Pcode']))
    valk=[k for k in x if k.startswith('SUM(Number of reached') and not k.endswith('#1')]
    vk=[k for k in valk if '_raw' in k] or valk
    ip=[k for k in x if k.startswith('CNTD(Implementing')]
    for i in range(len(x['Admin2 Pcode'])):
        rows.append({'workbook':wb,'month':m,'admin1':x.get('Admin 11',[None]*999)[i],'admin2':x.get('Admin 21',[None]*999)[i],'admin2_pcode':x['Admin2 Pcode'][i],'reached':x[vk[0]][i],'reached_label':x[valk[0]][i] if valk else None,'n_impl_partners':x[ip[0]][i] if ip else None})
    s=sum(float(str(rr['reached']).replace(',','')) for rr in rows if rr['month']==m and rr['reached'] is not None)
    print(m,'districts',len(x['Admin2 Pcode']),'sum',s,'tot',tot[:1])
with open(outcsv,'w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print(len(rows),'rows ->',outcsv)
