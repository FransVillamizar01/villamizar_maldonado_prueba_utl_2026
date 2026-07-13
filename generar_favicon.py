import base64

svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect width="100" height="100" rx="14" fill="#12161C"/><text x="50" y="66" font-size="58" text-anchor="middle" fill="#C89B3C" font-family="serif">B</text></svg>'''

b64 = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
print(f'<link rel="icon" href="data:image/svg+xml;base64,{b64}">')