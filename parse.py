import re
from typing import Optional, Union

Number = Union[int, float]

# More specific terms appear first to reduce category collisions.
CATEGORY_PATTERNS = [
    ("bopp_bag", r"\bbopp\b|\bbop\s*laminat(?:ed|ion)?\b|\bbopp[ -]*laminat(?:ed|ion)?\b"),
    ("fibc", r"\bfibc\b|\bjumbo\s*bags?\b|\bbulk\s*bags?\b|\b1\s*ton\s*bags?\b|\bcontainer\s*bags?\b"),
    ("woven_sack", r"\bwoven\s*(?:sacks?|bags?)?\b|\bcement\s*bags?\b|\bad[ -]*star\b|\bpp\s*(?:woven\s*)?sacks?\b|\bfertili[sz]er\s*bags?\b|\brace\s*bags?\b"),
    ("mono_carton", r"\bmono[ -]*cartons?\b|\bmono\s*carton\b"),
    ("corrugated_box", r"\bcorrugat(?:ed|ion)\b|\bcorrugated\s*(?:cartons?|boxes?)\b|\b(?:carton|cartons|box|boxes)\b"),
    ("pouch", r"\bpouch(?:es)?\b|\bstand[ -]*up\s*pouch(?:es)?\b|\bzip[ -]?lock\s*pouch(?:es)?\b|\bspout\s*pouch(?:es)?\b"),
    ("film", r"\bfilm\b|\bshrink[ -]?(?:wrap|film)\b|\bstretch[ -]?(?:wrap|film)\b|\bldpe\s*film\b|\bpoly(?:thene|ethylene)\s*film\b"),
]

SMALL_NUMBERS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
    "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
    "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
    "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17,
    "eighteen": 18, "nineteen": 19, "twenty": 20, "thirty": 30,
    "forty": 40, "fourty": 40, "fifty": 50, "sixty": 60,
    "seventy": 70, "eighty": 80, "ninety": 90,
}
SCALE_WORDS = {
    "hundred": 100, "thousand": 1000, "hazaar": 1000, "hazar": 1000,
    "k": 1000, "lakh": 100000, "lac": 100000, "lakhs": 100000,
    "lacs": 100000, "crore": 10000000, "cr": 10000000, "l": 100000,
}


def _clean_number(raw: str) -> str:
    return raw.lower().replace(",", "").strip()


def _number_value(raw: str) -> Optional[Number]:
    s = _clean_number(raw)
    m = re.fullmatch(r"(\d+(?:\.\d+)?)\s*(k|thousand|hazaar|hazar|lakh|lac|lakhs|lacs|crore|cr|l)", s)
    if m:
        scale = SCALE_WORDS[m.group(2)]
        value = float(m.group(1)) * scale
        return int(value) if value.is_integer() else value
    if re.fullmatch(r"\d+(?:\.\d+)?", s):
        value = float(s)
        return int(value) if value.is_integer() else value

    words = re.findall(r"[a-z]+|\d+(?:\.\d+)?", s)
    if not words:
        return None
    total = 0.0
    current = 0.0
    for word in words:
        if word in SMALL_NUMBERS:
            current += SMALL_NUMBERS[word]
        elif word in SCALE_WORDS:
            scale = SCALE_WORDS[word]
            if scale == 100:
                current = max(current, 1) * scale
            else:
                total += max(current, 1) * scale
                current = 0
        elif re.fullmatch(r"\d+(?:\.\d+)?", word):
            current += float(word)
        else:
            return None
    value = total + current
    if value == 0:
        return None
    return int(value) if value.is_integer() else value


# Number phrase accepted before an order unit. Keep it bounded to avoid consuming prose.
NUM_PHRASE = (
    r"(?:\d[\d,]*(?:\.\d+)?(?:\s*(?:k|thousand|hazaar|hazar|lakh|lac|lakhs|lacs|crore|cr|l))?"
    r"|(?:one|two|three|four|fourty|forty|five|six|seven|eight|nine|ten|eleven|twelve|"
    r"fifteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|"
    r"hazaar|hazar|lakh|lac|crore)(?:[ -]+(?:one|two|three|four|five|six|seven|eight|nine|ten|"
    r"eleven|twelve|fifteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|"
    r"thousand|hazaar|hazar|lakh|lac|crore)){0,3})"
)


def _extract_quantity_and_unit(text: str):
    s = text.lower().replace("µ", "u")
    # Remove specification/capacity values before looking for order quantity.
    s = re.sub(r"\b\d+(?:\.\d+)?\s*(?:g\.?s\.?m\.?|gsm|microns?|mic|um)\b", " ", s)
    s = re.sub(r"\b(?:capacity|cap\.?|load)\s*(?:of\s*)?\d+(?:\.\d+)?\s*(?:kg|kgs|mt|tonnes?|tons?)\b", " ", s)
    s = re.sub(r"\b\d+(?:\.\d+)?\s*(?:kg|kgs|mt|tonnes?|tons?)\s*(?:capacity|cap\.?|load|weight)\b", " ", s)
    s = re.sub(r"\b\d+(?:\.\d+)?\s*(?:mt|tonnes?|tons?)\s*(?:capacity|cap\.?|load|weight)\b", " ", s)
    s = re.sub(r"\b\d+(?:\.\d+)?\s*(?:kg|kgs)\s*(?:per\s*bag|each|each\s*bag)\b", " ", s)

    unit_patterns = [
        (rf"(?P<num>{NUM_PHRASE})\s*(?:pcs?|pieces?|nos?\.?|bags?|units?|sets?)\b", "pcs"),
        (rf"(?P<num>{NUM_PHRASE})\s*(?:kgs?|kilograms?)\b", "kg"),
        (rf"(?P<num>{NUM_PHRASE})\s*(?:mt|metric\s*tons?|tonnes?|tons?)\b", "mt"),
    ]
    candidates = []
    for pattern, unit in unit_patterns:
        for match in re.finditer(pattern, s, flags=re.I):
            value = _number_value(match.group("num"))
            if value is not None:
                candidates.append((match.start(), value, unit))
    if candidates:
        _, value, unit = min(candidates, key=lambda item: item[0])
        return value, unit

    # Quantity labels often omit a unit: Qty 15K / order quantity: 2 lakh.
    labelled = re.search(rf"\b(?:qty|quantity|order\s*qty|order\s*quantity|requirement)\s*[:= -]?\s*(?P<num>{NUM_PHRASE})\b", s, re.I)
    if labelled:
        value = _number_value(labelled.group("num"))
        if value is not None:
            return value, "pcs"

    # Written-out counts may be followed by a product noun rather than a unit.
    words_count = re.search(r"\b(?P<num>(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fifteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand)(?:[ -]+(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fifteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand)){0,2})\s+(?:pouches?|bags?|sacks?|cartons?|boxes?)\b", s)
    if words_count:
        value = _number_value(words_count.group("num"))
        if value is not None:
            return value, "pcs"

    # A multiplier without an explicit unit is normally a piece count in packaging RFQs.
    scaled = re.search(r"\b(\d[\d,]*(?:\.\d+)?\s*(?:k|thousand|hazaar|hazar|lakh|lac|lakhs|lacs|crore|cr|l))\b", s)
    if scaled:
        value = _number_value(scaled.group(1))
        if value is not None:
            return value, "pcs"

    # Last-resort standalone count, excluding any nearby measurement/capacity context.
    for match in re.finditer(r"\b\d[\d,]*(?:\.\d+)?\b", s):
        around = s[max(0, match.start() - 24): min(len(s), match.end() + 28)]
        if re.search(r"\b(?:gsm|g\.s\.m|mic|micron|um|capacity|cap|kg|kgs|mt|tonne|ton|mm|cm|size|weight)\b", around):
            continue
        value = _number_value(match.group())
        if value is not None:
            return value, "pcs"
    return None, "pcs"


def _extract_spec(text: str, pattern: str):
    match = re.search(pattern, text, flags=re.I)
    if not match:
        return None
    try:
        value = float(match.group(1).replace(",", ""))
        return int(value)
    except (ValueError, TypeError):
        return None


def _extract_location(text: str):
    # Explicit destination phrases are the strongest location signal.
    # Keep regex simple and trim trailing request words / numeric specs.
    cue = re.search(r"(?:deliver(?:y)?\s*(?:to|at)?|ship\s*to|send\s*to|dispatch\s*to|location\s*[:=-]?|destination\s*[:=-]?|\bin\b|\bat\b)\s*([A-Za-z][A-Za-z .'-]{1,45})", text, re.I)
    if cue:
        value = cue.group(1).strip(" ,.;:-")
        value = re.split(r"\b(?:please|urgent|asap|pin\s*code|pincode|quantity|qty)\b", value, flags=re.I)[0].strip(" ,.;:-")
        # If the cue captured a sentence, retain at most a short city/state phrase.
        value = re.sub(r"\s+(?:for|with)\s+.*$", "", value, flags=re.I).strip()
        if value:
            return value

    # A final comma-separated city is common in short RFQs.
    parts = re.split(r"[,;]", text)
    if len(parts) > 1:
        tail = parts[-1].strip(" .;:-")
        tail = re.sub(r"\b(?:please|required|urgent|asap)\b.*$", "", tail, flags=re.I).strip()
        if re.fullmatch(r"[A-Za-z][A-Za-z .'-]{1,40}", tail):
            if not re.search(r"\b(?:gsm|micron|pcs|pieces|bags|kg|mt|tonnes?)\b", tail, re.I):
                return tail
    return None


def parse_rfq(text: str) -> dict:
    """Parse a short packaging RFQ into the six fields required by the assignment."""
    if not isinstance(text, str):
        text = str(text or "")

    category = None
    for name, pattern in CATEGORY_PATTERNS:
        if re.search(pattern, text, re.I):
            category = name
            break

    quantity, unit = _extract_quantity_and_unit(text)
    gsm = _extract_spec(text, r"\b(\d+(?:\.\d+)?)\s*(?:g\.?s\.?m\.?|gsm)\b")
    micron = _extract_spec(text, r"\b(\d+(?:\.\d+)?)\s*(?:microns?|mic\.?|um)\b")
    location = _extract_location(text)

    return {
        "category": category,
        "quantity": quantity,
        "unit": unit,
        "gsm": gsm,
        "micron": micron,
        "location": location,
    }
