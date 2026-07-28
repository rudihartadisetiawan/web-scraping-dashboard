# AGENTS.md — Global Marketplace Price & Trend Monitor

Dibaca oleh semua subagent di awal tiap sesi. Ringkas, operasional, bukan naratif. Detail lengkap requirement ada di `PRD.md`, status progres di `PROGRESS.md`.

## Arsitektur Agent

- **Manager** — orkestrasi task, breakdown kerja ke subagent, review integrasi akhir
- **Backend** — scraper/API client, database, scheduler, logika analisis (pandas)
- **Frontend** — dashboard Streamlit, styling custom, UX
- **Security** — rate limiting, robots.txt compliance, penanganan credential/API key, review sebelum deploy

## Pemilihan Model per Jenis Tugas

Sesuaikan model ke kompleksitas tugas, jangan pakai model besar untuk kerja rutin dan jangan pakai model kecil untuk keputusan arsitektur — ini soal efisiensi biaya sekaligus kualitas hasil.

| Jenis tugas | Contoh konkret | Tier model |
|---|---|---|
| Boilerplate & tugas rutin | CRUD script, setup struktur folder, fetch API sederhana, format data, penulisan test dasar | Model ringan/cepat (tier hemat biaya) |
| Logika bisnis & analisis | Perhitungan tren harga, deteksi anomali, desain skema database, query pandas kompleks | Model menengah — reasoning cukup, tapi tidak perlu model paling mahal |
| Keputusan arsitektur & desain | Desain alur pipeline end-to-end, keputusan API-first vs scraping, review keamanan, styling dashboard (identitas visual, token desain) | Model paling kuat yang tersedia — butuh reasoning dalam dan sekali jalan harus benar |
| Debugging kompleks / masalah tidak jelas akar penyebabnya | Scraper gagal tanpa error jelas, data korup, race condition scheduler | Model paling kuat yang tersedia |

Gunakan rate-limit fallback plugin untuk otomatis pindah model kalau kena limit — jangan turunkan kualitas tugas arsitektur/keamanan hanya karena fallback ke model lebih murah; tunda tugas tersebut sampai model yang sesuai tersedia lagi.

## Aturan Umum (Semua Agent)

1. **Ikuti PRD.md sebagai sumber kebenaran scope.** Jangan menambah fitur di luar scope MVP tanpa dikonfirmasi dulu (lihat Bagian 5 PRD — Out of Scope).
2. **Kode minimal, tidak over-engineered** (sesuai prinsip Ponytail plugin) — hindari abstraksi/pattern yang tidak dibutuhkan untuk scope saat ini.
3. **Update PROGRESS.md di akhir sesi** — status singkat, apa yang selesai, apa yang jadi blocker, next step.
4. **Session handoff:** baca PROGRESS.md di awal sesi sebelum mulai kerja, jangan asumsi konteks dari percakapan sebelumnya.

## Aturan Khusus Backend

- Sumber data utama: eBay Browse API. Scraping (AliExpress) hanya untuk melengkapi, bukan sumber utama — lihat PRD Bagian 2.
- Setiap fetch data disimpan sebagai baris baru di tabel histori, tidak menimpa data lama.
- Scheduler (GitHub Actions) harus punya logging jelas kalau fetch gagal — jangan gagal senyap.
- Rate limit dan retry logic wajib ada di setiap pemanggilan eksternal (API maupun scraping).
- Koneksi MySQL wajib pakai connection pooling (mis. SQLAlchemy dengan `pool_pre_ping=True`), jangan buka koneksi baru tiap query — hindari connection leak di environment serverless (GitHub Actions, Streamlit Cloud).

## Aturan Khusus Frontend

- **Dashboard tidak boleh terlihat generic/AI-made.** Wajib baca Bagian 6 di PRD.md sebelum mulai styling.
- Pakai skill `streamlit` (dari `streamlit/agent-skills`, taruh di `.opencode/skills/streamlit/`) untuk best practice caching (`@st.cache_data`), state management, dan layout — hindari pola yang bikin dashboard lambat karena re-render.
- Hindari: palet warna default AI (cream+terracotta, dark+neon), layout kolom Streamlit default tanpa custom CSS, kartu metrik generik tanpa konteks.
- Wajib: token desain disengaja (palet warna dengan hex spesifik, tipografi bukan default sistem), satu elemen signature yang mencirikan project ini.
- Copy/label dashboard dalam Bahasa Inggris, aktif, spesifik — target audiens adalah klien internasional.
- Screenshot hasil sebelum dianggap selesai, bandingkan dengan checklist "generic AI look" di PRD.

## Aturan Khusus Security

- Verifikasi robots.txt dan ToS sumber data sebelum implementasi scraping dijalankan, bukan setelah.
- API key/credential tidak boleh hardcoded — pakai environment variable / secrets di GitHub Actions.
- Kredensial MySQL (host, port, user, password, database) wajib lewat env var / GitHub Actions secrets / Streamlit secrets — tidak boleh muncul hardcoded di kode, config, atau file apapun di repo.
- Review rate limiting sebelum deploy — pastikan tidak ada request yang bisa membanjiri sumber data.
- Tidak ada data pribadi/PII yang ikut tersimpan atau ditampilkan di dashboard publik.

## Batas Scope (Ringkas dari PRD Bagian 5)

Jangan implementasi tanpa diminta: multi-marketplace agregasi, proxy rotation/anti-bot stealth, prediksi ML, notifikasi/alert otomatis, autentikasi user. Ini semua kandidat Level Sedang/Sulit di roadmap portofolio berikutnya.