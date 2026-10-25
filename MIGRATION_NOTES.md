# Migration notes: python-telegram-bot &rarr Telethon

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

## Every "only usable in reply" command rejected its own Yes/No confirmation

Reported as: `.gift` (and, per the report, several other commands like
`.loan`) correctly accepted the initial command when sent in reply to the
target user's message, showing its confirmation prompt - but pressing
either Yes or No on that confirmation immediately popped
`COMMAND_NOT_IN_REPLY_ERROR` ("This command can only be used in a reply to
a message"), even though the command had, in fact, been used correctly in
reply.

**Root cause:** `manage_message.py` (shared, unchanged from PTB) re-checks
`command.only_in_reply` against `update.effective_message.reply_to_message`
on *every* update for a command, including the callback query generated by
pressing a confirmation button - not just the original message. For a
callback query, `effective_message` is the message the button is attached
to (the confirmation prompt itself), not the original command. In a group
chat, that confirmation message is itself sent as a reply to the original
command (`full_message_send`'s `quote_if_group` default) - so the real
reply chain needed to pass validation was always there, right up until
`runtime.py`'s callback query handler built the `Message` object with
`fetch_reply=False` explicitly, which unconditionally leaves
`reply_to_message` as `None` regardless of whether a real reply relationship
exists. The regular incoming-message handler uses `from_telethon`'s default
(`fetch_reply=True`), which is exactly why the *first* half of the flow (the
initial command) validated correctly and only the confirmation step broke.

This explains the report's own observation that it wasn't specific to
`.gift` - the bug is in the one, shared callback-query dispatch path every
button press goes through, not in any individual command's code, so it hit
every `only_in_reply` command that confirms via a callback button the same
way.

**Fix:** dropped the `fetch_reply=False` override in the callback query
handler, so it uses `from_telethon`'s default (`True`) - matching the
regular message handler. `from_telethon` only does the extra
`get_messages()` fetch when the message actually has a `reply_to` at all,
so this doesn't add cost to callback queries on messages that aren't
replies to begin with (e.g. most private-chat interactions).

**Verified:** isolated the exact conditional branch from `_message.py`
that decides whether to fetch the reply, and confirmed directly that
`fetch_reply=False` always produces `None` regardless of the real reply
chain, while `fetch_reply=True` correctly resolves it.

## Commands sent as /command@BotUsername were silently ignored

Reported as: `/reward` works, `/reward@ActualBotUsername` doesn't respond
at all - and this wasn't specific to one command, every command behaved
the same way with a username suffix attached.

**Root cause:** this one turned out to be in `manage_message.py` - shared,
unchanged code, not something the migration touched. Its command-name
extraction lowercases the whole first token of the message
(`(text.split(" ")[0])[1:].lower()`) - including any `@BotUsername` suffix
- and then tries to strip that suffix by removing `"@" + Env.BOT_USERNAME.get()`,
which is never itself lowercased anywhere in `Environment.py`. So the
strip silently does nothing whenever the registered username has any
uppercase letters in it - the normal case for Telegram usernames (e.g.
"OnePiece_BountyBot") - leaving `command_name` as e.g.
`"reward@onepiece_bountybot"`, which doesn't match any registered command
name and is just ignored. Reproduced directly with a realistic mixed-case
username before touching anything, and confirmed the fix (lowercasing the
username for this one comparison, since `command_name` is already
lowercase by that point) resolves it without affecting the plain
`/command` case.

Worth flagging: since this line is identical in the PTB codebase too, it's
very likely broken there in exactly the same way, not something specific
to this migration - the report just happened to surface it while testing
Telethon. Worth checking `/reward@YourActualUsername` against the PTB bot
too if you want that one fixed as well; the same one-line fix applies
there.

## Bot joining a group didn't send the usual "thanks for adding me" setup message

Reported as: PTB sends a welcome message with a feature-toggle keyboard
whenever it's added to a new group; Telethon sends nothing.

**Root cause, with appropriately less certainty than the fixes above** (this
one can't be fully confirmed without a live Telegram connection, which
isn't available in this environment): `group_chat_manager.py` (shared,
unchanged) detects "the bot was just added" by checking whether
`new_chat_members[0].id` matches the bot's own id. `_message.py`'s
`from_chat_action` builds that list by calling `client.get_entity(uid)`
for every user in the underlying `MessageActionChatAddUser` action -
including, when the bot itself is who got added, the bot's own id. A
fresh, first-ever-seen entity in a chat the client has no prior history
with is a documented Telethon rough edge (see e.g. the upstream issue
where a freshly-observed user in a `ChatAction` event comes back as a
"min" object with `access_hash=None`) - so this lookup failing (or
returning something that doesn't behave as expected) for the bot's *own*
id in a brand new chat would silently drop it out of `new_chat_members`
entirely, making `new_chat_members[0]` raise `IndexError` one level up
(already caught there, so no crash - just silent failure to detect the
join at all).

**Fix:** the bot's own id no longer needs any lookup - it's already known
from `get_me()` at startup (`runtime.py`), so `from_chat_action` now
constructs that one entry directly instead of resolving it, while other
newly-added users (real group members) still resolve normally via
`get_entity()` as before. This is a safe change regardless of whether it's
the *exact* mechanism at play - there's no scenario where trusting
already-known information about the bot's own identity over a fresh
network lookup for it could make anything worse - but flagging the
uncertainty rather than presenting this as a confirmed root cause, unlike
the fixes elsewhere in this document that were reproduced directly.
Verified the resolution logic itself in isolation: the bot now always
ends up in `new_chat_members` even when `get_entity()` is made to fail for
every id, while other users still go through the normal lookup path
unaffected.

If this doesn't fully resolve it, the next thing worth checking is
whether `event.get_chat()` (resolving the chat/group itself, earlier in
the same function) has a similar issue for a brand new chat - that one
was left alone here because, unlike the bot's own identity, there's no
safe way to construct a fallback without already knowing the chat's type
(private/group/supergroup/channel), and it seemed like the less likely of
the two given Telethon needs that info just to know which chat an update
even belongs to.

## "Thanks for adding me" progressed further, then hit a new crash: "No authorized users provided for delete button"

The bot-added-to-group fix above got the welcome-message flow actually
running (confirmed by the traceback showing `screen_settings_features.py`
being reached, which wasn't happening before) - but it now crashed one
step further in, in `get_keyboard()`'s validation that a delete button
must have at least one authorized user.

**Root cause:** the same fresh-entity fragility as the bot's own identity
fix above, just for the *other* side of that event. `get_keyboard()`
defaults `authorized_users` to whoever triggered the current update
(`update.effective_user`) when no explicit list is passed - which is what
`screen_settings_features.py` relies on here. But `effective_user` for
this event depends on `from_chat_action` resolving the *sender* of the
`MessageActionChatAddUser` action - the admin who did the adding - via
`event.get_sender()`, a full, network-resolved entity lookup. If that
admin has no prior history with the bot either (plausible - whoever adds
a bot to a *new* group isn't necessarily someone who's messaged it
directly before), that resolution can fail the same way, leaving
`from_user` (and so `effective_user`) as `None` - and everywhere that
lookup failure was already caught by a blanket `except Exception: pass`,
so it never crashed there, it just silently produced an empty
`authorized_users` list two layers away.

**Fix:** fall back to `event.sender_id` when full resolution fails -
confirmed via Telethon's own docs that, unlike `get_sender()`, this is a
local property with no network call involved, so it's available
regardless of whether the full entity is. A minimal `TelegramUser` built
from just that id is enough for everything downstream actually needs (the
id, not a display name). Verified in isolation: `effective_user` is never
`None` now even when full resolution is made to fail outright, and the
normal case (resolution succeeds) is unaffected.

## The only_in_reply check now runs once, not on every update for a command

Per explicit request: rather than making the callback-query re-check of
`command.only_in_reply` keep working reliably (the previous fix, above),
skip the re-check entirely - a command's reply-validity is a fact about
how it was originally invoked, not something to keep re-deriving from
every later update tied to it.

Turns out there was already a precedent for exactly this, one check below
it: `allow_reply_to_bot` already has `and not is_callback` in its
condition, under the same `REPLY_TO_MESSAGE_BUG_FIX` comment - this looks
like the same fix, just never finished being applied to the check right
above it. `only_in_reply` now has the identical `and not is_callback`
added to match.

The earlier fix (making `fetch_reply` actually populate
`reply_to_message` for callback queries) stays - it's not made redundant
by this, since `allow_self_reply`'s check a few lines down still reads
`reply_to_message` on every update, callbacks included, with no
`is_callback` gate of its own.

Since `manage_message.py` is shared, unchanged code, this applies equally
well on the PTB side - not fixing a bug there (PTB's `reply_to_message`
was always populated correctly), just removing a redundant re-check that
never had any reason to run twice in the first place.

## Note: "Server closed the connection: [Errno 104] Connection reset by peer"

This is Telethon's own logger (`telethon.network.connection.connection`),
not an exception from this codebase, and nothing crashed after it in the
logs that prompted this section - normal, periodic connection resets from
Telegram's servers are expected over a long-running connection, and
reconnecting from them is something Telethon already handles on its own.
Not treating this as something to fix; flagging it here so it's not
mistaken for an unaddressed item next time these logs come up.

## "No authorized users" again after the previous fix - this needed a different kind of fix, not another guess

The previous entry's fix (falling back to `event.sender_id`) did not resolve
this in practice - the exact same crash recurred after deploying it. Worth
being honest about that rather than describing this as confirmed-fixed
again, the same way the previous entry already had to walk back the one
before it.

Two changes this time, for two different reasons:

**Better resolution, on a best-effort basis:** added `event.get_added_by()`
as another attempt between the existing `get_sender()` and `sender_id`
fallbacks. This is Telethon's own purpose-built method for "who added this
user" specifically (confirmed from Telethon's own docs, not assumed) -
distinct from the generic `get_sender()`, and worth trying because it may
succeed via an internal strategy `get_sender()` doesn't use, particularly
for plain (non-supergroup) chats where a service message's sender isn't
necessarily populated the same way a regular message's is. This still isn't
verified against a live connection, so treat it the same way as the
previous attempt: plausible, not confirmed.

**A fix that doesn't depend on any of that working:** this is the actual
reason to expect this resolved now. `screen_settings_features.py` no
longer unconditionally asks for a delete button - it only does when
`update.effective_user` actually resolved to something, and skips the
button entirely otherwise. `get_keyboard()`'s authorized-users check can
only ever fire when a delete button was requested in the first place, so
this makes the crash structurally impossible for this message regardless
of whether entity resolution behaves the way the paragraph above expects
it to. Confirmed directly against `get_keyboard()`'s own validation code
that `add_delete_button=False` cannot raise this exception no matter what
`authorized_users` contains, and that the same code does raise it under
the old unconditional `True` - so this isn't a no-op change standing in
for a real fix, it removes the failure mode's only trigger.

Net effect: the group setup message should now send either way - with a
delete/close button when whoever added the bot could be identified, without
one when they couldn't. If it's still not sending after this, the crash
has moved somewhere other than this specific exception, and the next logs
would need to show a different error for that to be diagnosable.

## Unresolvable-peer crashes were only handled for notifications - generalized to every background task

A new unhandled `PeerIdInvalidError`/`BadRequest` crash showed up from a
`full_message_send` call that wasn't going through
`notification_service.py`'s `send_notification_execute` - meaning it didn't
benefit from that function's existing tolerance for this condition. A
search turned up dozens of other places in this codebase that also fire a
message to a specific user as a background task
(`context.application.create_task(...)`) - game results, location-change
DMs, etc. - none of which have their own handling for this.

Rather than patching each one individually, the fix went into
`runtime.py`'s `create_task()` wrapper itself - the one place every one of
those calls already funnels through. It now recognizes the same
"cannot start conversations"/"invalid peer" condition as benign and logs
it at info level, consistent with how `notification_service.py` already
treats it, instead of logging every occurrence as a scary unhandled
exception. Genuinely unexpected exceptions are unaffected - still logged
in full, as before.

## Local leaderboards regressed to the exact pattern PTB's history already moved away from

Reported as: local leaderboards not sending in groups (falling back to
showing global ranks instead), despite the feature being enabled and the
group having enough active players.

**Root cause:** confirmed directly against PTB's source - `leaderboard_service.py`
is not shared code between the two versions (unusual for this codebase; almost
everything else is), and it had genuinely diverged. PTB sends local
leaderboards to each group *sequentially*, one at a time, awaited, wrapped
in its own try/except - with a comment explaining this replaced an earlier
approach that spawned a concurrent task per group, which held every
group's leaderboard data (DB results, formatted images, pending Telegram
requests) in memory simultaneously and caused a RAM spike severe enough to
get the whole process killed. The Telethon version had exactly that
earlier, abandoned approach - firing all groups as concurrent
`create_task()` calls with no error handling of their own.

This lines up with the reported symptom well: the global leaderboard sends
first, synchronously, and completes before the concurrent local burst even
starts - so it always goes out. If that burst is what's crashing the
process (matching PTB's own documented history for this exact pattern),
every local leaderboard silently never arrives, and whatever a group falls
back to showing in its place would naturally look like "global ranks
instead."

**Fix:** replaced the Telethon version's loop with PTB's exact sequential
version, comment included. `leaderboard_service.py` is now identical
between both codebases apart from the usual import lines.

## Two other reports investigated - found to be shared code working as designed, not Telethon-specific bugs

**Sabaody location DM sent alongside the New World move confirmation:**
traced the full decision path (`location_service.py`'s `update_location()`,
`screen_change_region.py`'s `send_proposal()`, `notification_service.py`'s
`send_notification()`, and the `/reward` screen that triggers all of it) -
every one of these files is identical between PTB and Telethon, including
the exact conditions that decide whether to send the location-reached
notification versus the New World proposal. I couldn't find a compat-layer
difference that would explain PTB and Telethon behaving differently here
given genuinely identical logic. Two things worth checking on your end
that wouldn't be a code bug at all: whether `SEND_MESSAGE_LOCATION_UPDATE`
is set the same way in both deployments' environments, and whether the
specific test account has a different DM history with the PTB bot token
versus the Telethon bot token (they're presumably separate bot accounts,
so "has this player ever DMed *this specific* bot" can genuinely differ
between them even for the same person) - either would produce exactly this
kind of difference without any code being at fault. Flagging this rather
than guessing at a fix for code that's already identical between both
versions.

**Errors not appearing in `ERROR_LOG_CHAT_ID`:** checked this against PTB
directly rather than assume - forwarding to the error log chat
(`log_error()` in `message_service.py`) is called from exactly one place
in *both* codebases (`devil_fruit_service.py`), identically. The specific
example raised (the reddit image resize retry) was never wired to forward
in either version - it's a local, handled-retry diagnostic log, unrelated
to `log_error()`. Nor does the top-level exception handler in
`manage_message.py` (which catches essentially all command-processing
errors) call `log_error()` in either version - it only logs locally. So
this is accurately described as "the bot barely forwards anything to the
error log chat," but that's how the codebase has always worked in PTB too,
not something the migration changed. If the actual want is broader
error-log-chat coverage, that's a real, worthwhile feature to add - just a
different kind of task than "fix a Telethon regression," and one that
would change PTB's behavior too since the relevant code is shared.

## Local leaderboards: reverted back to concurrent sending, by explicit request

The sequential-sending fix two entries up (restoring PTB's approach, added
because of the RAM-spike/OOM-kill history PTB's own comment describes) was
explicitly reverted back to concurrent `create_task()` calls per direct
request - this is now an intentional, deliberate divergence from PTB, not
an oversight. If the OOM issue resurfaces, this is the first place to look;
PTB's sequential version (with its explanatory comment) is still sitting
in the PTB codebase unchanged if reverting back is ever wanted again.

Also lowered `LEADERBOARD_MIN_ACTIVE_USERS`'s default from 20 to 10 (also
explicit) - PTB's default is unchanged at 20, so this is now an
intentional difference between the two as well, not just this file's
sending strategy.

## New feature: all errors now forward to ERROR_LOG_CHAT_ID, not just the one devil-fruit case

**Follow-up refinement, same feature:** `report_error()` now sends as one or
more MarkdownV2 code blocks (```` ```python ... ``` ````) instead of plain
text, so Telegram renders it with syntax highlighting and a one-tap copy
button. And it no longer truncates - long text is split across as many
messages as it takes (on line boundaries, so a line is never cut mid-way),
so the complete traceback always gets through regardless of length.

Escaping is minimal by design: inside a MarkdownV2 code block, only `\` and
`` ` `` need escaping (per Bot API's own spec) - so `report_error()` escapes
just those two, per chunk, before wrapping it in the fence. Verified this
directly against the real `markdown_v2_to_html()` converter: a traceback
containing literal backslashes and backticks round-trips exactly, and
regular code content with underscores/asterisks (e.g. `player_language`,
`a*b`) renders as plain text inside the block rather than being
misinterpreted as italic/bold - confirming code blocks are treated as
literal content, not reprocessed as further markdown, exactly as intended.
Also verified a ~20,000-character traceback splits into multiple chunks
with the full content reproduced exactly when reassembled - nothing lost
to the old truncation.

Explicit request, and an explicit divergence from PTB (which only ever
forwarded that one specific error) - this Telethon bot now forwards every
unhandled exception it catches, with the full traceback, not just that one
case.

Added `Bot.report_error(text)` in `_bot.py`: sends `text` straight to
`Env.ERROR_LOG_CHAT_ID` as plain text (`parse_mode=None` - arbitrary
traceback content should never go through markdown/HTML parsing, which
could itself fail on unpredictable characters in the error text), never
raises itself (a failure while reporting an error shouldn't mask the
original one or crash whatever's already mid-failure), and truncates to
Telegram's message-length limit by keeping the *end* of long text, since
that's where the actually-relevant stack frame is.

Deliberately doesn't reuse `message_service.py`'s existing `log_error()`
(the one PTB-shared function that already forwards the devil-fruit case) -
that needs a full `context`/`update` and pulls in the whole markdown
pipeline, which several of the places below don't have or don't want for
raw traceback text. Left `log_error()` and its one existing call site
alone; `report_error()` is a separate, parallel path.

Wired into every place in the Telethon-specific layer that was catching
exceptions and only logging them locally:
- `manage_message.py`'s top-level per-update handler (catches essentially
  all command/message-processing errors)
- `runtime.py`'s `create_task()` wrapper (every background "fire and
  forget" task - game results, notifications, etc.)
- `runtime.py`'s three event handlers' own `except` blocks, for when
  building the compat `Message` object itself fails (`NewMessage`,
  `ChatAction`, and the callback-query handler)
- `_jobqueue.py`'s job runner (every scheduled APScheduler job) and
  `Job.run()` (manually-triggered jobs)

Not wired in: genuinely expected, non-fatal conditions that already get
their own quieter handling on purpose - the peer-resolution-failed case in
`create_task()`'s wrapper (logged at info level, not treated as an error at
all - see above), and anywhere already deliberately catching a *specific*
exception type to degrade gracefully (`Forbidden`, `bot_to_bot`, etc. in
`notification_service.py`) rather than treat it as unexpected.

A literal Python `SyntaxError` at import time (before the bot can connect
to Telegram at all) obviously can't be forwarded this way - there's no
bot connection yet for it to send through - so "all kinds of errors" here
means everything that can happen once the bot is actually running.

Verified `report_error()`'s properties directly: no-op when
`ERROR_LOG_CHAT_ID` isn't set, truncates long text while preserving the
end, and never raises even when the underlying send itself fails.

## Correction: the New World cap/confirmation WAS broken - just not for the reason first suspected

An earlier round of investigation (mentions of "PTB doesn't DM about
reaching Sabaody" a few entries back) traced this same general area,
concluded the shared cap-and-propose logic was correct, and even verified
that conclusion by simulating a Paradise -> deep-New-World jump in
isolation - which did cap correctly. That simulation just tested the wrong
starting condition. A screenshot of the real bot skipping the confirmation
outright (straight to "You are now on Fish-Man Island", no prompt) made
clear something was still wrong, and the user's own guess - "something to
do with the location before claiming the reward" - pointed at the right
place.

**Actual root cause:** `location_level` defaults to `0` in the database
(`SmallIntegerField(default=0)`) for any account that has never had a
location assigned through normal play. Level `0` isn't undefined, though -
it's a real, defined location: `ND = Location(0, "None", Region.ND, 0, "")`
- literally named "None", which is exactly what the `/status` screenshot
showed for this account before the fateful `/reward`. `Region.ND` is a
*third* region, distinct from both `Region.PARADISE` and
`Region.NEW_WORLD`.

The cap condition only checked `is_paradise_by_level(user.location_level)`
- true for an account already somewhere in Paradise, but false for one
still at ND, since `Region.ND != Region.PARADISE`. So an account whose
bounty reaches New World tier before its location has ever been set even
once (a gift, an admin grant, or - as in this whole conversation - a lot
of rapid test-bounty changes, all before the first `/reward` or command
that triggers a location check) skips the cap entirely: `is_paradise_by_level(0)`
is `False`, the whole condition is `False`, and `effective_location` stays
the raw, uncapped, straight-to-New-World location with no confirmation
ever shown - exactly the screenshot.

**Fix:** changed the condition to check `not is_new_world_by_level(user.location_level)`
instead of `is_paradise_by_level(...)` - "not already in New World" covers
both starting states (ND and Paradise) that should still cap on the way
into New World, while leaving already-New-World accounts free to keep
moving without re-triggering it. `is_new_world_by_level(0)` is also
correctly `False` (ND isn't New World either), so this doesn't
inadvertently cap accounts that are already progressing normally.

**Verified two ways:** first with simulated data across all five relevant
transitions (ND->Paradise, ND->New World, Paradise->Paradise,
Paradise->New World, New World->deeper New World) to confirm no
regressions - then directly against the real `Location.py` module and its
real data (with the minimal env vars needed just to import it), confirming
`ND.name` is literally `"None"`, `get_last_paradise()` returns Sabaody
Archipelago at level 20, Fish-Man Island is level 21 in `Region.NEW_WORLD`,
and the exact old-vs-new condition evaluates to `False`/`True`
respectively for this exact scenario using the bot's own real data, not
stand-ins.

This is shared, unchanged code (`location_service.py` and `Location.py`
are both identical to PTB), so it's a pre-existing gap, not something the
migration introduced - and it doesn't depend on which chat type the
triggering command came from, so it applies the same way in groups as in
DMs.

## Reddit job crashing on a transient Reddit API error (HTTP 500)

This one is different in kind from everything else in this document: the
traceback (`asyncprawcore.exceptions.ServerError: received 500 HTTP
response`, from `async for post in hot_posts:` in `reddit_service.py`) is
Reddit's own servers having a momentary problem, not a bug in this
codebase - nothing here talks to Telethon or PTB at all, it's the
`reddit_post_one_piece`/`reddit_post_meme_piece` timer fetching posts via
`asyncpraw`. The fact that this surfaced as a clean, readable traceback in
the error log chat rather than silently vanishing is the new error-reporting
feature (a few entries up) working as intended, for a different, unrelated
kind of error than it was built for.

**Fix:** wrapped the one call site (`timer_service.py`'s dispatch of
`Timer.REDDIT_POST_ONE_PIECE`/`REDDIT_POST_MEME_PIECE` - confirmed the only
caller of `reddit_service.py`'s `manage()`, imported there as
`send_reddit_post`) in a try/except for
`asyncprawcore.exceptions.AsyncPrawcoreException` - the base class covering
both `RequestException` (network/connection-level issues) and
`ResponseException` and its subclasses like `ServerError` (HTTP error
responses of any status). Logs a warning and moves on instead of raising -
the next scheduled run of the same timer just tries again, which is
already how APScheduler jobs behave here every few minutes/hours. Chose
this call site specifically (rather than wrapping the fetch loop inside
`reddit_service.py` itself, which would need re-indenting ~130 lines for
the same effect) since it's the only place this function is ever invoked
from, so the two are equivalent in what they protect.

**On verification:** couldn't pip-install `asyncpraw`/`asyncprawcore` in
this environment to test directly (repeated attempts returned "no matching
distribution found" even for the base package, seemingly a sandbox/network
issue rather than anything about these specific packages, which are
ordinary, actively-maintained PyPI packages). Confirmed the exception
class and hierarchy via two independent sources instead: the official
asyncpraw FAQ documentation, which names
`asyncprawcore.AsyncPrawcoreException` directly as the base to catch, and
the actual `asyncprawcore/exceptions.py` source, whose `ResponseException.__init__`
formats its message as `f"received {response.status_code} HTTP response"` -
matching the reported traceback's text exactly, which is what gives this
confidence despite not being able to execute it directly. Also verified the
try/except control-flow logic itself (catches the right category, doesn't
swallow an unrelated exception type) against a simulation built from that
same confirmed hierarchy.

## Blocked users, kicked-from-group and deleted-message errors were reported as bugs; Delete now also removes the user's command

Three separate error-log reports, one shared cause. A notification to a user
who had blocked the bot (`UserIsBlockedError`), an edit of a message that
had been deleted in the meantime (`MessageIdInvalidError`, "Message to edit
not found") and a "thanks for adding me" message in a group the bot had
been kicked/banned from (`ChannelPrivateError`) all surfaced as "Unhandled
exception in background task" / "Error handling update". The code that
copes with those situations (`except Forbidden` in
`notification_service.py`, the DM sends in `game_service.py`,
`broadcast_service.py`'s `_is_permanent_failure`, ...) was written for Bot
API, which reports "the user blocked the bot" and "the user's account was
deleted" as a **403 Forbidden**. MTProto reports the very same conditions
as **400**s, so `translate_errors()` turned them into a plain `BadRequest`
and they slipped past every one of those handlers.

**Fix:**
- `_errors.py` now maps `UserIsBlockedError` and `InputUserDeactivatedError`
  to `Forbidden` (with Bot API's own wording, "bot was blocked by the user" /
  "user is deactivated"). `ChannelPrivateError` deliberately stays a
  `BadRequest`: `_types._get_chat_member` and the `ignore_bad_request_exception=True`
  group edits in `game_service.py` already depend on it being one, so
  changing its type could turn a quietly-tolerated situation into a new crash.
  It only gets a stable text (`CHAT_NOT_ACCESSIBLE_MESSAGE`) to be recognised by.
  The four texts live in `error.py` so the code raising them and the code
  matching them can't drift apart.
- `runtime.py`'s `create_task()` wrapper (the same one extended for unresolvable
  peers in an earlier entry) now treats all four conditions - blocked, deactivated,
  message to edit gone, bot lost access to the chat - as expected outcomes
  and logs them at info level. Anything else is still logged in full and
  reported to `ERROR_LOG_CHAT_ID`, exactly as before.
- `manage_message.py`'s `manage_after_db` handles the "chat not accessible"
  `BadRequest` the same way it already handled `Forbidden` (a warning, not an
  "Error handling update" report).

**Delete also deletes the command that triggered the message.** Tapping a
Delete/Close button (group settings, any `add_delete_button=True` message,
a Yes/No confirmation whose button is a delete button, ...) now removes the
bot message and, in a group, the command the user sent to get it. In a group the bot quotes the
command it answers, so that command is the bot message's `reply_to_message`.
It is only deleted when it really is a command (starts with one of
`COMMAND_PREFIX_ALIASES`), was sent by the very user who tapped the button,
and isn't a forum-topic header - so a reply to *another* player's message
(e.g. `/status` on someone else's message) never deletes that player's
message. Deleting someone's message needs the bot's "delete messages" admin
right, so it's best effort: if the bot lacks it the bot message is still
deleted and nothing is raised. Not applicable in private chats, where the
bot doesn't quote the command. (This reply-based guess is now only the fallback:
the next entry covers commands used in reply to someone else's message and
group auto delete.)

**On verification:** ran the real code with real Telethon (1.45) error objects
and a fake client: the original code reproduces all three reported errors,
the fixed code doesn't; the pre-existing mappings (`FloodWaitError` ->
`RetryAfter`, "message is not modified", 403s, `PeerIdInvalidError`,
`UserNotParticipantError`, timeouts) and the reporting of genuine bugs are
unchanged; the Delete button's authorization check is unchanged, and the
command is left alone for a different user, a non-command, a bot/anonymous
sender, a topic header and private chats.

## Auto delete and Delete now remove the user's command wherever it was sent; two more background-task errors

Four reports from the error log / from use, fixed together.

**1. Group auto delete only deleted the bot's message, not the command.**
`auto_delete_process` (the minute job behind /settings' auto delete) only
knew the id of the bot message it had queued, and nothing linked that
message to the command it answered.

**2. Delete didn't remove some commands - the ones used in reply to another
message.** The previous entry found the command through the bot message's
`reply_to_message`. But some screens (`/status`, for one) answer the message the
command was *replying to* instead of the command, so the reply pointed at
somebody else's message, which is (rightly) never deleted.

**Fix for 1 and 2:** `message_service.py` now remembers, at the moment the bot
answers a command in a group, which command message each answer belongs to
(`link_message_to_command`, called by `full_message_send` and `full_media_send`
right after the send; it never raises, so it can't break a send). The link is
made only when the update is a message (not a button tap) whose text is a
command, in a group, and the answer went to that same chat; it doesn't matter
which message the bot replied to. The registry is bounded (20,000 links, oldest
dropped first). Then:
- Tapping Delete (`manage_message.delete_message_and_command`) deletes the bot
  message and the linked command. Any user the button authorizes can tap it, as
  before; the linked command is the one that triggered the message, whoever sent
  it. A tap by an unauthorized user changes nothing and keeps the link. Without
  a link (see below) it falls back to the previous entry's reply-based guess,
  with all its safety conditions.
- Auto delete (`auto_delete_process`) deletes the linked command right after the
  bot message. Nothing is deleted while the message is deferred because of an
  active challenge, and the link is kept for when it is finally deleted.
Limits: the registry lives in memory, so after a restart messages sent before it
have no link (Delete falls back to the reply-based guess; auto delete only
removes the bot message). Deleting somebody else's message needs the bot's
"delete messages" admin right: without it the bot message is still deleted and
nothing is raised. Flows that delete their own messages (fight/plunder retreat,
game rejection, ...) don't go through either path and are unchanged.

**3. `Could not find the input entity for PeerUser(user_id=...)` reported as an
unhandled background-task error.** Telethon can only message a user whose
access hash it has seen. For a user id the bot has never encountered it raises a
bare `ValueError`, which `translate_errors` turned into a generic
`TelegramError` - nothing treated that as a "recipient can't be reached" case.
`ensure_resolvable_peer` used to swallow the failed lookup and let the send
raise the same error. Now `ensure_resolvable_peer` returns False for exactly
that error (and True for anything else, e.g. a network hiccup, which the send
itself will report), and `Bot._warm_user_peer` raises
`BadRequest("Invalid peer: the bot has never encountered this user, so it cannot
message them")` before the doomed send (send_message, copy_message, send_photo,
send_video, send_animation). The text contains "invalid peer", which
`notification_service.py` and the `create_task` wrapper in `runtime.py` already
treat as expected, and deliberately none of the snippets `broadcast_service.py`
takes as "permanent" - the player isn't deactivated, since they can still become
reachable by messaging the bot. Any other `ValueError` still ends up as the
generic `TelegramError`.

**4. `Failed to generate a valid game board after multiple attempts` (C0) from
`restart_hint_thread_if_down`.** Punk Records, Shambles and Who's Who build
their board the first time it's needed. A game with no board therefore never
started - the players got that C0 message when they tried - but the periodic
hint-thread restarter kept trying to build it for every such game, every hint
interval: a burst of downloads that fail the same way, reported as an unhandled
background-task error each time. `restart_hint_thread_if_down` now skips games
whose board is missing (in a global game, also the opponent's). Starting the
game again from its Play button is what retries. Guess or Life builds its board
locally and is unaffected. Why the boards couldn't be built is the next entry.

**On verification:** the real functions against fake Telethon clients/bots and an
in-memory database: the previous code reproduces each report (auto delete
deleting `[bot message]` only, Delete leaving the command in the chat, the
unhandled `TelegramError` with Telethon's text, the `CommonChatException` from
the restarter), the new code doesn't, and the Round 1 behaviours (private chats,
unauthorized taps, the reply-based fallback, Forbidden/ChannelPrivate handling)
still pass. Not testable here: a live group - in particular whether the bot has
the "delete messages" right there.

## Who's Who: it can't start a game when the image host refuses the bot's downloads - the images can now ship with the bot

Every Who's Who game downloads the character's image when it starts, from
Fandom's image server (`static.wikia.nocookie.net`: all 678 `anime_image_url`s of
`assets/items/character.json`). If a download fails the game picks another
character, up to 10 times; if all 10 fail the player gets "Error C0: Failed to
generate a valid game board ... due to missing resources", and the restarter of
the previous entry used to repeat the failure in the background.

The download function is `download_temp_file()` in `src/utils/download_utils.py`
(not in `game_service.py`), and it was **already sending a browser User-Agent**
before any of this. So a User-Agent is not what's missing, and I can't tell you
which of the possible causes applies: Fandom's CDN couldn't be reached from where
this was built. The log says it, per attempt: `Dead image link for <name>: HTTP
Error 403: Forbidden` (the CDN refuses your server - the most likely one: CDNs
often distrust the addresses of cloud hosts, and some tell a script from a
browser by the TLS handshake whatever the User-Agent says), `HTTP Error 404`
(that image is gone from the wiki), `<urlopen error ...>` (network/DNS),
`Failed to process image` (what came back isn't an image).

**What changed**
- *The cause is no longer lost.* The `ValueError` of a failed image now carries
  it (`Image unavailable for Zoro (HTTP Error 403: Forbidden)`), and
  `get_generic_boards_for_guess_game` logs one ERROR with the last cause and the
  game id when it gives up. The player's message is unchanged.
- *Bundled images (the fix that doesn't depend on the CDN letting the server
  in).* `WhosWho` looks for `assets/images/characters/<name>.jpg` first and uses
  it - a copy in the temp folder, like a download - with no network at all; only
  characters without a bundled image are downloaded. `<name>` comes from the image
  url (`.../Abdullah_Anime_Infobox.png/revision/latest?cb=...` ->
  `Abdullah_Anime_Infobox.jpg`, `get_bundled_image_file_name`). A bundled file that
  can't be used (an empty file, or a Git LFS pointer deployed instead of the
  image) is ignored with a warning and the image is downloaded instead.
  `scripts/download_character_images.py` makes the bundle: run it on any machine
  that CAN download the images (your computer: if they open in your browser it
  works), then commit `assets/images/characters` and deploy. It downloads
  4 at a time, converts each image the way the bot already does (RGB, shrunk if
  longer than 1200 px, JPEG), skips what is already there (so stopping and
  re-running is fine), and ends with a summary by reason - including the dead
  links, whose characters Who's Who can't use (it moves on to another when it
  hits one). The files are `.jpg` on purpose, like the rest of the images in
  `assets/`: this repo's `.gitattributes` treats `*.jpg` specially (Git LFS), so
  they are committed exactly as `assets/images/saved_media/*.jpg` are.
- *A sturdier download, for the characters that aren't bundled.* The new
  `src/utils/image_fetch.py` (it imports nothing from the bot, so the script uses
  it too) sends everything a browser loading an image sends (Referer = the wiki's
  own page, Sec-Fetch-*, client hints; no `image/avif`, which Pillow 10 can't
  open) and, when that fails, tries other ways before giving up: **curl_cffi**
  (new in `requirements.txt`, optional: the bot runs without it), which does a
  real Chrome's TLS/HTTP2 handshake, and an **image proxy** if the
  `IMAGE_PROXY_URL` environment variable is set, e.g.
  `https://wsrv.nl/?url={url}&output=jpg` (the proxy downloads the image instead
  of your server, which is the way around a CDN that blocks its address). A dead
  link (400/404/410) is final: no other way is tried. A host that answers a web
  page with 200 instead of an error is now a failure (found by the file's
  signature), where it used to crash later with `PIL.UnidentifiedImageError` -
  which the retry loop didn't catch. Truncated and oversized images are refused the same
  way, and a WebP/other format is converted to JPEG (Telegram doesn't take every
  format as a photo; the old code saved WebP bytes under a `.jpg` name).
- The requests for a Who's Who image wait at most 15 s each (they waited 30).

**Not changed, worth knowing:** board creation and downloads still run on the bot's
event loop, so the bot doesn't answer anybody while one waits (bounded now, and
gone for bundled images); `cleanup_temp_dir()` still deletes *every* temp file on
each run (`or True`), which `WhosWho` was already written to survive by getting its
image again - from the bundle now, without the network.

**On verification:** the real `WhosWho`, `get_generic_boards_for_guess_game` (with a
real `Game` row) and the script (as a subprocess) against a local HTTP server
that behaves like the ways a CDN can refuse: 403 to scripts, a stand-in for TLS
fingerprinting, a 200 web page, a dead link, WebP, a truncated image, an oversized
one, 429s and a timeout. The previous code fails or crashes in most of them
(`Image unavailable`, `PIL.UnidentifiedImageError`, `OSError: image file is
truncated`); the new code works or fails cleanly with the cause. The names the
script writes are the ones `WhosWho` reads (checked with the CDN refusing
everything), and all 678 real urls get unique, filesystem-safe names. **What I
could not verify:** a download from the real Fandom CDN, and curl_cffi's TLS
handshake against a real TLS server (locally it's plain HTTP, so the code path
is exercised but the handshake isn't). That's why the bundle is the
recommended fix: it doesn't depend on either.

## Messaging another bot was reported as an unhandled exception

Error-log report: `Unhandled exception in background task <unnamed>`, ending in
`BadRequest: Bots can't send messages to other bots (caused by
SendMessageRequest)`, raised from `send_notification_execute` - a notification
addressed to a player that is a bot.

`notification_service.py` already skips that case quietly: its `except
BadRequest` looks for `"bot_to_bot"` in the error text. But the real MTProto
error for it is `USER_IS_BOT` (Telethon's `UserIsBotError`), whose text -
"Bots can't send messages to other bots" - has no such marker. So
`translate_errors()` made it a plain `BadRequest`, the check didn't match, the
handler re-raised it and the background-task wrapper reported it.

**Fix:**
- `_errors.py` maps `UserIsBotError` to a `BadRequest` whose text is
  `BOT_TO_BOT_MESSAGE` (`error.py`): "Bots can't send messages to other bots
  (bot_to_bot)". It is still a `BadRequest` - that is what the existing handler
  is written for - with the marker it looks for, and it still says what
  happened. (It has to be matched before the generic `BadRequestError` branch,
  which `UserIsBotError` is a subclass of.)
- `runtime.py`'s `create_task()` wrapper treats the marker as an expected outcome
  too (info log, no report), for the other background tasks that message a
  player without a handler of their own (game DMs, ...).

**On verification:** the real `send_notification` -> `create_task` ->
`send_notification_execute` -> `full_message_send` -> `Bot.send_message` ->
`translate_errors` chain with a real Telethon `UserIsBotError`. The previous code
reports exactly the traceback from the log; the new code reports nothing, and a
genuine `BadRequest` is still reported. **What I could not verify:** a real
Telegram server (the error object is built the way Telethon builds it).

## Predictions: lost bets stayed pending, "wagers refunded" winners weren't paid, deleting a prediction didn't return the wagers

Three bounty bugs in `prediction_service.py`. The code involved is identical in
the PTB source, so they are old game-logic bugs, not migration regressions.

1. **A lost bet stayed in the pending bounty after the result was set** ("the
   player who bet on a losing option still has the bounty he used to bet as
   pending"). Placing a bet moves the wager from `bounty` to `pending_bounty`.
   `set_results` released it for winning bets and for refunded bets, but skipped
   a lost bet that isn't refunded - the normal case - so the wager stayed pending
   until the next bounty reset, which turns pending back into bounty (the loser
   got the lost wager back as free bounty). `set_results` now releases it; the
   player doesn't get it back.
2. **On a prediction with "wagers refunded" the winners weren't paid their
   winnings.** Every bet - winners' too - went through a win/loss step and then a
   refund step, and `add_or_remove_bounty` reloads the user's bounty from the
   database on every call, so the second call discarded the first: the winner was
   left with the capped refund only (3 000 staked on a 4 000 pool: 7 400 instead of
   11 000, less than the 10 000 he started with). Each bet now gets exactly one call
   - winners their winnings, losing bets the refund (capped, or in full when no
   option is correct) - and the result notification only says "(Your wager was
   refunded)" to players who have a losing bet.
3. **Deleting a prediction that had bets didn't return the wagers.** The delete
   confirmation promises "they will be refunded", but `delete_prediction` called
   `add_or_remove_bounty` on the bettors without saving them (and they aren't the
   user whose update is being handled, who is the one that gets saved), so the
   wagers stayed in their pending bounty until the next reset. They are saved now.
   A *finished* prediction still pays nothing back when it is deleted - its result
   was already paid out, and returning the wagers on top would give everybody,
   losers included, a free refund - which is now explicit instead of a side effect
   of the missing save.

**Not changed, worth knowing:** nothing is repaired for what already happened:
players whose lost wager is still pending (a bounty reset that happened since
returned it to them as bounty, so the amount can't be worked out from the
database alone), winners of "wagers refunded" predictions who were paid the refund
only, and bettors of predictions deleted before this fix.

**On verification:** the real `save_prediction_option_user`, `close_bets`,
`set_results` and `delete_prediction` against an in-memory database with the
project's real tables (only the Telegram edge - sending notifications and
refreshing the group messages - is replaced). Each problem was reproduced on the
previous code first (loser: bounty 9 000, pending 1 000; "wagers refunded" winner:
7 400 where the same bets without the refund pay 11 000; a deleted prediction's
bettors: pending still 1 000 / 2 000), then checked on the new code: a loser, a
loser with pending bounty from elsewhere, a player with a winning and a losing bet,
a player with two losing bets, nobody on the correct option, no correct option at
all, a withdrawn bet, the "wagers refunded" variants of all of those, deleting
open, closed and finished predictions, and a creator who bet on his own prediction
(the save at the end of his own update doesn't undo the refund).

## The bot leaving a chat it had already left was reported as "Error handling update"

Error-log report: `Error handling update: <src.tg_compat._message.Update object at
0x...>`, ending in `UserNotParticipantError: The target user is not a member of the
specified megagroup or channel (caused by LeaveChannelRequest)`, raised from
`manage_message.py`'s `await update.effective_chat.leave()` and shown as a `BadRequest`.

When an update comes from a chat the bot isn't meant to be in - a broadcast channel
(other than the `TG_REST_CHANNEL_ID` and `UPDATES_CHAT_ID` ones), or, with
`LIMIT_TO_AUTHORIZED_GROUPS`, a group that isn't authorized - `manage_after_db` makes
the bot leave it and stops handling the update. That code is identical in the PTB
source. Here Telegram answered that the bot was no longer a member, so there was nothing
left to leave, but the error went up to `manage()`, which reports every exception: a
leave that had already happened was reported as a failure. (Most likely a second update
from the same channel was still being handled after the first one had made the bot
leave, or the bot had been removed from it in the meantime - the report can't tell
which.)

**Fix:**
- `Chat.leave()` (`_types.py`) now treats "the bot isn't in that chat (any more)" as done:
  Telegram's `USER_NOT_PARTICIPANT` (not a member) and `CHANNEL_PRIVATE` (kicked/banned, or
  the chat went private) - the two answers that mean exactly that - are logged at info level
  and nothing is raised. `is_not_in_chat_error()` (`_errors.py`) recognises them from the
  Telethon error the translated `BadRequest` was raised from. Any other failure to leave
  (flood wait, timeout, 403, any other `BadRequest`, ...) is raised as before, so it is still
  reported. Both `leave()` calls in `manage_after_db` are followed by a `return`, so nothing
  else changes for those updates.

**Found while checking this - the compat `Update` couldn't describe itself:**
- The report starts with `<... Update object at 0x...>` where PTB prints the update as JSON:
  the compat `Update` had no `__repr__`, so error reports and `logging.error(update)` said
  nothing about the chat, user or message involved. It now prints `Update({...})` with the
  chat, the sender and the text (or the callback data / the inline query), and can't raise.
- It also had no `to_dict()`, which `bounty_service.add_or_remove_bounty` calls when it logs a
  player who doesn't have enough bounty, and when it clamps a pending bounty that would go
  negative. Whenever the caller passed the update (gift, loan, Devil Fruit purchase, Doc Q,
  fights and plunders, wager games, Impel Down bail), that line raised `AttributeError:
  'Update' object has no attribute 'to_dict'` instead of the "not enough bounty" answer, and
  the player got an error report instead of an answer. Rare - most of those flows check the
  balance first - but the wrong failure. `to_dict()` now exists on `Update` and its parts
  (`Message`, `CallbackQuery`, `InlineQuery`, `TelegramUser`, `Chat`), as in PTB: only the
  fields that are set, media only marked as present.

**On verification:** the real `manage()` with an update from a channel whose client raises
Telethon's `UserNotParticipantError(LeaveChannelRequest)` on `delete_dialog`: the previous
code reports exactly the traceback from the log, the new code reports nothing. Also
checked: a normal leave still leaves once, the updates chat is still never left, and flood
wait / timeout / 403 / an unrelated `BadRequest` / any other error while leaving all still
surface and are reported. The real `add_or_remove_bounty` against an in-memory database
with the project's real tables, with an update passed: not enough bounty, and a pending
bounty clamped to 0 - `AttributeError` before, the "not enough bounty" answer
(`CommonChatException`) and a clean clamp now. **What I could not verify:** a real Telegram
server (the error object is built the way Telethon builds it), and why the bot was already
out of that channel.

## Global challenges: an expired challenge returned only half the wager, and it now lasts 24 hours, not 12

**How it works.** "Start as global" makes the challenger pay the wager at once
(`collect_game_wagers_and_set_in_progress`: bounty -> pending bounty) and puts the challenge
in the global list. If nobody accepts it, the cleanup job `end_inactive_games` (cron
`CRON_END_INACTIVE_GAMES`, every 5 minutes by default) ends it as a forced end once
`GAME_GLOBAL_INACTIVE_HOURS` hours have passed since the challenger started it (and it has been
idle for the usual 10 minutes). The default was 12 hours; it is now **24**. The setting is only
defined in `resources/Environment.py` and only read by `end_inactive_games`; an environment
variable of the same name overrides the default, so if `GAME_GLOBAL_INACTIVE_HOURS` is set
where the bot is deployed, change it there too (or delete it).

**The bug.** `end_game` assumed `game.wager` is a pot of two stakes - it is, once an opponent
has joined, because `collect_game_wagers_and_set_in_progress` doubles it - and so returned and
released `wager / 2` per player. An unaccepted global challenge has no opponent, so its
`wager` is only the challenger's own stake and half of it was returned: with a 4 000 wager
the challenger went from 10 000 to bounty 8 000 / pending 2 000, and the other half sat in
the pending bounty until the next bounty reset moved pending back into bounty. The code is
identical in the PTB source, so this is old game logic, not a migration regression.

**Fix:** `end_game` now works out what each player put in from the refreshed row, after the
atomic claim: half the pot when there is an opponent (exactly as before), the whole wager
when there isn't one. This also fixes a rare race found while testing: the cleanup job picks a
batch of games and ends them one at a time, so a challenge accepted in between used to be
handled with the stale, un-doubled wager and each player got half of what they had paid.

**Not changed, worth knowing:** nothing is repaired for challenges that already expired. The
other half of those wagers is still in the challengers' pending bounty; the next bounty reset
returns it, or `/rpending` returns one player's pending bounty right away (all of it - also
what is held by an open game or a prediction bet, so only use it on a player who has none).

**On verification:** the real `collect_game_wagers_and_set_in_progress` (a challenge opened and
accepted exactly as the two screens do it), `end_inactive_games` and `end_game`, against an
in-memory database with the project's real tables, moving the dates stored on the game back
to let time pass. Previous code: a 4 000 challenge came back as 8 000 / 2 000 (every wager
tried, odd ones too, and every game type); new code: 10 000 / 0, a player's pending bounty
from elsewhere is left alone, running the cleanup twice doesn't refund twice, a challenge
10 minutes under the limit is still open and 10 minutes over it is ended. The payouts of
games that do have an opponent - won, lost, drawn, and accepted-then-expired - were compared
to the previous code for several wagers and are identical. **What I could not verify:** the
real clock and Telegram (the dates were moved in the database).

## Crews are disbanded when the Captain misses 4 global leaderboards in a row - it had been switched off

**The rule.** A Crew is disbanded when its Captain was in none of the latest 4 global
leaderboards. The Captain gets a warning after missing the 3rd one in a row ("You have not
appeared in the last 3 global leaderboards. If you do not appear in the next leaderboard, your
Crew will be disbanded.", linking the latest global leaderboard, in English and Persian), so
there is one leaderboard in between to do something about it. Being in one leaderboard starts
the count over. "Appearing" is the same measure the Devil Fruit revocation uses: a row of the
Captain in the global leaderboard (the one without a group). The 4 is the new setting
`CREW_MAINTAIN_MIN_LATEST_LEADERBOARD_APPEARANCE` (default 4; the warning is always one
less).

**When it runs.** `manage_inactive_crews` (crew_service.py) runs after every weekly global
leaderboard: first it disbands, then it warns, so a Captain who has just lost the Crew is not
warned about it. The leaderboard job (`send_leaderboard`) starts it after the leaderboard is
created. On the leaderboard that resets the bounties, `reset_bounty` starts it at its end
instead (as it already did for the old disbanding): `reset_bounty` sets `can_create_crew` back
to true for everybody, and the Captain of a Crew disbanded now must not get that back - as
with any disbanding, he can't create a new Crew until the next reset.

**What it does to a Crew.** `disband_crew` (unchanged): every member is taken out of the Crew,
the Crew is marked inactive and everybody, the Captain included, gets "Your Crew has been
disbanded". A Crew in a Davy Back Fight or serving its penalty can't be disbanded
(`disband_crew` refuses): it is skipped and looked at again at the next leaderboard, and its
Captain keeps getting the warning until then. One Crew failing for another reason doesn't stop
the others: they are disbanded and warned first, then the first failure is raised so it
reaches `ERROR_LOG_CHAT_ID`.

**Who is never disbanded.** Admins, users exempt from the global leaderboard requirements,
active Warlords and active Legendary Pirates (the same exemptions as the Devil Fruit
revocation); first mates and conscripts are not Captains, so they don't count. A Captain who
created the Crew, or was promoted to Captain, after the oldest of the leaderboards being looked
at only counts the leaderboards since then: a new Crew isn't disbanded in its first week (the
date is the later of the Captain's `crew_join_date` and `crew_promotion_date`; a Captain with
neither recorded is treated as an old one). Nothing is disbanded while there are fewer than 4
global leaderboards, or when any of the 4 has nobody in it (such a leaderboard did not
complete, and everybody would have "missed" it).

**Why it was off.** `get_inactive_captains()` was a bare `return []` under the FIXME "To
encourage more Crews, do not currently disband any Crews", with the real query commented out
below it (the PTB source is the same). So nothing was ever warned or disbanded. That
function now takes the number of leaderboards and implements the rule above. The
activity-based version I delivered earlier in this round (Captains who hadn't used the bot
during the bounty season) is gone completely, including the optional argument it had added to
`get_previous_bounty_reset_time`, which is back to what it was.

**Check this before deploying: who appears in the global leaderboard.** Only about 20
ordinary players do: the Pirate King (at most 1), the Emperors (4) and First Mates (4) of the
New World, 11 Supernovas of Paradise, plus the active Warlords and Legendary Pirates. Every
Captain outside that list never appears, so with this rule most Captains will be warned
and then lose their Crew after 4 leaderboards - it is the same rule as the Devil Fruit
revocation, but it affects far more people. If that is not the intent, raise
`CREW_MAINTAIN_MIN_LATEST_LEADERBOARD_APPEARANCE` (an environment setting, read when the bot
starts), or say what else should count as appearing.

**TEMPORARY: the warning on startup.** The leaderboard job only warns a Captain right after
the leaderboard in which he missed the 3rd one, so the Captains who are already there when this
goes live would be disbanded without ever being warned. For that, every time the bot starts
`main.py` (`post_init`) calls `send_crew_disband_startup_warning`, which warns the Captains who
were in none of the latest 3 global leaderboards (it disbands nothing). A Captain who was in
none of the latest 3 and does not appear in the next leaderboard loses the Crew at it, so the
warning is the only notice. Until it is removed it is sent again on every restart: to stop it
without touching the code, set `CREW_DISBAND_STARTUP_WARNING=False`. **To remove it** (when it
is done): delete `send_crew_disband_startup_warning` in crew_service.py, the import and the
call at the end of `post_init` in main.py (both marked TEMPORARY) and the
`CREW_DISBAND_STARTUP_WARNING` setting in resources/Environment.py. Nothing else depends on
them.

**On verification:** the real `get_inactive_captains`, `disband_inactive_crews`,
`warn_inactive_captains`, `manage_inactive_crews`, `send_crew_disband_startup_warning`,
`disband_crew`, `send_leaderboard`, `reset_bounty` and `main.post_init`, and the real
notification classes in English and Persian, against an in-memory database with the project's
real tables (SQLite, with MySQL's `IF()` added for one raw query `reset_bounty` runs); only the
Telegram send was replaced, and the clock where the leaderboard job reads it. 98 checks, in 9
server time zones: who is returned for every N from 1 to 7 over the same leaderboards; fewer
leaderboards than N; admin / exempt / Warlord / Legendary Pirate (active and expired); first
mates and conscripts; new and newly promoted Captains; an empty leaderboard; the order of the
leaderboards across the year (2026 has a week 53); group leaderboards not counting; week by
week from the 3rd miss to the disbanding (the warning on the 3rd, the disbanding and the
disband notifications on the 4th, the count starting over after an appearance); Crews in a
Davy Back Fight or penalty skipped without stopping the others; one Crew failing without
blocking the others or the warnings; the setting changed to 1, 2 and 6; the startup warning
(on, off, started by `post_init`); and the weekly job at Oct 18, Oct 25 (the real bounty reset
runs, then the Crew management, and the disbanded Captain can't create a Crew while everybody
else can), Nov 1 and Nov 8. Before this change `get_inactive_captains()` returned `[]`, and a
Captain who missed 6 leaderboards was neither warned nor disbanded. **What I could not verify:**
Telegram, the real clock, MySQL (the tests ran on SQLite), and your data - how many Captains
this will affect.

## Bounty reset: the leaderboard on the 1st of a month reset the bounties a second time

**What was happening.** The weekly leaderboard job decides whether it is a bounty reset with
`should_reset_bounty(now)`. Bounties are meant to reset only on the last leaderboard of every
even month (Oct 25, 2026); the next leaderboard (Nov 1) is the first of the new season. The
check flagged that one too, so `reset_bounty` - bounties halved (capped), open games ended,
bets removed, locations reset - would have run a second time, a week later. The code is the
same in the PTB source, so the same applied to Mar 1, 2026, a week after the Feb 22 reset.
Two separate causes:
- The job runs at Sunday 00:00 in the bot's time zone (`TZ`, Asia/Kolkata by default -
  `main.py` sets it) but passes `now` in UTC, and the month was read from that UTC time. The
  Nov 1 leaderboard, 00:00 IST, is Oct 31 18:30 in UTC: October, an even month, with the next
  leaderboard in November - "the last leaderboard of October".
- An extra rule - "or today is the first, and the month before was even" - flagged any
  leaderboard on the 1st of an odd month: Nov 1 on a server in UTC. With the mismatch above it
  also fired on the 2nd, which is still the 1st in UTC: May 2 2027, Jan 2 2028 and Jul 2 2028
  would each have reset the bounties a second time as well.

**Fix:** `should_reset_bounty` compares the months in the time zone the leaderboard is scheduled
in (that of the next run) and the extra rule is gone: the bounties reset on the last
leaderboard of Feb / Apr / Jun / Aug / Oct / Dec, by the date in the bot's time zone, and
on no other. Oct 25 and every other real reset are unchanged; the only leaderboards that
change are the extra ones above (Mar 1 and Nov 1, 2026; May 2, 2027; Jan 2 and Jul 2, 2028).
Everything that asks the same function follows: the "next bounty reset" countdown and the Devil
Fruit cooldown that ends at it - after Oct 25 the next reset is now Dec 27, where it used to
say Nov 1.

**Not changed, worth knowing:** nothing is repaired for resets that already ran, and
`reset_bounty` itself still has no guard against running twice in a row - the calendar is what
prevents it.

**On verification:** the real `should_reset_bounty`, `get_next_bounty_reset_time`,
`get_previous_bounty_reset_time` and `send_leaderboard` (Telegram sending replaced, the clock
moved), at the real run time of each of the 157 Sunday leaderboards from Jan 2026 to Dec
2028, against an independent calendar (the last Sunday, by local date, of an even month), in 9
server time zones (UTC, Asia/Kolkata, Asia/Kathmandu, Rome, Auckland, Kiritimati, Los
Angeles, Honolulu, São Paulo). Previous code (run in IST and UTC): `send_leaderboard` calls
`reset_bounty` on Nov 1 and on Mar 1, and the check flags the Sundays listed above. New code:
it matches the calendar on every leaderboard in every zone, Oct 25 resets and Nov 1 doesn't,
and the next reset after Oct 25 is Dec 27. **What I could not verify:** the real clock and Telegram; other time zones
were simulated by changing the process's `TZ`.

## New: the bot can run on PostgreSQL (e.g. Supabase) instead of MySQL / TiDB

**Why.** TiDB Starter stops working when its monthly request units run out. The bot's data is
small (the database measured 5.2 MB) and the server is in US East (Virginia), so what is needed
is a free database in that region that doesn't have a request-unit meter: PostgreSQL on
Supabase's free plan, created in the region "East US (North Virginia)" (`us-east-1`). A NoSQL
database would not suit the bot better: it is built on relational queries (joins, sums, ranks,
76 foreign keys over 41 tables) and moving to NoSQL means rewriting about 57 files. PostgreSQL
needed the small changes listed below.

**Nothing changes until you switch.** `DB_TYPE` defaults to `mysql`, and the MySQL / TiDB path
behaves as before (the old and the new code were run on the same data on MariaDB and give the
same results). The bot talks to PostgreSQL only when `DB_TYPE=postgres`.

**New settings** (`resources/Environment.py`):
- `DB_TYPE` - `mysql` (default: MySQL, MariaDB, TiDB) or `postgres` (PostgreSQL, Supabase).
- `DB_SSL_MODE` - only used with `postgres`; default `require` (encrypted connection).
- `DB_NAME`, `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD` - the same variables as before, with
  the values of whichever database `DB_TYPE` points to.

**Setting up Supabase** (free plan):
1. Create a project at supabase.com. For the region choose **East US (North Virginia)** from the
   list of specific regions, not the automatic ("smart") choice, which can pick another one.
   Choose a database password and keep it: it is the `DB_PASSWORD`.
2. In the project click **Connect** and copy the **Session pooler** connection string. Don't use
   "Direct connection": it only works over IPv6 (unless you buy the IPv4 add-on) and many hosts
   have no IPv6. The Session pooler works over IPv4 on port 5432. The string looks like
   `postgresql://postgres.<project-ref>:<password>@<host>:5432/postgres`.
3. From it: `DB_HOST` = `<host>`, `DB_PORT` = `5432`, `DB_USER` = `postgres.<project-ref>` (with
   the project reference, not just `postgres`), `DB_PASSWORD` = the password, `DB_NAME` =
   `postgres`, and `DB_TYPE` = `postgres`. Leave `DB_SSL_MODE` alone.

**Moving the existing data** with `scripts/copy_mysql_to_postgres.py`, once:
1. On a computer with Python 3.11, in the project folder: `pip install -r requirements.txt`.
2. Make a file, e.g. `.env.postgres`, with `DB_TYPE` and the `DB_*` variables of the **new**
   database (step 3 above) and, for the **old** database, `SRC_DB_HOST`, `SRC_DB_PORT`,
   `SRC_DB_USER`, `SRC_DB_PASSWORD`, `SRC_DB_NAME` (today's `DB_*` values of TiDB). The script
   loads the bot's code, which refuses to start without `BOT_TOKEN`, `BOT_ID`, `BOT_USERNAME`,
   `API_ID` and `API_HASH`: put them in the file too (the script doesn't connect to Telegram, so
   placeholders are fine).
3. Stop the bot: what it writes to the old database after the copy would be lost.
4. Run `python scripts/copy_mysql_to_postgres.py --env-file .env.postgres` and type `copy`.
5. When it prints `Done: ... rows in 41 tables copied and checked`, set `DB_TYPE=postgres` and the
   new `DB_*` values wherever the bot runs (Render's environment variables) and start the bot.

What the script does: it only reads the old database; creates the tables in the new one the way
the bot does; copies every row with its id; sets the id counters so new rows continue after the
copied ones; then checks every table (row count and the sum of every number column) against the
old one. All of it is one transaction: if anything is wrong nothing is written to the new
database, and the message says what to do. PostgreSQL can't store the NUL character in a text, so
it is removed if one exists (the script says how many). It refuses to run when the new database
already has rows; `--wipe-target` empties the bot's tables there first to copy again.
**Going back** is `DB_TYPE=mysql` and the old `DB_*` values: the old database is untouched, as it
was when the bot was stopped (what happened on PostgreSQL after that is not in it).

**Supabase free plan: what to know.**
- 500 MB database (the bot's is about 5 MB) and 5 GB of traffic a month.
- A project with too little database activity for a week is paused. A bot that queries it all
  day doesn't qualify; if it ever happens, press Resume in the dashboard (data is kept).
- **There are no automatic backups on the free plan.** Export the database from time to time,
  e.g. with `pg_dump` and the Session pooler connection string (needs the PostgreSQL client
  tools; I did not test this one). Keeping the old TiDB cluster for a while is a backup of the
  data as it was on the day of the switch.
- Text comparisons with `=` / `LIKE` are case-sensitive on both TiDB's default collation and
  PostgreSQL, so searches behave the same. Sorting a text column (names with capital letters or
  accents) can come out in a slightly different order on PostgreSQL.

**What changed in the code** (everything else is untouched):
- `resources/Database.py` picks MySQL or PostgreSQL from `DB_TYPE` (anything else raises a clear
  error naming the accepted values). The PostgreSQL connection has a 10 second connect timeout
  and TCP keepalives so that a silently dropped connection is noticed in about a minute, and
  it reconnects by itself when the server closes the connection (peewee only recognizes MySQL's
  messages for that, so the PostgreSQL ones were added). `requirements.txt` gets
  `psycopg2-binary`; `resources/Environment.py` gets the two settings.
- **Dividing by two.** The bounty reset halves bounties (`User.bounty / 2`, 3 places in
  `bounty_service.py`) and `Crew.reset_level` halves levels. MySQL divides with decimals and
  rounds when it saves (5 / 2 gives 3); PostgreSQL divides whole numbers and rounds down (5 / 2
  gives 2), so every reset would have left people a little lower than on MySQL. The divisor is
  now `DIVIDE_BY_TWO` (`SQL("2.0")`, in `BaseModel.py`), which gives the same results on both.
  Writing `2.0` as a number doesn't work: peewee turns it into the integer 2 for an integer
  column, which is why it is written as SQL.
- `Crew.set_is_full_for_all_crews` was a hand-written MySQL query (`IF(...)`, and the table name
  `user` without quotes, a reserved word on PostgreSQL). It is now a normal peewee update.
- `ensure_legendary_pirate_schema` (`LegendaryPirate.py`) wrote MySQL column types (`DATETIME`,
  `TINYINT`) in its `ALTER TABLE`; it now writes the types of the database in use.
- 10 startup migrations (6 in `User.py`, one each in `Group.py`, `Game.py`, `BountyLoan.py`,
  `GroupChatAutoDelete.py`) used `MySQLMigrator` directly. On PostgreSQL its add-column and
  drop-not-null steps fail (they use MySQL's `DESCRIBE`) and the `try/except: pass` around them
  would have hidden it, so a column added by a future update would never be created. They use
  `SchemaMigrator.from_database(...)`, which gives the right migrator for the database in use.
  (Creating an index worked on both.)
- `scripts/copy_mysql_to_postgres.py` is new, as described above.

**On verification.** On a real PostgreSQL 16.2 and a real MariaDB 10.11 (the sandbox has no
TiDB, so MariaDB stands in for MySQL), through the bot's own `Database.py`:
- The 6 test suites that touch the real tables: 233 of 233 checks pass on each. All the older
  suites (525 checks, on SQLite) still pass.
- A smoke test filled all 41 tables with generated rows in every column (unicode, NULLs, big
  numbers, self links), then called every plain method of every model on several rows and the
  query-heavy service functions: 562 query calls, 0 SQL errors on PostgreSQL. As a control, the
  old hand-written query of `set_is_full_for_all_crews` is flagged by the same harness.
- Results of the halving, rounding and the rest of the changed expressions are identical on
  PostgreSQL and MariaDB.
- Copy script: 32 checks (from a SQLite copy of the tables, with generated data in every column
  of every table), then the actual command, MariaDB to PostgreSQL: 1,230 rows in 41 tables came
  across identical, row by row; the id counters continue after the last row; answering `no`
  writes nothing; a second run is refused; `--wipe-target` copies again.

**What I could not verify:** Supabase itself and TiDB (no access from here), Telegram, your real
data (the tests used generated rows), and the speed of the bot against Supabase from your host.
The code paths that need a live Telegram chat were not run on PostgreSQL; the database calls
they make were, through the models and services they use.

## Crew settings: four of the five ✅/❌ buttons showed the opposite of the setting; the emoji now comes after the text

**What was happening.** On the Crew settings screen, "Allow search", "Allow join", "Auto-accept
join" and "Allow Davy Back Fight request" showed ✅ when the setting was disabled and ❌ when it
was enabled (a Crew with the default settings, the first four on, showed four ❌). Only
"Auto-accept Davy Back Fight request" showed the real value. The "Current setting: ..." lines of
the message were right, so the screen contradicted itself. `screen_crew_modify.py` built the
emoji of those four with `get_enabled_emoji(not crew.<setting>)`; the `not` is in the PTB source
too (the same lines), so it is not a Telethon-specific bug.

**Fix:** the `not` is gone, so every button shows the value its setting has now, and pressing it
shows the new value. The emoji of the five buttons also comes after the text now ("Allow search
✅"), in English and in Persian (`PVT_KEY_CREW_EDIT_*` in `phrases_en.py` and `phrases_fa.py`, with
the `{}` moved to the end). The colors of the buttons are not affected: they are chosen from the
words of the button without the emoji, and these five have no color. **Not changed:** the
"Current setting: ✅ Enabled / ❌ Disabled" lines of the message, because that emoji belongs to the
"Enabled" / "Disabled" phrases that other screens share.

**On verification:** the real `screen_crew_modify.manage` on an in-memory SQLite database with the
project's real tables and real Crew / User rows, for all 32 combinations of the five settings in
English and in Persian (160 buttons each). Each button ends with the emoji of the stored value and
doesn't start with one; the "Current setting" lines show the stored values; pressing each of the
five buttons, from enabled and from disabled, changes only that setting and only that button; a
plain member sees the same buttons but gets the "only the Captain or First Mate" warning when
pressing one, and a First Mate can change a setting. On the previous code 26 of the test's 93
checks fail, as reported; now all 93 pass. **What I could not verify:** how Telegram draws it on
your phone, mainly the Persian text (right to left) with the emoji at the end.

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
  error text). MTProto's error for it is `USER_IS_BOT` (Telethon's
  `UserIsBotError`, "Bots can't send messages to other bots"), which
  `translate_errors()` turns into a `BadRequest` carrying that marker - see
  "Messaging another bot was reported as an unhandled exception" above. (An
  earlier version of this note said the real error couldn't be confirmed; an
  error-log report did.)
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
