#!/usr/bin/env python3
"""Build dist/: theme.css (src/theme.css + Material icon overrides), app.js, sw.js.

Each mapped ionicons class gets its glyph replaced by a Material Symbols path,
painted with currentColor through mask-image, so icons follow the text colour.
Unmapped ionicons keep rendering from the original icon font.
"""
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent

# Material Icons (Apache 2.0), 24x24 viewBox
P = {
    "search": "M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z",
    "dark_mode": "M12 3a9 9 0 1 0 9 9c0-.46-.04-.92-.1-1.36a5.389 5.389 0 0 1-4.4 2.26 5.403 5.403 0 0 1-3.14-9.8c-.44-.06-.9-.1-1.36-.1z",
    "light_mode": "M12 7c-2.76 0-5 2.24-5 5s2.24 5 5 5 5-2.24 5-5-2.24-5-5-5zM2 13h2c.55 0 1-.45 1-1s-.45-1-1-1H2c-.55 0-1 .45-1 1s.45 1 1 1zm18 0h2c.55 0 1-.45 1-1s-.45-1-1-1h-2c-.55 0-1 .45-1 1s.45 1 1 1zM11 2v2c0 .55.45 1 1 1s1-.45 1-1V2c0-.55-.45-1-1-1s-1 .45-1 1zm0 18v2c0 .55.45 1 1 1s1-.45 1-1v-2c0-.55-.45-1-1-1s-1 .45-1 1zM5.99 4.58a.996.996 0 0 0-1.41 0 .996.996 0 0 0 0 1.41l1.06 1.06c.39.39 1.03.39 1.41 0s.39-1.03 0-1.41L5.99 4.58zm12.37 12.37a.996.996 0 0 0-1.41 0 .996.996 0 0 0 0 1.41l1.06 1.06c.39.39 1.03.39 1.41 0a.996.996 0 0 0 0-1.41l-1.06-1.06zm1.06-10.96a.996.996 0 0 0 0-1.41.996.996 0 0 0-1.41 0l-1.06 1.06c-.39.39-.39 1.03 0 1.41s1.03.39 1.41 0l1.06-1.06zM7.05 18.36a.996.996 0 0 0 0-1.41.996.996 0 0 0-1.41 0l-1.06 1.06c-.39.39-.39 1.03 0 1.41s1.03.39 1.41 0l1.06-1.06z",
    "settings": "M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58a.49.49 0 0 0 .12-.61l-1.92-3.32a.488.488 0 0 0-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54a.484.484 0 0 0-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58a.49.49 0 0 0-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z",
    "visibility": "M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z",
    "thumb_up": "M1 21h4V9H1v12zm22-11c0-1.1-.9-2-2-2h-6.31l.95-4.57.03-.32c0-.41-.17-.79-.44-1.06L14.17 1 7.59 7.59C7.22 7.95 7 8.45 7 9v10c0 1.1.9 2 2 2h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73v-2z",
    "thumb_down": "M15 3H6c-.83 0-1.54.5-1.84 1.22l-3.02 7.05c-.09.23-.14.47-.14.73v2c0 1.1.9 2 2 2h6.31l-.95 4.57-.03.32c0 .41.17.79.44 1.06L9.83 23l6.59-6.59c.36-.36.58-.86.58-1.41V5c0-1.1-.9-2-2-2zm4 0v12h4V3h-4z",
    "rss": "M6.18 15.64a2.18 2.18 0 0 1 2.18 2.18C8.36 19 7.38 20 6.18 20 5 20 4 19 4 17.82a2.18 2.18 0 0 1 2.18-2.18M4 4.44A15.56 15.56 0 0 1 19.56 20h-2.83A12.73 12.73 0 0 0 4 7.27V4.44m0 5.66a9.9 9.9 0 0 1 9.9 9.9h-2.83A7.07 7.07 0 0 0 4 12.93V10.1z",
    "add": "M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z",
    "headphones": "M12 1c-4.97 0-9 4.03-9 9v7c0 1.66 1.34 3 3 3h3v-8H5v-2c0-3.87 3.13-7 7-7s7 3.13 7 7v2h-4v8h3c1.66 0 3-1.34 3-3v-7c0-4.97-4.03-9-9-9z",
    "chevron_right": "M10 6 8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z",
    "chevron_left": "M15.41 7.41 14 6l-6 6 6 6 1.41-1.41L10.83 12z",
    "expand_more": "M16.59 8.59 12 13.17 7.41 8.59 6 10l6 6 6-6z",
    "expand_less": "m12 8-6 6 1.41 1.41L12 10.83l4.59 4.58L18 14z",
    "verified": "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z",
    "description": "M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z",
    "code": "M9.4 16.6 4.8 12l4.6-4.6L8 6l-6 6 6 6 1.4-1.4zm5.2 0 4.6-4.6-4.6-4.6L16 6l6 6-6 6-1.4-1.4z",
    "favorite": "m12 21.35-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z",
    "notifications": "M12 22c1.1 0 2-.9 2-2h-4c0 1.1.89 2 2 2zm6-6v-5c0-3.07-1.64-5.64-4.5-6.32V4c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5 1.5v.68C7.63 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2z",
    "logout": "m17 7-1.41 1.41L18.17 11H8v2h10.17l-2.58 2.58L17 17l5-5zM4 5h8V3H4c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h8v-2H4V5z",
    "play": "M8 5v14l11-7z",
    "delete": "M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z",
    "download": "M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z",
    "close": "M19 6.41 17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z",
    "edit": "M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04a.996.996 0 0 0 0-1.41l-2.34-2.34a.996.996 0 0 0-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z",
    "pause": "M6 19h4V5H6v14zm8-14v14h4V5h-4z",
    "replay": "M12 5V1L7 6l5 5V7c3.31 0 6 2.69 6 6s-2.69 6-6 6-6-2.69-6-6H4c0 4.42 3.58 8 8 8s8-3.58 8-8-3.58-8-8-8z",
    "volume_up": "M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z",
    "volume_down": "M18.5 12c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM5 9v6h4l5 5V4L9 9H5z",
    "volume_mute": "M7 9v6h4l5 5V4l-5 5H7z",
    "volume_off": "M16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51A8.796 8.796 0 0 0 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3 3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06a8.99 8.99 0 0 0 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4 9.91 6.09 12 8.18V4z",
    "fullscreen": "M7 14H5v5h5v-2H7v-3zm-2-4h2V7h3V5H5v5zm12 7h-3v2h5v-5h-2v3zM14 5v2h3v3h2V5h-5z",
    "fullscreen_exit": "M5 16h3v3h2v-5H5v2zm3-8H5v2h5V5H8v3zm6 11h2v-3h3v-2h-5v5zm2-11V5h-2v5h5V8h-3z",
    "closed_caption": "M19 4H5a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h14c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm-8 7H9.5v-.5h-2v3h2V13H11v1c0 .55-.45 1-1 1H7c-.55 0-1-.45-1-1v-4c0-.55.45-1 1-1h3c.55 0 1 .45 1 1v1zm7 0h-1.5v-.5h-2v3h2V13H18v1c0 .55-.45 1-1 1h-3c-.55 0-1-.45-1-1v-4c0-.55.45-1 1-1h3c.55 0 1 .45 1 1v1z",
    "share": "M18 16.08c-.76 0-1.44.3-1.96.77L8.91 12.7c.05-.23.09-.46.09-.7s-.04-.47-.09-.7l7.05-4.11c.54.5 1.25.81 2.04.81 1.66 0 3-1.34 3-3s-1.34-3-3-3-3 1.34-3 3c0 .24.04.47.09.7L8.04 9.81C7.5 9.31 6.79 9 6 9c-1.66 0-3 1.34-3 3s1.34 3 3 3c.79 0 1.5-.31 2.04-.81l7.12 4.16c-.05.21-.08.43-.08.65 0 1.61 1.31 2.92 2.92 2.92s2.92-1.31 2.92-2.92-1.31-2.92-2.92-2.92z",
    "cinema": "M19 6H5c-1.1 0-2 .9-2 2v8c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zm0 10H5V8h14v8z",
    "cinema_on": "M19 6H5c-1.1 0-2 .9-2 2v8c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2z",
    "lock": "M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1 1.71 0 3.1 1.39 3.1 3.1v2z",
    "lock_open": "M12 17c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm6-9h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6h1.9c0-1.71 1.39-3.1 3.1-3.1 1.71 0 3.1 1.39 3.1 3.1v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm0 12H6V10h12v10z",
    "public": "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z",
    "account_circle": "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2a7.2 7.2 0 0 1-6-3.22c.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08a7.2 7.2 0 0 1-6 3.22z",
    "audiotrack": "M12 3v9.28a4.39 4.39 0 0 0-1.5-.28C8.01 12 6 14.01 6 16.5S8.01 21 10.5 21c2.31 0 4.2-1.75 4.45-4H15V6h4V3h-7z",
}

# video.js control icons: selector of the glyph pseudo-element -> (icon, size)
V = ":root body[class] .video-js"
VJS = {
    f"{V} .vjs-play-control .vjs-icon-placeholder::before": ("play", 26),
    f"{V} .vjs-play-control.vjs-playing .vjs-icon-placeholder::before": ("pause", 26),
    f"{V} .vjs-play-control.vjs-ended .vjs-icon-placeholder::before": ("replay", 24),
    f"{V} .vjs-big-play-button .vjs-icon-placeholder::before": ("play", 40),
    f"{V} .vjs-mute-control .vjs-icon-placeholder::before": ("volume_up", 24),
    f"{V} .vjs-mute-control.vjs-vol-2 .vjs-icon-placeholder::before": ("volume_down", 24),
    f"{V} .vjs-mute-control.vjs-vol-1 .vjs-icon-placeholder::before": ("volume_mute", 24),
    f"{V} .vjs-mute-control.vjs-vol-0 .vjs-icon-placeholder::before": ("volume_off", 24),
    f"{V} .vjs-fullscreen-control .vjs-icon-placeholder::before": ("fullscreen", 26),
    f"{V}.vjs-fullscreen .vjs-fullscreen-control .vjs-icon-placeholder::before": ("fullscreen_exit", 26),
    f"{V} .vjs-captions-button .vjs-icon-placeholder::before": ("closed_caption", 24),
    f"{V} .vjs-subs-caps-button .vjs-icon-placeholder::before": ("closed_caption", 24),
    f"{V} .vjs-audio-button .vjs-icon-placeholder::before": ("audiotrack", 22),
    f"{V} .vjs-http-source-selector .vjs-icon-placeholder::before": ("settings", 22),
    f"{V} .vjs-http-source-selector .vjs-icon-cog::before": ("settings", 22),
    f"{V} .vjs-share-control.vjs-icon-share::before": ("share", 20),
    f"{V} .vjs-close-button .vjs-icon-placeholder::before": ("close", 20),
    f"{V} .vjs-cinema-control .vjs-icon-placeholder::before": ("cinema", 26),
    f":root.iv-cinema body[class] .video-js .vjs-cinema-control .vjs-icon-placeholder::before": ("cinema_on", 26),
}

# ionicons class -> material icon
MAP = {
    "ion-ios-search": "search",
    "ion-ios-moon": "dark_mode",
    "ion-ios-sunny": "light_mode",
    "ion-ios-cog": "settings",
    "ion-ios-eye": "visibility",
    "ion-ios-thumbs-up": "thumb_up",
    "ion-ios-thumbs-down": "thumb_down",
    "ion-logo-rss": "rss",
    "ion-md-add": "add",
    "ion-md-headset": "headphones",
    "ion-ios-arrow-forward": "chevron_right",
    "ion-ios-arrow-back": "chevron_left",
    "ion-ios-arrow-down": "expand_more",
    "ion-ios-arrow-up": "expand_less",
    "ion-md-checkmark-circle": "verified",
    "ion-ios-paper": "description",
    "ion-logo-github": "code",
    "ion-logo-javascript": "code",
    "ion-ios-wallet": "favorite",
    "ion-ios-notifications": "notifications",
    "ion-ios-notifications-outline": "notifications",
    "ion-ios-log-out": "logout",
    "ion-ios-play": "play",
    "ion-md-trash": "delete",
    "ion-ios-trash": "delete",
    "ion-md-download": "download",
    "ion-ios-download": "download",
    "ion-md-close": "close",
    "ion-ios-close": "close",
    "ion-md-create": "edit",
    "ion-ios-lock": "lock",
    "ion-ios-unlock": "lock_open",
    "ion-ios-globe": "public",
    "ion-md-globe": "public",
    "ion-ios-create": "edit",
}


def data_uri(path: str) -> str:
    svg = f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'><path d='{path}'/></svg>"
    return "data:image/svg+xml," + quote(svg, safe="/:=' ")


def icons_css() -> str:
    sel = ",\n".join(f":root body[class] .{c}::before" for c in MAP)
    out = [
        "/* ---------- icons: ionicons glyphs -> Material, painted via mask ---------- */",
        "",
        sel + " {",
        "  content: \"\" !important;",
        "  display: inline-block;",
        "  width: 1.2em;",
        "  height: 1.2em;",
        "  vertical-align: -.24em;",
        "  background-color: currentColor;",
        "  -webkit-mask: var(--ico) center / contain no-repeat;",
        "  mask: var(--ico) center / contain no-repeat;",
        "}",
        "",
    ]
    # icons referenced directly from src/theme.css as var(--i-<name>)
    extra = {"account_circle", "logout", "expand_more", "chevron_right", "play"}
    used = sorted(set(MAP.values()) | {n for n, _ in VJS.values()} | extra)
    out.append(":root {")
    out += [f"  --i-{n}: url(\"{data_uri(P[n])}\");" for n in used]
    out += ["}", ""]
    for cls, name in MAP.items():
        out.append(f".{cls} {{ --ico: var(--i-{name}); }}")
    out += [
        "",
        "/* ---------- player icons ---------- */",
        "",
        ",\n".join(VJS) + " {",
        "  content: \"\" !important;",
        "  background-color: currentColor;",
        "  -webkit-mask: var(--ico) center / var(--ico-size, 24px) no-repeat;",
        "  mask: var(--ico) center / var(--ico-size, 24px) no-repeat;",
        "}",
        "",
    ]
    for sel, (name, size) in VJS.items():
        out.append(f"{sel} {{ --ico: var(--i-{name}); --ico-size: {size}px; }}")
    return "\n".join(out) + "\n"


def main() -> None:
    src = (ROOT / "src" / "theme.css").read_text()
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    css = src.rstrip() + "\n\n" + icons_css()
    (dist / "theme.css").write_text(css)
    (dist / "app.js").write_text((ROOT / "src" / "app.js").read_text())
    (dist / "sw.js").write_text((ROOT / "src" / "sw.js").read_text())
    print(f"dist/theme.css: {len(css)} bytes, {len(MAP)} icons")


if __name__ == "__main__":
    main()
