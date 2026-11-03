"""
Buzzer / Coordinated Behavior Detector untuk X
Jalankan: streamlit run screpping.py
Install : pip install -U streamlit twscrape pandas scikit-learn
"""
import asyncio
import os
import re
from urllib.parse import urlparse, parse_qs, unquote

import pandas as pd
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DB_PATH = "accounts.db"
ACC_NAME = "acc1"

def parse_id(s):
    """Ambil ID tweet dari link .../status/123..."""
    m = re.search(r"status/(\d+)", s)
    return int(m.group(1)) if m else None

def normalize_query(s):
    """Ubah link hashtag / search X menjadi query pencarian biasa."""
    s = s.strip()
    m = re.search(r"(?:x|twitter)\.com/hashtag/([^/?#]+)", s)
    if m:
        return "#" + unquote(m.group(1))
    if re.match(r"https?://(www\.)?(x|twitter)\.com/search", s):
        return unquote(parse_qs(urlparse(s).query).get("q", [""])[0])
    return s

def build_query(query, days=None):
    """Tambahkan batas waktu (operator since:) ke query pencarian."""
    q = normalize_query(query)
    if days and "since:" not in q:
        since = (pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=int(days))).strftime("%Y-%m-%d")
        q += f" since:{since}"
    return q

def clean_cookies(c):
    c = (c or "").strip().strip('"').strip("'")
    return re.sub(r"\s*;\s*", "; ", c)

async def _scrape(query, limit, cookies, fetch_replies=False, days=None):
    from twscrape import API, gather

    api = API(DB_PATH)  

    cookies = clean_cookies(cookies)
    if cookies:
        if "auth_token=" not in cookies or "ct0=" not in cookies:
            raise RuntimeError("Format cookies salah. Harus: auth_token=XXXX; ct0=YYYY")
        await api.pool.delete_accounts(ACC_NAME)  # buang akun lama
        await api.pool.add_account(ACC_NAME, "x", "x@x.com", "x", cookies=cookies)

    accounts = await api.pool.get_all()
    if not accounts:
        raise RuntimeError("Belum ada akun di accounts.db. Isi cookies di sidebar.")
    if not any(a.active for a in accounts):
        err = "; ".join(f"{a.username}: {a.error_msg}" for a in accounts)
        raise RuntimeError(
            f"Semua akun tidak aktif ({err}). Ambil cookies baru (auth_token & ct0) "
            "dari browser, lalu isi lagi di sidebar."
        )

    tid = parse_id(query)
    if tid:  # link postingan -> tweet + balasannya
        first = await api.tweet_details(tid)
        items = [first] if first else []
        items += await gather(api.tweet_replies(tid, limit=limit))
    else:  # keyword / isu / #hashtag / link hashtag
        items = await gather(api.search(build_query(query, days), limit=limit))
        if fetch_replies:
            seen = {t.id for t in items}
            for t in items[:20]:  # dibatasi supaya tidak kena rate limit
                if t.replyCount and t.replyCount > 0:
                    for r in await gather(api.tweet_replies(t.id, limit=50)):
                        if r.id not in seen:
                            seen.add(r.id)
                            items.append(r)

    rows = []
    for t in items:
        if t is None:
            continue
        u = t.user
        rows.append(dict(
            id=t.id, date=t.date, text=t.rawContent, username=u.username,
            created=u.created, followers=u.followersCount, following=u.friendsCount,
            statuses=u.statusesCount, bio=u.rawDescription or "",
            avatar=u.profileImageUrl or "",
            is_rt=t.retweetedTweet is not None,
            is_reply=t.inReplyToTweetId is not None,
            url=t.url,
        ))

    df = pd.DataFrame(rows)
    if not df.empty and days:  
        batas = pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=int(days))
        df = df[pd.to_datetime(df["date"], utc=True) >= batas]
    if df.empty:
        raise RuntimeError(
            "Akun aktif, tapi X tidak mengembalikan tweet. Kemungkinan rate limit, "
            "akun terkunci, atau query tidak ada hasil. Coba query lain "
            "atau jalankan: twscrape search \"indonesia\" --limit=5"
        )
    return df

def scrape(query, limit, cookies, fetch_replies=False, days=None):
    return asyncio.run(_scrape(query, limit, cookies, fetch_replies, days))

async def _accounts_status():
    from twscrape import API
    api = API(DB_PATH)
    return [dict(username=a.username, active=bool(a.active), error=a.error_msg)
            for a in await api.pool.get_all()]

def clean(t):
    t = re.sub(r"https?://\S+|@\w+|#", "", str(t).lower())
    return re.sub(r"\s+", " ", t).strip()

def score(df, sim_thr=0.8, burst_users=5):
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], utc=True)
    df["created"] = pd.to_datetime(df["created"], utc=True)
    df["is_rt"] = df["is_rt"].astype(str).str.lower().isin(["true", "1"])
    df["bio"] = df["bio"].fillna("")
    df["avatar"] = df["avatar"].fillna("")
    df["dup"] = 0.0

    o = df[~df["is_rt"]]
    if len(o) > 1:
        try:
            X = TfidfVectorizer().fit_transform(o["text"].map(clean))
            S = cosine_similarity(X)
            users = o["username"].values
            for i in range(len(o)):
                S[i, users == users[i]] = 0
            df.loc[o.index, "dup"] = (S.max(axis=1) >= sim_thr).astype(float)
        except ValueError: 
            pass

    df["minute"] = df["date"].dt.floor("min")
    nu = df.groupby("minute")["username"].transform("nunique")
    df["burst"] = (nu >= burst_users).astype(float)

    acc = df.groupby("username").agg(
        tweets_in_data=("id", "count"), followers=("followers", "first"),
        following=("following", "first"), statuses=("statuses", "first"),
        created=("created", "first"), bio=("bio", "first"),
        avatar=("avatar", "first"), dup_ratio=("dup", "mean"),
        burst_ratio=("burst", "mean"), rt_ratio=("is_rt", "mean"),
    ).reset_index()

    age = (pd.Timestamp.now(tz="UTC") - acc["created"]).dt.days.clip(lower=1)
    tpd = acc["statuses"] / age
    ratio = acc["following"] / acc["followers"].clip(lower=1)

    s = (
        (age < 90) * 10 + (age < 30) * 5
        + (tpd > 50) * 15
        + (ratio > 5) * 10
        + acc["avatar"].str.contains("default_profile", na=False) * 5
        + (acc["bio"].str.len() == 0) * 5
        + acc["username"].str.count(r"\d").ge(5) * 5
        + acc["dup_ratio"] * 25
        + acc["burst_ratio"] * 20
    )
    acc["age_days"] = age
    acc["tweets_per_day"] = tpd.round(1)
    acc["score"] = s.clip(upper=100).round(0).astype(int)
    return df, acc.sort_values("score", ascending=False)

st.set_page_config(page_title="Buzzer Detector X", layout="wide")
st.title("Deteksi Indikasi Perilaku Terkoordinasi di X")

mode = st.sidebar.radio("Sumber data", ["Scrape X", "Upload CSV"])
sim_thr = st.sidebar.slider("Ambang kemiripan teks", 0.5, 1.0, 0.8, 0.05)
burst_users = st.sidebar.slider("Min. akun per menit (burst)", 3, 20, 5)

raw = None

if mode == "Scrape X":
    q = st.text_input("Link postingan / keyword / #hashtag / link hashtag")
    isu = st.sidebar.text_input("Nama isu (nama file dataset)", "isu1")
    limit = st.sidebar.number_input("Jumlah maksimum tweet", 50, 5000, 200, 50)
    cookies = st.sidebar.text_input("Cookies akun tumbal (auth_token=...; ct0=...)",
                                    type="password")
    use_days = st.sidebar.checkbox("Batasi rentang waktu", True)
    days = st.sidebar.number_input("Maksimal berapa hari terakhir", 1, 365, 30) if use_days else None
    fetch_replies = st.sidebar.checkbox("Ambil balasan dari tiap tweet (lambat)", False)

    if st.sidebar.button("Cek status akun"):
        try:
            st.sidebar.write(asyncio.run(_accounts_status()) or "Belum ada akun.")
        except Exception as e:
            st.sidebar.error(f"Gagal cek akun: {e}")

    if st.button("Scrape & Analisis") and q:
        with st.spinner("Mengambil data dari X..."):
            try:
                data = scrape(q, int(limit), cookies, fetch_replies, days)
                data["isu"] = isu
                data["query"] = q
                os.makedirs("data/raw", exist_ok=True)
                path = f"data/raw/{isu}.csv"
                data.to_csv(path, index=False)
                st.session_state["raw"] = data
                st.session_state["path"] = path
            except Exception as e:
                st.session_state.pop("raw", None)
                st.error(f"Scraping gagal: {e}")

    raw = st.session_state.get("raw")
    if raw is not None:
        st.success(f"Data mentah tersimpan: {st.session_state['path']}")
else:
    f = st.file_uploader("CSV hasil scraping", type="csv")
    if f:
        raw = pd.read_csv(f)
        if "is_reply" not in raw.columns:
            raw["is_reply"] = False

if raw is not None and len(raw):
    try:
        df, acc = score(raw, sim_thr, burst_users)
    except KeyError as e:
        st.error(f"Kolom CSV tidak lengkap: {e}")
        st.stop()

    st.caption(f"{len(df)} tweet dari {acc.shape[0]} akun. "
               "Skor = indikasi perilaku terkoordinasi, bukan vonis.")
    c1, c2 = st.columns([3, 2])
    with c1:
        st.subheader("Akun dengan skor tertinggi")
        st.dataframe(acc.head(50), use_container_width=True)
        st.download_button("Unduh hasil (CSV)", acc.to_csv(index=False), "hasil.csv")
    with c2:
        st.subheader("Pola posting per jam")
        st.bar_chart(df.groupby(df["date"].dt.floor("h")).size())
    st.subheader("Tweet yang mirip antar akun")
    st.dataframe(df[df["dup"] == 1][["date", "username", "text"]].sort_values("text"),
                 use_container_width=True)
elif raw is not None:
    st.warning("Tidak ada data yang didapat.")