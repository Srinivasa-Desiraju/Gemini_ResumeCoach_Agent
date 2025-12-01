#!/usr/bin/env python3
"""Simple CLI for the Resume Coach Agent."""
import argparse
import json
from pathlib import Path

from src.resume_coach.agent import parse_resume, parse_jd, suggest_resume_updates, match_and_score, generate_coaching_questions, tailor_resume_text
from src.resume_coach.llm import call_gemini_flash
import os


def load_text(path_or_text: str) -> str:
    p = Path(path_or_text)
    if p.exists():
        return p.read_text(encoding='utf-8')
    return path_or_text


def main():
    p = argparse.ArgumentParser(description='Resume Coach Agent - tailor resume and generate coaching tips')
    p.add_argument('--resume', '-r', required=True, help='Path to resume text file or paste resume text')
    p.add_argument('--jd', '-j', required=True, help='Path to job description text file or paste JD text')
    p.add_argument('--out', '-o', help='Output tailored resume path (defaults to tailored_resume.txt)', default='tailored_resume.txt')
    args = p.parse_args()

    resume_text = load_text(args.resume)
    jd_text = load_text(args.jd)

    resume = parse_resume(resume_text)
    jd = parse_jd(jd_text)

    score, missing = match_and_score(resume, jd)
    suggestions = suggest_resume_updates(resume, jd)
    coaching = generate_coaching_questions(jd)

    # If GOOGLE_API_KEY is present, call Gemini Flash 2.5 to produce a tailored resume.
    tailored = None
    if os.environ.get('GOOGLE_API_KEY'):
        prompt = (
            "Tailor the resume below to the job description. Produce a concise, professional, and ATS-friendly resume "
            "that highlights relevant skills and quantifiable achievements. Keep formatting as plain text.\n\n"
            "JOB DESCRIPTION:\n" + jd_text + "\n\nRESUME:\n" + resume_text + "\n\n" 
            "Make changes only to wording (do not invent credentials). If information is missing, add suggested skill lines prefixed with 'Suggested Skill:'.\n"
        )
        llm_out = call_gemini_flash(prompt)
        # If LLM returned an error-like string, fall back to heuristic tailoring
        if llm_out and not llm_out.startswith('LLM request failed') and 'failed' not in llm_out.lower():
            tailored = llm_out

    if not tailored:
        tailored = tailor_resume_text(resume_text, suggestions)

    Path(args.out).write_text(tailored, encoding='utf-8')

    output = {
        'match_score': score,
        'missing_skills': missing,
        'suggestions': suggestions,
        'coaching_questions': coaching,
        'tailored_resume_path': str(Path(args.out).resolve())
    }

    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
