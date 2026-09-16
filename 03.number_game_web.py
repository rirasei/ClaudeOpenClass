import random
import uuid

from fastapi import FastAPI, Cookie, Form
from fastapi.responses import HTMLResponse

app = FastAPI()

# session_id -> {"answer": int, "attempts": int, "message": str, "done": bool}
games: dict[str, dict] = {}


def new_game() -> dict:
    return {
        "answer": random.randint(1, 100),
        "attempts": 0,
        "message": "1부터 100 사이의 숫자를 맞춰보세요!",
        "done": False,
    }


def render(game: dict) -> str:
    if game["done"]:
        body = f"""
        <p class="msg success">{game["message"]}</p>
        <form method="post" action="/reset">
            <button type="submit">다시 하기</button>
        </form>
        """
    else:
        body = f"""
        <p class="msg">{game["message"]}</p>
        <p>시도 횟수: {game["attempts"]}</p>
        <form method="post" action="/guess">
            <input type="number" name="guess" min="1" max="100" required autofocus>
            <button type="submit">제출</button>
        </form>
        """

    return f"""
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <title>숫자 맞추기 게임</title>
        <style>
            body {{ font-family: sans-serif; max-width: 400px; margin: 60px auto; text-align: center; }}
            .msg {{ font-size: 1.2rem; margin-bottom: 1rem; }}
            .success {{ color: green; font-weight: bold; }}
            input {{ font-size: 1rem; padding: 4px 8px; width: 100px; }}
            button {{ font-size: 1rem; padding: 4px 12px; margin-left: 8px; }}
        </style>
    </head>
    <body>
        <h1>숫자 맞추기 게임</h1>
        {body}
    </body>
    </html>
    """


@app.get("/", response_class=HTMLResponse)
def index(session_id: str | None = Cookie(default=None)):
    if session_id is None or session_id not in games:
        session_id = str(uuid.uuid4())
        games[session_id] = new_game()

    response = HTMLResponse(render(games[session_id]))
    response.set_cookie("session_id", session_id, httponly=True)
    return response


@app.post("/guess", response_class=HTMLResponse)
def guess(guess: int = Form(...), session_id: str | None = Cookie(default=None)):
    if session_id is None or session_id not in games:
        session_id = str(uuid.uuid4())
        games[session_id] = new_game()

    game = games[session_id]

    if not game["done"]:
        game["attempts"] += 1

        if guess < game["answer"]:
            game["message"] = "낮습니다."
        elif guess > game["answer"]:
            game["message"] = "높습니다."
        else:
            game["message"] = (
                f"정답입니다! {game['attempts']}번 만에 맞추셨습니다. 축하합니다!"
            )
            game["done"] = True

    response = HTMLResponse(render(game))
    response.set_cookie("session_id", session_id, httponly=True)
    return response


@app.post("/reset", response_class=HTMLResponse)
def reset(session_id: str | None = Cookie(default=None)):
    if session_id is None:
        session_id = str(uuid.uuid4())

    games[session_id] = new_game()

    response = HTMLResponse(render(games[session_id]))
    response.set_cookie("session_id", session_id, httponly=True)
    return response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
