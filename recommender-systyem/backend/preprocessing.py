"""
preprocessing.py
Text cleaning utility — direct port of the tested standalone version.
Place this file at:  recommender-systyem/backend/preprocessing.py

Usage (from any backend module):
    from preprocessing import clean_text
"""
import re
import nltk

# ── NLTK data auto-download (runs once on first import) ───────────────────────
for _resource, _pkg in [
    ('corpora/stopwords',  'stopwords'),
    ('tokenizers/punkt',   'punkt'),
    ('corpora/wordnet',    'wordnet'),
    ('tokenizers/punkt_tab', 'punkt_tab'),
]:
    try:
        nltk.data.find(_resource)
    except LookupError:
        nltk.download(_pkg, quiet=True)

from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

# ── Contraction map (extend as needed) ────────────────────────────────────────
_CONTRACTIONS = {
    "ain't":    "am not",
    "aren't":   "are not",
    "can't":    "cannot",
    "can't've": "cannot have",
    "cause":    "because",
    "could've": "could have",
    "couldn't": "could not",
    "didn't":   "did not",
    "doesn't":  "does not",
    "don't":    "do not",
    "hadn't":   "had not",
    "hasn't":   "has not",
    "haven't":  "have not",
    "he'd":     "he would",
    "he'll":    "he will",
    "he's":     "he is",
    "i'd":      "i would",
    "i'll":     "i will",
    "i'm":      "i am",
    "i've":     "i have",
    "isn't":    "is not",
    "it's":     "it is",
    "let's":    "let us",
    "she'd":    "she would",
    "she'll":   "she will",
    "she's":    "she is",
    "shouldn't":"should not",
    "that's":   "that is",
    "there's":  "there is",
    "they'd":   "they would",
    "they'll":  "they will",
    "they're":  "they are",
    "they've":  "they have",
    "wasn't":   "was not",
    "we'd":     "we would",
    "we're":    "we are",
    "we've":    "we have",
    "weren't":  "were not",
    "what'll":  "what will",
    "what're":  "what are",
    "what's":   "what is",
    "what've":  "what have",
    "where's":  "where is",
    "who'll":   "who will",
    "who's":    "who is",
    "won't":    "will not",
    "wouldn't": "would not",
    "you'd":    "you would",
    "you'll":   "you will",
    "you're":   "you are",
    "you've":   "you have",
}

# Build a single compiled regex (longest keys first to avoid partial matches)
_sorted_keys    = sorted(_CONTRACTIONS.keys(), key=len, reverse=True)
_CONTRACTION_RE = re.compile(
    r'\b(' + '|'.join(re.escape(k) for k in _sorted_keys) + r')\b',
    flags=re.IGNORECASE
)

# Emoji pattern (compiled once)
_EMOJI_RE = re.compile(
    "["
    u"\U0001F600-\U0001F64F"
    u"\U0001F300-\U0001F5FF"
    u"\U0001F680-\U0001F6FF"
    u"\U0001F1E0-\U0001F1FF"
    u"\U00002702-\U000027B0"
    u"\U000024C2-\U0001F251"
    "]+",
    flags=re.UNICODE
)

_STOP_WORDS  = set(stopwords.words("english"))
_LEMMATIZER  = WordNetLemmatizer()


# ── PUBLIC API ────────────────────────────────────────────────────────────────

def clean_text(text: str, remove_stopwords: bool = True) -> str:
    """
    Clean and normalise a review / product text string.

    Steps (same as tested pipeline):
      1. Lowercase
      2. Expand contractions
      3. Remove URLs, @mentions, HTML tags
      4. Remove punctuation / special chars
      5. Remove emojis
      6. Tokenise
      7. (optionally) remove stopwords
      8. Lemmatise

    Returns empty string for null / empty input.
    """
    if not text or (isinstance(text, float)):
        return ""

    text = str(text).lower()

    # Expand contractions
    text = _CONTRACTION_RE.sub(
        lambda m: _CONTRACTIONS[m.group(0).lower()], text
    )

    # Remove noise
    text = re.sub(r'https?://\S+|www\.\S+', ' ', text)   # URLs
    text = re.sub(r'@\w+',                  ' ', text)   # mentions
    text = re.sub(r'<[^>]+>',               ' ', text)   # HTML tags
    text = re.sub(r'[_"\\\-;%()|+&=*%.,!?:#$@\[\]/]', ' ', text)
    text = re.sub(r'\s+',                   ' ', text)   # collapse spaces

    # Remove emojis
    text = _EMOJI_RE.sub('', text)

    # Tokenise
    words = word_tokenize(text)

    # Optionally strip stopwords and short tokens
    if remove_stopwords:
        words = [w for w in words if w not in _STOP_WORDS and len(w) > 2]

    # Lemmatise
    words = [_LEMMATIZER.lemmatize(w) for w in words]

    return " ".join(words)
