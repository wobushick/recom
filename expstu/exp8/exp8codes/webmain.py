import random
import string
import time
import os
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Depends, File, UploadFile, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing_extensions import Annotated

from sqlmodel import Session, SQLModel, create_engine, Field, select

# ── Settings ──────────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class GSetting:
    data_dir = os.path.join(BASE_DIR, "data")
    post_files_dir = os.path.join(data_dir, "post")
    sqlite_path = os.path.join(data_dir, "sqlite_database.db")
    static_dir = os.path.join(BASE_DIR, "static")
    token_expired_time = 7 * 24 * 60 * 60  # 7 days

gsetting = GSetting()

# ── Database engine ───────────────────────────────────────────────────────

sqlite_url = f"sqlite:///{gsetting.sqlite_path}?nolock=1"
engine = create_engine(sqlite_url)

def get_session():
    with Session(engine) as session:
        yield session

# ── Models ────────────────────────────────────────────────────────────────

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    email: Optional[str] = None
    username: str = Field(index=True, unique=True)
    password: str
    age: Optional[int] = None
    bearer_token: Optional[str] = Field(default=None, unique=True)
    bearer_token_datesec: Optional[float] = None
    userclass: str = "normal"

class Post(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    userid: int = Field(default=None, index=True, foreign_key="user.id")
    rdir: str = ""
    filename: str = ""
    datesec: float = 0.0
    is_del: bool = False
    favors: int = 0

class Favor(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    userid: int = Field(default=None, foreign_key="user.id")
    postid: int = Field(default=None, foreign_key="post.id")
    rdir: str = ""
    datesec: float = 0.0

# ── OAuth2 scheme ─────────────────────────────────────────────────────────

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/user/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/user/login", auto_error=False)
TokenDep = Annotated[str, Depends(oauth2_scheme)]

# Form_data for login/register (reuses OAuth2PasswordRequestForm)
Form_data = Annotated[OAuth2PasswordRequestForm, Depends()]

# ── Pydantic request models ───────────────────────────────────────────────

from pydantic import BaseModel

class GetPostsRequest(BaseModel):
    scope: str = "home"       # 'home' or 'self'
    order: str = "time_descending"  # 'time_descending' or 'time_ascending'
    offset: int = 0
    limit: int = 10

class SetPostRequest(BaseModel):
    postid: int
    isdel: bool = False
    isfavor: Optional[bool] = None  # True=favor, False=unfavor, None=no change

class RecommendRequest(BaseModel):
    limit: int = 5

# ── Helper functions ──────────────────────────────────────────────────────

def db_make_unique_bearer_token() -> str:
    chars = string.digits + string.ascii_letters
    with Session(engine) as session:
        while True:
            token = "".join(random.choices(chars, k=64))
            existing = session.exec(
                select(User).where(User.bearer_token == token)
            ).first()
            if existing is None:
                return token


def db_register(username: str, password: str) -> dict:
    if len(username) < 5 or len(password) < 5:
        return {"result": "too_short"}
    with Session(engine) as session:
        existing = session.exec(
            select(User).where(User.username == username)
        ).first()
        if existing is not None:
            return {"result": "username_exist"}
        userclass = "admin" if username.startswith("admin") else "normal"
        user = User(username=username, password=password, userclass=userclass)
        session.add(user)
        session.commit()
        session.refresh(user)
        return db_user_login(username, password)


def db_user_login(username: str, password: str) -> dict:
    with Session(engine) as session:
        user = session.exec(
            select(User).where(User.username == username)
        ).first()
        if user is None:
            return {"result": "username_unexist"}
        if user.password != password:
            return {"result": "password_wrong"}
        token = db_make_unique_bearer_token()
        user.bearer_token = token
        user.bearer_token_datesec = time.time()
        session.add(user)
        session.commit()
        session.refresh(user)
        return {
            "result": "success",
            "bearer_token": token,
            "userid": user.id,
            "username": user.username,
            "userclass": user.userclass,
        }


def db_get_user_by_token(token: str) -> Optional[User]:
    with Session(engine) as session:
        user = session.exec(
            select(User).where(User.bearer_token == token)
        ).first()
        if user is None:
            return None
        if user.bearer_token is None:
            return None
        elapsed = time.time() - (user.bearer_token_datesec or 0)
        if elapsed > gsetting.token_expired_time:
            return None
        return user


def db_user_uploadpdf(
    user: User, filename: str, file_bytes: bytes
) -> dict:
    now = time.time()
    ext = os.path.splitext(filename)[1].lower()
    if ext not in (".pdf", ".md"):
        ext = ".pdf"
    with Session(engine) as session:
        post = Post(
            userid=user.id,
            filename=filename,
            rdir="",
            datesec=now,
        )
        session.add(post)
        session.commit()
        session.refresh(post)
        post_dir = os.path.join(gsetting.post_files_dir, str(post.id), "main")
        os.makedirs(post_dir, exist_ok=True)
        file_path = os.path.join(post_dir, f"main{ext}")
        with open(file_path, "wb") as f:
            f.write(file_bytes)
        post.rdir = f"{post.id}/main/main{ext}"
        session.add(post)
        session.commit()
        session.refresh(post)
        return {"result": "success", "postid": post.id}


def db_get_posts(scope: str, order: str, offset: int, limit: int,
                 userid: Optional[int] = None) -> list:
    with Session(engine) as session:
        query = select(Post)
        if scope == "self" and userid is not None:
            query = query.where(Post.userid == userid)
        else:
            query = query.where(Post.is_del == False)
        if order == "time_ascending":
            query = query.order_by(Post.datesec.asc())
        else:
            query = query.order_by(Post.datesec.desc())
        query = query.offset(offset).limit(limit)
        posts = session.exec(query).all()

        result = []
        for p in posts:
            post_user = session.get(User, p.userid)
            # Check if current user has favored this post
            isfavor = False
            if userid is not None:
                fav = session.exec(
                    select(Favor).where(
                        Favor.userid == userid, Favor.postid == p.id
                    )
                ).first()
                isfavor = fav is not None

            result.append({
                "id": p.id,
                "username": post_user.username if post_user else "unknown",
                "userid": p.userid,
                "filename": p.filename,
                "rdir": p.rdir,
                "datesec": p.datesec,
                "is_del": p.is_del,
                "favors": p.favors,
                "isfavor": isfavor,
            })
        return result


def db_set_post(user: User, postid: int, isdel: bool,
                isfavor: Optional[bool]) -> dict:
    with Session(engine) as session:
        post = session.get(Post, postid)
        if post is None:
            return {"result": "post_not_exist"}
        # Delete / restore
        if isdel:
            if user.userclass != "admin" and post.userid != user.id:
                return {"result": "permission_denied"}
            post.is_del = True
            session.add(post)
            session.commit()
        # Favor / unfavor
        if isfavor is not None:
            existing_fav = session.exec(
                select(Favor).where(
                    Favor.userid == user.id, Favor.postid == postid
                )
            ).first()
            if isfavor and existing_fav is None:
                fav = Favor(userid=user.id, postid=postid,
                            rdir=post.rdir, datesec=time.time())
                session.add(fav)
                post.favors += 1
                session.add(post)
            elif not isfavor and existing_fav is not None:
                session.delete(existing_fav)
                post.favors = max(0, post.favors - 1)
                session.add(post)
            session.commit()
        return {"result": "success"}


def db_get_recommendations(userid: Optional[int] = None, limit: int = 5) -> list:
    """Return recommended posts for a user.

    Uses User-based Collaborative Filtering (Jaccard similarity) when the
    user has favor history. Falls back to popularity-based ranking otherwise.
    """
    with Session(engine) as session:
        # ── Collaborative Filtering ──────────────────────────────────
        if userid is not None:
            user_favs = session.exec(
                select(Favor).where(Favor.userid == userid)
            ).all()
            user_favored_ids = {f.postid for f in user_favs}

            if user_favored_ids:
                # Find all other users who favored at least one same post
                related_favs = session.exec(
                    select(Favor).where(Favor.postid.in_(user_favored_ids))
                ).all()

                # Collect unique other user IDs
                other_user_ids = {f.userid for f in related_favs} - {userid}

                # Score candidate posts by summed Jaccard similarity.
                # Fetch each other user's FULL favor set for correct Jaccard.
                post_scores: dict[int, float] = {}
                for other_uid in other_user_ids:
                    all_other_favs = session.exec(
                        select(Favor).where(Favor.userid == other_uid)
                    ).all()
                    all_other_ids = {f.postid for f in all_other_favs}

                    intersection = user_favored_ids & all_other_ids
                    union = user_favored_ids | all_other_ids
                    if len(union) == 0:
                        continue
                    jaccard = len(intersection) / len(union)
                    for pid in all_other_ids - user_favored_ids:
                        post_scores[pid] = post_scores.get(pid, 0) + jaccard

                sorted_posts = sorted(
                    post_scores.items(), key=lambda x: x[1], reverse=True
                )

                result = []
                for pid, score in sorted_posts:
                    post = session.get(Post, pid)
                    if post is None or post.is_del:
                        continue
                    post_user = session.get(User, post.userid)
                    result.append({
                        "id": post.id,
                        "username": post_user.username if post_user else "unknown",
                        "userid": post.userid,
                        "filename": post.filename,
                        "rdir": post.rdir,
                        "datesec": post.datesec,
                        "favors": post.favors,
                        "score": round(score, 3),
                        "method": "collaborative",
                    })
                    if len(result) >= limit:
                        return result
                if result:
                    return result

        # ── Popularity fallback ──────────────────────────────────────
        posts = session.exec(
            select(Post)
            .where(Post.is_del == False)
            .order_by(Post.favors.desc())
            .limit(limit * 3)
        ).all()

        result = []
        for p in posts:
            if userid is not None:
                existing = session.exec(
                    select(Favor).where(
                        Favor.userid == userid, Favor.postid == p.id
                    )
                ).first()
                if existing:
                    continue
            post_user = session.get(User, p.userid)
            result.append({
                "id": p.id,
                "username": post_user.username if post_user else "unknown",
                "userid": p.userid,
                "filename": p.filename,
                "rdir": p.rdir,
                "datesec": p.datesec,
                "favors": p.favors,
                "score": p.favors,
                "method": "popularity",
            })
            if len(result) >= limit:
                break
        return result


# ── Lifespan ──────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(gsetting.data_dir, exist_ok=True)
    os.makedirs(gsetting.post_files_dir, exist_ok=True)
    SQLModel.metadata.create_all(engine, checkfirst=True)
    yield

# ── FastAPI app ───────────────────────────────────────────────────────────

app = FastAPI(lifespan=lifespan)

# ── API routes ────────────────────────────────────────────────────────────

@app.get("/", response_class=RedirectResponse)
def app_read_root(request: Request):
    return "/static/index.html"


@app.post("/user/login")
def app_login(form_data: Form_data):
    return db_user_login(form_data.username, form_data.password)


@app.post("/user/register")
def app_register(form_data: Form_data):
    return db_register(form_data.username, form_data.password)


@app.post("/user/userinfo")
def app_userinfo(token: TokenDep):
    user = db_get_user_by_token(token)
    if user is None:
        return {"result": "token_expired"}
    return {
        "result": "success",
        "userid": user.id,
        "username": user.username,
        "userclass": user.userclass,
        "age": user.age,
        "email": user.email,
    }


@app.post("/user/getposts")
def app_getposts(body: GetPostsRequest,
                 token: Optional[str] = Depends(oauth2_scheme_optional)):
    userid = None
    if token:
        user = db_get_user_by_token(token)
        if user:
            userid = user.id
    posts = db_get_posts(body.scope, body.order, body.offset, body.limit, userid)
    return {"result": "success", "data": posts}


@app.post("/user/setpost")
def app_setpost(body: SetPostRequest, token: TokenDep,
                session: Session = Depends(get_session)):
    user = db_get_user_by_token(token)
    if user is None:
        return {"result": "token_expired"}
    return db_set_post(user, body.postid, body.isdel, body.isfavor)


@app.post("/user/uploadfile")
def app_uploadfile(
    request: Request,
    token: TokenDep,
    filePdf: UploadFile = File(),
):
    user = db_get_user_by_token(token)
    if user is None:
        return {"result": "token_expired"}
    ext = os.path.splitext(filePdf.filename)[1].lower()
    if ext not in (".pdf", ".md"):
        return {"result": "invalid_file_type"}
    file_bytes = filePdf.file.read()
    return db_user_uploadpdf(user, filePdf.filename, file_bytes)


@app.post("/user/recommend")
def app_recommend(body: RecommendRequest,
                  token: Optional[str] = Depends(oauth2_scheme_optional)):
    userid = None
    if token:
        user = db_get_user_by_token(token)
        if user:
            userid = user.id
    recs = db_get_recommendations(userid, body.limit)
    return {"result": "success", "data": recs}


@app.get("/post/{post_id}")
def app_get_post(post_id: int, session: Session = Depends(get_session)):
    """Return metadata for a single post."""
    post = session.get(Post, post_id)
    if post is None or post.is_del:
        return {"result": "post_not_exist"}
    post_user = session.get(User, post.userid)
    return {
        "result": "success",
        "post": {
            "id": post.id,
            "filename": post.filename,
            "username": post_user.username if post_user else "unknown",
            "userid": post.userid,
            "rdir": post.rdir,
            "datesec": post.datesec,
            "favors": post.favors,
        },
    }


# ── Static files mount ────────────────────────────────────────────────────

app.mount("/static", StaticFiles(directory=gsetting.static_dir), name="static")
app.mount("/post", StaticFiles(directory=gsetting.post_files_dir), name="post_files")

# ── Server entry ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5246, reload=False)
