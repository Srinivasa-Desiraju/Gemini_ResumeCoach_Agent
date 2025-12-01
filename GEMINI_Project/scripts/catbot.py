#!/usr/bin/env python3
"""CLI wrapper to run CatBot coaching via Gemini Flash (API key required)."""
import argparse
import json
from pathlib import Path
import os

from src.resume_coach.catbot import coach_candidate


def load_text(path_or_text: str) -> str:
    p = Path(path_or_text)
    if p.exists():
        return p.read_text(encoding='utf-8')
    return path_or_text


def main():
    p = argparse.ArgumentParser(description='CatBot - coaching assistant using Gemini Flash')
    p.add_argument('--resume', '-r', required=True, help='Path to resume text file or paste resume text')
    p.add_argument('--jd', '-j', required=True, help='Path to job description text file or paste JD text')
    p.add_argument('--questions', '-n', type=int, default=6, help='Number of tailored questions to generate')
    p.add_argument('--out', '-o', help='Output file for coaching text (defaults to catbot_coaching.txt)', default='catbot_coaching.txt')
    p.add_argument('--api-key', help='Optional: provide GOOGLE_API_KEY here; otherwise the environment is used')
    args = p.parse_args()

    resume_text = load_text(args.resume)
    jd_text = load_text(args.jd)

    api_key = args.api_key or os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        print('ERROR: GOOGLE_API_KEY must be set in the environment or provided with --api-key')
        raise SystemExit(1)

    output_text = coach_candidate(jd_text=jd_text, resume_text=resume_text, n_questions=args.questions, api_key=api_key)

    Path(args.out).write_text(output_text, encoding='utf-8')
    print(json.dumps({'coaching_path': str(Path(args.out).resolve())}, ensure_ascii=False))


if __name__ == '__main__':
    main()
