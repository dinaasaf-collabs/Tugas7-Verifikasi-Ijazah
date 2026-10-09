
import cv2
import numpy as np
import pytesseract
import csv
import json
from pathlib import Path

# ==================================================
# 1. KONFIGURASI
# ==================================================

BASE_DIR = Path(__file__).resolve().parent
DATASET_DIR = BASE_DIR / "dataset" / "gambar"
HASIL_DIR = BASE_DIR / "hasil"
HASIL_DIR.mkdir(exist_ok=True)

TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

if Path(TESSERACT_PATH).exists():
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

METODE = ["brightness", "contrast", "equalization"]
FILE_KOORDINAT = BASE_DIR / "koordinat_crop.json"


# ==================================================
# 2. ENHANCEMENT CITRA
# ==================================================

def enhancement_citra(gray, metode):

    if metode == "brightness":
        return cv2.convertScaleAbs(
            gray, alpha=1.2, beta=20
        )

    elif metode == "contrast":
        rendah, tinggi = np.percentile(gray, (2, 98))

        if tinggi <= rendah:
            return gray.copy()

        hasil = (
            (gray.astype(np.float32) - rendah)
            * 255.0 / (tinggi - rendah)
        )

        return np.clip(hasil, 0, 255).astype(np.uint8)

    elif metode == "equalization":
        hasil = cv2.equalizeHist(gray)

        _, hasil = cv2.threshold(
            hasil,
            0,
            255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )

        return hasil

    raise ValueError("Metode enhancement tidak dikenal.")


# ==================================================
# 3. OCR NOMOR IJAZAH
# ==================================================

def baca_nomor_ijazah(area):

    konfigurasi = (
        "--oem 3 --psm 7 "
        "-c tessedit_char_whitelist=0123456789"
    )

    teks = pytesseract.image_to_string(
        area,
        config=konfigurasi
    )

    angka = "".join(
        karakter for karakter in teks
        if karakter.isdigit()
    )

    return angka


# ==================================================
# 4. DETEKSI TANDA TANGAN
# ==================================================

def deteksi_tanda_tangan(area):

    gray = cv2.cvtColor(
        area,
        cv2.COLOR_BGR2GRAY
    )

    _, threshold = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )

    kernel = np.ones((2, 2), np.uint8)

    bersih = cv2.morphologyEx(
        threshold,
        cv2.MORPH_OPEN,
        kernel
    )

    jumlah_tinta = cv2.countNonZero(bersih)
    luas = bersih.shape[0] * bersih.shape[1]

    persen = (
        jumlah_tinta / luas * 100
        if luas > 0 else 0
    )

    status = "PRESENT" if persen >= 0.5 else "ABSENT"

    return status, persen, bersih


# ==================================================
# 5. MENGHITUNG CHARACTER ERROR RATE (CER)
# ==================================================

def hitung_cer(teks_benar, teks_ocr):

    benar = "".join(
        karakter for karakter in teks_benar
        if karakter.isdigit()
    )

    hasil = "".join(
        karakter for karakter in teks_ocr
        if karakter.isdigit()
    )

    if not benar:
        return None

    baris = list(range(len(hasil) + 1))

    for i, a in enumerate(benar, start=1):

        baru = [i]

        for j, b in enumerate(hasil, start=1):

            biaya = 0 if a == b else 1

            baru.append(min(
                baru[-1] + 1,
                baris[j] + 1,
                baris[j - 1] + biaya
            ))

        baris = baru

    return baris[-1] / len(benar) * 100


# ==================================================
# 6. MEMILIH DAN MENYIMPAN AREA CROP
# ==================================================

def pilih_area(gambar, judul):

    cv2.namedWindow(judul, cv2.WINDOW_NORMAL)

    x, y, w, h = cv2.selectROI(
        judul,
        gambar,
        showCrosshair=True,
        fromCenter=False
    )

    cv2.destroyWindow(judul)

    if w == 0 or h == 0:
        raise ValueError(
            "Area tidak dipilih. Jalankan program kembali."
        )

    return [int(x), int(y), int(w), int(h)]


def muat_atau_pilih_crop(gambar_acuan):

    if FILE_KOORDINAT.exists():

        try:
            with open(
                FILE_KOORDINAT,
                "r",
                encoding="utf-8"
            ) as file:

                data = json.load(file)

            if "nomor" in data and "tanda_tangan" in data:

                print("Menggunakan koordinat crop yang tersimpan.")

                return data["nomor"], data["tanda_tangan"]

        except (json.JSONDecodeError, OSError):
            print("Koordinat tidak terbaca. Pilih crop ulang.")

    print("\nPilih nomor ijazah pada gambar acuan.")
    print("Pilih angka nomor saja, lalu tekan ENTER.")

    roi_nomor = pilih_area(
        gambar_acuan,
        "Pilih Nomor Ijazah"
    )

    print("\nPilih area tanda tangan.")
    print("Tarik kotak pada area tanda tangan, lalu tekan ENTER.")

    roi_ttd = pilih_area(
        gambar_acuan,
        "Pilih Tanda Tangan"
    )

    with open(
        FILE_KOORDINAT,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            {
                "nomor": roi_nomor,
                "tanda_tangan": roi_ttd
            },
            file,
            indent=4
        )

    print("Koordinat crop berhasil disimpan.")

    return roi_nomor, roi_ttd


def potong_area(gambar, koordinat):

    x, y, w, h = koordinat

    if (
        x + w > gambar.shape[1]
        or y + h > gambar.shape[0]
    ):
        raise ValueError(
            "Area crop di luar gambar. Periksa ukuran gambar."
        )

    return gambar[y:y + h, x:x + w]


# ==================================================
# 7. PROGRAM UTAMA
# ==================================================

def main():

    print("=" * 50)
    print("PROTOTYPE VERIFIKASI IJAZAH")
    print("PEMROSESAN BANYAK GAMBAR")
    print("=" * 50)

    try:
        print(
            "Tesseract OCR:",
            pytesseract.get_tesseract_version()
        )

    except Exception as error:

        print("Tesseract OCR tidak dapat dijalankan.")
        print("Periksa lokasi instalasi Tesseract.")
        print("Detail:", error)

        return

    if not DATASET_DIR.exists():

        print("Folder gambar tidak ditemukan:", DATASET_DIR)
        return

    ekstensi = {".jpg", ".jpeg", ".png", ".bmp"}

    daftar_file = sorted(
        [
            file for file in DATASET_DIR.iterdir()
            if file.is_file()
            and file.suffix.lower() in ekstensi
        ],
        key=lambda file: file.name.lower()
    )

    if not daftar_file:

        print("Tidak ada gambar di folder dataset/gambar.")
        return

    print(f"\nJumlah gambar ditemukan: {len(daftar_file)}")

    gambar_acuan = cv2.imread(str(daftar_file[0]))

    if gambar_acuan is None:

        print("Gambar acuan gagal dibaca.")
        return

    try:

        roi_nomor, roi_ttd = muat_atau_pilih_crop(
            gambar_acuan
        )

    except (ValueError, cv2.error) as error:

        print("Pemilihan area gagal:", error)
        return

    nomor_benar = input(
        "\nMasukkan nomor ijazah yang benar "
        "(kosongkan jika belum tahu): "
    ).strip()

    nomor_benar = "".join(
        karakter for karakter in nomor_benar
        if karakter.isdigit()
    )

    hasil_tabel = []

    # ==================================================
    # 8. PROSES SEMUA GAMBAR
    # ==================================================

    for nomor, file_gambar in enumerate(
        daftar_file,
        start=1
    ):

        print(
            f"\nMemproses [{nomor}/{len(daftar_file)}]: "
            f"{file_gambar.name}"
        )

        gambar = cv2.imread(str(file_gambar))

        if gambar is None:

            print("Gambar gagal dibaca, dilewati.")
            continue

        try:

            area_nomor = potong_area(
                gambar,
                roi_nomor
            )

            area_ttd = potong_area(
                gambar,
                roi_ttd
            )

        except ValueError as error:

            print(error)
            print("Gambar ini dilewati.")
            continue

        gray_nomor = cv2.cvtColor(
            area_nomor,
            cv2.COLOR_BGR2GRAY
        )

        gray_nomor = cv2.rotate(
            gray_nomor,
            cv2.ROTATE_90_CLOCKWISE
        )

        hasil_ocr = {}

        for metode in METODE:

            enhanced = enhancement_citra(
                gray_nomor,
                metode
            )

            enhanced = cv2.resize(
                enhanced,
                None,
                fx=2,
                fy=2,
                interpolation=cv2.INTER_CUBIC
            )

            cv2.imwrite(
                str(
                    HASIL_DIR
                    / f"{file_gambar.stem}_{metode}.jpg"
                ),
                enhanced
            )

            hasil_ocr[metode] = baca_nomor_ijazah(
                enhanced
            )

        # Deteksi tanda tangan

        status_ttd, persen_tinta, citra_ttd = (
            deteksi_tanda_tangan(area_ttd)
        )

        cv2.imwrite(
            str(
                HASIL_DIR
                / f"{file_gambar.stem}_ttd.jpg"
            ),
            citra_ttd
        )

        # Hitung CER setiap metode

        cer_metode = {}

        if nomor_benar:

            for metode in METODE:

                cer_metode[metode] = hitung_cer(
                    nomor_benar,
                    hasil_ocr[metode]
                )

            metode_valid = [
                metode for metode in METODE
                if hasil_ocr[metode]
                and cer_metode[metode] is not None
            ]

            if metode_valid:

                metode_terbaik = min(
                    metode_valid,
                    key=lambda metode: cer_metode[metode]
                )

            else:

                metode_terbaik = ""

        else:

            metode_valid = [
                metode for metode in METODE
                if hasil_ocr[metode]
            ]

            metode_terbaik = (
                metode_valid[0]
                if metode_valid
                else ""
            )

        nomor_final = (
            hasil_ocr[metode_terbaik]
            if metode_terbaik
            else ""
        )

        cer_final = (
            cer_metode[metode_terbaik]
            if nomor_benar and metode_terbaik
            else None
        )

        hasil_tabel.append({
            "nama_file": file_gambar.name,
            "ocr_brightness": hasil_ocr["brightness"],
            "ocr_contrast": hasil_ocr["contrast"],
            "ocr_equalization": hasil_ocr["equalization"],
            "nomor_terpilih": nomor_final,
            "metode_terbaik": (
                metode_terbaik
                if metode_terbaik
                else "tidak terbaca"
            ),
            "cer_persen": (
                round(cer_final, 2)
                if cer_final is not None
                else ""
            ),
            "status_tanda_tangan": status_ttd,
            "persentase_tinta": round(persen_tinta, 2)
        })

        print(
            "OCR brightness :",
            hasil_ocr["brightness"] or "[tidak terbaca]"
        )

        print(
            "OCR contrast   :",
            hasil_ocr["contrast"] or "[tidak terbaca]"
        )

        print(
            "OCR equalization:",
            hasil_ocr["equalization"] or "[tidak terbaca]"
        )

        print(
            "OCR terpilih   :",
            nomor_final or "[tidak terbaca]"
        )

        print(
            "Metode terbaik :",
            metode_terbaik or "tidak terbaca"
        )

        if cer_final is not None:
            print(f"CER terpilih   : {cer_final:.2f}%")

        print("Tanda tangan   :", status_ttd)
        print(f"Persentase tinta: {persen_tinta:.2f}%")

    # ==================================================
    # 9. SIMPAN HASIL KE CSV
    # ==================================================

    if hasil_tabel:

        kolom = list(hasil_tabel[0].keys())

        with open(
            HASIL_DIR / "hasil_verifikasi.csv",
            "w",
            newline="",
            encoding="utf-8-sig"
        ) as file_csv:

            penulis = csv.DictWriter(
                file_csv,
                fieldnames=kolom
            )

            penulis.writeheader()
            penulis.writerows(hasil_tabel)

    print("\n" + "=" * 50)
    print("SELESAI MEMPROSES GAMBAR")
    print("Jumlah berhasil:", len(hasil_tabel))
    print("Hasil CSV:", HASIL_DIR / "hasil_verifikasi.csv")
    print("Folder hasil:", HASIL_DIR)
    print("=" * 50)


if __name__ == "__main__":
    main()