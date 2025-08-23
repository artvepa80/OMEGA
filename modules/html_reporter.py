from pathlib import Path

def generate_report(title: str, sections: dict, out_path: str = "outputs/reporte_prediccion.html"):
    html = [f"<html><head><meta charset='utf-8'><title>{title}</title></head><body>"]
    html.append(f"<h1>{title}</h1>")
    for k, v in sections.items():
        html.append(f"<h2>{k}</h2><pre>{v}</pre>")
    html.append("</body></html>")
    Path(out_path).write_text("\n".join(html), encoding="utf-8")
    return out_path
