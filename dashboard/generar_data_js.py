import json

with open("dashboard/data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

with open("dashboard/data.js", "w", encoding="utf-8") as f:
    f.write("const DASHBOARD_DATA = ")
    json.dump(data, f, ensure_ascii=False, indent=2)
    f.write(";")

print("data.js generado correctamente")