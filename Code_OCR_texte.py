import pdfplumber
import fitz  # PyMuPDF — pip install pymupdf
from pathlib import Path
from pdf2image import convert_from_path
import cv2
import pytesseract
import numpy as np
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
import multiprocessing
import multiprocessing.shared_memory as sm
import threading
import time

POPPLER_PATH  = r"C:\Users\lilia\OneDrive\Bureau\Python\RAA\poppler\bin"
TESSERACT_CMD = r"C:\Users\lilia\Tesseract-OCR\tesseract.exe"

CPU_COUNT   = multiprocessing.cpu_count()
OCR_WORKERS = 8      # 10 cœurs → 8 workers OCR (laisse 2 au système)
ANA_WORKERS = 4      # 4 threads détection (I/O léger)
SHM_THREADS = 1      # 1 seule conversion à la fois pour éviter MemoryError
DPI         = 200    # 200 DPI : réduit pour éviter MemoryError sur 16 Go

print_lock = threading.Lock()

def safe_print(*args, **kwargs):
    with print_lock:
        print(*args, **kwargs)

def format_duree(secondes):
    if secondes < 60:
        return f"{secondes:.1f}s"
    m, s = divmod(int(secondes), 60)
    return f"{m}m {s:02d}s"

def sep(car="─", n=60):
    safe_print(car * n)


# ======================
# DESKEW (redressement automatique)
# ======================
def deskew(gray):
    """Détecte et corrige l'inclinaison d'un scan (jusqu'à ±45°)."""
    inv = cv2.bitwise_not(gray)
    coords = np.column_stack(np.where(inv > 0))
    if len(coords) < 100:
        return gray
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = 90 + angle
    if abs(angle) < 0.3:
        return gray
    h, w = gray.shape
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(gray, M, (w, h),
                          flags=cv2.INTER_LINEAR,
                          borderMode=cv2.BORDER_REPLICATE)


# ======================
# PREPROCESS OCR — optimisé scans N&B
# ======================
def preprocess_image(img):
    """
    Pipeline optimisé pour scans N&B :
      1. Niveaux de gris
      2. Deskew (redressement)
      3. Threshold d'Otsu (rapide, optimal pour N&B pur)
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = deskew(gray)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresh


# ======================
# OCR RECONSTRUCTION
# ======================
def reconstruct_text(results):
    if not results:
        return ""

    results_sorted = sorted(results, key=lambda x: x[1][1])
    lines = []
    current_line = []
    last_y = None

    for (word, (x1, y1, x2, y2)) in results_sorted:
        if last_y is None or abs(y1 - last_y) < 15:
            current_line.append((x1, word))
        else:
            current_line.sort(key=lambda x: x[0])
            lines.append(" ".join(w[1] for w in current_line))
            current_line = [(x1, word)]
        last_y = y1

    if current_line:
        current_line.sort(key=lambda x: x[0])
        lines.append(" ".join(w[1] for w in current_line))

    return "\n".join(lines)


# ======================
# TACHE UNITAIRE : 1 PAGE OCR
# ======================
def ocr_page(args):
    pdf_stem, page_idx, shm_name, shape, dtype_str, tesseract_cmd = args

    pid = multiprocessing.current_process().pid
    t0  = time.perf_counter()

    existing_shm = sm.SharedMemory(name=shm_name)
    page_array   = np.ndarray(shape, dtype=np.dtype(dtype_str), buffer=existing_shm.buf)

    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
    img       = cv2.cvtColor(page_array, cv2.COLOR_RGB2BGR)
    processed = preprocess_image(img)
    existing_shm.close()

    data = pytesseract.image_to_data(
        processed,
        lang="fra",
        config=r"--psm 6 --oem 1 -c preserve_interword_spaces=1",
        output_type=pytesseract.Output.DICT
    )

    t_list   = data["text"]
    l_list   = data["left"]
    top_list = data["top"]
    w_list   = data["width"]
    h_list   = data["height"]

    results = [
        (t_list[j].strip(), (l_list[j], top_list[j], l_list[j] + w_list[j], top_list[j] + h_list[j]))
        for j in range(len(t_list)) if t_list[j].strip()
    ]

    duree = time.perf_counter() - t0
    return pdf_stem, page_idx, reconstruct_text(results), pid, duree


# ======================
# PHASE 1A : DÉTECTION (threads légers)
# ======================
def detecter_mode(pdf_file):
    tid = threading.current_thread().name
    t0  = time.perf_counter()
    safe_print(f"  [Thread {tid}] ▶ Détection  {pdf_file.name}", flush=True)

    try:
        with pdfplumber.open(pdf_file) as pdf:
            contient_image = any(
                page.images for i, page in enumerate(pdf.pages) if i > 0
            )
            if not contient_image:
                texte = [t for page in pdf.pages if (t := page.extract_text())]
                texte_joint = "\n\n".join(texte)

                # Détection police corrompue : (cid:N) = caractères non mappés
                # On calcule le ratio (cid:) sur le total de caractères
                nb_cid = texte_joint.count("(cid:")
                ratio_cid = nb_cid / max(len(texte_joint), 1)

                if ratio_cid > 0.01:  # >1% de (cid:) → police corrompue → OCR
                    duree = time.perf_counter() - t0
                    safe_print(
                        f"  [Thread {tid}] ⚠ CID ({ratio_cid*100:.0f}%) → OCR  "
                        f"{pdf_file.name}  ({format_duree(duree)})",
                        flush=True
                    )
                else:
                    duree = time.perf_counter() - t0
                    safe_print(f"  [Thread {tid}] ✔ Texte      {pdf_file.name}  ({format_duree(duree)})", flush=True)
                    return pdf_file, "texte", texte_joint
    except Exception as e:
        safe_print(f"  [Thread {tid}] ⚠ Erreur     {pdf_file.name} : {e}", flush=True)

    duree = time.perf_counter() - t0
    safe_print(f"  [Thread {tid}] ✔ OCR prévu  {pdf_file.name}  ({format_duree(duree)})", flush=True)
    return pdf_file, "ocr", None


# ======================
# PHASE 1B : CONVERSION IMAGE + SHARED MEMORY
# ======================
BATCH_SIZE = 10


def ocr_batch(pdf_file, batch_args, shm_list, ocr_index, pdf_debuts,
              dossier_resultats, executor, global_counter):
    """Soumet un batch de pages OCR et attend les résultats avant de libérer la RAM."""
    futures = {executor.submit(ocr_page, task): task for task in batch_args}
    for future in as_completed(futures):
        pdf_stem, page_idx, text, pid, duree_page = future.result()
        entry = ocr_index[pdf_stem]
        entry["pages"][page_idx] = text

        pages_faites = len(entry["pages"])
        total_pdf    = entry["total"]
        pct_pdf      = pages_faites / total_pdf * 100

        # Progression globale : PDFs finis + fraction du PDF courant
        with global_counter["lock"]:
            pdfs_done  = global_counter["done"]
            pdfs_total = global_counter["total"]
        pct_global = (pdfs_done + pages_faites / total_pdf) / pdfs_total * 100

        safe_print(
            f"  [PID {pid}]  {pdf_stem:<30}  "
            f"p.{page_idx + 1:>3}/{total_pdf}  ({duree_page:.1f}s)  "
            f"{pct_pdf:5.1f}%  —  "
            f"PDF {pdfs_done + 1}/{pdfs_total}  ({pct_global:.1f}%)",
            flush=True
        )

    for shm in shm_list:
        try:
            shm.close()
            shm.unlink()
        except Exception:
            pass


def traiter_pdf_ocr_par_batch(pdf_file, ocr_index, pdf_debuts,
                               dossier_resultats, executor, global_counter):
    """
    Traite un PDF par batchs de BATCH_SIZE pages :
      1. Convertit BATCH_SIZE pages avec fitz
      2. Lance l'OCR sur ces pages
      3. Attend les résultats
      4. Libère la RAM
      5. Passe au batch suivant
    → Pic RAM = BATCH_SIZE pages seulement, quelle que soit la taille du PDF.
    """
    try:
        doc = fitz.open(str(pdf_file))
    except Exception as e:
        safe_print(f"  ⚠ Impossible d'ouvrir {pdf_file.name} : {e}", flush=True)
        return

    zoom    = DPI / 72.0
    matrix  = fitz.Matrix(zoom, zoom)
    n_pages = len(doc)
    ocr_index[pdf_file.stem]["total"] = n_pages

    safe_print(f"  🖼  {pdf_file.name}  ({n_pages} pages · batchs de {BATCH_SIZE})", flush=True)

    for batch_start in range(0, n_pages, BATCH_SIZE):
        batch_end  = min(batch_start + BATCH_SIZE, n_pages)
        batch_args = []
        batch_shm  = []

        for i in range(batch_start, batch_end):
            try:
                pix = doc[i].get_pixmap(matrix=matrix, colorspace=fitz.csGRAY, alpha=False)
                arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width)
                arr = cv2.cvtColor(arr, cv2.COLOR_GRAY2BGR)
                pix = None

                shm = sm.SharedMemory(create=True, size=arr.nbytes)
                buf = np.ndarray(arr.shape, dtype=arr.dtype, buffer=shm.buf)
                buf[:] = arr
                del arr

                batch_shm.append(shm)
                batch_args.append((
                    pdf_file.stem, i,
                    shm.name, buf.shape, str(buf.dtype),
                    TESSERACT_CMD
                ))
            except Exception as e:
                safe_print(f"  ⚠ Erreur conversion page {i+1} : {e}", flush=True)
                continue

        if batch_args:
            ocr_batch(pdf_file, batch_args, batch_shm, ocr_index,
                      pdf_debuts, dossier_resultats, executor, global_counter)

    doc.close()

    # Écriture du fichier texte final
    entry    = ocr_index[pdf_file.stem]
    txt_file = dossier_resultats / (pdf_file.stem + ".txt")
    combined = "\n".join(
        f"\n===== PAGE {i + 1} =====\n{entry['pages'].get(i, '')}"
        for i in range(entry["total"])
    )
    txt_file.write_text(combined, encoding="utf-8")

    # Incrémente le compteur global une fois le PDF entièrement terminé
    with global_counter["lock"]:
        global_counter["done"] += 1
        pdfs_done  = global_counter["done"]
        pdfs_total = global_counter["total"]

    duree = time.perf_counter() - pdf_debuts[pdf_file.stem]
    sep()
    safe_print(
        f"  ✔ {pdf_file.name}  [OCR · {entry['total']} pages]  "
        f"⏱ {format_duree(duree)}  —  PDF {pdfs_done}/{pdfs_total} terminés"
    )
    sep()


# ======================
# MAIN FUNCTION
# ======================
def convertir_dossier_pdf_en_txt(dossier, ocr_workers=OCR_WORKERS, ana_workers=ANA_WORKERS):
    dossier = Path(dossier)
    dossier_resultats = dossier / "resultats_txt"
    dossier_resultats.mkdir(exist_ok=True)

    pdfs = list(dossier.glob("*.pdf"))

    sep("═")
    print(f"  📁 Dossier         : {dossier}")
    print(f"  📄 PDF             : {len(pdfs)}")
    print(f"  🔍 Threads détect. : {ana_workers}")
    print(f"  ⚙️  Workers OCR     : {ocr_workers} / {CPU_COUNT} cœurs")
    print(f"  📦 Batch size      : {BATCH_SIZE} pages")
    print(f"  🖼  DPI             : {DPI}")
    sep("═")

    if not pdfs:
        print("  ❌ Aucun PDF trouvé !")
        return

    debut_total = time.perf_counter()
    pdf_debuts  = {pdf.stem: time.perf_counter() for pdf in pdfs}

    # ── PHASE 1A : Détection en parallèle ─────────────────────────
    print(f"\n  PHASE 1A — Détection en parallèle ({ana_workers} threads)\n")
    sep()

    texte_direct = {}
    ocr_pdfs     = []

    with ThreadPoolExecutor(max_workers=ana_workers, thread_name_prefix="Det") as executor:
        futures = {executor.submit(detecter_mode, pdf): pdf for pdf in pdfs}
        for future in as_completed(futures):
            pdf_file, mode, result = future.result()
            if mode == "texte":
                texte_direct[pdf_file.stem] = (pdf_file, result)
            else:
                ocr_pdfs.append(pdf_file)

    sep()

    for stem, (pdf_file, texte) in texte_direct.items():
        txt_file = dossier_resultats / (stem + ".txt")
        txt_file.write_text(texte, encoding="utf-8")
        duree = time.perf_counter() - pdf_debuts[stem]
        print(f"  ✔ {pdf_file.name}  [texte]  ⏱ {format_duree(duree)}", flush=True)

    if not ocr_pdfs:
        total = time.perf_counter() - debut_total
        sep("═")
        print(f"\n  🎉 Terminé en {format_duree(total)}\n")
        sep("═")
        return

    # ── PHASES 1B + 2 : OCR par batch ─────────────────────────────
    print(f"\n  PHASES 1B+2 — Conversion et OCR par batchs de {BATCH_SIZE} pages\n")
    sep()

    ocr_index = {pdf.stem: {"file": pdf, "pages": {}, "total": 0} for pdf in ocr_pdfs}

    # Compteur global partagé entre les appels (thread-safe via lock)
    global_counter = {
        "done":  0,
        "total": len(ocr_pdfs),
        "lock":  threading.Lock(),
    }

    with ProcessPoolExecutor(max_workers=ocr_workers) as executor:
        for pdf_file in ocr_pdfs:
            traiter_pdf_ocr_par_batch(
                pdf_file, ocr_index, pdf_debuts, dossier_resultats,
                executor, global_counter
            )

    total = time.perf_counter() - debut_total
    sep("═")
    print(f"\n  🎉 {len(pdfs)} PDF traités en {format_duree(total)}\n")
    sep("═")


# ======================
# EXECUTION
# ======================
if __name__ == "__main__":
    multiprocessing.freeze_support()

    dossier_pdf = r"C:\Users\lilia\OneDrive\Bureau\Python\RAA\2016"

    convertir_dossier_pdf_en_txt(
        dossier_pdf,
        ocr_workers=OCR_WORKERS,
        ana_workers=ANA_WORKERS
    )