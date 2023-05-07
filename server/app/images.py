import base64

def image_data(svg_bytes):
    svg_base64 = base64.b64encode(svg_bytes).decode("ascii")
    return f"data:image/svg+xml;base64,{svg_base64}"
