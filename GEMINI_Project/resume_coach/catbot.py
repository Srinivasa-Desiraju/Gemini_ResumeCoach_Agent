"""CatBot: an assistant that uses Gemini Flash to coach a candidate for a job.

CatBot composes careful prompts combining the job description and resume,
then calls the `call_gemini_flash` wrapper to get coaching guidance, interview
questions, and feedback on sample answers. This module keeps prompts explicit
so the behavior is easy to iterate on.
"""
from typing import Optional
import os
from .llm import call_gemini_flash

DEFAULT_MODEL = 'gemini-2.5-flash'


def _build_coaching_prompt(jd_text: str, resume_text: str, n_questions: int = 6) -> str:
    return (
        "You are CatBot, an expert interview coach. Provide concise, actionable coaching "
        "for the candidate given the Job Description and Resume below.\n\n"
        "Instructions:\n"
        "- Produce an ordered list of the top {n} likely interview questions tailored to the JD.\n"
        "- For each question, provide a 2-3 sentence model answer structure (STAR format) and a 1-2 sentence coaching tip.\n"
        "- Provide a short (3-5) point checklist of resume improvements specific to the JD (what to emphasize, which metrics to add).\n"
        "- Keep responses plain text and clearly labeled (Question, Model Answer, Tip, Resume Checklist).\n"
        "- Do NOT invent credentials, dates, or companies. If information is missing, suggest how the candidate could phrase hypothetical improvements using terms like 'If applicable, mention...'.\n\n"
        "JOB DESCRIPTION:\n" + jd_text + "\n\nRESUME:\n" + resume_text + "\n\n"
    ).replace('{n}', str(n_questions))


def coach_candidate(jd_text: str, resume_text: str, n_questions: int = 6, api_key: Optional[str] = None, model: str = DEFAULT_MODEL) -> str:
    """Run CatBot and return the coaching text produced by the model.

    Uses the environment `GOOGLE_API_KEY` if `api_key` is not provided.
    """
    api_key = api_key or os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        raise RuntimeError('GOOGLE_API_KEY required for CatBot to call Gemini Flash')

    prompt = _build_coaching_prompt(jd_text, resume_text, n_questions=n_questions)
    # Ask Gemini Flash for a focused coaching output
    return call_gemini_flash(prompt=prompt, api_key=api_key, model=model, max_output_tokens=1024, temperature=0.15)


if __name__ == '__main__':
    print('CatBot is a module; call coach_candidate(jd_text, resume_text).')
