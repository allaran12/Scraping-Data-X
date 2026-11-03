# X Data Scraper

Tool untuk scraping data mentah dari X (Twitter) dengan UI web interaktif. Ambil tweet, profile, replies dari keyword, hashtag, atau link postingan.

## Features

- **Scraping real-time** dari X menggunakan cookies browser
- **Multiple input types**: keyword, hashtag, link tweet, link hashtag
- **Data lengkap**: text, username, bio, followers, tanggal, URL
- **Filter waktu**: ambil data N hari terakhir
- **Scrape replies**: ambil balasan dari tiap tweet
- **UI web interaktif** dengan Streamlit
- **Export CSV** untuk analisis lanjutan
- **Bonus**: analisis perilaku terkoordinasi (deteksi buzzer, duplikasi konten, burst activity)

## Requirements

```
Python 3.8+
streamlit
twscrape
pandas
scikit-learn
```

## Installation

```bash
pip install -U streamlit twscrape pandas scikit-learn
```

## Usage

### 1. Jalankan aplikasi

```bash
streamlit run screpping.py
```

### 2. Ambil cookies dari browser

Login ke X, buka DevTools (F12) → Application/Storage → Cookies, copy:
- `auth_token`
- `ct0`

Format: `auth_token=XXXX; ct0=YYYY`

### 3. Input query

Masukkan salah satu:
- Link tweet: `https://x.com/user/status/123456789` → ambil tweet + replies
- Keyword: `pilpres 2024` → search tweets
- Hashtag: `#pilpres2024` → search hashtag
- Link hashtag: `https://x.com/hashtag/pilpres2024` → auto convert ke search

### 4. Atur parameter

- **Nama isu**: nama file output (misal: `pilpres_nov`, `banjir_jakarta`)
- **Limit**: jumlah tweet (50-5000)
- **Rentang waktu**: filter N hari terakhir (opsional)
- **Ambil balasan**: scrape replies dari tiap tweet (lambat, untuk analisis diskusi)

### 5. Scrape

Klik **Scrape & Analisis**. Data mentah tersimpan di `data/raw/[nama_isu].csv`.

## Data Output

### CSV Mentah (`data/raw/[nama_isu].csv`)

Setiap row = 1 tweet dengan kolom:

| Kolom | Keterangan |
|-------|------------|
| `id` | Tweet ID |
| `date` | Timestamp posting |
| `text` | Konten tweet (raw) |
| `username` | Username akun |
| `created` | Tanggal akun dibuat |
| `followers` | Jumlah followers |
| `following` | Jumlah following |
| `statuses` | Total tweet akun |
| `bio` | Bio/deskripsi akun |
| `avatar` | URL avatar |
| `is_rt` | Boolean (retweet atau bukan) |
| `is_reply` | Boolean (reply atau bukan) |
| `url` | Link ke tweet |
| `isu` | Nama isu (dari input) |
| `query` | Query pencarian |

Format: UTF-8 CSV, bisa dibuka Excel/Pandas/R.

## Fitur Analisis (Bonus)

Setelah scraping, aplikasi otomatis menampilkan:

### 1. Tabel Akun
Agregasi per username: total tweets, followers, following, rasio RT, dll.

### 2. Chart Posting Per Jam
Visualisasi kapan tweet paling banyak (identifikasi jam ramai).

### 3. Deteksi Duplikasi
Tweet mirip antar akun (cosine similarity >0.8) - indikasi copy-paste.

### 4. Scoring Akun
Skor 0-100 berdasarkan:
- Umur akun, tweet/day, rasio following/followers
- Duplikasi konten & burst activity
- Untuk riset buzzer/koordinasi (opsional)

Atur threshold di sidebar:
- **Ambang kemiripan teks**: 0.5-1.0 (default 0.8)
- **Min. akun per menit**: 3-20 (default 5)

## Use Cases

- **Riset media sosial**: analisis isu, sentimen, akun influencer
- **Monitoring brand**: mention, hashtag campaign
- **Jurnalisme data**: investigasi pola diskusi publik
- **Akademik**: penelitian komunikasi, sosiologi digital
- **OSINT**: intelligence gathering dari data publik

## Catatan

⚠️ **Disclaimer:**
- Data hasil scraping adalah data **publik** dari X
- Fitur scoring hanya **indikasi**, bukan bukti atau vonis
- Gunakan untuk riset/monitoring, bukan harassment

⚠️ **Rate Limits:**
- X membatasi scraping per akun
- Gunakan akun tumbal (dummy account)
- Jika limit tercapai, ganti cookies atau tunggu

⚠️ **Legal:**
- Patuhi Terms of Service X
- Jangan gunakan untuk harassment
- Data untuk penelitian/monitoring saja

## Troubleshooting

**"Belum ada akun di accounts.db"**
→ Isi cookies di sidebar

**"Semua akun tidak aktif"**
→ Cookies expired, ambil yang baru dari browser

**"Tidak mengembalikan tweet"**
→ Rate limit atau query salah, coba:
```bash
twscrape search "indonesia" --limit=5
```

**"Format cookies salah"**
→ Pastikan ada `auth_token=` dan `ct0=`

## Advanced

### Upload Mode

Analisis ulang CSV lama tanpa scraping lagi:
1. Pilih "Upload CSV" di sidebar
2. Upload file dari `data/raw/` atau hasil scraping sebelumnya
3. Atur threshold similarity & burst di sidebar
4. Lihat analisis dengan parameter berbeda

### CLI Mode / Automation

Import fungsi untuk scripting:

```python
from screpping import scrape, score

# Scraping
df = scrape(
    query="keyword atau #hashtag",
    limit=200,
    cookies="auth_token=...; ct0=...",
    fetch_replies=False,
    days=7  # 7 hari terakhir
)

# Save mentah
df.to_csv("output.csv", index=False)

# Analisis (opsional)
tweets_df, accounts_df = score(df, sim_thr=0.8, burst_users=5)
print(accounts_df[["username", "score"]].head())
```

## File Structure

```
.
├── screpping.py      # Main app
├── accounts.db       # twscrape account storage
├── data/
│   └── raw/         # CSV datasets
└── README.md
```

## License

MIT - Gunakan dengan bijak dan bertanggung jawab.

---

🤖 *Scrape data X untuk riset, monitoring, dan analisis*
