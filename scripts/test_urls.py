import re
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.email_service.email_templates import *

html1 = template_disputes_detected('a@b.com', 'A', 2, 100, [])
html2 = template_claim_submitted('a@b.com', 'A', 'REF-01', 'Carrier', 10, 'CMD1', 'api')
html3 = template_claim_accepted('a@b.com', 'A', 'REF-01', 'Carrier', 10, 8, 2)
html4 = template_claim_rejected('a@b.com', 'A', 'REF-01', 'Carrier', 'reason')

print("Disputes:", re.search(r'href=[\"\'\']([^\"\'\']+)', html1).group(1))
print("Submitted:", re.search(r'href=[\"\'\']([^\"\'\']+)', html2).group(1))
print("Accepted:", re.search(r'href=[\"\'\']([^\"\'\']+)', html3).group(1))
print("Rejected:", re.search(r'href=[\"\'\']([^\"\'\']+)', html4).group(1))
