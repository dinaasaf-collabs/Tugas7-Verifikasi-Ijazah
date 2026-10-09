# Tugas 7 — Verifikasi Ijazah

## 1. Deskripsi Proyek

Proyek ini merupakan aplikasi sederhana untuk melakukan verifikasi nomor ijazah menggunakan Optical Character Recognition (OCR) dan mendeteksi keberadaan tanda tangan pada citra ijazah.

Sistem menguji sembilan gambar ijazah dengan kondisi citra yang berbeda, seperti kontras rendah, blur, noise, resolusi rendah, pencahayaan kurang, perubahan warna, artefak kompresi JPEG, dan degradasi gabungan.

## 2. Tujuan

- Membaca nomor ijazah secara otomatis menggunakan OCR.
- Membandingkan metode peningkatan citra brightness, contrast stretching, dan histogram equalization.
- Mengukur kesalahan pembacaan nomor ijazah menggunakan Character Error Rate (CER).
- Mendeteksi indikasi keberadaan tanda tangan menggunakan pemrosesan citra.
- Menyimpan hasil pengujian dalam file CSV.

## 3. Teknologi yang Digunakan

- Python
- OpenCV
- NumPy
- Pytesseract
- Tesseract OCR
- CSV dan JSON

## 4. Struktur Folder

```text
Tugas7_Verifikasi_Ijazah/
├── dataset/
│   └── gambar/
├── hasil/
│   └── hasil_verifikasi.csv
├── main.py
├── requirements.txt
└── README.md
```

## 5. Alur Pemrosesan

1. Membaca gambar ijazah dari folder dataset.
2. Memilih area nomor ijazah dan area tanda tangan.
3. Melakukan peningkatan citra dengan beberapa metode.
4. Membaca nomor ijazah menggunakan OCR.
5. Membandingkan hasil OCR dengan nomor acuan menggunakan CER.
6. Memilih hasil OCR dengan nilai CER terendah.
7. Menganalisis area tanda tangan untuk memperkirakan keberadaannya.
8. Menyimpan hasil pemrosesan ke dalam file CSV.

## 6. Hasil Pengujian

Pengujian dilakukan terhadap sembilan gambar ijazah. Berdasarkan hasil yang tersimpan pada `hasil/hasil_verifikasi.csv`, seluruh nomor ijazah terpilih sesuai dengan nomor acuan `571012022000056` dan menghasilkan CER sebesar 0%.

Metode brightness menghasilkan pembacaan yang benar pada delapan gambar, sedangkan metode contrast menghasilkan pembacaan yang benar pada gambar blur `03_Blurred.jpg`.

Pada pengujian ini, metode histogram equalization belum menghasilkan teks OCR yang terbaca. Oleh karena itu, metode tersebut masih perlu diperbaiki atau dievaluasi lebih lanjut.

Seluruh gambar terdeteksi memiliki tanda tangan (`PRESENT`). Namun, kemampuan membedakan gambar bertanda tangan dan tanpa tanda tangan masih perlu diuji menggunakan data tanpa tanda tangan.

## 7. Cara Menjalankan Program

1. Pastikan Python dan Tesseract OCR sudah terpasang.
2. Buka terminal pada folder proyek.
3. Instal pustaka yang diperlukan:

```bash
pip install -r requirements.txt
```

4. Jalankan program:

```bash
python main.py
```

5. Ikuti instruksi untuk memilih area nomor ijazah, memilih area tanda tangan, dan memasukkan nomor ijazah acuan.
6. Periksa hasil pengujian pada folder `hasil`.

## 8. Kesimpulan

Berdasarkan pengujian terhadap sembilan gambar, sistem berhasil menghasilkan pembacaan nomor ijazah terpilih dengan CER 0% terhadap nomor acuan yang digunakan. Metode brightness dan contrast memberikan hasil OCR yang terbaca, sedangkan histogram equalization belum berhasil pada pengujian ini.

Deteksi tanda tangan masih berupa estimasi berdasarkan karakteristik piksel citra dan tidak digunakan untuk memastikan keaslian tanda tangan atau ijazah.