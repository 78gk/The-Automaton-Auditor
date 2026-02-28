"""
Automaton Auditor — Document Forensic Tools
Implements PDF ingestion using docling with RAG-lite chunked querying.
Also handles image extraction for VisionInspector.
"""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# PDF Ingestion (docling-based)
# ---------------------------------------------------------------------------

def ingest_pdf(pdf_path: str) -> Dict[str, Any]:
    """
    Ingest a PDF report using docling and return structured text chunks.
    Falls back to PyPDF2 if docling is unavailable.
    Returns dict with: full_text, chunks, images_found, metadata.
    """
    pdf_path_obj = Path(pdf_path)
    if not pdf_path_obj.exists():
        return {"error": f"PDF not found: {pdf_path}", "full_text": "", "chunks": []}

    # Try docling first (preferred — handles complex PDFs better)
    try:
        from docling.document_converter import DocumentConverter
        converter = DocumentConverter()
        result = converter.convert(str(pdf_path_obj))
        full_text = result.document.export_to_markdown()
        chunks = _chunk_text(full_text)
        return {
            "full_text": full_text,
            "chunks": chunks,
            "source": "docling",
            "pdf_path": str(pdf_path_obj),
            "images_found": _count_images_docling(result),
        }
    except ImportError:
        logger.warning("docling not available, falling back to pypdf")
    except Exception as e:
        logger.warning(f"docling failed: {e}, falling back to pypdf")

    # Fallback: pypdf
    try:
        import pypdf
        reader = pypdf.PdfReader(str(pdf_path_obj))
        full_text = "\n\n".join(
            page.extract_text() or "" for page in reader.pages
        )
        chunks = _chunk_text(full_text)
        return {
            "full_text": full_text,
            "chunks": chunks,
            "source": "pypdf",
            "pdf_path": str(pdf_path_obj),
            "images_found": sum(
                len(page.images) for page in reader.pages
            ),
        }
    except ImportError:
        logger.warning("pypdf not available either")
    except Exception as e:
        logger.warning(f"pypdf failed: {e}")

    return {
        "error": "No PDF parser available (install docling or pypdf)",
        "full_text": "",
        "chunks": [],
    }


def _chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """Split text into overlapping chunks for RAG-lite retrieval."""
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


def _count_images_docling(result: Any) -> int:
    """Count images found in a docling result."""
    try:
        count = 0
        for element in result.document.body.children:
            if hasattr(element, "image"):
                count += 1
        return count
    except Exception:
        return 0


# ---------------------------------------------------------------------------
# RAG-lite Query
# ---------------------------------------------------------------------------

def query_document(
    doc_data: Dict[str, Any],
    query: str,
    top_k: int = 3,
) -> List[str]:
    """
    Simple keyword-based retrieval from document chunks.
    Returns the top_k most relevant chunks for the query.
    In production this would use embeddings; here we use TF-IDF-lite scoring.
    """
    chunks = doc_data.get("chunks", [])
    if not chunks:
        return []

    query_terms = set(query.lower().split())
    scored = []
    for chunk in chunks:
        chunk_lower = chunk.lower()
        score = sum(1 for term in query_terms if term in chunk_lower)
        if score > 0:
            scored.append((score, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [chunk for _, chunk in scored[:top_k]]


# ---------------------------------------------------------------------------
# Theoretical Depth Analysis
# ---------------------------------------------------------------------------

FORENSIC_KEYWORDS = {
    "Dialectical Synthesis": [
        "dialectical synthesis", "dialectical", "thesis-antithesis", "synthesis",
    ],
    "Fan-In / Fan-Out": [
        "fan-in", "fan-out", "fan in", "fan out", "parallel branch", "parallel execution",
    ],
    "Metacognition": [
        "metacognition", "metacognitive", "self-evaluation", "self-audit",
        "evaluating the evaluator",
    ],
    "State Synchronization": [
        "state synchronization", "state sync", "reducer", "operator.add",
        "operator.ior", "annotated", "parallel state",
    ],
}


def analyze_theoretical_depth(doc_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Search for forensic keywords and determine if they appear in substantive
    architectural explanations or are just buzzwords.
    Returns evidence of theoretical depth per keyword.
    """
    full_text = doc_data.get("full_text", "").lower()
    results = {}

    for concept, variants in FORENSIC_KEYWORDS.items():
        found_variants = [v for v in variants if v in full_text]
        if not found_variants:
            results[concept] = {
                "found": False,
                "depth": "absent",
                "context": None,
            }
            continue

        # Extract surrounding context (200 chars around each match)
        contexts = []
        for variant in found_variants:
            idx = full_text.find(variant)
            while idx != -1:
                start = max(0, idx - 100)
                end = min(len(full_text), idx + len(variant) + 200)
                contexts.append(full_text[start:end])
                idx = full_text.find(variant, idx + 1)

        # Heuristic: if context contains implementation details, it's substantive
        depth_indicators = [
            "implement", "node", "edge", "graph", "code", "function",
            "class", "src/", "operator", "langgraph", "stategraph",
        ]
        has_depth = any(
            indicator in ctx
            for ctx in contexts
            for indicator in depth_indicators
        )

        results[concept] = {
            "found": True,
            "depth": "substantive" if has_depth else "keyword_drop",
            "context": contexts[0][:300] if contexts else None,
            "occurrences": len(contexts),
        }

    return results


# ---------------------------------------------------------------------------
# File Path Cross-Reference (Hallucination Detection)
# ---------------------------------------------------------------------------

def extract_file_paths_from_text(text: str) -> List[str]:
    """Extract repo-relative file paths mentioned in text.

    We intentionally keep this conservative to reduce false positives:
    - only paths containing at least one slash
    - extensions 1-6 chars
    - trims punctuation and normalizes separators
    """
    # Capture common forms: src/... , ./... , docs/... , reports/... , etc.
    pattern = r"(?:(?:\./)?(?:src|docs|reports|audit|tests?)/[\w\-./]+\.[A-Za-z0-9]{1,6})"
    matches = re.findall(pattern, text)

    def normalize(p: str) -> str:
        p = p.strip().strip('`').strip('"').strip("'")
        p = p.rstrip('.,;:()[]{}<>')  # trailing punctuation
        p = p.replace('\\\\', '/').replace('\\', '/')
        if p.startswith('./'):
            p = p[2:]
        # collapse duplicate slashes
        while '//' in p:
            p = p.replace('//', '/')
        return p

    seen = set()
    unique: List[str] = []
    for m in matches:
        nm = normalize(m)
        if nm and nm not in seen:
            seen.add(nm)
            unique.append(nm)
    return unique


def cross_reference_paths(
    mentioned_paths: List[str],
    actual_files: List[str],
) -> Dict[str, Any]:
    """
    Cross-reference file paths mentioned in the PDF report against
    files that actually exist in the repository.
    Returns verified vs. hallucinated paths.
    """
    # Normalize paths (forward slashes, no leading ./)
    def _norm(p: str) -> str:
        p = p.replace("\\", "/")
        if p.startswith("./"):
            p = p[2:]
        # collapse duplicate slashes
        while "//" in p:
            p = p.replace("//", "/")
        return p

    normalized_actual = {_norm(f) for f in actual_files}

    verified = []
    hallucinated = []

    for path in mentioned_paths:
        norm_path = path.strip()
        # remove common wrappers
        norm_path = norm_path.strip('"').strip("'")
        norm_path = norm_path.replace('`', '')
        # remove trailing punctuation only (keep leading ./ for explicit handling)
        norm_path = norm_path.rstrip('.,;:()[]{}<>')
        norm_path = norm_path.replace("\\", "/")
        if norm_path.startswith("./"):
            norm_path = norm_path[2:]
        if norm_path.startswith("/"):
            norm_path = norm_path[1:]
        # Check exact match or suffix match
        if norm_path in normalized_actual or any(
            f.endswith(norm_path) for f in normalized_actual
        ):
            verified.append(path)
        else:
            hallucinated.append(path)

    return {
        "mentioned_paths": mentioned_paths,
        "verified_paths": verified,
        "hallucinated_paths": hallucinated,
        "hallucination_rate": (
            len(hallucinated) / len(mentioned_paths)
            if mentioned_paths else 0.0
        ),
    }


# ---------------------------------------------------------------------------
# Image Extraction
# ---------------------------------------------------------------------------

def extract_images_from_pdf(pdf_path: str, output_dir: str) -> List[str]:
    """
    Extract images from a PDF and save them to output_dir.
    Returns list of saved image file paths.
    """
    saved_images = []
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    try:
        import pypdf
        reader = pypdf.PdfReader(pdf_path)
        img_count = 0
        for page_num, page in enumerate(reader.pages):
            for img_obj in page.images:
                img_filename = output_path / f"page{page_num}_img{img_count}.png"
                img_filename.write_bytes(img_obj.data)
                saved_images.append(str(img_filename))
                img_count += 1
        return saved_images
    except ImportError:
        logger.warning("pypdf not available for image extraction")
    except Exception as e:
        logger.warning(f"Image extraction failed: {e}")

    return saved_images
