# X Buzzer Detector

Deteksi indikasi perilaku terkoordinasi (buzzer) di X (Twitter) menggunakan analisis pola posting, kemiripan konten, dan karakteristik akun.

## Features

- **Scraping real-time** dari X menggunakan cookies browser
- **Deteksi konten duplikat** dengan TF-IDF cosine similarity
- **Analisis burst activity** - banyak akun posting bersamaan
- **Scoring berbasis karakteristik** akun mencurigakan:
  - Akun baru (<90 hari)
  - Tweet per hari tinggi (>50/hari)
  - Rasio following/followers tidak wajar
  - Bio kosong atau avatar default
  - Username banyak angka
- **UI web interaktif** dengan Streamlit
- **Export CSV** untuk analisis lanjutan

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
- Link tweet: `https://x.com/user/status/123456789`
- Keyword: `pilpres 2024`
- Hashtag: `#pilpres2024`
- Link hashtag: `https://x.com/hashtag/pilpres2024`

### 4. Analisis

Klik **Scrape & Analisis**. Data tersimpan di `data/raw/[nama_isu].csv`.

## Cara Kerja

### Scoring System (0-100)

| Faktor | Bobot | Keterangan |
|--------|-------|------------|
| Akun <90 hari | +10 | Akun sangat baru |
| Akun <30 hari | +5 | Tambahan untuk akun ekstrem baru |
| Tweets/day >50 | +15 | Aktivitas tidak wajar |
| Following/followers >5x | +10 | Rasio mencurigakan |
| Avatar default | +5 | Tidak ada personalisasi |
| Bio kosong | +5 | Kurang kredibilitas |
| Username banyak angka (≥5) | +5 | Auto-generated pattern |
| Duplikasi konten | +25 | Copy-paste campaign |
| Burst activity | +20 | Koordinasi waktu posting |

### Deteksi Duplikasi

- TF-IDF vectorization pada teks tweet
- Cosine similarity antar akun
- Threshold default: 0.8 (80% mirip)
- Mengabaikan URL, mention, hashtag

### Burst Detection

- Grouping tweet per menit
- Flagging jika ≥N akun posting bersamaan
- Default: 5 akun/menit

## Output

### 1. Tabel Akun

Akun diurutkan berdasarkan skor (tertinggi = paling mencurigakan):

- Username, followers, following, statuses
- Umur akun (days)
- Tweets per day
- Rasio duplikasi & burst
- **Score** (0-100)

### 2. Pola Posting Per Jam

Chart untuk mendeteksi jam-jam aktivitas terkoordinasi.

### 3. Tweet Duplikat

Daftar tweet yang mirip antar akun berbeda (indikasi copy-paste).

### 4. CSV Export

- `data/raw/[isu].csv` - data mentah scraping
- `hasil.csv` - hasil scoring (download button)

## Catatan

⚠️ **Disclaimer:**
- Skor adalah **indikasi**, bukan vonis
- Akun genuine bisa punya skor tinggi (misal: news bot)
- Selalu verifikasi manual sebelum menyimpulkan
- Tool ini untuk riset, bukan akusasi

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

Jika sudah punya CSV hasil scraping:
1. Pilih "Upload CSV" di sidebar
2. Upload file CSV
3. Atur threshold similarity & burst
4. Analisis otomatis

### CLI Mode

Untuk integrasi atau automation, import fungsi:

```python
from screpping import scrape, score

# Scrape
df = scrape("keyword", limit=200, cookies="auth_token=...; ct0=...")

# Score
tweets_df, accounts_df = score(df, sim_thr=0.8, burst_users=5)
print(accounts_df.head())
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

🤖 *Deteksi buzzer untuk ekosistem digital yang lebih sehat*
