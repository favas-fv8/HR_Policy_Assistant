import re

FALLBACK_TITLES = {"", "new chat", "new conversation", "user question"}
FILLER_WORDS = {
    "a", "an", "the", "please", "kindly", "can", "could", "would", "you",
    "me", "my", "i", "we", "us", "our", "tell", "about", "for", "to", "of",
    "in", "on", "at", "is", "are", "was", "were", "do", "does", "did",
    "what", "whats", "what's", "how", "why", "when", "where", "who", "which",
    "should", "will", "may", "might", "need", "want", "like", "give",
    "show", "explain", "describe", "summarize", "summary", "provide", "get",
    "let", "know", "any", "some", "this", "that", "these", "those", "it",
    "have", "has", "had", "many", "much", "year", "years",
}
GREETING_WORDS = {"hi", "hello", "hey", "greetings", "good", "morning", "afternoon", "evening", "thanks", "thank", "please"}
MAX_TITLE_LENGTH = 60
MAX_TITLE_WORDS = 7


def is_default_chat_title(title):
    return (title or "").strip().lower() in FALLBACK_TITLES


def generate_chat_title(message, max_words=MAX_TITLE_WORDS, max_length=MAX_TITLE_LENGTH):
    text = (message or "").strip()
    if not text:
        return "New Chat"

    # Remove URLs/emails and collapse whitespace
    text = re.sub(r"https?://\S+|www\.\S+|\S+@\S+", " ", text)
    text = re.sub(r"[`*_#>\[\](){}]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return "New Chat"

    # Split into sentences/clauses; use first meaningful segment
    segments = re.split(r"[?!.:\n\r]+", text)
    segment = next((s.strip() for s in segments if s.strip()), text)

    words_raw = re.findall(r"[A-Za-z0-9][A-Za-z0-9&/-]*", segment)
    if not words_raw:
        return "New Chat"

    # Drop leading greetings/filler
    i = 0
    while i < len(words_raw) and words_raw[i].lower() in GREETING_WORDS:
        i += 1
    words = words_raw[i:] or words_raw

    filtered = [w for w in words if w.lower() not in FILLER_WORDS and w.lower() not in GREETING_WORDS]
    if not filtered:
        return "New Chat"

    # Keep concise title
    title_words = filtered[:max_words]
    # Avoid ending on weak words
    while len(title_words) > 3 and title_words[-1].lower() in {"and", "or", "for", "to", "of", "with", "by"}:
        title_words.pop()

    lower_words = [w.lower() for w in title_words]
    if "candidate" in lower_words and len(title_words) > 1:
        # Prefer "Candidate X" phrasing for candidate-focused questions
        rest = [w for w in title_words if w.lower() != "candidate"]
        title_words = [next(w for w in title_words if w.lower() == "candidate")] + rest

    title = " ".join(_cap_word(w) for w in title_words).strip()
    title = re.sub(r"\s+", " ", title)
    if len(title) > max_length:
        title = title[:max_length].rstrip(" -,:;")
        # don't cut mid-word harshly if possible
        if " " in title:
            parts = title.rsplit(" ", 1)
            if len(parts[0]) >= 20:
                title = parts[0]
    title = title.strip(" -,:;!?")
    return title or "New Chat"


def _cap_word(word):
    upper = word.upper()
    if upper in {"HR", "PDF", "AI", "IT", "PTO", "USA", "UK"}:
        return upper
    if any(c.isdigit() for c in word) or "/" in word or "&" in word or "-" in word:
        return word.upper() if word.isupper() else word[:1].upper() + word[1:]
    return word.capitalize()
