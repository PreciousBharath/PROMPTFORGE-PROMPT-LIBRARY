"""PromptForge — Prompt library & playground: reusable {{variable}} templates, live quality scoring, version history
with diffs, favourites, ratings, a community gallery and an LLM playground (bring your own key).
Run:  python app.py   →  http://127.0.0.1:5000   (demo: demo@example.com / Demo@1234)
"""
import requests
from flask import abort, flash, g, jsonify, redirect, render_template, request, url_for

from core import create_app, execute, login_required, now, query
from prompt_tools import analyse, diff, render, tokens, variables
from seed_prompts import SEED

CATS = {"Sales": "#F72585", "Education": "#4CC9F0", "Coding": "#7209B7", "Data": "#4361EE", "Marketing": "#F77F00",
        "Productivity": "#06D6A0", "Career": "#FFD166", "Support": "#EF476F", "Content": "#8338EC", "Other": "#9AA0C3"}
UI = dict(
    name="PromptForge", short="Prompt Library & Playground", icon="✨", accent1="#A855F7", accent2="#EC4899", home="library",
    tagline="Build, score, version and share reusable AI prompts. Fill variables, preview instantly and run them on any LLM.",
    hero='Craft prompts like <span class="gradient-text">a pro engineer.</span>', badge="Generative AI toolkit",
    features=[("bi-braces", "{{Variable}} templates", "Auto-detected fields turn prompts into reusable forms"),
              ("bi-speedometer2", "Live quality score", "Role, clarity, format & constraint analysis as you type"),
              ("bi-clock-history", "Versions & sharing", "Diff history, favourites, ratings and community gallery")],
    float=['⭐ <b>4.9</b> · "Code reviewer" used 1,284×', '🧩 <b class="gradient-text">{{topic}}</b> → filled & copied'],
    nav=[("My Library", "library", "bi-collection"), ("Explore", "explore", "bi-globe2"), ("New Prompt", "new_prompt", "bi-plus-square"), ("Playground", "playground", "bi-terminal")],
    search_hint="Search prompts…", promo_title="Privacy", promo="Your API key stays in your browser session and is only forwarded when you press Run.",
)
SCHEMA = """
CREATE TABLE IF NOT EXISTS prompts (
    id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, title TEXT NOT NULL,
    description TEXT, category TEXT, emoji TEXT DEFAULT '✨', body TEXT NOT NULL, is_public INTEGER DEFAULT 1, uses INTEGER DEFAULT 0,
    created_at TEXT, updated_at TEXT);
CREATE TABLE IF NOT EXISTS versions (id INTEGER PRIMARY KEY AUTOINCREMENT, prompt_id INTEGER NOT NULL REFERENCES prompts(id) ON DELETE CASCADE, body TEXT NOT NULL, note TEXT, created_at TEXT);
CREATE TABLE IF NOT EXISTS favorites (user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, prompt_id INTEGER NOT NULL REFERENCES prompts(id) ON DELETE CASCADE, PRIMARY KEY(user_id, prompt_id));
CREATE TABLE IF NOT EXISTS ratings (user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, prompt_id INTEGER NOT NULL REFERENCES prompts(id) ON DELETE CASCADE, stars INTEGER NOT NULL, PRIMARY KEY(user_id, prompt_id));
"""


def seed_demo(uid):
    import random
    rng = random.Random(2)
    for i, (title, cat, emo, desc, body) in enumerate(SEED):
        pid = execute("INSERT INTO prompts(user_id,title,description,category,emoji,body,uses,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)",
                      (uid, title, desc, cat, emo, body, rng.randint(20, 1400), now(), now()))
        execute("INSERT INTO versions(prompt_id,body,note,created_at) VALUES(?,?,?,?)", (pid, "\n\n".join(body.split("\n\n")[:2]), "First draft", now()))
        execute("INSERT INTO versions(prompt_id,body,note,created_at) VALUES(?,?,?,?)", (pid, body, "Added constraints & output format", now()))
        execute("INSERT INTO ratings VALUES(?,?,?)", (uid, pid, rng.choice([4, 5, 5])))
        if i % 3 == 0:
            execute("INSERT INTO favorites VALUES(?,?)", (uid, pid))


app = create_app(__name__, UI, SCHEMA, seed_demo=seed_demo)

LIST_SQL = ("SELECT p.*, u.name author, (SELECT ROUND(AVG(stars),1) FROM ratings r WHERE r.prompt_id=p.id) rating, "
            "(SELECT COUNT(*) FROM ratings r WHERE r.prompt_id=p.id) n_ratings, "
            "EXISTS(SELECT 1 FROM favorites f WHERE f.prompt_id=p.id AND f.user_id=?) fav FROM prompts p JOIN users u ON u.id=p.user_id ")


def enrich(rows):
    for r in rows:
        r["vars"] = variables(r["body"])
        r["score"] = analyse(r["body"])["overall"]
    return rows


def prompt_or_404(pid, must_own=False):
    p = query(LIST_SQL + "WHERE p.id=?", (g.user["id"], pid), one=True)
    if not p or (not p["is_public"] and p["user_id"] != g.user["id"]) or (must_own and p["user_id"] != g.user["id"]):
        abort(404)
    return p


@app.route("/library")
@login_required
def library():
    rows = enrich(query(LIST_SQL + "WHERE p.user_id=? OR p.id IN (SELECT prompt_id FROM favorites WHERE user_id=?) ORDER BY p.updated_at DESC",
                        (g.user["id"], g.user["id"], g.user["id"])))
    st = dict(total=sum(r["user_id"] == g.user["id"] for r in rows), favs=sum(r["fav"] for r in rows), uses=sum(r["uses"] for r in rows),
              avg=round(sum(r["score"] for r in rows) / len(rows)) if rows else 0)
    return render_template("library.html", rows=rows, st=st, CATS=CATS, page_title="My Library")


@app.route("/explore")
@login_required
def explore():
    rows = enrich(query(LIST_SQL + "WHERE p.is_public=1 ORDER BY rating DESC, p.uses DESC", (g.user["id"],)))
    return render_template("library.html", rows=rows, st=None, CATS=CATS, explore=True, page_title="Explore Community")


@app.route("/prompt/<int:pid>")
@login_required
def prompt(pid):
    p = prompt_or_404(pid)
    vs = query("SELECT * FROM versions WHERE prompt_id=? ORDER BY id DESC", (pid,))
    mine = query("SELECT stars FROM ratings WHERE user_id=? AND prompt_id=?", (g.user["id"], pid), one=True)
    return render_template("prompt.html", p=p, vars=variables(p["body"]), a=analyse(p["body"]), versions=vs, my_rating=mine["stars"] if mine else 0,
                           CATS=CATS, page_title=p["title"][:40])


@app.route("/new", methods=["GET", "POST"])
@app.route("/edit/<int:pid>", methods=["GET", "POST"])
@login_required
def new_prompt(pid=None):
    p = prompt_or_404(pid, must_own=True) if pid else None
    if request.method == "POST":
        f = request.form
        title, body = f.get("title", "").strip()[:120], f.get("body", "").strip()[:12000]
        if len(title) < 3 or len(body) < 10:
            flash("Title and prompt body are required.", "danger")
            return redirect(request.url)
        vals = (title, f.get("description", "")[:200], f.get("category") if f.get("category") in CATS else "Other", f.get("emoji", "✨")[:4], body, int(bool(f.get("public"))))
        if p:
            execute("UPDATE prompts SET title=?,description=?,category=?,emoji=?,body=?,is_public=?,updated_at=? WHERE id=?", vals + (now(), pid))
            if body != p["body"]:
                execute("INSERT INTO versions(prompt_id,body,note,created_at) VALUES(?,?,?,?)", (pid, body, f.get("note", "")[:120] or "Edited", now()))
        else:
            pid = execute("INSERT INTO prompts(user_id,title,description,category,emoji,body,is_public,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)",
                          (g.user["id"],) + vals + (now(), now()))
            execute("INSERT INTO versions(prompt_id,body,note,created_at) VALUES(?,?,?,?)", (pid, body, "Created", now()))
        flash("Prompt saved ✨", "success")
        return redirect(url_for("prompt", pid=pid))
    return render_template("editor.html", p=p, CATS=CATS, page_title="Edit Prompt" if p else "New Prompt")


@app.post("/prompt/<int:pid>/delete")
@login_required
def delete_prompt(pid):
    prompt_or_404(pid, must_own=True)
    execute("DELETE FROM prompts WHERE id=?", (pid,))
    flash("Prompt deleted.", "info")
    return redirect(url_for("library"))


@app.post("/prompt/<int:pid>/fork")
@login_required
def fork(pid):
    p = prompt_or_404(pid)
    nid = execute("INSERT INTO prompts(user_id,title,description,category,emoji,body,is_public,created_at,updated_at) VALUES(?,?,?,?,?,?,0,?,?)",
                  (g.user["id"], p["title"] + " (copy)", p["description"], p["category"], p["emoji"], p["body"], now(), now()))
    execute("INSERT INTO versions(prompt_id,body,note,created_at) VALUES(?,?,?,?)", (nid, p["body"], f"Forked from #{pid}", now()))
    flash("Copied to your library — edit away!", "success")
    return redirect(url_for("new_prompt", pid=nid))


@app.route("/playground")
@login_required
def playground():
    pid = request.args.get("prompt", type=int)
    p = prompt_or_404(pid) if pid else None
    mine = query("SELECT id, title, emoji FROM prompts WHERE user_id=? ORDER BY title", (g.user["id"],))
    return render_template("playground.html", p=p, mine=mine, page_title="Playground")


# ---------------------------------------------------------------- API
@app.post("/api/analyse")
@login_required
def api_analyse():
    body = str(request.get_json(force=True).get("body", ""))[:12000]
    return jsonify(dict(analyse(body), vars=variables(body)))


@app.post("/api/render/<int:pid>")
@login_required
def api_render(pid):
    p = prompt_or_404(pid)
    out = render(p["body"], request.get_json(force=True).get("values", {}))
    execute("UPDATE prompts SET uses=uses+1 WHERE id=?", (pid,))
    return jsonify(text=out, tokens=tokens(out))


@app.post("/api/favorite/<int:pid>")
@login_required
def api_fav(pid):
    prompt_or_404(pid)
    if query("SELECT 1 FROM favorites WHERE user_id=? AND prompt_id=?", (g.user["id"], pid), one=True):
        execute("DELETE FROM favorites WHERE user_id=? AND prompt_id=?", (g.user["id"], pid))
        return jsonify(fav=False)
    execute("INSERT INTO favorites VALUES(?,?)", (g.user["id"], pid))
    return jsonify(fav=True)


@app.post("/api/rate/<int:pid>")
@login_required
def api_rate(pid):
    prompt_or_404(pid)
    stars = max(1, min(5, int(request.get_json(force=True).get("stars", 5))))
    execute("INSERT INTO ratings VALUES(?,?,?) ON CONFLICT(user_id,prompt_id) DO UPDATE SET stars=excluded.stars", (g.user["id"], pid, stars))
    r = query("SELECT ROUND(AVG(stars),1) a, COUNT(*) n FROM ratings WHERE prompt_id=?", (pid,), one=True)
    return jsonify(avg=r["a"], n=r["n"])


@app.get("/api/diff/<int:vid>")
@login_required
def api_diff(vid):
    v = query("SELECT v.*, p.user_id, p.is_public FROM versions v JOIN prompts p ON p.id=v.prompt_id WHERE v.id=?", (vid,), one=True)
    if not v or (not v["is_public"] and v["user_id"] != g.user["id"]):
        abort(404)
    prev = query("SELECT body FROM versions WHERE prompt_id=? AND id<? ORDER BY id DESC LIMIT 1", (v["prompt_id"], vid), one=True)
    return jsonify(diff(prev["body"] if prev else "", v["body"]))


@app.post("/api/run")
@login_required
def api_run():
    d = request.get_json(force=True)
    text = str(d.get("prompt", ""))[:20000]
    key, base, model = d.get("key"), (d.get("base_url") or "https://api.openai.com/v1").rstrip("/"), d.get("model") or "gpt-4o-mini"
    if not text.strip():
        return jsonify(error="Prompt is empty"), 400
    if not key:
        return jsonify(dry_run=True, tokens=tokens(text), output="🔌 No API key provided — dry run only.\n\nYour prompt is ready: "
                       f"{tokens(text)} estimated input tokens. Add an OpenAI-compatible key (OpenAI, Groq, Together, local Ollama) to get a real completion.")
    try:
        r = requests.post(base + "/chat/completions", timeout=90, headers={"Authorization": f"Bearer {key}"},
                          json={"model": model, "temperature": float(d.get("temperature", .7)), "messages": [{"role": "user", "content": text}]})
        r.raise_for_status()
        j = r.json()
        return jsonify(output=j["choices"][0]["message"]["content"], tokens=j.get("usage", {}).get("total_tokens"), model=model)
    except Exception as e:
        return jsonify(error=f"LLM request failed: {e}"), 502


if __name__ == "__main__":
    app.run(debug=True)
