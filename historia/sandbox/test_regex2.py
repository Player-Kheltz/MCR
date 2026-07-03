import re
# Mini test
p = r'\bbusc\w*\b'
print('Pattern:', repr(p))
m = re.search(p, 'busque')
print('Match:', m)
if m:
    print('Group:', repr(m.group()))
    print('Span:', m.span())
# Test without word boundary
p2 = r'busc\w*'
m2 = re.search(p2, 'busque')
print('\nWithout boundary:', m2, repr(m2.group() if m2 else None))
