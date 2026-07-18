"""
Helper for answering inline queries (telegram.InlineQuery.answer). This is a
much smaller surface than regular messages - src/chat/inline_query/inline_query_manager.py
is the only caller in the whole codebase.
"""

from ._markdown import markdown_v2_to_html
from ._keyboard import convert_markup_to_buttons


async def build_and_answer_inline_query(event, results, **kwargs):
    built = []
    for r in results:
        text = r.input_message_content.message_text if r.input_message_content else r.title
        html_text = markdown_v2_to_html(text)
        built.append(
            event.builder.article(
                title=r.title,
                description=r.description,
                text=html_text,
                parse_mode="html",
                buttons=convert_markup_to_buttons(r.reply_markup),
                id=r.id,
                thumb=r.thumbnail_url,
            )
        )
    await event.answer(built)
