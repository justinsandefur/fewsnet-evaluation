"""Rebuild record-level table from an xlsx pivot cache. usage: pivotcache.py file.xlsx N out.csv"""
import sys, zipfile, csv
import xml.etree.ElementTree as ET
ns={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
f,n,out=sys.argv[1],sys.argv[2],sys.argv[3]
z=zipfile.ZipFile(f)
d=ET.fromstring(z.read(f'xl/pivotCache/pivotCacheDefinition{n}.xml'))
fields=[];shared=[]
def val(e):
    t=e.tag.split('}')[1]
    if t=='m': return ''
    return e.get('v','')
for cf in d.find('m:cacheFields',ns):
    fields.append(cf.get('name').replace('_x000a_',' ').strip())
    si=cf.find('m:sharedItems',ns)
    shared.append([val(e) for e in si] if si is not None else [])
w=csv.writer(open(out,'w',newline=''))
w.writerow(fields)
cnt=0
with z.open(f'xl/pivotCache/pivotCacheRecords{n}.xml') as fh:
    for ev,el in ET.iterparse(fh):
        if el.tag.endswith('}r'):
            row=[]
            for i,c in enumerate(el):
                t=c.tag.split('}')[1]
                row.append(shared[i][int(c.get('v'))] if t=='x' else val(c))
            w.writerow(row); cnt+=1; el.clear()
print(cnt,'records')
