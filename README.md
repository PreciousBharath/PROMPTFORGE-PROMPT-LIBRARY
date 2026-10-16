<div align="center">

# ✨ PromptForge — Prompt Library & Playground

**Build, score, version and share reusable AI prompts — fill {{variables}}, preview instantly and run them on any LLM.**

![Python-3.10%2B](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white) ![Flask-3.x](https://img.shields.io/badge/Flask-3.x-000000?style=for-the-badge&logo=flask&logoColor=white) ![SQLite-Database](https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite&logoColor=white) ![Chart.js-Charts](https://img.shields.io/badge/Chart.js-Charts-FF6384?style=for-the-badge&logo=chartdotjs&logoColor=white) ![GenAI-Prompts](https://img.shields.io/badge/GenAI-Prompts-A855F7?style=for-the-badge&logo=openai&logoColor=white)

`Generative AI · Prompt Engineering` · `Full-stack web app` · `Register / Login` · `Dark & light themes`

</div>

---

![PROMPTFORGE-PROMPT-LIBRARY](assets/library.png)

## ✨ Features

- **{{variable}} templates** — fields auto-detected and turned into a fill-in form with live highlighted preview
- **Live quality analyser** (role, clarity, context, format, constraints, reusability) with radar chart & tips
- Smart editor with one-click snippets (role, CoT, JSON, constraints)
- **Version history** with line-by-line diffs, **favourites ❤️**, **star ratings**, usage counts
- **Community gallery** + fork-to-my-library
- **Playground** for any OpenAI-compatible API (OpenAI, Groq, Together, Ollama) — key stays in your browser session; dry-run mode without a key
- 14 curated starter templates (sales, coding, data, career, teaching…)

## 🎨 UI / UX highlights

- **Glassmorphism design system** with animated gradient blobs, grid overlay and per-project colour theme
- **Dark / light mode** toggle (remembered per browser) — every chart re-themes instantly
- **Split-screen auth pages** with an interactive particle network, floating cards and a typing "Try demo" button
- **Motion everywhere**: staggered fade-ups, count-up numbers, animated progress bars, ripple buttons, toast notifications, modals
- **Fully responsive** — collapsible sidebar on mobile, Ctrl + K search shortcut
- Works **offline**: Chart.js, Bootstrap Icons and Poppins font are bundled in `static/`

## 🔐 Authentication & security

- **Register / Login / Logout** with salted password hashing (Werkzeug PBKDF2)
- Live **password-strength meter**, show/hide password, "remember me" sessions (14 days)
- **CSRF protection** on every form and API call, brute-force lockout after 5 failed logins
- HttpOnly + SameSite cookies, security headers, per-user data isolation
- **Profile & settings**: edit name, avatar colour, change password, delete account

## 🖼️ Screenshots

| Sign in | Register |
|---|---|
| ![login](assets/login.png) | ![register](assets/register.png) |

| | |
|---|---|
| ![prompt](assets/prompt.png) | ![editor](assets/editor.png) |
| ![playground](assets/playground.png) | ![explore](assets/explore.png) |

## 🏗️ How it works

```mermaid
flowchart LR
    S0["Write template"] --> S1
    S1["live scoring"] --> S2
    S2["save version"] --> S3
    S3["fill variables"] --> S4
    S4["copy or run in playground"]
```

## 🧰 Tech stack

| Layer | Technology |
|---|---|
| Backend | Python 3, Flask, SQLite, requests |
| Frontend | HTML5, CSS3 (custom glassmorphism design system), vanilla JavaScript |
| Charts & icons | Chart.js 4, Bootstrap Icons, Poppins (bundled locally) |
| Security | Werkzeug password hashing, CSRF tokens, secure sessions |

## 📁 Project structure

```
PROMPTFORGE-PROMPT-LIBRARY/
├── app.py                 # Flask app: routes, business logic & JSON API
├── core.py                # Shared core: app factory, SQLite, auth, CSRF, profile
├── app.py                 # Routes, library, ratings, versions, LLM proxy
├── prompt_tools.py        # Variables, rendering, analyser, diff
├── seed_prompts.py        # Starter templates
├── templates/             # Jinja2 pages (auth, base layout, feature pages)
├── static/                # style.css, main.js + bundled Chart.js, icons & fonts
├── assets/                # README screenshots
├── requirements.txt
└── LICENSE
```

## 🚀 Run it locally

```bash
git clone https://github.com/PreciousBharath/PROMPTFORGE-PROMPT-LIBRARY.git
cd PROMPTFORGE-PROMPT-LIBRARY
python -m venv venv && source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5000** → click **"Try the demo account"** (`demo@example.com` / `Demo@1234`) or register your own account.
The SQLite database is created automatically in `instance/` and seeded with realistic demo data.

## ⚙️ Production tips

- Set a strong `SECRET_KEY` environment variable and run behind **gunicorn** / **waitress** with HTTPS
- `DATABASE=/path/to/app.db` overrides the database location

## 👨‍💻 Author

**Bharath** — Software Developer · Project Engineer · Technical Trainer

[![LinkedIn](https://img.shields.io/badge/LinkedIn-connectbharath-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://linkedin.com/in/connectbharath)
[![Portfolio](https://img.shields.io/badge/Portfolio-Visit-00C7B7?style=for-the-badge&logo=netlify&logoColor=white)](https://itsbharathportfolio.netlify.app)
[![GitHub](https://img.shields.io/badge/GitHub-PreciousBharath-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/PreciousBharath)

⭐ If you like this project, please give it a star!

## 📄 License

Released under the [MIT License](LICENSE).
