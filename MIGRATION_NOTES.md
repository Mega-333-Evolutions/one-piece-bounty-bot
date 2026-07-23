# Migration notes: python-telegram-bot &rarr; Telethon

This codebase has been fully converted from `python-telegram-bot` (PTB) to
[Telethon](https://docs.telethon.dev/). `python-telegram-bot` is no longer a
dependency anywhere in the project - every Telegram API call, from sending a
message to checking whether someone is a group admin, now goes through
Telethon's `TelegramClient`.

## Why a compatibility layer, not a line-by-line rewrite

This is a large codebase: 288 Python files, ~54,000 lines, and PTB's
`Update` / `CallbackContext` objects are threaded through nearly all of it -
not just the top-level handlers, but deep into ~150 screen files and every
service module, via a central `src/service/message_service.py` that all
message sending funnels through.

Rewriting every one of those 288 files to use Telethon's native idioms
(`events.NewMessage.Event`, `client.send_message()`, etc.) directly would
mean touching business logic (crews, devil fruits, bounties, predictions,
games...) in every single file, with no way to test-run the result against a
real bot token in this environment. That's a lot of surface area for
something that has nothing to do with *what the bot does* and everything to
do with *which library it talks through*.

Instead, `src/tg_compat/` is a compatibility layer: it implements the same
`Update`, `CallbackContext`, `InlineKeyboardMarkup`, error classes, etc. that
PTB provided, but every one of them is backed entirely by Telethon under the
hood - `python-telegram-bot` is not installed, not imported, and not
referenced anywhere in the final code. All 138 files that used to
`from telegram import ...` now `from src.tg_compat import ...` instead (a
mechanical, one-line-per-import change - see `git diff` on any screen file
for what that looks like). The business logic inside those files - the part
that actually implements the game - is untouched.

This is the same "adapter/strangler-fig" approach a human engineering team
would use to migrate a codebase this size safely, and it has a real
advantage over a full rewrite beyond just risk: it was possible to audit
*every* `telegram.*` symbol, every `context.bot.*` call, and every
`update.*`/`.effective_*` attribute access across the whole codebase (see
"How this was verified" below) and confirm each one is handled, which
wouldn't have been feasible to do with equal confidence across 288
independently-rewritten files.

## What's new / what you need to do

### 1. Get a Telegram API id/hash pair

Telethon talks to Telegram's MTProto API directly, rather than going through
the Bot API's HTTP layer like PTB did. That means it needs the same
`api_id`/`api_hash` pair any Telegram client uses, in addition to the bot
token:

1. Go to <https://my.telegram.org>, log in, and open "API Development
   tools".
2. Create an application (any name/platform is fine) and copy the `App
   api_id` and `App api_hash`.
3. Add them to your `.env`:
   ```
   API_ID=12345
   API_HASH=0123456789abcdef0123456789abcdef
   ```

`environment/env.example` and `README.md` have been updated to mention
these.

### 2. Install the new dependency

`requirements.txt` now has `Telethon>=1.40,<2.0` instead of
`python-telegram-bot[rate-limiter]==22.7`. Everything else is unchanged.

### 3. Session file

On first run, Telethon will create a `one_piece_bot.session` file (SQLite)
next to `main.py` to persist your login so it doesn't need to re-authenticate
every restart. `.gitignore` has been updated to exclude `*.session` /
`*.session-journal`. Treat this file like a credential (anyone with it can
act as your bot) - back it up if you care about not re-creating it, but it's
not required for the bot to work (a fresh one is created automatically).

### 4. Test before deploying

I was not able to run this bot against a live Telegram connection or install
Telethon in this environment to test it end-to-end (no network access here) -
everything below was verified statically (syntax, real imports against a
hand-written Telethon stub matching its documented API, and a full audit of
every Telegram API touchpoint in the codebase - see the next section). I'd
recommend running it against a test bot/group before pointing it at
production, in particular exercising: sending/editing messages with
keyboards in both private chats and groups, a full game flow (e.g. `/fight`),
crew creation/invites, and whatever forum-topic groups you use if any.

## How this was verified

Since Telethon couldn't be installed in this environment, correctness was
checked without execution, in three layers:

1. **Every file compiles.** `python -m py_compile` across all 302 files
   (288 original + 14 new in `src/tg_compat/`) - catches syntax errors.
2. **Every file actually imports.** A hand-written stub package mirroring
   Telethon's and APScheduler's real API surface (classes, method
   signatures) was used to import all 302 files for real, catching
   `ImportError`/`NameError`/`AttributeError` - e.g. a typo in what
   `src/tg_compat/__init__.py` exports vs. what a screen file imports would
   show up here. All 302 import cleanly.
3. **Every `context.bot.*` call site was cross-checked.** Every call to a
   `Bot` method anywhere in the codebase was extracted (via AST, not regex)
   and its keyword arguments were checked against `Bot`'s actual method
   signatures in `src/tg_compat/_bot.py`. The only mismatches found were
   `read_timeout`/`write_timeout` (PTB-specific HTTP transport tuning that
   doesn't apply to Telethon's persistent MTProto connection - see below),
   which are intentionally accepted-and-ignored.

What this *can't* catch: whether my understanding of Telethon's actual
method signatures and behavior (`send_file`, `edit_message`,
`get_permissions`, error class names, etc.) is 100% correct, since there's
no real Telethon install here to check against. I'm reasonably confident in
these (they're stable, well-documented, long-standing parts of the library),
but this is the main reason to test against a real bot token before
deploying.

## Architecture of `src/tg_compat/`

| File | Mirrors | Purpose |
|---|---|---|
| `__init__.py` | `telegram` | `Update`, `Message`, `Chat`, `User`, keyboard/media/inline-query classes |
| `ext.py` | `telegram.ext` | `ContextTypes`, `CallbackContext`, `Application`, `Job`, `JobQueue` |
| `error.py` | `telegram.error` | `BadRequest`, `Forbidden`, `TimedOut`, `NetworkError`, `RetryAfter`, `ChatMigrated` |
| `constants.py` | `telegram.constants` | `ChatMemberStatus` |
| `helpers.py` | `telegram.helpers` | `mention_markdown` |
| `_types.py` | - | `Chat`/`User`/`PhotoSize`/`ChatMember`/etc. implementations |
| `_message.py` | - | `Message`/`Update`/`CallbackQuery`/`InlineQuery` implementations, built from real Telethon events |
| `_bot.py` | - | The `Bot` class - all 14 `context.bot.*` methods used in the codebase, implemented via Telethon |
| `_keyboard.py` | - | `InlineKeyboardButton`/`Markup`, `InputMedia*`, `InlineQueryResult*` |
| `_markdown.py` | - | Converts this codebase's MarkdownV2 into HTML for Telethon's own parser - see "Hyperlinks and user mentions" below |
| `_mentions.py` | - | Pre-resolves user mentions before sending, degrading gracefully to plain text if a user can't be resolved - see below |
| `_jobqueue.py` | - | `Job`/`JobQueue`, a thin wrapper directly around APScheduler (already a project dependency) |
| `_errors.py` | - | Translates Telethon/MTProto errors into `telegram.error` equivalents |
| `_inline.py` | - | Answering inline queries |
| `runtime.py` | - | `Application`/`Context`, and the code that turns real Telethon events into `Update`/`Context` objects |

`main.py` is the only "business logic" file that changed substantially -
it now builds a Telethon `TelegramClient` instead of a PTB `Application`,
but `pre_init()`, `post_init()`, logging, and Sentry setup are all unchanged.

## MarkdownV2 rendering

The codebase formats all its text in Bot API's MarkdownV2 dialect (see
`constants.TG_DEFAULT_PARSE_MODE`, and the `escape_valid_markdown_chars` /
`escape_invalid_markdown_chars` helpers in `message_service.py`). Telethon
ships its own markdown dialect with different escaping rules, so feeding
already-Bot-API-escaped text into Telethon's own markdown parser would leave
stray backslashes visible to users - `src/tg_compat/_markdown.py` instead
converts Bot API's exact MarkdownV2 dialect into HTML, and sends with
`parse_mode='html'`. See "Hyperlinks and user mentions" below for the full
detail on this (it went through a couple of iterations - that section
explains the current, working approach and why it replaced an earlier one).

## Bugs found after the first real deployment (now fixed)

The first version of this conversion was written and validated entirely
statically (no Telethon install, no live bot) - see "How this was verified"
above for why. After deploying it against a real bot token, several real
bugs turned up. All are now fixed; each is documented here because they're
genuine gaps in my original reasoning, not hypothetical edge cases, and
knowing the mechanism matters if something similar turns up later.

- **Images/videos/animations were sending as generic "unnamed" file
  attachments instead of rendering inline.** Root cause: Telethon decides
  whether an upload is a photo or a generic document by looking at the
  *file name extension* (`telethon.utils.is_image()` just checks the
  extension, it doesn't inspect the bytes) - and the freshly-uploaded-bytes
  case in `Bot._resolve_media_input()` was wrapping raw bytes in a bare
  `io.BytesIO` with no `.name` set at all. Fixed by giving that `BytesIO` a
  synthetic name with the right extension (`.jpg` for photos, `.mp4` for
  video/animation) before handing it to `send_file()`.
- **`/status` (and anything else that downloads a replied-to user's profile
  photo for the bounty poster) crashed with `PIL.UnidentifiedImageError`.**
  Root cause: handing a bare `Photo` object (as returned by
  `get_profile_photos()`) directly to `download_media()` is a
  [known Telethon rough edge](https://github.com/LonamiWebs/Telethon/issues/1519) -
  it can end up downloading a tiny/placeholder thumbnail representation
  instead of the full photo, which isn't a file PIL can open. Fixed by
  switching to `client.download_profile_photo(user, file=path,
  download_big=True)` - Telethon's purpose-built method for exactly this -
  instead of the more manual `get_profile_photos()` + `download_media()`
  chain.
- **Edited messages (captions specifically) were losing all MarkdownV2
  formatting** - showing up with literal backslashes, asterisks, and raw
  `tg://user?id=` link syntax instead of rendering bold/links/mentions (the
  Doc Q screenshot). Root cause: python-telegram-bot has an
  Application-wide default parse mode (`Defaults(parse_mode=...)`, configured
  in the original `main.py`) that silently kicks in for any call that
  doesn't explicitly pass `parse_mode`. `Bot.edit_message_caption()`'s one
  call site in `message_service.py` was relying on exactly that fallback and
  never passed `parse_mode` explicitly - which worked fine under PTB, but my
  compat `Bot` class had no equivalent fallback and defaulted to `None` (no
  parsing) instead. Fixed by giving `parse_mode` the same
  `"MarkdownV2"` default PTB effectively had, everywhere text is sent or
  edited (`send_message`, `edit_message_text`, `edit_message_caption`,
  `send_photo`, `send_video`, `send_animation`, and `InputMedia`'s own
  default for the `edit_message_media` path) - so any current or future call
  site that omits `parse_mode` now behaves the way it did under PTB, instead
  of silently sending raw markup.
- **`reward.message_id = message.id` crashed with `AttributeError`** (daily
  reward screens), which also explains the follow-up "chat_id and message_id
  must be specified to delete message" error a minute later in the same
  log - that reward's message_id was never saved because of the crash, so
  the later attempt to delete/edit that message had nothing to work with.
  PTB added `Message.id` as an alias for `Message.message_id` (for
  consistency with `Chat.id`/`User.id`) at some point, and several newer
  screens in this codebase (daily reward, devil fruit trade, RPS/RR games)
  use `.id` rather than `.message_id`. Fixed by adding `.id` as a property
  alias on the compat `Message` class.
- **Colored buttons still wouldn't show up even after the Bot API 9.4
  support was added.** This one was my own bug, not a Telethon gap: real
  PTB's `InlineKeyboardButton(text, api_kwargs={"style": "success"})` nests
  the style *inside* an `api_kwargs` dict (that's literally what
  `api_kwargs` is - a bucket of extra fields merged into the Bot API JSON
  request), but my style-lookup code was checking for a top-level `style`
  key instead of `extra["api_kwargs"]["style"]`, so it silently never found
  a style to apply. Fixed the lookup to check inside `api_kwargs` first.
- **Most group commands (`/settings`, `/add`, and effectively anything
  requiring a response from `group_chat_manager.py`) silently did nothing,
  and the "thanks for adding me" welcome message never sent.** This was the
  big one. `group_chat_manager.py`'s very first step on *every* group
  message checks whether it's a join/leave event via
  `update.message.new_chat_members[0].id == ...`, wrapped in
  `except (AttributeError, IndexError)` - which only makes sense (and only
  ever worked) because PTB guarantees `Message.new_chat_members` is always
  at least an empty tuple, never `None`, so indexing `[0]` on an ordinary
  message raises `IndexError` (caught) rather than crashing. My compat
  `Message` defaulted it to `None` instead (unlike `.photo`, which I did
  correctly default to `[]`) - so on every regular group message, that same
  line raised `TypeError: 'NoneType' object is not subscriptable`, which
  *isn't* one of the caught exception types. That exception then propagated
  up to `manage_after_db`'s catch-all `except Exception`, got logged, and
  the message was dropped with no response - before command dispatch, the
  admin check, or anything else ever ran. Every group interaction that
  needed `group_chat_manager.py` to actually respond was affected; things
  that don't touch it (or that you tested in private chat) were fine, which
  is why it looked like only specific commands were broken rather than
  groups being broken outright. Fixed by defaulting `new_chat_members` to
  `()`, matching what PTB actually guarantees.
- **Games (Guess or Life, Who's Who, Punk Records, Shambles) sent no
  initial hint, and no follow-up hints after their interval (30s/60s
  depending on the game).** These games run their hint loop entirely via
  `context.application.create_task(...)` - an initial send, then
  `await asyncio.sleep(hint_wait_seconds)`, then the function calls itself
  again to repeat. My `Application.create_task()` wrapped the coroutine in
  `asyncio.ensure_future()` and returned it, same as every call site in the
  codebase does - discarding the return value, since none of them need to
  await or track it themselves. That's the exact pattern
  [Python's own asyncio docs warn against](https://docs.python.org/3/library/asyncio-task.html#asyncio.create_task):
  a task with nothing holding a strong reference to it can be garbage
  collected before it finishes, "even before it's done" - and the longer a
  task stays suspended, the bigger that window gets. A quick fire-and-send
  task might survive by luck; a task suspended in `asyncio.sleep(30)` or
  `asyncio.sleep(60)` had a much larger window to get swept away mid-wait,
  which matches exactly what was reported (the recursive nature of the hint
  loop meant that once one iteration got collected, every hint after it
  silently stopped too). Fixed by having `Application` hold a strong
  reference to every task it creates in a set, removing it via
  `add_done_callback` once it completes - the standard fix for this,
  confirmed with a test that forces a GC pass mid-`asyncio.sleep()` and
  checks the task is still tracked and still completes.
- **Scheduled jobs and the game hint loop crashed with `ValueError: Cannot
  get entity by phone number as a bot`, and the games issue turned out to
  have a second cause on top of the task GC one above.** `User.tg_user_id`
  (and `Group.tg_group_id`) are stored as `CharField` - plain strings - and
  this codebase passes them as `chat_id` more or less interchangeably with
  actual ints throughout (`full_message_send`'s `chat_id` parameter is
  explicitly typed `int | str`). Bot API's HTTP/JSON transport never cared
  either way, but Telethon's entity resolution does: given a bare numeric
  *string* rather than an int, it doesn't recognize "this is just an ID" -
  it tries to resolve it the way a real user account would (username, phone
  number, ...), and a bot account is forbidden from doing that kind of
  lookup at all, so it fails with `BotMethodInvalidError` wrapped in a
  confusing `ValueError`. This hit every `context.bot.*` call anywhere a
  string id was passed - including the games' `chat_id=u.tg_user_id` in
  their hint loop, which explains why fixing the task-GC issue alone didn't
  fully fix them: the very first send in the chain was throwing before ever
  reaching the sleep-and-recurse step, so the chain never got anywhere,
  independent of whether the task itself survived. Fixed with a
  `coerce_peer()` helper, applied everywhere a chat/user id reaches
  Telethon (`Bot`'s methods, `Message.forward()`, chat-member lookups) -
  any string that's actually just a plain (optionally negative) integer
  gets converted to a real `int`; anything else (usernames, already-resolved
  entities) passes through unchanged. Verified end-to-end with a test that
  calls `Bot.send_message(chat_id='1001484109', ...)` (a string, exactly how
  the game code calls it) and confirms Telethon's own `send_message`
  receives a real `int`.

If you deploy this and hit something that looks similarly "off," the most
useful thing to send back is the exact command/action plus the traceback or
a screenshot - that's what made all of these findable.

## Correction: button colors are real, and now implemented

My first pass of this migration said the `style` field
`src/utils/button_style_utils.py` attaches to buttons (`api_kwargs={"style":
...}`) had no real effect, on the assumption that Bot API has no per-button
color field. That assumption was wrong, and post-dates my training data
either way: **Bot API 9.4 (February 9, 2026) added a real `style` field to
`InlineKeyboardButton`**, letting bots color buttons red/green/blue
(danger/success/primary) - which is exactly what `api_kwargs={"style":
...}` was already doing under python-telegram-bot (PTB hadn't added a typed
parameter for it yet, so `api_kwargs` - PTB's escape hatch for
not-yet-wrapped Bot API fields - was the correct way to reach it even in
the original bot).

This is now properly implemented in `src/tg_compat/_keyboard.py`: buttons
are sent using the raw MTProto `KeyboardButtonStyle` type
(`bg_success`/`bg_danger`/`bg_primary`) Telegram introduced alongside the
Bot API field. If your installed Telethon version's bundled schema doesn't
have this field yet, it's caught and the button is sent without a color
rather than failing the whole send - check your logs for a
`tg_compat: this Telethon version doesn't support colored buttons` warning
if colors don't show up; that means it's worth updating Telethon.

## Hyperlinks and user mentions - architectural change

Two previous rounds of fixes here (sorting entities, normalizing URLs) did
not resolve reports that hyperlinks still weren't rendering. Rather than
continue hypothesis-by-hypothesis against the earlier approach - hand-
constructing raw `telethon.tl.types.MessageEntity*` objects and passing them
via `formatting_entities=`, bypassing Telethon's own parser entirely - this
round replaces that approach altogether.

**What changed:** `src/tg_compat/_markdown.py` now converts this codebase's
MarkdownV2 into HTML, and every send/edit call uses `parse_mode='html'`
instead of hand-built entities. Telethon ships its own HTML parser
(`telethon/extensions/html.py`) - the same code every other Telethon-based
bot relies on - which handles the actual entity construction, including the
access-hash resolution mentions need. This removes an entire class of "did I
build the exact right binary protocol object" bugs that hand-rolling raw TL
entities was exposed to, in favor of generating a string (HTML) that's
trivial to read and verify correctness of directly, and letting mature,
widely-used library code do the rest.

Every construct maps onto a plain HTML tag: `*bold*` → `<b>`, `_italic_` →
`<i>`, `__underline__` → `<u>`, `~strike~` → `<s>`, `` `code` `` → `<code>`,
` ```lang ` blocks → `<pre><code class="language-lang">`, spoilers →
`<tg-spoiler>`, and `>quoted` blocks → `<blockquote>` (or
`<blockquote expandable>` for this codebase's `||`-suffixed expandable-quote
convention). Links and mentions both become `<a href="...">` - a regular
`https://` URL for links, `tg://user?id=X` for mentions - exactly the
mechanism confirmed in Telethon's own changelog ("Support
`<a href="tg://user?id=123">` mentions in HTML parse mode"), and exactly
the syntax you pointed me to. Nesting (a link inside a blockquote, bold
inside a link, etc.) falls out naturally from properly nested tags instead
of needing manual offset/length bookkeeping, which is also what made the
earlier approach hard to get fully right.

Tested directly against every construct this codebase actually uses,
including the full real `SHOW_USER_STATUS` message reconstructed field-for-
field (mention, bold bounty figures, an emoji-containing rank, a crew
deeplink, and an expandable-quoted location) - the HTML output is correct
and, unlike the old entity-offset approach, is something you can just read
to confirm: `User: <a href="tg://user?id=1001484109">Bharath</a>` /
`Crew: <a href="https://t.me/OnePieceBot?start=abc123">Jolly Pirates</a>` /
`<blockquote expandable>Location: Sabaody Archipelago</blockquote>`.

**Mentions specifically - the access-hash problem you flagged is real, and
now has two layers of defense:**

Constructing a working inline mention requires the sending account to know
the target user's access_hash, which Telegram only ever provides once the
bot has "encountered" that user somehow (a message, a shared chat, a
callback query - an ID alone is never enough; see
https://docs.telethon.dev/en/stable/concepts/entities.html). This is true
regardless of markdown vs. HTML vs. raw entities - it's a property of how
Telegram's API works, not something either parsing approach can bypass.
Two things now address it:

1. **`src/tg_compat/_types.py` now maintains its own access-hash cache**,
   fed by `remember_access_hash()` - called from `TelegramUser.from_entity()`,
   which is the single choke point through which every user entity observed
   anywhere in this codebase already passes (every incoming message, every
   callback query, every chat-member lookup). This is a durable, whole-bot
   cache of every user this bot has ever seen, independent of - and
   potentially more complete than - relying solely on Telethon's own
   internal session cache.
2. **`src/tg_compat/_mentions.py`** scans outgoing text for
   `[name](tg://user?id=X)` mentions before it's converted to HTML. For each,
   it checks the cache above first, then falls back to an explicit
   `get_entity()` call. If the user turns out to be genuinely unresolvable
   (never encountered by this bot in any capacity), the mention is rewritten
   from a link into plain `*bold*` text - so the person's name still shows
   and the rest of the message sends normally, rather than the mention
   silently failing or (worse) risking the whole send. Verified directly: a
   resolvable user's mention is left as a working link; an unresolvable
   one's is rewritten to bold; and a second mention of the same resolvable
   user reuses the cache without another network call.

This means a mention can still legitimately show as plain text rather than
a link - not because of a bug, but because Telegram itself has no way to
let a bot construct a clickable reference to someone it has never actually
encountered. If that happens for someone you'd expect to be resolvable
(e.g. they've definitely messaged the bot or share a group with it before),
that's worth flagging, since it would mean this fallback is triggering more
broadly than it should.

## Correction: hyperlinks were still not rendering, and are now actually fixed

Despite the "tested directly... the HTML output is correct" claim in the
section above, a live deployment showed every hyperlink in the bot -
Support Group, Global Challenge deeplinks, crew invites, all of it -
rendering as plain, non-clickable text. Bold text and blockquotes were
unaffected, which was the key clue that this was link-specific rather than
a general parsing failure.

**Root cause:** `message_service.py`'s `escape_invalid_markdown_chars()`
(unchanged from the original PTB codebase) runs over the *entire* outgoing
message, including any `[text](url)` link already built into it, and
backslash-escapes `# + - = { } . !` wherever they occur - so
`[Support Group](https://t.me/OnePieceSupportGroup)` actually reaches
`_prepare_text` as `[Support Group](https://t\.me/OnePieceSupportGroup)`,
and a deeplink's base64 payload (routinely ending in `=` padding) picks up
its own escapes on top of that. Real Bot API MarkdownV2 - what PTB relies
on, since Telegram's own servers do the parsing - unescapes `\X` to `X`
uniformly everywhere in a message, including inside a link's URL. That's
why PTB was never affected: this was never an "escaping is wrong" bug, it
was this compat layer's reimplementation not replicating that unescaping
for the one piece of a message it takes as a raw slice (a link's URL, and
`code`/`pre` content) instead of recursively re-parsing. Every other
construct recurses through `_to_html()`, which already unescapes correctly.

**Fix:** `_markdown.py` now has an `_unescape()` helper, applied to a
link's URL before it goes into the `href` attribute (and to `code`/`pre`
content, which had the identical gap - a code-formatted
`/challenge 10.000.000` example was showing literal backslashes before
each period). The closing `)` of a link is now located with the same
escape-aware scan already used for the closing `]`, rather than a plain
`str.find(")")`, so a URL containing an escaped `\)` works too.

A second instance of the same gap was in `_mentions.py`: its fast-path
check (`"tg://user?id=" not in text`) and its matching regex both expected
an unescaped `=`, so once `id=` became `id\=`, mentions were silently never
detected - meaning the access-hash resolvability check (and its bold-text
fallback for unresolvable users, above) never ran for *any* mention. The
mention still rendered as a link either way (via the `_markdown.py` fix),
but the fallback safety net for genuinely unresolvable users was quietly
bypassed rather than protecting anything. Both checks now tolerate the
escaped form.

**How this was actually verified:** by running the real
`escape_invalid_markdown_chars` together with the real
`markdown_v2_to_html`/`resolve_mentions` against realistic message text -
including a reconstruction of `SHOW_USER_STATUS` with a resolvable mention,
an unresolvable one, a bold bounty figure, and a crew deeplink - and
asserting on the resulting HTML, rather than reasoning about the code and
reading the output for plausibility. That's the difference from the
previous round: the reasoning about Telethon's HTML parser itself wasn't
wrong, it just was never actually exercised against what
`escape_invalid_markdown_chars` really does to a URL. Recommend testing
against a real bot token before fully trusting this too, for the same
reason as everything else in this document (no live Telegram/Telethon
connection in this environment) - though this round's testing at least
exercises the actual escaping + conversion code paths together, not just
one in isolation.

## Second correction: a link nested inside bold/italic/etc. could lose its URL entirely

Reported as: a Reddit repost's attribution line showed the poster's u/username
correctly (underscore intact) as the link *text*, but the underlying link
*target* was missing the underscore - and, more generally, any link nested
inside this codebase's `_..._`-wrapped caption lines (see
`reddit_service.py`'s `"_Posted by [u/{}]({}) on [r/{}]({})_"`) could fail to
render as a link at all, leaking raw `[brackets](and parens)` into the sent
message instead.

**Root cause:** `reddit_service.py` builds `author_url` by concatenating a
prefix with `post.author.name` - Reddit's own username, never escaped,
because escaping it would corrupt the URL. That's correct as far as it
goes. The problem is what the URL sits next to: the whole line is wrapped
in `_..._` for italics, and `_to_html()`'s delimiter search
(`_find_unescaped`, used by `consume_wrapped`) was a plain left-to-right
scan for the next unescaped `_` - with no awareness that it might be
scanning *through* a URL nested inside that italic span. A username like
"Ok_Direction3138" put a raw, unescaped `_` right in the middle of the URL,
and the scan latched onto that as the italic span's closing delimiter -
truncating it mid-URL. The link's own closing `)` was now past the point
where parsing had already stopped looking, so the link-forming branch never
found one, and the truncated fragment fell back to literal, broken-looking
markdown syntax. The swallowed `_` (consumed as a delimiter, the same way
the asterisks around `*bold*` never appear in the rendered output) is
exactly why the leaked URL text was missing its underscore - and the
"link" the report describes seeing was Telegram's own plain-text
URL auto-detection picking up that leaked fragment, not the compat layer
producing a real link entity.

This is a different mechanism from the first correction above (that one was
about characters *inside* a URL being wrongly escaped; this one is about a
raw character inside a URL being read as formatting syntax for something
entirely unrelated to that URL) - both happen to involve a link's URL, but
neither fix stands in for the other.

**Fix:** added `_atomic_span_end()`, which recognizes a
`[text](url)`/`` `code` ``/```` ```pre``` ```` construct starting at a given
position and returns where it ends without interpreting its interior, and
`_find_closing_delim()`, which uses it to skip over such constructs whole
while scanning for an outer delimiter - the same way a real MarkdownV2
parser treats them as opaque rather than rescanning their contents.
`consume_wrapped()` (bold/italic/underline/strikethrough/spoiler) now uses
`_find_closing_delim()` instead of the plain scan. Verified directly against
the real `CREW_JOIN_REQUEST_CAPTION` template too (an italic line wrapping
two more `[Captain]/[First Mate]` deeplinks), plus constructed cases with a
link-in-bold and a link-in-underline, and two genuinely separate italic
spans in one message (to confirm the new skip logic doesn't over-skip when
there's nothing to skip).

**Audit for the same failure mode elsewhere:** grepped for every place a URL
is built by concatenating a prefix with free-form dynamic text (as opposed
to `get_deeplink()`'s own base64-encoded-JSON URLs, whose alphabet can't
contain `_`/`*`/`~`/etc. and so was never at risk here) - `reddit_service.py`
is the only place that does this; Reddit is also the only external content
source in the codebase (no Twitter/Instagram/YouTube integration to check).
Everywhere else that puts dynamic text in a link's *display* text (crew
names via `Crew.get_name_escaped()`, item names, etc.) already runs it
through `escape_valid_markdown_chars()` first, which was always sufficient
on its own regardless of this bug - an escaped `\_` was never a candidate
delimiter match even before this fix. The gap was specifically "raw,
unescaped dynamic text in a URL, nested inside outer formatting," and
`reddit_service.py` was the only place with both halves of that.

## Ctrl+C / SIGTERM produced a raw traceback instead of shutting down cleanly

Reported as: pressing Ctrl+C printed a `CancelledError` from
`runtime.py`'s `run()` (at `await self._client.run_until_disconnected()`),
immediately followed by "During handling of the above exception, another
exception occurred" and a re-raised `KeyboardInterrupt` from
`asyncio/runners.py`.

**Root cause:** PTB's own `run_polling()`/`run_webhook()` install signal
handlers - by default for `SIGINT`, `SIGTERM`, and `SIGABRT` on non-Windows
platforms, per its own documentation - that stop the `Application` cleanly
(log a message, stop, return) - this codebase's `main.py`/`runtime.py` had
no equivalent, so Ctrl+C fell through to `asyncio.run()`'s own default
handling instead: on `KeyboardInterrupt`, it cancels the running task,
waits for that cancellation to finish propagating (the `CancelledError`
half of the traceback), and then re-raises the original
`KeyboardInterrupt` (the second half) once the task has actually stopped -
undocumented as a "bug" anywhere, it's just `asyncio.run()`'s documented
behavior, with nothing in this codebase catching it. Confirmed this was
the exact mechanism by reproducing an identical-shaped
`CancelledError`-into-`KeyboardInterrupt` traceback with a minimal
stand-in client and a real, self-delivered `SIGINT` - and separately
confirmed that `SIGTERM` (sent by whatever is supervising the process -
`systemctl stop` on a plain VPS, a container platform stopping/restarting
the container, etc. - the signal and the gap are identical regardless of
where this runs) was actually worse: Python has no default handler for it
at all, so the process was killed immediately with no graceful shutdown
opportunity whatsoever, not even a traceback.

**Fix:** `Application.run()` (`src/tg_compat/runtime.py`) now installs
handlers for `SIGINT`, `SIGTERM`, and `SIGABRT` via
`loop.add_signal_handler()` before awaiting `run_until_disconnected()` -
the same three signals, via the same mechanism, that PTB's own
`stop_signals` default handles (PTB's docs note the identical
`add_signal_handler`-not-implemented-on-Windows limitation too, which is
why this keeps the same `NotImplementedError` fallback). All three call
`client.disconnect()` (via the existing `create_task` tracking, so it
can't be garbage-collected mid-call) rather than doing nothing and letting
the signal fall through to Python's default behavior - `disconnect()`
resolves `client.disconnected` on its own (confirmed directly from this
bug report's own traceback, which showed `_run_until_disconnected` as
literally `await self.disconnected` in the installed Telethon version), so
`run_until_disconnected()` then returns normally with no cancellation
involved, and `run()` logs a clean "Bot stopped." instead. `main.py` also
keeps a `try/except KeyboardInterrupt` around the top-level
`asyncio.run(async_main())` as a fallback, for a signal arriving before
those handlers are registered (e.g. mid-`client.start()`) or on a platform
where `add_signal_handler` isn't available (it's POSIX-only).

**How this was verified:** by actually sending real `SIGINT`, `SIGTERM`,
and `SIGABRT` (via `os.kill` on itself, not a simulated call) to a minimal
stand-in process built around the exact same shape this report's
traceback revealed about the real client, both before and after the fix -
confirming the unfixed version reproduces the identical `CancelledError`-
into-`KeyboardInterrupt` traceback (for `SIGINT`) and an instant, ungraceful kill
with exit code 143 (for `SIGTERM`), and the fixed version exits 0 with a
clean "Received SIG.../Bot stopped." log and no traceback either way.

## Three bugs from live production logs: a missing import, an empty keyboard, and unresolvable notification recipients

**`NameError: name 'get_current_language' is not defined`** in
`game_service.py`'s `end_text_based_game`. Plain missing import, dropped
during the PTB-to-Telethon migration: `game_service.py` imported only
`set_current_language`, not `get_current_language`, from
`language_service.py` (which is itself unchanged/identical between both
versions - this was purely an import-list mistake, not a logic gap).
Checked every other call site of `get_current_language()` in the codebase;
all of them already import it correctly, so this was the one place it got
dropped. Fixed by restoring the import.

**`ReplyMarkupInvalidError: The provided reply markup is invalid`** from
`end_text_based_game` sending a global game's result message.
`get_keyboard()` in `message_service.py` unconditionally builds
`InlineKeyboardMarkup(keyboard_list)` whenever its `keyboard` argument
isn't `None` - including when it's an empty list, which is exactly what
`end_text_based_game` passes for a global game (`game.is_global()` means
there's no "go to message in group" button to add, so
`outbound_keyboard` stays `[]`). PTB/real Telegram's Bot API silently
treats an empty `inline_keyboard` array as no markup at all, but
`_keyboard.py`'s `convert_markup_to_buttons()` was turning that into an
actual, empty `buttons=[]` list handed to Telethon - which builds a real
(if empty) `ReplyInlineMarkup` for a non-`None`, non-empty-vs-missing
argument, and Telegram's raw MTProto layer rejects that outright, unlike
the Bot API layer which normalizes it away first. Fixed by having
`convert_markup_to_buttons()` return `None` whenever the result would have
no actual buttons in it (covers both an empty top-level list and a
markup whose rows are all individually empty). Verified directly: an
`InlineKeyboardMarkup([])` and an `InlineKeyboardMarkup([[]])` both now
convert to `None`; a normal one-button markup is unaffected.

**`PeerIdInvalidError` / `"bots cannot start conversations"`** from
`notification_service.py` sending a proactive notification. This one
isn't really a bug so much as a real architectural gap between the two
libraries, the same shape as the access-hash problem already documented
above for mentions - just hitting a different code path. Bot API lets a
bot message any user who has ever `/start`-ed it, indefinitely, with no
extra requirement; MTProto (what Telethon actually speaks) requires the
sending account to already have that specific user's access_hash, which
Telegram only ever provides once the bot has "encountered" them somehow
since the current session was established. A user who interacted with the
bot before this migration (or just hasn't messaged it again since) can be
a perfectly valid, long-time user - sitting right there in this
codebase's own database - and still be unreachable by direct send, purely
because Telethon's session has never independently observed their entity.
There is no way to retroactively obtain an access_hash for such a user;
this is a hard protocol constraint, not a missing feature.

Two changes, matching the two things already done for the mention case:
1. **`_types.py` gained `ensure_resolvable_peer()`**, mirroring
   `resolve_mentions()`'s cache-then-`get_entity()` pattern, called from
   every "new message to a user" method in `_bot.py`
   (`send_message`/`send_photo`/`send_video`/`send_animation`/
   `copy_message`, gated on the chat_id being a positive int - group/channel
   ids are negative in this codebase's numbering and don't have this
   problem, since the bot resolves those via its own membership) right
   after `coerce_peer()`. Unlike the mention case, there's no graceful
   in-message fallback for a message send, so this deliberately swallows
   every exception - it's a best-effort cache warm-up before the real
   send, not a gate, and the actual send raises its own correctly-typed
   error regardless of whether this ran.
2. **`notification_service.py`'s existing `except BadRequest` handler**
   (which already tolerated `bot_to_bot` sends as a non-fatal, expected
   outcome) now also tolerates this - logging and moving on instead of
   crashing the background task - since it belongs in exactly the same
   category: a legitimate reason a specific recipient can't be reached
   right now, not a bug to surface as an unhandled exception. Verified the
   classification logic directly against the real error string from this
   report's own traceback.

If notifications to specific long-time users keep failing this way, that's
this protocol constraint doing exactly what it's documented to do, not a
regression - the same as an unresolvable mention correctly falling back to
bold text isn't a bug either. The only real mitigation available is the one
already in place: the more places in the codebase a user's entity gets
observed (which happens automatically any time they interact with the bot
again), the more of them stay reachable for future proactive sends.

## Known limitations / things worth knowing

A few places where Telethon's model doesn't map 1:1 onto Bot API's, in order
of how likely they are to matter in practice:

- **Media re-use / "file_id" caching.** The original code uploads each
  static game image (bounty posters, etc.) once and caches the returned Bot
  API `file_id` string in `context.bot_data` to avoid re-uploading on every
  subsequent send (see `full_media_send` in `message_service.py`). Bot API
  `file_id`s are effectively long-lived. Telethon/MTProto's equivalent (a
  `Photo`/`Document` reference) expires after roughly an hour. The compat
  layer replicates the same caching pattern using an encoded reference
  string in place of a `file_id`, and if Telegram rejects a cached reference
  as stale, that specific send attempt will fail (visible in logs as a
  `BadRequest`) rather than silently succeeding - a restart clears the cache
  and the next send re-uploads fresh. In practice this means images sent
  very repeatedly (e.g. `/fight`) may occasionally need a fresh upload after
  the bot has been running for a while, rather than the near-100%-cached
  behavior PTB had. If this turns out to matter in practice, the fix would
  be extending `message_service.py` to pass the original file path through
  as an explicit fallback for re-upload.
- **DMing another bot.** Bot API rejects bot-to-bot private messages with a
  specific error (`notification_service.py` checks for `"bot_to_bot"` in the
  error text). This is now translated as a `BadRequest`, but I could not
  fully confirm which underlying MTProto error Telegram's servers return for
  this specific scenario, since I don't have a way to test it. Unlikely to
  come up (it only applies when messaging another bot account), but worth
  knowing if you ever see an unexpected error there.
- **Inline query results are plain text.** `InlineQuery.answer()` (used by
  `src/chat/inline_query/inline_query_manager.py`) strips MarkdownV2
  formatting down to plain text rather than converting it to entities, since
  Telethon's inline-result builder is a narrower API than regular message
  sending. This is the smallest-usage part of the codebase (one 34-line
  file).
- **`protect_content` and `allow_sending_without_reply`** (Bot API
  parameters for disabling forwarding and for tolerating a reply-to-deleted
  message) are accepted but currently no-ops - Telethon doesn't expose a
  confirmed equivalent for these. Neither affects whether messages send
  successfully, only these two secondary behaviors.
- **Chat admin/membership checks** (`is_chat_admin`, `user_is_chat_member`)
  use Telethon's `get_permissions()`. This is Telethon's documented,
  standard way to do this, but wasn't testable against a live chat here.

None of these affect the core game loop (sending/editing messages and
keyboards, callback queries, commands, group admin actions, scheduled jobs) -
they're all narrower edge cases, called out here so they're easy to
recognize if they come up rather than being a surprise.
