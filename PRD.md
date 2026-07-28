# PRD.md — Global Marketplace Price & Trend Monitor

## 1. Latar Belakang & Tujuan

Project ini adalah portofolio freelance untuk menunjukkan kemampuan **web scraping/data collection + analisis data + dashboard** kepada calon klien internasional (Upwork/Fiverr, dsb). Ini adalah **Level 1 (Mudah)** dari rencana progresi portofolio (Mudah → Sedang → Sulit), dengan fondasi yang bisa dikembangkan lanjut di project berikutnya tanpa dibangun ulang dari nol.

**Target audiens portofolio:** klien luar negeri (reseller, dropshipper, brand kecil) yang butuh pemantauan harga/tren produk kompetitor secara berkala.

**Prinsip utama:** reliability dan kedalaman insight lebih penting daripada "kesulitan target scraping". Sumber data mengutamakan API resmi untuk stabilitas jangka panjang; scraping murni hanya dipakai di titik yang datanya memang tidak tersedia lewat API.

## 2. Sumber Data

- **Sumber utama:** eBay Browse API (resmi, gratis untuk volume kecil, tidak butuh proxy/anti-bot handling)
- **Sumber pelengkap (opsional, kalau waktu memungkinkan):** scraping ringan AliExpress untuk 1 kategori produk, dengan rate limiting sopan dan patuh robots.txt — tujuannya menunjukkan skill BeautifulSoup/Playwright, bukan sebagai sumber data utama
- **Kategori produk contoh:** pilih 1 kategori spesifik dan niche (misal "wireless earbuds" atau "mechanical keyboard") — jangan terlalu luas, biar insight lebih tajam

## 3. Alur Data (Pipeline)

```
Sumber Data (API/Scraping)
    → Fetch harian terjadwal (scheduler)
    → Simpan ke database (MySQL hosted)
    → Proses analisis (pandas)
    → Tampilkan di dashboard (Streamlit)
    → Deploy publik (Streamlit Community Cloud)
```

## 4. Fitur Inti (Scope MVP)

1. **Pengambilan data terjadwal** — job harian (cron / GitHub Actions) menarik data produk: nama, harga, rating, jumlah terjual/review, seller, timestamp
2. **Histori harga** — setiap fetch disimpan sebagai baris baru (bukan overwrite), sehingga terbentuk time-series harga per produk
3. **Analisis:**
   - Tren harga per produk dari waktu ke waktu
   - Deteksi produk yang harganya turun signifikan (>X%) dibanding rata-rata 7 hari terakhir
   - Ranking produk berdasarkan rasio harga vs rating (value for money)
   - Perbandingan harga antar seller untuk produk sejenis
4. **Dashboard interaktif (Streamlit):**
   - Filter kategori, rentang harga, rentang tanggal
   - Grafik tren harga (line chart) per produk terpilih
   - Tabel "top deals" (produk dengan penurunan harga terbesar)
   - Ringkasan statistik (rata-rata harga, jumlah produk terpantau, dsb)

## 5. Yang TIDAK Masuk Scope (Out of Scope untuk Level 1)

- Multi-marketplace agregasi (masuk Level Sedang/Sulit)
- Proxy rotation / anti-bot stealth handling
- Machine learning untuk prediksi tren (masuk Level Sulit)
- Notifikasi/alert otomatis (email, dsb) — kandidat kuat untuk Level Sedang
- Autentikasi user / multi-tenant dashboard

## 6. Kualitas Visual Dashboard — PENTING

Dashboard **tidak boleh terlihat seperti template Streamlit default atau hasil generate AI generik**. Ini poin krusial karena dashboard adalah bagian yang paling dilihat klien.

Yang harus dihindari:
- Layout default Streamlit tanpa penyesuaian (font default, warna default, layout kolom generik)
- Palet warna generik AI (cream + terracotta, dark mode + neon hijau/vermilion, atau broadsheet dengan hairline rules dan grid berita) kecuali memang jadi pilihan sadar yang cocok dengan subjek
- Kartu metrik "angka besar + label kecil + aksen gradient" tanpa alasan kuat
- Emoji/ikon acak sebagai pengganti hierarki visual yang jelas

Yang harus ada:
- Identitas visual yang disengaja: palet warna spesifik (4-6 warna bernama hex), tipografi yang dipilih sadar (bukan default sans-serif sistem), layout yang mencerminkan subjek (e-commerce/marketplace data — bisa terinspirasi dari struktur katalog produk, tag harga, dsb)
- Satu elemen "signature" yang jadi ciri khas dashboard ini
- Copy/label berbahasa Inggris yang jelas, aktif, dan spesifik (karena target klien internasional) — bukan istilah teknis backend

## 7. Deliverables

- Repository GitHub publik, rapi, dengan struktur folder jelas (`scraper/`, `analysis/`, `dashboard/`, `data/`)
- README.md berisi: masalah yang diselesaikan, arsitektur singkat, screenshot dashboard, link demo live, penjelasan keputusan teknis (kenapa API-first, dsb)
- Dashboard live yang bisa diakses tanpa instalasi (link Streamlit Cloud)
- Case study singkat (bisa jadi bagian dari README atau file terpisah `CASE_STUDY.md`) yang ditulis dari sudut pandang "masalah bisnis apa yang ini selesaikan buat klien reseller/dropshipper"

## 8. Tech Stack

| Layer | Tools |
|---|---|
| Data collection | Python, `requests` (eBay API), `BeautifulSoup`/`Playwright` (scraping pelengkap) |
| Storage | MySQL hosted (Alibaba Cloud PolarDB for MySQL — always free tier 2C8G + 50GB, 100% MySQL-compatible, kompatibel juga PostgreSQL/Oracle). Alasan: scraper (GitHub Actions) dan dashboard (Streamlit Cloud) jalan di dua environment terpisah yang butuh akses ke database yang sama, sehingga butuh DB terpisah yang bisa dihubungi dari keduanya |
| Scheduling | GitHub Actions (cron) |
| Analisis | pandas |
| Dashboard | Streamlit (dengan custom CSS untuk keluar dari tampilan default) |
| Deployment | Streamlit Community Cloud |
| Version control | Git + GitHub |

## 9. Kriteria Selesai (Definition of Done)

- [ ] Data terkumpul otomatis minimal 7 hari berturut-turut tanpa intervensi manual
- [ ] Dashboard live, bisa diakses publik, tidak error
- [ ] Ada minimal 3 insight analisis yang berjalan dan terlihat di dashboard (bukan placeholder)
- [ ] Desain dashboard sudah lolos review visual (lihat Bagian 6) — tidak terlihat generic/AI-made
- [ ] README + case study lengkap dan bisa dibaca calon klien tanpa penjelasan tambahan dari kamu
- [ ] Robots.txt dan ToS sumber data sudah dicek dan dipatuhi
