#!/usr/bin/env python3
"""Sistem pakar kualitas air kolam lele (forward chaining, mesin ditulis sendiri).

Pemakaian:
  python expert.py                      # mode tanya-jawab (y/t)
  python expert.py --fakta "a;b"        # fakta "ya" langsung, dipisah titik koma
  python expert.py --uji                # jalankan semua kasus uji
"""
import argparse
import json
import sys
from pathlib import Path

KASUS_UJI = [
    ("Kasus 1", ["oksigen terlarut kurang dari 3 mg/L", "ikan megap-megap di permukaan"],
     {"kekurangan oksigen"}),
    ("Kasus 2 (negatif)", ["ikan megap-megap di permukaan"], set()),
    ("Kasus 3", ["pH lebih dari 8,5", "oksigen terlarut kurang dari 3 mg/L", "ikan megap-megap di permukaan"],
     {"kekurangan oksigen", "air di luar kisaran optimal"}),
    ("Kasus 4", ["sisa pakan menumpuk", "amonia terukur tinggi"],
     {"masalah amonia akibat limbah pakan"}),
]


def muat_kb(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def syarat_terpenuhi(aturan, memori):
    """Mode 'dan': semua syarat ada di memori. Mode 'atau': salah satu cukup."""
    ada = [j for j in aturan["jika"] if j in memori]
    if aturan["mode"] == "dan":
        return len(ada) == len(aturan["jika"]), ada
    return len(ada) > 0, ada


def forward_chaining(kb, fakta_awal):
    memori = list(fakta_awal)
    asal = {}   # hasil -> (aturan, syarat yang terpenuhi)
    log = []
    while True:
        cocok = []
        for r in kb["aturan"]:
            if r["maka"] in memori:      # hasil sudah ada: jangan dijalankan lagi
                continue
            ok, ada = syarat_terpenuhi(r, memori)
            if ok:
                cocok.append((r, ada))
        if not cocok:
            break
        r, ada = cocok[0]                # ambil aturan pertama
        memori.append(r["maka"])
        asal[r["maka"]] = (r, ada)
        log.append(r)
    return memori, asal, log


def fakta_yang_ditanya(kb):
    """Fakta yang tidak pernah menjadi hasil aturan, urut kemunculan."""
    hasil = {r["maka"] for r in kb["aturan"]}
    urut = []
    for r in kb["aturan"]:
        for j in r["jika"]:
            if j not in hasil and j not in urut:
                urut.append(j)
    return urut


def kesimpulan_akhir(kb, asal):
    """Hasil yang tidak dipakai sebagai syarat aturan lain."""
    dipakai = {j for r in kb["aturan"] for j in r["jika"]}
    return [h for h in asal if h not in dipakai]


def cetak_alasan(h, asal, tingkat=1):
    r, ada = asal[h]
    print(f"{'  ' * tingkat}{h}  <- {r['id']} ({', '.join(ada)}) [{', '.join(r['sumber'])}]")
    for s in ada:
        if s in asal:
            cetak_alasan(s, asal, tingkat + 1)


def tanya(kb):
    print("Jawab y/t.")
    ya = []
    for i, f in enumerate(fakta_yang_ditanya(kb), 1):
        while True:
            jawab = input(f"{i}. {kb['fakta'][f]} (y/t) > ").strip().lower()
            if jawab in ("y", "t"):
                break
            print("   Ketik y atau t.")
        if jawab == "y":
            ya.append(f)
    return ya


def jalankan(kb, fakta_ya, tampil_log=True):
    print(f"\nFakta awal: {', '.join(fakta_ya) if fakta_ya else '(tidak ada)'}\n")
    memori, asal, log = forward_chaining(kb, fakta_ya)
    for i, r in enumerate(log, 1):
        print(f"Siklus {i}: {r['id']} -> {r['maka']}")
    print(f"Siklus {len(log) + 1}: tidak ada aturan baru, berhenti\n")
    akhir = kesimpulan_akhir(kb, asal)
    if akhir:
        print("Kesimpulan: " + ", ".join(akhir))
        print("Alasan:")
        for h in akhir:
            cetak_alasan(h, asal)
    else:
        print("Kesimpulan: tidak ada kesimpulan yang dapat ditarik dari fakta tersebut.")
    print(f"\nCatatan: {kb['batas']}")
    return set(akhir)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kb", default=str(Path(__file__).with_name("kb_lele.json")))
    ap.add_argument("--fakta", help="fakta 'ya', dipisah titik koma")
    ap.add_argument("--uji", action="store_true", help="jalankan kasus uji")
    a = ap.parse_args()
    kb = muat_kb(a.kb)

    if a.uji:
        gagal = 0
        for nama, fakta, harap in KASUS_UJI:
            print("=" * 60 + f"\n{nama}")
            hasil = jalankan(kb, fakta)
            status = "LULUS" if hasil == harap else "GAGAL"
            gagal += hasil != harap
            print(f"\n[{status}] diharapkan: {sorted(harap) or 'tidak ada'}")
        sys.exit(1 if gagal else 0)

    print(kb["judul"])
    if a.fakta is not None:
        fakta = [x.strip() for x in a.fakta.split(";") if x.strip()]
        tidak_dikenal = [f for f in fakta if f not in kb["fakta"]]
        if tidak_dikenal:
            sys.exit("Fakta tidak dikenal: " + "; ".join(tidak_dikenal))
    else:
        fakta = tanya(kb)
    jalankan(kb, fakta)


if __name__ == "__main__":
    main()
