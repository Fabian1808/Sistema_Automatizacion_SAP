def analyze_ids(lines):
    valid = []
    duplicates = []
    invalid = []
    seen = set()
    for raw in lines:
        cleaned = str(raw).strip().replace(" ", "")
        if not cleaned:
            continue
        if cleaned.isdigit():
            if cleaned in seen:
                duplicates.append(cleaned)
            else:
                seen.add(cleaned)
                valid.append(cleaned)
        else:
            invalid.append(str(raw).strip())
    return {"valid": valid, "duplicates": duplicates, "invalid": invalid}


def normalize_ids(lines):
    return analyze_ids(lines)["valid"]