#!/usr/bin/env python3
import os
import re
import xml.etree.ElementTree as ET

OPENSONG_DIR = "/home/norbert/Projects/spiewnik-pielgrzyma-chordpro/opensong"
HYMNS_DIR = "/home/norbert/Projects/spiewnik-pielgrzyma-chordpro/hymns"

SECTION_RE = re.compile(r'^\[([A-Za-z]+\d*[A-Za-z]?)\]$')


def section_type(tag):
    tag_upper = tag.upper()
    if tag_upper.startswith('V'):
        return 'verse'
    if tag_upper.startswith('C') or tag_upper.startswith('R'):
        return 'chorus'
    return 'verse'


def parse_lyrics(lyrics_text):
    lines = lyrics_text.split('\n')
    sections = []
    current_type = None
    current_lines = []

    def flush():
        if current_type is not None:
            content = []
            for l in current_lines:
                content.append(l)
            # Strip trailing empty lines
            while content and content[-1] == '':
                content.pop()
            if content:
                sections.append((current_type, content))

    for line in lines:
        stripped = line.strip()
        m = SECTION_RE.match(stripped)
        if m:
            flush()
            current_type = section_type(m.group(1))
            current_lines = []
        elif current_type is None:
            continue
        else:
            # Strip leading dot (opensong chord lines) - check if it's actually lyrics text
            if line.startswith('.'):
                content = line[1:].strip()
                # If contains Polish/latin letters, it's lyrics mislabeled as chord line
                if content and re.search(r'[a-zA-ZąćęłńóśźżĄĆĘŁŃÓŚŹŻ]', content):
                    current_lines.append(content)
                # else: skip real chord line
            elif stripped == '':
                if current_lines and current_lines[-1] != '':
                    current_lines.append('')
            else:
                current_lines.append(stripped)

    flush()
    return sections


def convert(opensong_path, output_path):
    try:
        tree = ET.parse(opensong_path)
        root = tree.getroot()
    except ET.ParseError:
        print(f"XML error: {opensong_path}")
        return False

    title_el = root.find('title')
    lyrics_el = root.find('lyrics')

    if title_el is None or lyrics_el is None:
        print(f"Missing title/lyrics: {opensong_path}")
        return False

    title = (title_el.text or '').strip()
    lyrics_text = (lyrics_el.text or '').strip()
    sections = parse_lyrics(lyrics_text)

    out = [f'{{title: {title}}}']

    for sec_type, sec_lines in sections:
        out.append('')
        out.append(f'{{start_of_{sec_type}}}')
        out.extend(sec_lines)
        out.append(f'{{end_of_{sec_type}}}')

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out) + '\n')

    return True


def main():
    converted = skipped = errors = 0

    for filename in sorted(os.listdir(OPENSONG_DIR)):
        path = os.path.join(OPENSONG_DIR, filename)
        if not os.path.isfile(path):
            continue

        m = re.match(r'^([A-Z]?\d+)', filename)
        if not m:
            print(f"No number in: {filename}")
            continue

        out_path = os.path.join(HYMNS_DIR, f"{m.group(1)}.chordpro")
        if os.path.exists(out_path):
            skipped += 1
            continue

        if convert(path, out_path):
            converted += 1
        else:
            errors += 1

    print(f"Converted: {converted}, Skipped: {skipped}, Errors: {errors}")


if __name__ == '__main__':
    main()
