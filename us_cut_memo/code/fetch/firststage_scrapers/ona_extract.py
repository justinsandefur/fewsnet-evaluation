import openpyxl,csv,gzip,sys,datetime
src,out=sys.argv[1],sys.argv[2]
wb=openpyxl.load_workbook(src,read_only=True,data_only=True)
ws=wb['DATA from ONA']
n=0
with gzip.open(out,'wt',newline='') as f:
    w=csv.writer(f)
    for row in ws.iter_rows(values_only=True):
        if n>0 and all(v is None for v in row): continue
        w.writerow(['' if v is None else (v.isoformat() if isinstance(v,(datetime.date,datetime.datetime)) else v) for v in row]); n+=1
        if n%20000==0: print(n,flush=True)
print('rows',n)
