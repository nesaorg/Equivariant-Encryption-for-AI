mapped_chars = {
    ".": "#a#",
    ">": "#b#",
    "*": "#c#",
    " ": "#d#"
}
def sanitize_subject_token(s):
    for k, v in mapped_chars.items():
        s = s.replace(k, v)
    return s.lower()

def desanitize_subject_token(s):
    for k, v in mapped_chars.items():
        s = s.replace(v, k)
    return s