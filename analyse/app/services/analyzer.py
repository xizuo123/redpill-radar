import json
import logging

from groq import AsyncGroq
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import CategoryConfig
from app.schemas import AnalysisResult

logger = logging.getLogger(__name__)

_client: AsyncGroq | None = None


def _get_client() -> AsyncGroq:
    global _client
    if _client is None:
        _client = AsyncGroq(api_key=settings.groq_api_key)
    return _client


async def _build_category_context(db: AsyncSession) -> dict[str, list[str]]:
    """Fetch active categories from DB grouped by category_group."""
    result = await db.execute(
        select(CategoryConfig).where(CategoryConfig.is_active.is_(True))
    )
    rows = result.scalars().all()

    groups: dict[str, list[str]] = {}
    for row in rows:
        groups.setdefault(row.category_group, []).append(row.category_value)
    return groups


def _build_prompt(category_groups: dict[str, list[str]], content_text: str) -> str:
    category_lines = []
    for group, values in category_groups.items():
        label = group.replace("_", " ").title()
        category_lines.append(f"- {label}: [{', '.join(values)}]")

    categories_block = "\n".join(category_lines) if category_lines else (
        "- Age Category: [12-18, 18+]\n"
        "- Content Type: [safe, harmful]\n"
        "- Harmful Subcategory: [female_abuse, female_sexual_content]"
    )

    return f"""Analyze the following social media content for harmful or hateful speech targeting women/females.

Classify the content using EXACTLY these categories:
{categories_block}

Rules:
1. A piece of content can be assigned MULTIPLE harmful subcategories if applicable.
2. Age category refers to the likely age group of the target audience or victim.
3. If the content is safe, harmful_subcategories should be an empty list.
4. Provide a confidence score between 0.0 and 1.0.
5. Provide brief reasoning for your classification.

You MUST respond with valid JSON only, no extra text. Use this exact structure:
{{
  "age_category": "<one of the age category values>",
  "content_type": "<safe or harmful>",
  "harmful_subcategories": ["<subcategory1>", "<subcategory2>"],
  "confidence": 0.0,
  "reasoning": "<brief explanation>"
}}

Content to analyze:
\"{content_text}\""""


async def analyze_content(
    content_text: str, db: AsyncSession
) -> tuple[AnalysisResult, dict]:
    """
    Analyze content via Groq LLM.

    Returns (parsed_result, raw_response_dict).
    """
    category_groups = await _build_category_context(db)
    prompt = _build_prompt(category_groups, content_text)

    client = _get_client()

    try:
        chat_completion = await client.chat.completions.create(
            model=settings.groq_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a content moderation specialist focused on "
                        "detecting harmful or hateful content targeting women and girls. "
                        "Always respond with valid JSON only."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=1024,
            response_format={"type": "json_object"},
        )

        raw_text = chat_completion.choices[0].message.content or "{}"
        raw_dict = json.loads(raw_text)

        result = AnalysisResult(
            age_category=raw_dict.get("age_category"),
            content_type=raw_dict.get("content_type"),
            harmful_subcategories=raw_dict.get("harmful_subcategories", []),
            confidence=float(raw_dict.get("confidence", 0.0)),
            reasoning=raw_dict.get("reasoning", ""),
        )

        raw_response = {
            "model": settings.groq_model,
            "usage": {
                "prompt_tokens": chat_completion.usage.prompt_tokens,
                "completion_tokens": chat_completion.usage.completion_tokens,
                "total_tokens": chat_completion.usage.total_tokens,
            }
            if chat_completion.usage
            else None,
            "raw_output": raw_dict,
        }

        return result, raw_response

    except Exception:
        logger.exception("Groq analysis failed")
        raise
