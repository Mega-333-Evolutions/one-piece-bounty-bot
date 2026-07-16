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
| `_markdown.py` | - | A MarkdownV2 (Bot API flavor) parser - see below |
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
already-Bot-API-escaped text into Telethon's parser would leave stray
backslashes visible to users.

`src/tg_compat/_markdown.py` is a from-scratch MarkdownV2 parser that
converts Bot API's exact dialect (bold, italic, underline, strikethrough,
spoiler, code, pre blocks, links, `tg://user?id=` mentions, and blockquotes,
with proper
UTF-16 offset counting for emoji) directly into Telethon's raw entity
objects, bypassing Telethon's own parser entirely. This was tested against
the specific formatting patterns actually used in `resources/phrases_en.py`
(bold, spoiler, inline code, user mentions).

User mentions (`[name](tg://user?id=X)`, produced by `mention_markdown()`,
used ~95 times across the codebase) need an extra step: Telegram requires a
resolved `InputUser` (id + access hash) to send a clickable mention, not just
a bare user id. `Bot._prepare_text()` resolves this via
`client.get_input_entity()` for every outgoing message with a mention. This
should succeed for essentially every real case (anyone the bot is mentioning
has necessarily messaged it before, so Telethon's session cache has them) -
if resolution ever fails, the mention degrades gracefully to plain text
instead of crashing the send. This is the same mechanism PTB used
(`mention_markdown_v2` produces the exact same `tg://user?id=` MarkdownV2
syntax under both libraries) - it's not something this conversion changed;
it just wasn't rendering correctly until the parse_mode fix below.

**Collapsed/expandable quotes:** `resources/phrases_en.py`'s
`surround_with_expandable_quote()` marks a quote as expandable by ending its
content in `||` (that's this codebase's own convention, not raw Bot API
syntax). The parser recognizes that marker, strips it from the visible text,
and sets Telethon's `MessageEntityBlockquote(collapsed=True)` accordingly -
so `>`-quoted text ending in `||` renders as a genuine collapsible quote,
matching whatever `surround_with_expandable_quote()` is used on.

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

If you deploy this and hit something that looks similarly "off," the most
useful thing to send back is the exact command/action plus the traceback or
a screenshot - that's what made all of these findable.

If that's not it, the most useful next thing is a concrete repro: does a
plain command (e.g. `/start`) get any response at all in the group, and if
not, is there anything in the logs at that timestamp (even if it looks
unrelated)?

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
