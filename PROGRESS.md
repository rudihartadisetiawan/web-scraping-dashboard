# PROGRESS.md

## Session 1 — 2026-07-28

**Selesai:**
- Audit konfigurasi opencode.json (verifikasi schema, role coverage, model-tier, permissions).
- Rewrite opencode.json: 4 agent (Manager/Backend/Frontend/Security) pakai model tier-sesuai AGENTS.md untuk efisiensi budget (semua model terverifikasi tersedia via `opencode models`).
- Install plugin `opencode-rate-limit-fallback` → ditambahkan ke root config plugin array.
- Security agent kembali ke `opencode-go/qwen3.7-max` (reasoning kuat untuk review security, jarang dipanggil jadi kuota ketat tidak masalah; keterangan user).
- Switch storage SQLite → MySQL hosted (Alibaba Cloud PolarDB for MySQL — always free tier 2C8G + 50GB, 100% MySQL-compatible). Alasan: scraper (GitHub Actions) dan dashboard (Streamlit Cloud) jalan di 2 environment terpisah yang butuh akses DB sama.
- Update AGENTS.md: backend rules + aturan connection pooling MySQL; security rules + eksplisit kredensial MySQL wajib env var/secrets.
- Update PRD.md: flow diagram & tech stack table pakai MySQL hosted.

**Blocker:** tidak ada.

**Next:**
- Saat kerja Frontend dimulai: install skill `streamlit/agent-skills@developing-with-streamlit` ke `.opencode/skills/streamlit/`.
- Mulai implementasi backend: skema MySQL + scraper eBay Browse API. Pastikan connection pooling (SQLAlchemy pool_pre_ping) sejak awal.
- Provider MySQL locked: Alibaba Cloud PolarDB for MySQL (always free tier). Next: daftar akun, ambil connection string, simpan sebagai GitHub Actions secret + Streamlit secret saat implementasi backend mulai.

## Session 2 — 2026-07-28 (continued)

**Selesai:**
- Buat struktur folder project: `scraper/`, `analysis/`, `dashboard/`, `data/` dengan `.gitkeep`.
- Buat `.env.example` dengan placeholder kredensial MySQL lokal (Laragon).
- Desain skema tabel awal di `scraper/schema.sql`: tabel `produk` dan `histori_harga` dengan index & FK sesuai spec.
- Buat `scraper/db.py` (SQLAlchemy engine dengan `pool_pre_ping=True`, kredensial dari env var) dan `scraper/test_db_connection.py`.
- Buat `.gitignore` (`.env`, Python cache, IDE, OS files).
- Setup venv project dan install `sqlalchemy`, `pymysql`, `python-dotenv`.
- Buat database `price_monitor` di MySQL lokal dan apply `schema.sql`.
- Test koneksi DB: **SUCCESS** — `SELECT 1` berhasil, tabel `produk` dan `histori_harga` terbuat.
- Implementasi `scraper/fetcher.py`: OAuth token client credentials (cache + refresh), eBay Browse API search (`sneakers`, $1–$50 USD, 50/page, max 5 pages), retry/backoff (1s/2s/4s) + 429 `Retry-After` handling, mapping ke tabel `produk`/`histori_harga`, upsert, UUID fetch batch, logging.
- Buat `scraper/test_fetcher.py` dengan `--dry-run` flag.
- Install `requests` di venv.
- `python scraper/test_fetcher.py --dry-run` berjalan, skip karena `.env` belum ada (kredensial placeholder) — expected.

**Blocker:**
- Perlu kredensial eBay asli (`EBAY_CLIENT_ID`, `EBAY_CLIENT_SECRET`) dan `.env` aktif untuk test live call.
- Perlu validasi field `seller_rating` dengan `feedbackPercentage` eBay: disimpan sebagai proporsi 0–1 agar muat di `DECIMAL(3,2)`. Kalau ingin persen penuh (0–100), kolom skema perlu diubah ke `DECIMAL(5,2)`.

**Next:**
- Setup scheduler skeleton (GitHub Actions workflow) setelah fetcher dasar berjalan.
- Test live insert ke DB dengan kredensial eBay asli.

## Session 3 — 2026-07-28

**Selesai:**
- Tambahkan placeholder kredensial eBay (`EBAY_CLIENT_ID`, `EBAY_CLIENT_SECRET`, `EBAY_ENVIRONMENT`) ke `.env.example`.
- Implementasi fetcher eBay Browse API (`scraper/fetcher.py`): OAuth client credentials flow, in-memory token cache + auto-refresh, search endpoint untuk keyword `sneakers` ($1–$50 USD, 50/page, max 5 halaman), retry dengan exponential backoff (1s/2s/4s) + 429 `Retry-After` handling, upsert `produk` + insert `histori_harga` per fetch batch (UUID).
- Buat `scraper/test_fetcher.py` dengan `--dry-run` flag (skip DB write, uji token + search saja).
- Security audit #1 (existing code): temukan 1 issue di `db.py:47` — SQLAlchemy exception leak connection string (termasuk password). **Fixed**: ganti ke `type(exc).__name__`.
- Security audit #2 (fetcher.py): **PASS** — semua credential dari env var, rate limit aman (6 calls/run, jauh di bawah 5000/day), tidak ada token/credential di-log, semua query pakai parameterized SQL.
- Install `requests` di venv.

**Blocker:**
- Perlu kredensial eBay asli di `.env` untuk test live call. Saat ini `test_fetcher.py --dry-run` mendeteksi placeholder dan skip dengan benar.

**Next:**
- Setup scheduler GitHub Actions workflow (cron daily + manual trigger).
- Test live insert ke DB dengan kredensial eBay asli.
- Mulai modul `analysis/` — kalkulasi tren harga, deteksi penurunan harga, rasio value-for-money.

## Session 4 — 2026-07-28 (Waiting eBay approval — reprioritized)

**Selesai:**
- Update price filter di `fetcher.py`: `[1..50]` → `[20..300]` (range lebih representatif untuk sneakers retail).
- Setup GitHub Actions scheduler skeleton: `.github/workflows/daily_fetch.yml` — cron daily 06:00 UTC + manual `workflow_dispatch`, env var dari GitHub Secrets untuk semua kredensial (eBay + MySQL).
- Buat dataset dummy (`scraper/seed_dummy.py`): 13 produk sneakers realistis + 91 rows histori harga (7 hari, 7 batch UUID berbeda). 3 produk disimulasikan dengan penurunan harga ~30% untuk testing fitur deteksi.
- Build package `analysis/` (semua query parameterized, pakai SQLAlchemy `text()`):
  - `analysis/trends.py` — `get_price_trend()`, `get_all_product_trends()`
  - `analysis/alerts.py` — `detect_price_drops(days, threshold_pct)`, `get_top_deals(limit)`
  - `analysis/rankings.py` — `value_for_money_rank(limit)`, `seller_price_comparison(keyword)`
  - `analysis/summary.py` — `get_summary_stats()`
  - `analysis/test_analysis.py` — smoke test, semua fungsi terverifikasi: `total_products=13`, `avg_price=177.10`, `products_with_drops=3`, top deals detected.
- Build dashboard Streamlit (`dashboard/app.py` + `dashboard/.streamlit/config.toml`):
  - **Design tokens** (PRD Bagian 6 compliant — bukan generic AI look):
    - Palet: charcoal `#1a1d23`/`#242830`/`#2d323c`, text `#e8e8ec`/`#9195a0`, **signature accent signal lime `#ccff00`**, drop-red `#ff4444`, rise-green `#00e676`, border `#3a3f4b`
    - Font: **Bebas Neue** (display/big numerals), **Inter** (body), **JetBrains Mono** (ticker/data) — via Google Fonts
    - **Signature element:** animated price-drop ticker (horizontal scroll, "DROPS" label in volt) + subtle tread-pattern diagonal background band
  - Custom CSS: override metric cards (flat bordered, no gradient), sidebar, sliders (volt thumb), dataframe headers (volt uppercase), empty states
  - Layout: sidebar filter (category, price range from DB min/max, date range, drop threshold %) + 4 main sections — summary metric row (4 cards with avg price trend delta), price trend line chart (top-5 compare / single focus), top deals table (rows >threshold shaded red), value-for-money ranking full width
  - `@st.cache_data(ttl=300)` untuk semua query; defensive `ImportError` fallback untuk analysis module
  - Smoke test: `streamlit run` boot clean, `AppTest` renders without exception (graceful empty state)
- Install deps: `pandas`, `streamlit` di venv.

**Blocker:**
- **eBay credentials masih pending approval (1 hari kerja).** Semua fitur scraper (fetcher.py) sudah siap — tinggal jalankan `test_fetcher.py` begitu `.env` ada. Sementara itu, semua development lain (analysis, dashboard) sudah bisa lanjut pakai data dummy.
- Dashboard belum bisa di-screenshot dengan data riil — saat ini render empty state yang sudah didesain. Butuh data ≥7 hari untuk validasi visual penuh.

**Next:**
- Begitu kredensial eBay tersedia: jalankan live test `fetcher.py` + verifikasi data masuk MySQL.
- Deploy ke Streamlit Community Cloud (secrets: MYSQL_*).
- README + case study.

## Session 5 — 2026-07-28 (Minor fix, session closed)

**Selesai:**
- Rename "Nike volt" → "signal lime" di dashboard design tokens (`app.py` docstring + komentar, `PROGRESS.md`). Hex `#ccff00` tetap — hanya penamaan dinetralkan karena dashboard memantau multi-brand sneakers, bukan satu brand.

**Blocker:** eBay credentials pending approval.

---

## ➡️ Next session (setelah eBay approval):

### 1. Live test eBay fetcher
```
cp .env.example .env                                 # isi kredensial asli
python scraper/test_fetcher.py                        # verifikasi token + search
python scraper/fetcher.py                             # full pipeline: insert ke MySQL
python analysis/test_analysis.py                      # verifikasi analysis jalan
```

### 2. Deploy Streamlit Cloud
- Push repo ke GitHub
- Sambungkan ke Streamlit Community Cloud
- Set secrets: `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`
- Dashboard live di URL publik

### 3. GitHub Actions secrets
- Set di repo Settings → Secrets: `EBAY_CLIENT_ID`, `EBAY_CLIENT_SECRET`, `EBAY_ENVIRONMENT`, `MYSQL_*`
- Trigger manual `workflow_dispatch` pertama, verifikasi run sukses
- Biarkan cron daily berjalan — target 7 hari data berturut-turut

### 4. Setelah data ≥7 hari
- Screenshot dashboard (validasi PRD Bagian 6 — pastikan tidak generic AI look)
- README.md (masalah yang diselesaikan, arsitektur, screenshot, link demo, keputusan teknis)
- CASE_STUDY.md (dari sudut pandang "masalah bisnis reseller/dropshipper")
- Siapkan untuk showcase portofolio