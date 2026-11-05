# MediaLoop

A photo and video sharing app. The backend is a **FastAPI** REST API, and the web frontend (**Auralink**) is plain HTML, CSS and JavaScript served by the same FastAPI app, with a light/dark mode switch.

## Features

- **Accounts:** sign up, log in with a JWT, change your password, log out (the token is revoked) and delete your account.
- **Posts:** upload a photo or video with an optional caption, browse a shared feed, and delete your own posts.
- **Media storage:** files are uploaded to [ImageKit](https://imagekit.io) and only the URL is stored in the database.
- **Frontend:**
  - Light and dark themes with a switch. The choice is remembered and defaults to your system setting.
  - Responsive layout: a sidebar on desktop and a bottom tab bar on phones.
  - Feed filters (All / Photos / Videos), a photo lightbox, and drag-and-drop uploads with a progress bar.

## Tech stack

| Layer    | Tools                                      |
| -------- | ------------------------------------------ |
| API      | FastAPI, Uvicorn                           |
| Database | SQLite via SQLAlchemy                      |
| Auth     | OAuth2 password flow, JWT (`python-jose`), bcrypt (`passlib`) |
| Media    | ImageKit (`imagekitio`)                    |
| Frontend | Vanilla HTML / CSS / JS (no build step)    |

## Project structure

```
MediaLoop-project/
├── .env.example
├── .gitignore
├── LICENSE
├── README.md
├── requirements.txt
└── MediaLoop/
    ├── app.py          # FastAPI app, routers, serves the frontend
    ├── db.py           # SQLAlchemy engine and session
    ├── models.py       # Users, Posts, RevokedToken tables
    ├── images.py       # ImageKit client
    ├── router/
    │   ├── auth.py     # register, login (token)
    │   ├── users.py    # profile, password, logout, delete account
    │   └── posts.py    # upload, feed, delete post
    └── frontend/
        ├── index.html
        ├── styles.css
        └── app.js
```

## Getting started

### Prerequisites

- Python 3.10 or newer
- A free ImageKit account (for the private key, public key and URL endpoint)

### Installation

```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### Configuration

Copy the example file and fill in your ImageKit credentials:

```bash
cp .env.example .env
```

```env
IMAGEKIT_PRIVATE_KEY=your_private_key
IMAGEKIT_PUBLIC_KEY=your_public_key
IMAGEKIT_URL_ENDPOINT=https://ik.imagekit.io/your_id
```

> `.env` is listed in `.gitignore`. Never commit your real keys.

### Run

Start the server from inside the `MediaLoop` folder:

```bash
cd MediaLoop
uvicorn app:app --reload
```

| URL                          | What it is           |
| ---------------------------- | -------------------- |
| http://127.0.0.1:8000        | Web app (Auralink)   |
| http://127.0.0.1:8000/docs   | Interactive API docs |

The SQLite database (`post.db`) is created automatically on first run, in the folder you start the server from.

## API overview

| Method | Endpoint               | Auth | Description                          |
| ------ | ---------------------- | ---- | ------------------------------------ |
| POST   | `/auth/`               | No   | Create an account                    |
| POST   | `/auth/token`          | No   | Log in and receive a JWT (20 min)    |
| GET    | `/users/`              | Yes  | Current user's profile               |
| PUT    | `/users/password`      | Yes  | Change password                      |
| POST   | `/users/logout`        | Yes  | Revoke the current token             |
| DELETE | `/users/`              | Yes  | Delete the current account           |
| POST   | `/posts/`              | Yes  | Upload a photo or video with caption |
| GET    | `/posts/feed`          | No   | List all posts, newest first         |
| DELETE | `/posts/delete/{id}`   | Yes  | Delete one of your own posts         |

Authenticated requests send the header `Authorization: Bearer <token>`.

## Security notes

This is a learning project. Before deploying it publicly, you should:

- Move `SECRET_KEY` in `router/auth.py` into `.env`, and generate a new one.
- Stop `GET /users/` from returning the password hash (add a response model).
- Restrict the `role` field on sign-up. The frontend always registers `user`, but the API accepts any value.
- Switch from SQLite to a production database and serve over HTTPS.

## License

Distributed under the GNU General Public License v2.0. See [`LICENSE`](LICENSE) for details.