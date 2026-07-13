"""
Helper for answering inline queries (telegram.InlineQuery.answer). This is a
much smaller surface than regular messages - src/chat/inline_query/inline_query_manager.py
is the only caller in the whole codebase.

Note: inline query results are rendered as plain text (MarkdownV2 markup is
stripped rather than converted to entities) - see MIGRATION_NOTES.md.
"""

from ._markdown import parse_markdown_v2
from ._keyboard import convert_markup_to_buttons


async def build_and_answer_inline_query(event, results, **kwargs):
    built = []
    for r in results:
        text = r.input_message_content.message_text if r.input_message_content else r.title
        plain_text, _entities = parse_markdown_v2(text)
        built.append(
            event.builder.article(
                title=r.title,
                description=r.description,
                text=plain_text,
                parse_mode=None,
                buttons=convert_markup_to_buttons(r.reply_markup),
                id=r.id,
                thumb=r.thumbnail_url,
            )
        )
    await event.answer(built)
