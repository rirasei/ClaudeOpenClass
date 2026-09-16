import hashlib
import html
import json
import os
from datetime import datetime

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

app = FastAPI()

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "guestboard.json")


def load_entries() -> list[dict]:
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_entries(entries: list[dict]) -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def next_id(entries: list[dict]) -> int:
    return max((e["id"] for e in entries), default=0) + 1


def render_entry(entry: dict) -> str:
    name = html.escape(entry["name"])
    message = html.escape(entry["message"]).replace("\n", "<br>")
    created_at = entry["created_at"]
    initial = html.escape(entry["name"][0].upper()) if entry["name"] else "?"

    return f"""
    <li class="entry">
        <div class="avatar">{initial}</div>
        <div class="entry-body">
            <div class="entry-header">
                <span class="entry-name">{name}</span>
                <span class="entry-date">{created_at}</span>
            </div>
            <p class="entry-message">{message}</p>
            <details class="delete-toggle">
                <summary>삭제</summary>
                <form method="post" action="/delete/{entry['id']}" class="delete-form">
                    <input type="password" name="password" placeholder="비밀번호" required>
                    <button type="submit">확인</button>
                </form>
            </details>
        </div>
    </li>
    """


def render_page(entries: list[dict], error: str | None = None) -> str:
    entries_sorted = sorted(entries, key=lambda e: e["id"], reverse=True)
    entries_html = "".join(render_entry(e) for e in entries_sorted) or (
        '<li class="empty">아직 남겨진 방명록이 없습니다. 첫 글을 남겨보세요!</li>'
    )
    error_html = f'<p class="error">{html.escape(error)}</p>' if error else ""

    return f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>방명록</title>
        <style>
            :root {{
                --main: #2e7d32;
                --main-light: #4caf50;
                --main-bg: #eef7ee;
                --text: #1b2a1b;
                --muted: #6b7d6b;
            }}
            * {{ box-sizing: border-box; }}
            body {{
                margin: 0;
                font-family: "Pretendard", "Apple SD Gothic Neo", "Malgun Gothic", sans-serif;
                background: linear-gradient(180deg, var(--main-bg) 0%, #ffffff 320px);
                color: var(--text);
            }}
            .container {{
                max-width: 640px;
                margin: 0 auto;
                padding: 40px 20px 80px;
            }}
            h1 {{
                text-align: center;
                color: var(--main);
                font-size: 2rem;
                margin-bottom: 4px;
            }}
            .subtitle {{
                text-align: center;
                color: var(--muted);
                margin-bottom: 32px;
                font-size: 0.95rem;
            }}
            .card {{
                background: #fff;
                border-radius: 16px;
                box-shadow: 0 4px 16px rgba(46, 125, 50, 0.10);
                padding: 24px;
                margin-bottom: 32px;
            }}
            form.write-form label {{
                display: block;
                font-size: 0.85rem;
                color: var(--muted);
                margin-bottom: 4px;
                margin-top: 14px;
            }}
            form.write-form label:first-child {{ margin-top: 0; }}
            input, textarea {{
                width: 100%;
                padding: 10px 12px;
                border: 1px solid #d7e6d7;
                border-radius: 10px;
                font-size: 0.95rem;
                font-family: inherit;
                background: #fbfffb;
                color: var(--text);
                transition: border-color 0.15s ease;
            }}
            input:focus, textarea:focus {{
                outline: none;
                border-color: var(--main-light);
            }}
            textarea {{ resize: vertical; min-height: 80px; }}
            .name-password-row {{
                display: flex;
                gap: 12px;
            }}
            .name-password-row > div {{ flex: 1; }}
            .submit-btn {{
                margin-top: 20px;
                width: 100%;
                padding: 12px;
                border: none;
                border-radius: 10px;
                background: var(--main);
                color: #fff;
                font-size: 1rem;
                font-weight: 600;
                cursor: pointer;
                transition: background 0.15s ease;
            }}
            .submit-btn:hover {{ background: var(--main-light); }}
            .error {{
                color: #c0392b;
                font-size: 0.85rem;
                margin-top: 10px;
                margin-bottom: 0;
            }}
            ul.entry-list {{
                list-style: none;
                margin: 0;
                padding: 0;
                display: flex;
                flex-direction: column;
                gap: 16px;
            }}
            .entry {{
                display: flex;
                gap: 14px;
                background: #fff;
                border: 1px solid #e3f1e3;
                border-radius: 14px;
                padding: 16px 18px;
                box-shadow: 0 2px 8px rgba(46, 125, 50, 0.06);
            }}
            .avatar {{
                flex-shrink: 0;
                width: 40px;
                height: 40px;
                border-radius: 50%;
                background: var(--main-light);
                color: #fff;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 700;
                font-size: 1rem;
            }}
            .entry-body {{ flex: 1; min-width: 0; }}
            .entry-header {{
                display: flex;
                justify-content: space-between;
                align-items: baseline;
                gap: 8px;
                flex-wrap: wrap;
            }}
            .entry-name {{ font-weight: 700; color: var(--main); }}
            .entry-date {{ font-size: 0.78rem; color: var(--muted); }}
            .entry-message {{
                margin: 8px 0 4px;
                line-height: 1.5;
                word-break: break-word;
                white-space: pre-wrap;
            }}
            .delete-toggle {{ margin-top: 6px; }}
            .delete-toggle summary {{
                cursor: pointer;
                font-size: 0.78rem;
                color: var(--muted);
                width: fit-content;
            }}
            .delete-toggle summary:hover {{ color: var(--main); }}
            .delete-form {{
                display: flex;
                gap: 8px;
                margin-top: 8px;
            }}
            .delete-form input {{ flex: 1; }}
            .delete-form button {{
                padding: 8px 14px;
                border: none;
                border-radius: 8px;
                background: var(--main);
                color: #fff;
                cursor: pointer;
                font-size: 0.85rem;
            }}
            .delete-form button:hover {{ background: var(--main-light); }}
            .empty {{
                text-align: center;
                color: var(--muted);
                padding: 30px 0;
                list-style: none;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🌿 방명록</h1>
            <p class="subtitle">따뜻한 한마디를 남겨주세요</p>

            <div class="card">
                <form class="write-form" method="post" action="/write">
                    <label for="name">이름</label>
                    <div class="name-password-row">
                        <div>
                            <input type="text" id="name" name="name" placeholder="이름" maxlength="20" required>
                        </div>
                        <div>
                            <input type="password" id="password" name="password" placeholder="비밀번호 (삭제 시 필요)" maxlength="30" required>
                        </div>
                    </div>
                    <label for="message">내용</label>
                    <textarea id="message" name="message" placeholder="방명록에 남길 이야기를 적어주세요" maxlength="500" required></textarea>
                    <button type="submit" class="submit-btn">방명록 남기기</button>
                    {error_html}
                </form>
            </div>

            <ul class="entry-list">
                {entries_html}
            </ul>
        </div>
    </body>
    </html>
    """


@app.get("/", response_class=HTMLResponse)
def index():
    return render_page(load_entries())


@app.post("/write")
def write(name: str = Form(...), password: str = Form(...), message: str = Form(...), request: Request = None):
    name = name.strip()
    message = message.strip()

    if not name or not password or not message:
        return HTMLResponse(render_page(load_entries(), error="이름, 비밀번호, 내용을 모두 입력해주세요."))

    entries = load_entries()
    entry = {
        "id": next_id(entries),
        "name": name,
        "message": message,
        "password": hash_password(password),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "ip": request.client.host if request and request.client else "unknown",
    }
    entries.append(entry)
    save_entries(entries)

    return RedirectResponse(url="/", status_code=303)


@app.post("/delete/{entry_id}")
def delete(entry_id: int, password: str = Form(...)):
    entries = load_entries()
    target = next((e for e in entries if e["id"] == entry_id), None)

    if target is None:
        return RedirectResponse(url="/", status_code=303)

    if target["password"] != hash_password(password):
        return HTMLResponse(render_page(entries, error="비밀번호가 일치하지 않습니다."))

    entries = [e for e in entries if e["id"] != entry_id]
    save_entries(entries)

    return RedirectResponse(url="/", status_code=303)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
