from src.reports.pdf_generator import PDFGenerator
from tempfile import mkstemp
import os
kpis={'total_recovered':100.0,'total_claims':1,'success_rate':50.0,'average_processing_time':1.2,'by_carrier':{}}
fd, path = mkstemp(suffix='.pdf')
os.close(fd)
print('Generating to', path)
g = PDFGenerator()
try:
    g.generate_monthly_report('Client Test','test@example.com','Janvier 2026',kpis,[],path)
    with open(path,'rb') as f:
        data=f.read()
    try:
        txt=data.decode('latin1')
    except Exception:
        txt=data.decode('utf-8',errors='ignore')
    print('---BEGIN PDF TEXT SNIPPET---')
    print(txt[:2000])
    print('---END PDF TEXT SNIPPET---')
    print('Contains Client Test?', 'client test' in txt.lower())
except Exception as e:
    print('Error:', e)
