import ast
import json
import os
import re


def merge_json_files(target_file: str, source_file: str, output_path: str) -> None:
    """
    Merges two JSON files and writes the merged result into an output file.
    - Retains existing values in the target JSON.
    - Adds missing keys from the source JSON.
    - Saves the merged result to the specified output path.

    Args:
        target_file (str): Path to the primary JSON file.
        source_file (str): Path to the secondary JSON file.
        output_path (str): Path where the merged JSON will be saved.
    """

    # Load target JSON file (or create an empty dictionary if not found)
    if os.path.exists(target_file):
        with open(target_file, "r", encoding="utf-8") as f:
            target_data = json.load(f)
    else:
        target_data = {}

    # Load source JSON file (or create an empty dictionary if not found)
    if os.path.exists(source_file):
        with open(source_file, "r", encoding="utf-8") as f:
            source_data = json.load(f)
    else:
        source_data = {}

    # Merge source_data into target_data without overwriting existing values
    for key, value in source_data.items():
        if key not in target_data:
            target_data[key] = value

    # Save the merged JSON into output_path
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(target_data, f, indent=4, ensure_ascii=False)

    print(f"Merged JSON successfully saved to: {output_path}")


def clean_json_response(response):
    """Extract a valid JSON object/array from the LLM response."""

    def strip_code_fence(text: str) -> str:
        text = text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```[a-zA-Z0-9_-]*\n?", "", text)
            if text.endswith("```"):
                text = text[: text.rfind("```")]
        return text.strip()

    def try_parse(candidate: str):
        if not candidate:
            return None
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            try:
                return ast.literal_eval(candidate)
            except Exception:
                return None

    def extract_block(text: str) -> str | None:
        stack = []
        start = None
        openers = {"{": "}", "[": "]"}
        closers = {"}": "{", "]": "["}
        for idx, ch in enumerate(text):
            if ch in openers and start is None:
                start = idx
                stack.append(ch)
            elif ch in openers:
                stack.append(ch)
            elif ch in closers and stack:
                expected = closers[ch]
                if stack[-1] == expected:
                    stack.pop()
                    if not stack and start is not None:
                        return text[start : idx + 1]
        return None

    def extract_segments(text: str):
        decoder = json.JSONDecoder()
        segments = []
        idx = 0
        length = len(text)
        while idx < length:
            match = re.search(r"[\{\[]", text[idx:])
            if not match:
                break
            start = idx + match.start()
            try:
                obj, end = decoder.raw_decode(text[start:])
                segments.append(obj)
                idx = start + end
            except json.JSONDecodeError:
                idx = start + 1
        return segments

    stripped = strip_code_fence(response)
    parsed = try_parse(stripped)
    if parsed is not None:
        return parsed

    block = extract_block(stripped)
    parsed = try_parse(block)
    if parsed is not None:
        return parsed

    segments = extract_segments(stripped)
    if not segments:
        return None
    if len(segments) == 1:
        return segments[0]
    return segments
