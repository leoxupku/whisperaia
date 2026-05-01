import difflib
import re
import sqlite3
from pathlib import Path

DB_PATH = Path.home() / ".whisperaia" / "vocabulary.db"


def _normalize(s: str) -> str:
    return re.sub(r'[\s,，。.!?！？、…—～·]+', '', s)


def _extract_word_pairs(original: str, corrected: str) -> list[tuple[str, str]]:
    """Diff two sentences and return the minimal changed substrings."""
    orig_n = _normalize(original)
    corr_n = _normalize(corrected)
    if orig_n == corr_n:
        return []
    matcher = difflib.SequenceMatcher(None, orig_n, corr_n, autojunk=False)
    pairs = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'replace':
            orig_chunk = orig_n[i1:i2]
            corr_chunk = corr_n[j1:j2]
            if orig_chunk and corr_chunk and 2 <= len(orig_chunk) <= 8:
                pairs.append((orig_chunk, corr_chunk))
    return pairs


class PersonalVocabulary:
    def __init__(self):
        DB_PATH.parent.mkdir(exist_ok=True)
        self._conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS corrections (
                original TEXT, corrected TEXT, count INTEGER DEFAULT 1,
                PRIMARY KEY (original, corrected)
            );
            CREATE TABLE IF NOT EXISTS word_corrections (
                original TEXT, corrected TEXT, count INTEGER DEFAULT 1,
                PRIMARY KEY (original, corrected)
            );
        """)
        self._conn.commit()

    def record(self, original: str, corrected: str):
        self._upsert("corrections", original, corrected)
        for orig_word, corr_word in _extract_word_pairs(original, corrected):
            self._upsert("word_corrections", orig_word, corr_word)
            print(f"  [词典] {orig_word!r} → {corr_word!r}")
        self._conn.commit()

    def apply_substitutions(self, text: str) -> str:
        """Directly replace known bad patterns before LLM sees the text."""
        # Longer patterns first to avoid partial replacements
        rows = self._conn.execute(
            "SELECT original, corrected FROM word_corrections "
            "ORDER BY length(original) DESC, count DESC"
        ).fetchall()
        for orig, corr in rows:
            text = text.replace(orig, corr)
        return text

    def get_top_word_corrections(self, limit: int = 10) -> list[tuple[str, str]]:
        return self._conn.execute(
            "SELECT original, corrected FROM word_corrections "
            "ORDER BY count DESC LIMIT ?", (limit,)
        ).fetchall()

    def _upsert(self, table: str, original: str, corrected: str):
        self._conn.execute(
            f"INSERT INTO {table} (original, corrected) VALUES (?, ?) "
            "ON CONFLICT(original, corrected) DO UPDATE SET count = count + 1",
            (original, corrected),
        )
