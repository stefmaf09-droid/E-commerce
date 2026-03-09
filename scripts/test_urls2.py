import re
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.email_service.email_templates import *

html1 = template_disputes_detected('a@b.com', 'A', 2, 100, [])
html2 = template_claim_submitted('a@b.com', 'A', 'REF-01', 'Carrier', 10, 'CMD1', 'api')
html3 = template_claim_accepted('a@b.com', 'A', 'REF-01', 'Carrier', 10, 8, 2)
html4 = template_claim_rejected('a@b.com', 'A', 'REF-01', 'Carrier', 'reason')

print("1:", re.findall(r'href=[\"\'\']([^\"\'\']+)', html1))
print("2:", re.findall(r'href=[\"\'\']([^\"\'\']+)', html2))
print("3:", re.findall(r'href=[\"\'\']([^\"\'\']+)', html3))
print("4:", re.findall(r'href=[\"\'\']([^\"\'\']+)', html4))
