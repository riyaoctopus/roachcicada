"""
Builds a local embedding index over the RoachCicada markdown knowledge base.
Run: python build_index.py
Writes: index/chunks.json  (list of {id, source, heading, text, images, videos, embedding})
"""
import json
import re
import sys

from openai import OpenAI

from common import ROOT, INDEX_PATH, EMBEDDING_MODEL, extract_media_paths, load_api_key

client = OpenAI(api_key=load_api_key())

MD_FILES = sorted(ROOT.glob("*.md"))

HEADING_RE = re.compile(r"^(#{1,3})\s+(.*)$", re.MULTILINE)


def split_into_sections(text: str):
    """Split a markdown file into (heading_path, body) chunks on ## / ### boundaries."""
    matches = list(HEADING_RE.finditer(text))
    if not matches:
        return [("", text.strip())]

    sections = []
    # Preamble before first heading (title / intro), if any
    if matches[0].start() > 0:
        pre = text[: matches[0].start()].strip()
        if pre:
            sections.append(("", pre))

    for i, m in enumerate(matches):
        level = len(m.group(1))
        heading = m.group(2).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if level == 1:
            # Treat H1 title as context prefix for subsequent chunks; skip as own chunk if trivial
            if body:
                sections.append((heading, body))
            continue
        sections.append((heading, body))
    return [(h, b) for h, b in sections if b]


def chunk_document(path):
    text = path.read_text()
    title_match = re.search(r"^#\s+(.*)$", text, re.MULTILINE)
    doc_title = title_match.group(1).strip() if title_match else path.stem
    sections = split_into_sections(text)

    chunks = []
    for heading, body in sections:
        # Further split very long sections (e.g. FAQ) on H3-level '###' inside body already
        # handled by split_into_sections since it captures all heading levels 1-3.
        if len(body) < 40:
            continue
        images, videos = extract_media_paths(body)
        chunks.append(
            {
                "source": path.name,
                "doc_title": doc_title,
                "heading": heading,
                "text": body,
                "images": images,
                "videos": videos,
            }
        )
    return chunks


def embed_batch(texts):
    resp = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    return [d.embedding for d in resp.data]


def main():
    all_chunks = []
    for path in MD_FILES:
        doc_chunks = chunk_document(path)
        print(f"{path.name}: {len(doc_chunks)} chunks")
        all_chunks.extend(doc_chunks)

    if not all_chunks:
        print("No chunks found — aborting.")
        sys.exit(1)

    print(f"\nTotal chunks: {len(all_chunks)}. Embedding with {EMBEDDING_MODEL}...")

    # Embed in batches to stay well under request size limits
    batch_size = 64
    embeddings = []
    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i : i + batch_size]
        texts = [f"{c['doc_title']} — {c['heading']}\n\n{c['text']}" for c in batch]
        vecs = embed_batch(texts)
        embeddings.extend(vecs)
        print(f"  embedded {min(i + batch_size, len(all_chunks))}/{len(all_chunks)}")

    for c, e in zip(all_chunks, embeddings):
        c["id"] = f"{c['source']}::{c['heading'][:60]}"
        c["embedding"] = e

    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(INDEX_PATH, "w") as f:
        json.dump(all_chunks, f)

    print(f"\nWrote {len(all_chunks)} chunks to {INDEX_PATH}")


if __name__ == "__main__":
    main()
