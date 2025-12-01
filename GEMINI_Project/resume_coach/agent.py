"""Resume reading and coaching agent (lightweight helpers).

Provides parsing, matching and suggestion helpers for tailoring a resume
to a job description. These functions are deterministic and don't require
an LLM; the CLI can optionally invoke an LLM to produce richer rewrites.
"""
from typing import List, Dict, Tuple
import re

VERB_KEYWORDS = [
    "managed", "led", "developed", "designed", "implemented", "built", "created",
    "improved", "optimized", "automated", "reduced", "increased", "delivered",
]


def _lines(text: str) -> List[str]:
    return [l.strip() for l in (text or '').splitlines() if l.strip()]


def parse_resume(text: str) -> Dict:
    lines = _lines(text)
    summary_lines = []
    skills = []
    experience = []

    section = None
    for line in lines:
        llow = line.lower()
        if re.match(r'^(skills|technical skills|skillset)[:\- ]', llow) or llow == 'skills':
            section = 'skills'
            continue
        if re.match(r'^(experience|work experience|professional experience)[:\- ]', llow) or llow == 'experience':
            section = 'experience'
            continue
        if re.match(r'^(summary|profile|professional summary)[:\- ]', llow) or llow == 'summary':
            section = 'summary'
            continue

        if section == 'skills':
            parts = re.split(r'[;,|]', line)
            for p in parts:
                val = p.strip()
                if val:
                    skills.append(val)
            continue

        if section == 'experience':
            experience.append(line)
            continue

        if line.startswith(('-', '•', '*')) or any(v in llow for v in VERB_KEYWORDS):
            experience.append(line.lstrip('-•* ').strip())
            continue

        if len(summary_lines) < 3 and len(line.split()) < 40:
            summary_lines.append(line)

    summary = ' '.join(summary_lines).strip()
    return {'summary': summary, 'skills': skills, 'experience': experience}


def parse_jd(text: str) -> Dict:
    lines = _lines(text)
    title = lines[0] if lines else ''
    skills = []
    responsibilities = []
    section = None
    for line in lines[1:]:
        llow = line.lower()
        if 'skills' in llow or 'requirements' in llow or 'technologies' in llow:
            section = 'skills'
            continue
        if 'responsibil' in llow or 'what you will' in llow:
            section = 'responsibilities'
            continue

        if section == 'skills':
            parts = re.split(r'[;,|]', line)
            for p in parts:
                val = p.strip()
                if val:
                    skills.append(val)
            continue

        if section == 'responsibilities':
            responsibilities.append(line)
            continue

        if ',' in line and len(line) < 120:
            parts = [p.strip() for p in line.split(',') if p.strip()]
            if len(parts) > 1:
                skills.extend(parts)

    return {'title': title, 'skills': skills, 'responsibilities': responsibilities}


def match_and_score(resume: Dict, jd: Dict) -> Tuple[float, List[str]]:
    resume_skills = {s.lower() for s in resume.get('skills', [])}
    jd_skills = {s.lower() for s in jd.get('skills', [])}
    if not jd_skills:
        return 0.0, []
    matched = resume_skills.intersection(jd_skills)
    missing = sorted(list(jd_skills - resume_skills))
    score = 100.0 * len(matched) / len(jd_skills)
    return round(score, 1), missing


def suggest_resume_updates(resume: Dict, jd: Dict, max_suggestions: int = 6) -> Dict:
    title = jd.get('title', '')
    suggested_summary = resume.get('summary', '')
    if title:
        suggested_summary = f"{title} - {suggested_summary}" if suggested_summary else f"{title} candidate with relevant experience."

    _, missing = match_and_score(resume, jd)
    add_skills = missing[:10]

    rewritten = []
    for b in resume.get('experience', [])[:max_suggestions]:
        nums = re.findall(r"\d+[\.,]?\d*%?|\d+", b)
        if nums:
            rewritten.append(b if len(b) < 240 else b[:240] + '...')
            continue
        rewritten.append(b + ' (include quantifiable impact, e.g., reduced X by Y% or improved throughput by N)')

    return {'suggested_summary': suggested_summary, 'add_skills': add_skills, 'rewritten_experience': rewritten}


def generate_coaching_questions(jd: Dict, n: int = 8) -> List[Dict]:
    skills = jd.get('skills', [])
    responsibilities = jd.get('responsibilities', [])
    questions = []

    for s in (skills[:n] if skills else []):
        q = f"Can you describe your experience with {s}?"
        tip = f"Mention specific projects, your role, technologies used, and outcomes or metrics."
        questions.append({'question': q, 'tip': tip})

    for r in responsibilities[:max(0, n - len(questions))]:
        q = f"Tell me about a time you {r.strip('.').lower()}"
        tip = "Use STAR (Situation, Task, Action, Result) and quantify results when possible."
        questions.append({'question': q, 'tip': tip})

    while len(questions) < n:
        questions.append({'question': 'Describe a technical challenge you solved recently.', 'tip': 'Explain trade-offs, your approach, and measurable outcome.'})

    return questions


def tailor_resume_text(original_text: str, suggestions: Dict) -> str:
    lines = _lines(original_text)
    out = []
    if suggestions.get('suggested_summary'):
        out.append(suggestions['suggested_summary'])
        out.append('')

    if suggestions.get('add_skills'):
        out.append('Skills:')
        out.append(', '.join(suggestions['add_skills']))
        out.append('')

    replaced = 0
    max_replace = len(suggestions.get('rewritten_experience', []))
    for line in lines:
        if replaced < max_replace and (line.startswith('-') or any(v in line.lower() for v in VERB_KEYWORDS)):
            out.append('- ' + suggestions['rewritten_experience'][replaced])
            replaced += 1
            continue
        out.append(line)

    if replaced < max_replace:
        out.append('')
        out.append('Experience (suggested improvements):')
        for i in range(replaced, max_replace):
            out.append('- ' + suggestions['rewritten_experience'][i])

    return '\n'.join(out)


if __name__ == '__main__':
    print('Resume coach helpers available.')
