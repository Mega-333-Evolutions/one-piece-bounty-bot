import resources.Environment as Env
from src.model.enums.CommandName import CommandName
from src.model.enums.Emoji import Emoji


def surround_with_arrows(text: str) -> str:
    """
    Surround the text with left and right arrows
    :param text: The text
    :return: The text surrounded with left and right arrows
    """
    return Emoji.RIGHT_ARROW + text + Emoji.LEFT_ARROW


def surround_with_expandable_quote(text: str) -> str:
    """
    Surround the text with expandable quote
    :param text: The text
    :return: The text surrounded with expandable quote
    """

    # Add quote to every line
    text = text.replace("\n", "\n>")
    # Remove double quotes
    text = text.replace("\n>>", "\n>")

    # Add quote to beginning of the text if not already present
    if not text.startswith(">") and not text.startswith("\n"):
        text = ">" + text

    # Add || to the end of the text if not already present
    if not text.endswith("||"):
        text += "||"

    return text


ANTI_SPAM_WARNING = "پیام‌های زیادی ارسال شده، لطفاً آهسته‌تر پیش بروید..."
SUPPORT_GROUP_DEEPLINK = f"[گروه پشتیبانی]({Env.SUPPORT_GROUP_LINK.get()})"

COMMAND_NOT_IN_REPLY_ERROR = "این دستور فقط در پاسخ به یک پیام قابل استفاده است"
COMMAND_IN_REPLY_TO_BOT_ERROR = "این دستور را نمی‌توان در پاسخ به یک ربات استفاده کرد"
COMMAND_IN_REPLY_TO_ERROR = "این دستور را نمی‌توان در پاسخ به پیام خودتان استفاده کرد"
COMMAND_NOT_ACTIVE_ERROR = "این دستور دیگر در دسترس نیست"
COMMAND_NOT_ACTIVE_WITH_REPLACEMENT_ERROR = (
    COMMAND_NOT_ACTIVE_ERROR + ". " + "لطفاً به‌جای آن از {} استفاده کنید"
)
COMMAND_FOR_NEW_WORLD_USERS_ERROR = "این دستور فقط برای کاربران دنیای جدید در دسترس است"
COMMAND_FOR_USERS_AFTER_LOCATION_ERROR = (
    "این دستور فقط برای کاربرانی در دسترس است که به *{}* رسیده‌اند.\n\nموقعیت فعلی: *{}*"
)
COMMAND_FOR_USERS_AFTER_LOCATION_BOUNTY_ERROR = (
    "\nجایزه فعلی: ฿*{}*\nجایزه مورد نیاز: ฿*{}*\nجایزه کسری: ฿*{}*"
)
COMMAND_FOR_USERS_AFTER_LOCATION_ERROR_JOIN_CREW = (
    "\n\n_برای بالا بردن سریع‌تر سطح موقعیت خود، به یک خدمه بپیوندید!_"
)
COMMAND_WHILE_ARRESTED_ERROR = "این دستور در زمانی که بازداشت هستید در دسترس نیست"
COMMAND_ONLY_BY_CREW_CAPTAIN_ERROR = "این دستور فقط برای کاپیتان‌های خدمه در دسترس است"
COMMAND_ONLY_BY_CREW_CAPTAIN_OR_FIRST_MATE_ERROR = (
    "این دستور فقط برای کاپیتان‌ها و معاون‌های اول خدمه در دسترس است"
)
COMMAND_NOT_IN_REPLY_TO_CREW_MEMBER_ERROR = (
    "این دستور فقط در پاسخ به پیامی از یک عضو خدمه قابل استفاده است"
)
COMMAND_ONLY_BY_BOSS_ERROR = (
    "این دستور فقط توسط یک ادمین، پادشاه دزدان دریایی یا یک دزد دریایی افسانه‌ای قابل استفاده است"
)
COMMAND_IN_REPLY_TO_ARRESTED_ERROR = (
    "این دستور را نمی‌توان در پاسخ به پیامی از یک کاربر بازداشت‌شده استفاده کرد"
)
COMMAND_ONLY_BY_CHAT_ADMIN_ERROR = "این دستور فقط توسط ادمین چت قابل استفاده است"
COMMAND_FEATURE_DISABLED_ERROR = (
    "این قابلیت در حال حاضر در این {} غیرفعال است.\nمی‌توانید از یک ادمین بخواهید آن را از طریق"
    f" {CommandName.SETTINGS.get_formatted()} فعال کند"
)
COMMAND_NOT_ALLOWED_FROM_DEEPLINK_ERROR = "این دستور از طریق دیپ‌لینک مجاز نیست"
COMMAND_START_IN_GROUP_ERROR = "شما نمی‌توانید از این دستور اینجا استفاده کنید.\n\nبرای شروع ربات در پیام خصوصی، دکمه زیر 👇 را بزنید."
COMMAND_START_IN_GROUP_BUTTON = "شروع"

SHOW_USER_STATUS = "کاربر: {}\nجایزه: ฿*{}*{}\nرتبه: {}{}{}"
SHOW_USER_STATUS_LOCATION = "\nموقعیت: {}"
SHOW_USER_STATUS_FROZEN_BOUNTY = " \\(منجمد شده\\)"
SHOW_USER_STATUS_RANK_PRISONER = Emoji.PRISONER + " زندانی"
SHOW_USER_STATUS_IMPEL_DOWN = "ایمپل دان"
SHOW_USER_STATUS_PENDING_BOUNTY = "\nجایزه در انتظار: ฿*{}*"
SHOW_USER_STATUS_REMAINING_SENTENCE = "\nمدت باقی‌مانده محکومیت: {}"
SHOW_USER_STATUS_PERMANENT_IMPEL_DOWN = "دائمی"
SHOW_USER_STATUS_RESTRICTIONS = f"\n\n{Emoji.LOG_NEGATIVE}*محدودیت‌ها*{{}}"
SHOW_USER_STATUS_FIGHT_IMMUNITY = "\nمصونیت نبرد: {}"
SHOW_USER_STATUS_FIGHT_COOLDOWN = "\nزمان انتظار نبرد: {}"
SHOW_USER_STATUS_PLUNDER_IMMUNITY = "\nمصونیت غارت: {}"
SHOW_USER_STATUS_PLUNDER_COOLDOWN = "\nزمان انتظار غارت: {}"
SHOW_USER_STATUS_WARLORD_REMAINING_TIME = "\nزمان باقی‌مانده جنگ‌سالار: {}"
SHOW_USER_STATUS_CREW = "\nخدمه: {}"
SHOW_USER_STATUS_BOUNTY_DEDUCTIONS_TITLE = "\n\n*کسورات جایزه*"
SHOW_USER_STATUS_BOUNTY_DEDUCTIONS_TEXT = "\n{}{} \\({}%\\)"
SHOW_USER_STATUS_EXPIRED_LOAN = "وام منقضی‌شده"
SHOW_USER_STATUS_INCOME_TAX = "مالیات بر درآمد"
SHOW_USER_STATUS_ADD_REPLY = "_درخواست‌شده توسط {}_"
SHOW_USER_STATUS_DEVIL_FRUIT = "\n\n*میوه شیطانی*\n_{}_{}"
SHOW_USER_STATUS_CREW_ABILITIES = "\n\n*توانایی‌های خدمه*{}"
NOT_ALLOWED_TO_VIEW_REPLIED_STATUS = (
    "شما فقط می‌توانید وضعیت کسانی که رتبه پایین‌تری از شما دارند را ببینید.\n\nرتبه {}: {}\nرتبه {}: {}"
)
SHOW_USER_STATUS_DAILY_REWARD = (
    f"\n\n>یک جایزه روزانه در انتظار شماست، برای دریافت آن از {CommandName.DAILY_REWARD.get_non_formatted()} در"
    " پیام خصوصی با ربات یا در یک گروه استفاده کنید!"
)
ROOKIE_STATUS_PRIVATE_CHAT_ONLY = "تازه‌کارها فقط می‌توانند وضعیت خود را در پیام خصوصی مشاهده کنند"
PRISONER_STATUS_PRIVATE_CHAT_ONLY = "زندانی‌ها فقط می‌توانند وضعیت خود را در پیام خصوصی مشاهده کنند"
STATUS_PRIVATE_CHAT_KEY = "مشاهده در پیام خصوصی"

JOIN_SUPPORT_GROUP = f">برای سوالات یا پیشنهادات، لطفاً به {SUPPORT_GROUP_DEEPLINK} بپیوندید"

LEADERBOARD = (
    "جدول امتیازات *{}* برای هفته *{}* از *{}*\n\n*در اینجا برترین {} کاربر با بیشترین"
    " جایزه‌ها آورده شده‌اند*:{}{}{}{}{}\n\n{}_بازنشانی بعدی جایزه در {} \\(در {}\\)_\n" + JOIN_SUPPORT_GROUP
)
LEADERBOARD_USER_ROW = "\n\n{}°: {}\n{} - ฿*{}*"
LEADERBOARD_CREW_ROW = "\n\n{}°: {}\n*کاپیتان*: {}"
LEADERBOARD_CREW = f"\n\n\n{Emoji.CREW}*در اینجا برترین {{}} خدمه آورده شده‌اند*:{{}}"
LEADERBOARD_LOCAL = "محلی"
LEADERBOARD_GLOBAL = "جهانی"
LEADERBOARD_VIEW_GLOBAL_LEADERBOARD = "\n\n\n" + Emoji.GLOBE + "[جدول امتیازات جهانی]({})"
LEADERBOARD_WARLORDS = "\n\n\n" + Emoji.LEADERBOARD_WARLORD + " *جنگ‌سالاران*"
LEADERBOARD_WARLORD_ROW = "\n• [{}]({})"
LEADERBOARD_LEGENDARY_PIRATES = "\n\n\n" + Emoji.LEADERBOARD_LEGENDARY_PIRATE + " *دزدان دریایی افسانه‌ای*"
LEADERBOARD_LEGENDARY_PIRATE_ROW = "\n• [{}]({})"
LEADERBOARD_RANK_PIRATE_KING = "پادشاه دزدان دریایی"
LEADERBOARD_RANK_EMPEROR = "امپراتور"
LEADERBOARD_RANK_FIRST_MATE = "معاون اول"
LEADERBOARD_RANK_SUPERNOVA = "سوپرنوا"
LEADERBOARD_RANK_ROOKIE = "تازه‌کار"
LEADERBOARD_RANK_ADMIN = "دریابان"
LEADERBOARD_RANK_LEGENDARY_PIRATE = "دزد دریایی افسانه‌ای"
LEADERBOARD_RANK_WARLORD = "جنگ‌سالار"
LEADERBOARD_VIEW_BOUNTIES_RESET = f"\n>{Emoji.INFO}*جایزه‌ها بازنشانی شده‌اند*\n"


SAVE_MEDIA_NOT_IN_REPLY_TO_MEDIA = "این دستور فقط در پاسخ به یک پیام رسانه‌ای قابل استفاده است"
SAVED_MEDIA_UNKNOWN_TYPE = "نوع رسانه ناشناخته. انواع موجود عبارتند از: *{}*"
SAVE_MEDIA_SUCCESS = "رسانه با نام *{}* ذخیره شد"

GAME_WIN_LOSE_STATUS = (
    "جایزه فعلی: ฿*{}*\nجایزه نهایی در صورت برد: ฿*{}*\nجایزه نهایی در صورت باخت: ฿*{}*"
)
GAME_WIN_STATUS = "_شما ฿*{}* بردید!_\n_جایزه فعلی: ฿*{}*_"
GAME_LOSE_STATUS = "_شما ฿*{}* باختید!_\n_جایزه فعلی: ฿*{}*_"

DOC_Q_GAME_NOT_ENOUGH_BOUNTY = (
    "برای احضار داک کیو به جایزه‌ای حداقل ฿*{}* نیاز دارید.\n\n_جایزه فعلی: ฿*{}*_"
)
DOC_Q_GAME_LIMIT_REACHED = "شما به محدودیت بازی‌های داک کیو رسیده‌اید. می‌توانید دوباره در *{}* بازی کنید"
DOC_Q_GAME_START = (
    "سلام {}، اجازه بده یک سیب به تو پیشنهاد بدم.\nاگر سیب درست را انتخاب کنی، ฿*{}* برنده می‌شوی، در غیر این صورت"
    " ฿*{}* می‌بازی.\nعاقلانه انتخاب کن!" + "\n\n" + GAME_WIN_LOSE_STATUS
)

DOC_Q_GAME_NOT_FOUND = "بازی داک کیو یافت نشد"
DOC_Q_GAME_CANCEL = "دفعه بعد می‌بینمت!"
DOC_Q_GAME_WIN = (
    "تو... ها ها... کوف! کوف!... واقعاً خوش‌شانسی {}.\nبزن بریم، استرانگر... آه..!"
    + "\n\n{}"
    + GAME_WIN_STATUS
)
DOC_Q_GAME_LOSE = (
    "به نظر می‌رسد امروز روز شانس تو نبود {}... کوف!... فقط سیب *{}°* دستکاری‌نشده بود"
    " ها ها...\nاینقدر بی‌احتیاط نباش وگرنه در این دریاهای خطرناک دوام نمی‌آوری!\nبزن"
    " بریم، استرانگر... آه..!" + "\n\n{}" + GAME_LOSE_STATUS
)

# Error messages
USER_NOT_FOUND = "کاربر یافت نشد"
UNRECOGNIZED_SCREEN = "دستور ناشناخته"
SAVED_MEDIA_NOT_FOUND = "رسانه ذخیره‌شده یافت نشد"
UNKNOWN_EXTRA_STEP = "مرحله اضافی ناشناخته"
PRIVATE_STEP_NOT_SET = "مرحله خصوصی تنظیم نشده است"
SAVED_USER_DATA_NOT_FOUND = "اطلاعات ذخیره‌شده کاربر یافت نشد"
RESTART_BOT = "اوه، به نظر می‌رسد خطایی رخ داده است. لطفاً ربات را ری‌استارت کنید"
FORWARD_TO_SUPPORT_GROUP = f". لطفاً این پیام را به {SUPPORT_GROUP_DEEPLINK} فوروارد کنید"

# Keyboard options
KEYBOARD_OPTION_CANCEL = Emoji.CANCEL + " لغو"
KEYBOARD_OPTION_DELETE = Emoji.DELETE + " حذف"
KEYBOARD_OPTION_CLOSE = Emoji.CLOSE + " بستن"
KEYBOARD_OPTION_ACCEPT = Emoji.ACCEPT + " پذیرفتن"
KEYBOARD_OPTION_REJECT = Emoji.REJECT + " رد کردن"
KEYBOARD_OPTION_FIGHT = Emoji.FIGHT + " نبرد"
KEYBOARD_OPTION_PLUNDER = Emoji.PLUNDER + " غارت"
KEYBOARD_OPTION_RETREAT = Emoji.RETREAT + " عقب‌نشینی"
KEYBOARD_OPTION_BACK = Emoji.BACK + " بازگشت"
KEYBOARD_OPTION_YES = Emoji.YES + " بله"
KEYBOARD_OPTION_NO = Emoji.NO + " خیر"
KEYBOARD_OPTION_SEND_REQUEST = Emoji.YES + " ارسال درخواست"
KEYBOARD_OPTION_RESET = Emoji.RESET + " بازنشانی"
KEYBOARD_OPTION_SCOUT = Emoji.BINOCULARS + " شناسایی"
KEYBOARD_OPTION_NEW_SCOUT = Emoji.BINOCULARS + " شناسایی جدید"
KEYBOARD_OPTION_CHOOSE = Emoji.ENABLED + " انتخاب"

TEXT_YES = "بله"
TEXT_NO = "خیر"
TEXT_WON = "برد"
TEXT_LOST = "باخت"
TEXT_IT_WAS = "بود"
TEXT_THEY_WERE = "بودند"
TEXT_FROM = "از"
TEXT_TO = "به"
TEXT_TOPIC = "موضوع"
TEXT_GROUP = "گروه"
TEXT_NOT_SET = "تنظیم نشده"
TEXT_RANDOM = "تصادفی"
TEXT_ONLY = "فقط {}"
TEXT_YOU = "شما"
TEXT_YOUR = "شما"
TEXT_STOLE = "دزدید"
TEXT_OWE = "[بدهکار]({})"
TEXT_OWE_NOTHING_IMMUNE = "چیزی بدهکار نبود \\(مصون\\)"
TEXT_NEVER = "هرگز"
TEXT_YOURSELF = "خودتان"

TEXT_DAY = "روز"
TEXT_DAYS = "روز"

EXCEPTION_CHAT_ID_NOT_PROVIDED = "chat_id is None and update.effective_chat.id is None"
EXCEPTION_NO_EDIT_MESSAGE = "new_message is False but update.callback_query is None"

KEYBOARD_NOT_FOUND = "کیبورد یافت نشد"
KEYBOARD_USE_UNAUTHORIZED = "شما مجاز به استفاده از این کیبورد نیستید"

SWAP_SUCCESSFUL = "جابه‌جایی موفقیت‌آمیز بود"
RESET_SUCCESSFUL = "بازنشانی موفقیت‌آمیز بود"
VIEW_ALL_WITH_EMOJI = "\n>" + Emoji.RIGHT_ARROW + " [مشاهده همه]({})"

LOCATION_CHANGE_REGION_PROPOSAL = "{}{} آیا مایلید به {} نقل مکان کنید؟"
LOCATION_CHANGE_REGION_PROPOSAL_REJECTED = "{}بعداً می‌توانید با دستور {} به {} نقل مکان کنید"
LOCATION_NEW_WORLD_REQUEST_REJECTED_NOT_ENOUGH_BOUNTY = (
    "برای نقل مکان به دنیای جدید به جایزه‌ای حداقل ฿*{}* نیاز دارید."
)
LOCATION_ALREADY_IN_REGION = "شما همین حالا در {} هستید"
LOCATION_CANNOT_CHANGE_REGION = "شما می‌توانید منطقه را در *{}* تغییر دهید"
LOCATION_INVALID_CHANGE_REGION_REQUEST = "منطقه نامعتبر"

CHALLENGER = "چالش‌دهنده"
OPPONENT = "حریف"
SENDER = "فرستنده"
RECEIVER = "گیرنده"

FIGHT_NOT_FOUND = "نبرد یافت نشد"
FIGHT_OPPONENT_NOT_FOUND = "حریف یافت نشد"
FIGHT_CANNOT_FIGHT_USER = "شما نمی‌توانید با این کاربر مبارزه کنید"
FIGHT_CANNOT_FIGHT_CREW_MEMBER = "شما نمی‌توانید با یکی از اعضای خدمه خود مبارزه کنید"
FIGHT_USER_IN_COOLDOWN = "زمان انتظار نبرد فعال است. می‌توانید نبردی را در *{}* آغاز کنید"
FIGHT_CONFIRMATION_ODDS_RECALCULATED = (
    "\n_*\\(احتمال بر اساس میانگین جایزه خدمه حریف دوباره محاسبه شد\\)*_"
)
FIGHT_CONFIRMATION_REQUEST = (
    "{} آیا مطمئنید که می‌خواهید با {} مبارزه کنید؟\nمن احتمال {}% برای {} پیش‌بینی می‌کنم."
    + "{}\n\n"
    + GAME_WIN_LOSE_STATUS
)
FIGHT_CONFIRMATION_OUTCOME_VICTORY = "پیروزی"
FIGHT_CONFIRMATION_OUTCOME_DEFEAT = "شکست"
FIGHT_WIN = (
    "همان‌طور که پیش‌بینی کردم، {} نبرد را در برابر {} برد.\nنیازی به کارت‌ها ندارم تا بگویم که"
    " قدرت تو باورنکردنی است..." + "\n\n" + GAME_WIN_STATUS
)
FIGHT_LOSE = (
    "همان‌طور که پیش‌بینی کردم، {} نبرد را در برابر {} باخت.\nبه نظر می‌رسد شانست تمام شده..."
    + "\n\n"
    + GAME_LOSE_STATUS
)
FIGHT_CONFIRMATION_RETREAT = "شما با موفقیت عقب‌نشینی کردید"
FIGHT_REVENGE_TOO_LATE = (
    "فقط در صورتی می‌توانید انتقام یک نبرد را بگیرید که کمتر از {} از زمان حمله گذشته باشد.\n\nزمان سپری‌شده: {}"
)
FIGHT_REVENGE_ALREADY_REVENGED = "این نبرد قبلاً انتقام گرفته شده است\n\n[مشاهده انتقام]({})"
FIGHT_PLUNDER_SCOUT_FEE = "\n\nهزینه شناسایی: ฿*{}*\nجایزه فعلی: ฿*{}*"
FIGHT_PLUNDER_GROUP_INSUFFICIENT_SCOUT_BOUNTY = (
    "جایزه کافی برای شناسایی حریف وجود ندارد." + FIGHT_PLUNDER_SCOUT_FEE
)
FIGHT_PLUNDER_PRIVATE_INSUFFICIENT_SCOUT_BOUNTY = (
    "جایزه کافی برای شناسایی حریفان وجود ندارد." + FIGHT_PLUNDER_SCOUT_FEE
)
FIGHT_PLUNDER_SCOUT_USER_GROUP = "آیا مطمئنید که می‌خواهید {} را شناسایی کنید؟\nهزینه آن ฿*{}* خواهد بود"
FIGHT_PLUNDER_SCOUT_SEARCH = "آیا مایلید به دنبال حریف بگردید؟" + FIGHT_PLUNDER_SCOUT_FEE
FIGHT_PLUNDER_SCOUT_SEARCH_USER = (
    "حریف: *{}*\nاحتمال برد: *{}%*\nبرد احتمالی: ฿*{}*\nباخت احتمالی: ฿*{}*{}\n\nهزینه"
    " شناسایی بعدی:  ฿*{}*\nجایزه فعلی: ฿*{}*"
)
FIGHT_PLUNDER_SCOUT_SEARCH_USER_NEW = "حریف جدید یافت شد!\n\n"
FIGHT_PLUNDER_SCOUT_USER_JAIL_TIME = "\nزمان احتمالی حبس: *{}*"
FIGHT_PLUNDER_SCOUT_NO_OPPONENT_FOUND = (
    "هیچ حریفی یافت نشد، لطفاً بعداً دوباره امتحان کنید.\n\n_هیچ هزینه شناسایی کسر نشد_"
)
FIGHT_PLUNDER_SCOUT_NEXT_FEE = "\n\nهزینه شناسایی بعدی: ฿*{}*"

ENABLED = Emoji.ENABLED + " فعال"
DISABLED = Emoji.DISABLED + " غیرفعال"
CURRENT_SETTING = "تنظیم فعلی: {}"

INLINE_QUERY_SEND_ITEM = "ارسال مورد"

# General
KEY_MANAGE = "مدیریت"
KEY_VIEW = "مشاهده"
KEY_CREATE = Emoji.CREATE + " ایجاد"
KEY_SAVE = Emoji.SAVE + " ذخیره"
KEY_ENABLE = Emoji.ENABLED + " فعال‌سازی"
KEY_DISABLE = Emoji.DISABLED + " غیرفعال‌سازی"
KEY_OPEN = "باز کردن"
KEY_CLOSE = Emoji.CLOSE + " بستن"
KEY_SHARE = Emoji.SHARE + " اشتراک‌گذاری"
KEY_SEND_TO_GROUP = Emoji.GROUP + " ارسال به گروه"
KEY_SET_RESULT = "تنظیم نتیجه"
KEY_CONFIRM = "تأیید"
KEY_MODIFY = "ویرایش"
KEY_RESET = "بازنشانی"
KEY_SHOP = Emoji.SHOP + " فروشگاه"
KEY_REMOVE = Emoji.DELETE + " حذف"
KEY_BUY = "خرید"
KEY_MANAGE_DEVIL_FRUIT = "مدیریت میوه شیطانی"
KEY_JOIN_A_CREW = "پیوستن به یک خدمه"
KEY_VIEW_LOG = "مشاهده گزارش"

TXT_SETTINGS = "کدام تنظیم را می‌خواهید تغییر دهید؟"

# Private chat
PVT_TXT_START = (
    "به One Piece Bounty Bot خوش آمدید، رباتی که سیستم جایزه را به هر گروه چتی می‌آورد!"
    f"\n\n{JOIN_SUPPORT_GROUP}"
)
PVT_KEY_SETTINGS = Emoji.SETTINGS + " تنظیمات"
PVT_KEY_STATUS = Emoji.STATUS + " وضعیت"
PVT_KEY_SETTINGS_LOCATION_UPDATE = "به‌روزرسانی موقعیت"
PVT_TXT_SETTINGS_LOCATION_UPDATE = (
    "آیا می‌خواهید هنگام رفتن به موقعیت جدید به‌روزرسانی دریافت کنید؟"
)
PVT_KEY_CREW = Emoji.CREW + " خدمه"
PVT_KEY_CREW_MEMBERS = "اعضا"
PVT_KEY_CREW_MEMBER_VIEW = "مشاهده عضو"
PVT_KEY_CREW_LEAVE = "خروج"
PVT_KEY_CREW_SEARCH = Emoji.SEARCH + " جستجو"
PVT_KEY_CREW_SEARCH_JOIN = "پیوستن"
PVT_KEY_CREW_EDIT_NAME = "نام"
PVT_KEY_CREW_EDIT_DESCRIPTION = "توضیحات"
PVT_KEY_CREW_EDIT_REQUIRED_BOUNTY = "جایزه مورد نیاز"
PVT_KEY_CREW_EDIT_ALLOW_VIEW_IN_SEARCH = "{} اجازه جستجو"
PVT_KEY_CREW_EDIT_ALLOW_JOIN_FROM_SEARCH = "{} اجازه پیوستن"
PVT_KEY_CREW_EDIT_AUTO_ACCEPT_JOIN = "{} پذیرش خودکار عضویت"
PVT_KEY_CREW_EDIT_ALLOW_DAVY_BACK_FIGHT_REQUEST = "{} اجازه درخواست دیوی بک فایت"
PVT_KEY_CREW_EDIT_AUTO_ACCEPT_DAVY_BACK_FIGHT_REQUEST = "{} پذیرش خودکار درخواست دیوی بک فایت"
PVT_KEY_CREW_EDIT_DAVY_BACK_FIGHT_DEFAULT_PARTICIPANTS = "شرکت‌کنندگان پیش‌فرض DBF"
PVT_KEY_CREW_DISBAND = Emoji.DELETE + " انحلال"
PVT_KEY_CREW_MEMBER_REMOVE = "اخراج"
PVT_KEY_CREW_MEMBER_FIRST_MATE_PROMOTE = "ارتقا به معاون اول"
PVT_KEY_CREW_MEMBER_FIRST_MATE_DEMOTE = "تنزل از معاون اول"
PVT_KEY_CREW_MEMBER_CAPTAIN_PROMOTE = "ارتقا به کاپیتان"
KEY_POST_BAIL = "پرداخت وثیقه"
PVT_KEY_CREW_ABILITY = "توانایی‌ها"
PVT_KEY_CREW_ABILITY_ACTIVATE = "فعال‌سازی"
PVT_KEY_CREW_ABILITY_RANDOM = Emoji.DICE + " تصادفی"
PVT_KEY_CREW_POWERUP = "تقویت"
PVT_KEY_CREW_LEVEL = "سطح"
PVT_KEY_CREW_LEVEL_UP = "ارتقای سطح"
PVT_KEY_CREW_DAVY_BACK_FIGHT = Emoji.FIGHT + " دیوی بک فایت"
PVT_KEY_CREW_DAVY_BACK_FIGHT_EDIT_PARTICIPANTS = "ویرایش شرکت‌کنندگان"
PVT_KEY_CREW_DAVY_BACK_FIGHT_EDIT_DURATION = "ویرایش مدت زمان"
PVT_KEY_CREW_DAVY_BACK_FIGHT_EDIT_PENALTY = "ویرایش جریمه"
PVT_KEY_CREW_DAVY_BACK_FIGHT_PARTICIPANT_SELECT = "انتخاب بازیکنان"
PVT_KEY_CREW_DAVY_BACK_FIGHT_PARTICIPANT_VIEW = "بازیکنان"
PVT_KEY_CREW_DAVY_BACK_FIGHT_CONSCRIPT_OPPONENT = "سربازگیری حریف"
PVT_KEY_SETTINGS_NOTIFICATIONS = "اعلان‌ها"
PVT_TXT_SETTINGS_NOTIFICATIONS = "کدام دسته از اعلان‌ها را می‌خواهید تغییر دهید؟"
PVT_TXT_SETTINGS_NOTIFICATIONS_TYPE = "کدام اعلان را می‌خواهید تغییر دهید؟"
PVT_KEY_MANAGE_NOTIFICATION_SETTINGS = "مدیریت تنظیمات اعلان"
PVT_KEY_SETTINGS_TIMEZONE = "منطقه زمانی"
PVT_TXT_SETTINGS_TIMEZONE = (
    "\nزمان فعلی: *{}*\nمنطقه زمانی فعلی: *{}* \\({}\\)\n\nبرای تنظیم منطقه زمانی جدید، نام یک"
    " موقعیت \\(شهر، منطقه، ایالت یا کشور\\) ارسال کنید"
)
PVT_TXT_SETTINGS_TIMEZONE_INVALID = (
    "موقعیت نامعتبر. لطفاً نام موقعیت صحیح \\(شهر، منطقه، ایالت یا کشور\\) ارسال کنید"
)
PVT_KEY_SETTINGS_TIMEZONE_RESET = "بازنشانی"
PVT_TXT_SETTINGS_TIMEZONE_UNKNOWN = "پیش‌فرض - " + Env.TZ.get()
PVT_KEY_SETTINGS_LANGUAGE = "زبان"
PVT_TXT_SETTINGS_LANGUAGE = (
    "زبانی که می‌خواهید در پیام خصوصی با شما استفاده کنم را انتخاب کنید."
    "\n\nزبان فعلی: *{}*"
)

PVT_KEY_LOGS = Emoji.LOGS + " گزارش‌ها"
PVT_TXT_LOGS = "کدام گزارش را می‌خواهید مشاهده کنید؟"
PVT_KEY_LOGS_STATS = Emoji.STATS + " آمار"
PVT_KEY_PREVIOUS_PAGE = Emoji.LEFT_ARROW
PVT_KEY_NEXT_PAGE = Emoji.RIGHT_ARROW
PVT_KEY_PREDICTION = Emoji.PREDICTION + " پیش‌بینی‌ها"
PVT_KEY_PREDICTION_DETAIL_PLACE_BET = "ثبت شرط"
PVT_KEY_PREDICTION_DETAIL_REMOVE_BET = "حذف شرط"
PVT_KEY_PREDICTION_DETAIL_EDIT = "ویرایش"
PVT_KEY_PREDICTION_CREATE_ALLOW_MULTIPLE_CHOICES = "اجازه انتخاب چندگانه"
PVT_KEY_PREDICTION_CREATE_ALLOW_BET_WITHDRAWAL = "اجازه لغو شرط"
PVT_KEY_PREDICTION_CREATE_IS_PUBLIC = "عمومی"
PVT_KEY_PREDICTION_CREATE_SET_CLOSE_DATE = Emoji.PREDICTION_CLOSED + " تنظیم تاریخ بسته شدن"
PVT_KEY_PREDICTION_CREATE_REMOVE_CLOSE_DATE = Emoji.PREDICTION_CLOSED + " حذف تاریخ بسته شدن"
PVT_KEY_PREDICTION_CREATE_SET_CUT_OFF_DATE = Emoji.PREDICTION_CUT_OFF + " تنظیم تاریخ قطع شرط‌بندی"
PVT_KEY_PREDICTION_CHANGE_POLL = Emoji.CHANGE + " تغییر نظرسنجی"
PVT_KEY_PREDICTION_NO_CORRECT_OPTION = "بدون گزینه صحیح"
PVT_KEY_DEVIL_FRUIT = Emoji.DEVIL_FRUIT + " میوه شیطانی"
PVT_KEY_DEVIL_FRUIT_DETAIL_EAT = "خوردن"
PVT_KEY_DEVIL_FRUIT_DETAIL_SELL = "فروش"
PVT_KEY_DEVIL_FRUIT_DETAIL_DISCARD = "دور انداختن"
PVT_KEY_DEVIL_FRUIT_VIEW_IN_SHOP = "مشاهده در فروشگاه"
PVT_KEY_GO_TO_MESSAGE = "رفتن به پیام"
PVT_KEY_BOUNTY_LOAN = Emoji.MONEY + " وام"
PVT_KEY_BOUNTY_LOAN_DETAIL_PAY = "پرداخت"
PVT_KEY_BOUNTY_LOAN_DETAIL_FORGIVE = "بخشش"
PVT_KEY_BOUNTY_LOAN_DETAIL_PAY_ALL = "پرداخت همه"
PVT_KEY_STRING_FILTER_REMOVE = "حذف فیلتر {}"
PVT_KEY_SHOW_ALL = "بازگشت به لیست"
PVT_KEY_FIGHT_REVENGE = Emoji.FIGHT + " انتقام"
PVT_KEY_PLUNDER_REVENGE = Emoji.PLUNDER + " انتقام"

GRP_KEY_DEVIL_FRUIT_BUY = Emoji.MONEY + " خرید"
GRP_KEY_SETTINGS_FEATURES = "قابلیت‌ها"
GRP_KEY_SETTINGS_AUTO_DELETE = "حذف خودکار"
GRP_KEY_SETTINGS_LANGUAGE = "زبان"
GRP_TXT_SETTINGS_LANGUAGE = (
    "زبانی که می‌خواهید در این گروه استفاده کنم را انتخاب کنید."
    "\n\nزبان فعلی: *{}*"
)
GRP_TXT_FEATURES = "{}کدام قابلیت‌های سیستم جایزه را می‌خواهید در این {} فعال کنید؟"
GRP_KEY_PREDICTION_BET_IN_PRIVATE_CHAT = "شرط‌بندی در پیام خصوصی"
GRP_KEY_PREDICTION_VIEW_IN_PRIVATE_CHAT = "مشاهده در پیام خصوصی"
GRP_KEY_GAME_PLAY = "بازی"
GRP_KEY_DAILY_REWARD_PRIZE_ACCEPT = Emoji.MONEY + " پذیرفتن پیشنهاد"
GRP_KEY_DAILY_REWARD_PRIZE_RANDOM = Emoji.GIFT + " جایزه تصادفی"
GRP_KEY_GAME_START_GLOBAL = "شروع فوری به‌صورت جهانی"

DATETIME_EXAMPLES = """
تاریخ را با این فرمت بنویسید:
dd/mm/yy hh:mm

*مثال‌ها*:
• 1/4/2022 22:30
• in 10 days 5 hours 2 minutes
• Tomorrow at 12:00

زمان فعلی: *{}*
منطقه زمانی فعلی: *{}* \\({}\\)
[تغییر منطقه زمانی]({})
""".strip()

DATETIME_EXAMPLES_NO_DURATION = """
تاریخ را با این فرمت بنویسید:
dd/mm/yy hh:mm

*مثال‌ها*:
• 1/4/2022 22:30
• 10 hours ago
• Yesterday at 12:00

زمان فعلی: *{}*
منطقه زمانی فعلی: *{}* \\({}\\)
[تغییر منطقه زمانی]({})
""".strip()

DATETIME_REMAINING = "{} باقی‌مانده"
DATETIME_REMAINING_PARENTHESIS = f" _\\({DATETIME_REMAINING}\\)_"
DATETIME_ELAPSED = "{} پیش"
DATETIME_ELAPSED_PARENTHESIS = f" _\\({DATETIME_ELAPSED}\\)_"

ITEM_LINK = "[{}]({})"

ACTION_INSUFFICIENT_BOUNTY = "جایزه ناکافی، شما حداقل به ฿*{}* نیاز دارید"
ACTION_WAGER_LESS_THAN_MIN = "حداقل مقدار ฿*{}* است"
ACTION_INVALID_WAGER_AMOUNT = (
    "مقدار نامعتبر. مطمئن شوید که عددی با جداکننده اعشاری '.' یا ',' یا با"
    " مقیاس معتبر است.\n\nمثال: \n- 10.000.000 یا 10,000,000\n- 10k, 10thousand, 10m,"
    " 10million, 10b, 10billion"
)
ACTION_INVALID_DURATION = (
    "مدت زمان نامعتبر. مطمئن شوید که عددی با جداکننده اعشاری '.' یا ',' یا با"
    " واحد معتبر است.\n\nمثال: \n - 1min, 1h, 1d, 1week"
)

SYSTEM_UPDATE = (
    f"{Emoji.CONFETTI}به‌روزرسانی جدید{Emoji.CONFETTI}"
    "\n\n*{}*\n\n{}"
    "\n\n[مشاهده تغییرات کامل]({})"
    f"\n\n{Emoji.HELP}{SUPPORT_GROUP_DEEPLINK}"
)

GAME_CANNOT_CHALLENGE_USER = "شما نمی‌توانید این کاربر را به چالش بکشید"
GAME_CHOOSE_GAME = "کدام بازی را می‌خواهید انجام دهید؟"
GAME_NO_WAGER_AMOUNT = (
    "باید مبلغ شرط را مشخص کنید.\n\nمثال:"
    f" {CommandName.GAME.get_formatted()} 10.000.000"
)

GAME_NOT_FOUND = "بازی یافت نشد"
GAME_REQUEST = (
    "{}، شما توسط {} برای بازی *{}* با شرط"
    " ฿*{}* به چالش کشیده شده‌اید.\n\n_*توضیحات*: {}_\n\nآیا مایلید بپذیرید؟\n\nاگر چالش ظرف"
    f" {Env.GAME_CONFIRMATION_TIMEOUT.get_int()} ثانیه پذیرفته نشود، به‌طور خودکار"
    " رد خواهد شد."
)
GAME_REQUEST_OPEN_HEADER = (
    "{} هر کسی را به چالش می‌کشد تا *{}* را با شرط ฿*{}* بازی کند."
    "\n\n_*توضیحات*: {}_"
    "\n\nبرای پذیرفتن، دکمه زیر را فشار دهید."
)
GAME_REQUEST_OPEN = (
    GAME_REQUEST_OPEN_HEADER + "\n\nاگر چالش ظرف"
    f" {Env.GAME_CONFIRMATION_TIMEOUT.get_int()} ثانیه پذیرفته نشود، به‌طور خودکار رد خواهد شد."
    "\n\n>می‌توانید این بازی را به‌عنوان یک چالش جهانی شروع کنید، "
    "که به شما اجازه می‌دهد بلافاصله بازی کنید در حالی که بازیکن دیگری بعداً نتیجه شما را به چالش می‌کشد"
)
GAME_CANCELED = "بازی لغو شد"
GAME_CHALLENGE_REJECTED = "{} چالش را رد کرده است"
GAME_INVALID = "بازی نامعتبر"
GAME_NOT_SELECTED_NAME = "انتخاب نشده"
GAME_TEXT = "*{}*\n\n_*توضیحات*: {}_\n\n{} در برابر {}\nشرط: ฿*{}*{}\n\n{}"
GAME_TEXT_WITHOUT_PLAYERS = "*{}*\n\n_*توضیحات*: {}_\n\nشرط: ฿*{}*{}\n\n{}"
GAME_STATUS_AWAITING_CHOICE = "وضعیت: در انتظار انتخاب"
GAME_STATUS_AWAITING_USER_CHOICE = "وضعیت: در انتظار انتخاب {}"
GAME_RESULT_DRAW = "نتیجه: مساوی"
GAME_RESULT_WIN = Emoji.WINNER + " {} برد"
GAME_NOT_YOUR_TURN = "نوبت شما نیست"
GAME_TURN = "وضعیت: نوبت {}"
GAME_ENDED = "این بازی به پایان رسیده است"
GAME_CANNOT_INITIATE = (
    "محدودیت چالش پر شده است، مطمئن شوید که چالش‌های در انتظار خود را لغو کرده‌اید.\nمی‌توانید"
    " چالش دیگری را در *{}* آغاز کنید، اما در این میان می‌توانید از کاربر دیگری بخواهید"
    " شما را به چالش بکشد یا یک چالش جهانی موجود را بپذیرید."
)
GAME_GLOBAL_COOLDOWN =(
    "محدودیت پذیرش چالش جهانی پر شده است.\n\n"
    "می‌توانید چالش جهانی دیگری را در *{}* بپذیرید، اما در این میان می‌توانید چالش‌های عادی را"
    " بپذیرید یا خودتان چالشی را آغاز کنید."
)
GAME_PENDING_KEY = "چالش در انتظار"
GAME_FORCED_END = (
    "این بازی به دلیل بازنشانی جایزه یا عدم فعالیت به پایان رسیده است. شرط‌ها به"
    " بازیکنان بازگردانده شده است."
)

GAME_STATUS_ND = "تعریف نشده"
GAME_STATUS_IN_PROGRESS = "در حال انجام"
GAME_STATUS_WON = "برد"
GAME_STATUS_LOST = "باخت"
GAME_STATUS_DRAW = "مساوی"
GAME_STATUS_AWAITING_SELECTION = "در انتظار انتخاب بازی"
GAME_STATUS_AWAITING_OPPONENT_CONFIRMATION = "در انتظار تأیید حریف"
GAME_STATUS_FORCED_END = "پایان به دلیل بازنشانی جایزه یا عدم فعالیت"
GAME_STATUS_COUNTDOWN_TO_START = "شمارش معکوس تا شروع"
GAME_STATUS_WINNING = "در حال برد"
GAME_STATUS_LOSING = "در حال باخت"
GAME_COUNTDOWN = "بازی در *{}* شروع خواهد شد"
GAME_STARTED = "بازی در حال انجام"
GAME_TIMEOUT = (
    "این بازی به دلیل اتمام زمان انتظار برای تأیید حریف لغو شد.\n\nشرط به"
    " چالش‌دهنده بازگردانده شد."
)
GAME_INPUT_NOT_PLAYER = "شما بازیکن این بازی نیستید"
GAME_INPUT_GAME_FINISHED = "این بازی به پایان رسیده است"
GAME_INPUT_COUNTDOWN = (
    "بازی هنوز شروع نشده است.\nدر این چت بمانید تا اولین پیام را از دست ندهید!"
)
GAME_RESULT_CHARACTER = "شخصیت: {}"
GAME_RESULT_TERM = "کلمه: {}"
GAME_DIFFICULTY = "\nسطح دشواری: {}"
GAME_DIFFICULTY_EASY = "آسان"
GAME_DIFFICULTY_MEDIUM = "متوسط"
GAME_DIFFICULTY_HARD = "سخت"
GAME_GLOBAL_ITEM_TEXT = "{} - ฿{}"
GAME_GLOBAL_ITEM_DEEPLINK = "{}[{}]({})"
GAME_GLOBAL_ALREADY_ACCEPTED = "این چالش قبلاً توسط بازیکن دیگری پذیرفته شده است"
GAME_GLOBAL_OPPONENT_CONFIRMATION_REQUEST = (
    "_*توضیحات*: {}_"
    "\n\n*حریف*: {}"
    "\n*شرط*: ฿{}"
    "\n\nآیا می‌خواهید این چالش را بپذیرید؟"
)
GAME_GLOBAL_CHALLENGE_ACCEPTED_ALERT = "چالش پذیرفته شد"
GAME_GLOBAL_CHALLENGE_ITEM_TEXT_FILL_IN = "چالش جهانی"
GAME_AUTO_MOVE_WARNING = "\n\n>در صورت عدم انتخاب، بدترین حرکت ممکن به‌طور خودکار پس از {} انجام خواهد شد"
GAME_POINTS = "{} امتیاز: *{}/{}*"
GAME_POINTS_FINISHED = " \\(پایان یافته\\)"
GAME_OPPONENT_AND_WAGER = "\n\n*حریف*: {}" "\n*شرط*: ฿{}"
GAME_GLOBAL_CURRENT_TIME = "زمان فعلی: {}"
GAME_GLOBAL_COMPLETION_TIME = "زمان تکمیل: {}"
GAME_GLOBAL_OPPONENT_TIME = "زمان حریف: {}"
GAME_GLOBAL_REMAINING_TIME = "\nزمان باقی‌مانده: *{}*"
GAME_GLOBAL_WAIT_FOR_OPPONENT = (
    "بازی به پایان رسید، پس از اینکه حریف شما نیز بازی را تمام کرد، از نتیجه مطلع خواهید شد"
)
GAME_GLOBAL_PENDING_CHALLENGER = (
    "\n\n>پس از اینکه بازیکن دیگری بازی را پذیرفت و بازی را به پایان رساند، به شما اطلاع داده خواهد شد، یا از دکمه "
    "اشتراک‌گذاری زیر برای دعوت از یک دوست جهت به چالش کشیدن نتیجه‌تان استفاده کنید"
)
GAME_GLOBAL_PENDING_OPPONENT = "\n\n>پس از اینکه چالش‌دهنده بازی را تمام کرد، به شما اطلاع داده خواهد شد"
GAME_GLOBAL_GUESS_WAIT_OPPONENT = (
    "\n\n>پس از اینکه حریف شما نیز بازی را تمام کرد، از نتیجه مطلع خواهید شد"
)
GAME_GLOBAL_GUESS_ALREADY_GUESSED = "شما قبلاً به‌درستی حدس زده‌اید.{}{}"
GAME_GLOBAL_INLINE_RESULT_SHARE = "اشتراک‌گذاری بازی"

ROCK_PAPER_SCISSORS_GAME_NAME = "سنگ کاغذ قیچی"
ROCK_PAPER_SCISSORS_GAME_DESCRIPTION = (
    "سعی کنید با انتخاب سنگ، کاغذ یا قیچی حریف خود را شکست دهید. \nسنگ قیچی را می‌برد،"
    " قیچی کاغذ را می‌برد و کاغذ سنگ را می‌برد."
)
ROCK_PAPER_SCISSORS_CHOICE = "شما {} را انتخاب کردید"
ROCK_PAPER_SCISSORS_CHOICE_ROCK = Emoji.ROCK + " سنگ"
ROCK_PAPER_SCISSORS_CHOICE_PAPER = Emoji.PAPER + " کاغذ"
ROCK_PAPER_SCISSORS_CHOICE_SCISSORS = Emoji.SCISSORS + " قیچی"
ROCK_PAPER_SCISSORS_CHOICES = "{} {} را انتخاب کرد \n{} {} را انتخاب کرد\n\n"
ROCK_PAPER_SCISSORS_PENDING_OPPONENT = (
    "\n\n>پس از اینکه چالش‌دهنده گزینه‌ای را انتخاب کرد، به شما اطلاع داده خواهد شد"
)

RUSSIAN_ROULETTE_GAME_NAME = "روسی رولت"
RUSSIAN_ROULETTE_GAME_DESCRIPTION = "سعی کنید از انتخاب خانه‌ای که گلوله در آن است اجتناب کنید."

RUSSIAN_ROULETTE_GAME_CHAMBER_ALREADY_FIRED = (
    "این خانه قبلاً شلیک شده است. خانه دیگری انتخاب کنید."
)
RUSSIAN_ROULETTE_GAME_BULLET_SHOT = "شما مردید"
RUSSIAN_ROULETTE_GAME_BULLET_NOT_SHOT = "شما یک دور دیگر جان سالم به در بردید"

GUESS_GAME_INPUT_CAPTION_HINT = "\n\n" + Emoji.NEW + "*راهنمایی*: {}"
GUESS_GAME_INPUT_CAPTION_SECONDS_TO_NEXT_HINT = "\n\n>در *{}* ثانیه، یک راهنمایی ارسال خواهد شد"
GUESS_GAME_INPUT_CAPTION_SECONDS_TO_NEXT_IMAGE = (
    "\n\n>در *{}* ثانیه، نسخه ساده‌تری ارسال خواهد شد"
)
GUESS_GAME_INPUT_CAPTION_SECONDS_TO_NEXT_LIFE_1 = ">در *{}* ثانیه، یک جان جدید صادر خواهد شد"
GUESS_GAME_INPUT_CAPTION_SECONDS_TO_NEXT_LIFE_2 = ">هر {} ثانیه یک جان جدید صادر خواهد شد"
GUESS_GAME_INPUT_CAPTION_SECONDS_TO_NEXT_DETAIL = (
    "\n\n>در *{}* ثانیه، جزئیات جدیدی ارائه خواهد شد"
)

GUESS_CHARACTER_GAME_INPUT_CAPTION = (
    ">_حدس‌های خود را به‌صورت پیام متنی ارسال کنید، در صورت صحیح بودن به شما اطلاع داده خواهد شد._"
    f"\n>_نام باید دقیقاً همان نامی باشد که در [ویکی وان‌پیس]({Env.ONE_PIECE_WIKI_URL.get()}) استفاده شده است_"
)
GUESS_TERM_GAME_INPUT_CAPTION = (
    ">_حدس‌های خود را به‌صورت پیام متنی ارسال کنید، در صورت صحیح بودن به شما اطلاع داده خواهد شد._"
    f"\n>_عبارت باید دقیقاً همانی باشد که در [ویکی وان‌پیس]({Env.ONE_PIECE_WIKI_URL.get()}) استفاده شده است_"
)
GUESS_GAME_CORRECT_ANSWER = f"تبریک می‌گویم، شما درست حدس زدید{Emoji.CONFETTI}\n\n{{}}"
GUESS_GAME_OPPONENT_CORRECT_ANSWER = (
    f"اوه، حریف شما زودتر از شما توانست حدس بزند😔\nدفعه بعد شانس بهتری داشته باشید!\n\n{{}}"
)

WHOS_WHO_GAME_NAME = "این کیست"
WHOS_WHO_GAME_DESCRIPTION = (
    "شخصیت تار شده را حدس بزنید. \nهر {} ثانیه، تصویری کمتر تار ارسال خواهد شد تا"
    " شخصیت به‌طور کامل نمایان شود.\nاین بازی در پیام خصوصی با ربات انجام می‌شود."
)

SHAMBLES_GAME_NAME = "شمبلز"
SHAMBLES_GAME_DESCRIPTION = (
    "کلمه مرتبط با وان‌پیس را از یک جدول کلمات متقاطع حدس بزنید. \nهر {} ثانیه، یک حرف اضافی"
    " از جدول حذف خواهد شد تا حدس زدن آسان‌تر شود.\nاین بازی در پیام خصوصی"
    " با ربات انجام می‌شود."
)

GUESS_OR_LIFE_GAME_NAME = "حدس یا جان"
GUESS_OR_LIFE_GAME_DESCRIPTION = (
    "حروف گمشده کلمه مرتبط با وان‌پیس را حدس بزنید، هر حدس اشتباه یک جان از شما می‌گیرد.\nیک"
    " جان جدید هر {} ثانیه صادر خواهد شد."
)
GUESS_OR_LIFE_GAME_CORRECT_LETTER = f"{Emoji.CORRECT} حرف درست!"
GUESS_OR_LIFE_GAME_WRONG_LETTER = f"{Emoji.LOG_NEGATIVE} حرف اشتباه"
GUESS_OR_LIFE_GAME_WORD_LIVES = "{}{}\nجان‌ها: {}{}"
GUESS_OR_LIFE_GAME_NAME_WORD = "*{}*\n{}"
GUESS_OR_LIFE_GAME_NAME_WORD_LIVES = "*{}*\n" + GUESS_OR_LIFE_GAME_WORD_LIVES
GUESS_OR_LIFE_GAME_REMAINING_USED_LETTERS = "\n\nحروف باقی‌مانده: {}\n\nحروف استفاده‌شده: {}"
GUESS_OR_LIFE_GAME_PRIVATE_RECAP = "{}\n\n{}"

PUNK_RECORDS_GAME_NAME = "پانک رکوردز"
PUNK_RECORDS_GAME_DESCRIPTION = (
    "شخصیت مرتبط با وان‌پیس را از جزئیات مربوط به او حدس بزنید. \nهر {} ثانیه، یک"
    " جزئیات جدید آشکار خواهد شد تا حدس زدن آسان‌تر شود.\nاین بازی در پیام خصوصی با"
    " ربات انجام می‌شود."
)
PUNK_RECORDS_GAME_RECAP = "{}{}"
PUNK_RECORDS_GAME_RECAP_DETAIL = "\n{}*{}*: {}"
PUNK_RECORDS_GAME_RECAP_DETAIL_LIST = "\n*{}*\n{}"

PREDICTION_NOT_FOUND = "پیش‌بینی یافت نشد"
PREDICTION_NOT_IN_NEW_STATUS = "پیش‌بینی در وضعیت NEW نیست"
PREDICTION_NOT_SENT = "پیش‌بینی ارسال نشده است"
PREDICTION_NOT_IN_SENT_STATUS = "پیش‌بینی در وضعیت SENT نیست"
PREDICTION_NOT_IN_BETS_CLOSED_STATUS = "پیش‌بینی در وضعیت BETS\\_CLOSED نیست"
UNKNOWN_PREDICTION_ACTION = "عملیات پیش‌بینی ناشناخته"
PREDICTION_TEXT = "*{}*\n{}\n\n*مجموع شرط*: ฿{}\n*وضعیت*: {}{}{}{}{}"
PREDICTION_CREATE_RECAP = "*{}*\n{}{}"
PREDICTION_TEXT_OPTION = "\n{}. {}"
PREDICTION_TEXT_OPTION_WITH_PERCENTAGE = PREDICTION_TEXT_OPTION + " \\(*{}%*\\){}"
PREDICTION_CLOSING_DATE = "\n*تاریخ بسته شدن*: {}"
PREDICTION_CUT_OFF_DATE = "\n*تاریخ قطع شرط‌بندی*: {}"
PREDICTION_WAGERS_REFUNDED = "\n{} شرط‌ها بازگردانده شد{}"
PREDICTION_WAGERS_REFUNDED_MAX = " \\(حداکثر ฿{}\\)"
PREDICTION_MULTIPLE_BETS_ALLOWED = "\n{} شرط‌بندی چندگانه مجاز است"
PREDICTION_MULTIPLE_BETS_ALLOWED_DESCRIPTION = "\n_\\(کاربران می‌توانند روی چندین گزینه شرط ببندند\\)_"
PREDICTION_CAN_WITHDRAW_BETS = "\n{} امکان لغو شرط وجود دارد"
PREDICTION_CAN_WITHDRAW_BETS_DESCRIPTION = (
    "\n_\\(کاربران می‌توانند شرط‌های خود را قبل از بسته شدن پیش‌بینی لغو کنند\\)_"
)
PREDICTION_IS_PUBLIC = "\n{} عمومی"
PREDICTION_IS_PUBLIC_DESCRIPTION = (
    "\n_\\(هر کسی در گروه‌های شما می‌تواند این پیش‌بینی را پیدا کند.\nاگر غیرفعال شود، فقط کسانی که"
    " پیش‌بینی را با آن‌ها به اشتراک گذاشته‌اید می‌توانند آن را ببینند.\nهم‌خدمه‌های شما همیشه می‌توانند آن را"
    " پیدا کنند._\\)"
)
PREDICTION_BET_INVALID_FORMAT = (
    "مطمئن شوید که شرط شما در قالب زیر است:"
    f"\n{CommandName.PREDICTION_BET.get_formatted()} <amount\\> <option"
    f" number\\>\n\nمثال: {CommandName.PREDICTION_BET.get_formatted()} 10.000.000 1"
)
PREDICTION_BET_HOW_TO_PLACE_BET = (
    "\n\n_برای ثبت شرط، با دستور زیر به این پیام پاسخ"
    f" دهید:\n{CommandName.PREDICTION_BET.get_formatted()} <amount\\> <option"
    f" number\\>\nمثال: {CommandName.PREDICTION_BET.get_formatted()} 10.000.000 1_"
)
PREDICTION_BET_HOW_TO_REMOVE_BET = (
    "\n\n_برای حذف یک شرط، با دستور زیر به پیش‌بینی پاسخ"
    f" دهید:\n{CommandName.PREDICTION_BET_REMOVE.get_formatted()} <option number\\>\nمثال:"
    f" {CommandName.PREDICTION_BET_REMOVE.get_formatted()} 1_"
)
PREDICTION_BET_HOW_TO_REMOVE_ALL_BETS = (
    "\n\n_برای حذف همه شرط‌ها، با دستور زیر به پیش‌بینی پاسخ"
    f" دهید:\n{CommandName.PREDICTION_BET_REMOVE.get_formatted()}_"
)
PREDICTION_BET_HOW_TO_VIEW_BET_STATUS = (
    "\n\n_برای مشاهده وضعیت شرط خود، با دستور زیر به پیش‌بینی پاسخ"
    f" دهید:\n{CommandName.PREDICTION_BET_STATUS.get_formatted()}_"
)

PREDICTION_CLOSED_FOR_BETS = "این پیش‌بینی دیگر شرط نمی‌پذیرد"
PREDICTION_NOT_FOUND_IN_REPLY = (
    "پیش‌بینی در پیام پاسخ‌داده‌شده یافت نشد. مطمئن شوید که به یک پیش‌بینی پاسخ داده‌اید یا"
    " ممکن است پیش‌بینی حذف شده باشد."
)
PREDICTION_ALREADY_BET = "شما قبلاً روی این پیش‌بینی شرط بسته‌اید"
PREDICTION_ALREADY_BET_ON_OPTION = "شما قبلاً روی این گزینه شرط بسته‌اید"
PREDICTION_OPTION_NOT_FOUND = "گزینه *{}* در پیش‌بینی یافت نشد"
PREDICTION_BET_SUCCESS = "شرط با موفقیت ثبت شد"
PREDICTION_RESULTS_SET = "نتایج این پیش‌بینی تنظیم شده است"
PREDICTION_BET_REMOVE_INVALID_FORMAT = (
    "مطمئن شوید که دستور شما در قالب زیر است:"
    f"\n{CommandName.PREDICTION_BET_REMOVE.get_formatted()} ]<option number\\>\n\nمثال:"
    f" {CommandName.PREDICTION_BET_REMOVE.get_formatted()} 1"
)
PREDICTION_BET_REMOVE_SUCCESS = "شرط با موفقیت حذف شد"
PREDICTION_BET_USER_HAS_NOT_BET = "شما روی این پیش‌بینی شرط نبسته‌اید"
PREDICTION_BET_REMOVE_ALL_SUCCESS = (
    "همه شرط‌های شما روی این پیش‌بینی با موفقیت حذف شد"
)
PREDICTION_CLOSED_FOR_BETS_REMOVAL = "شما دیگر نمی‌توانید شرط‌ها را از این پیش‌بینی لغو کنید"
PREDICTION_DOES_NOT_ACCEPT_BETS_WITHDRAWAL = "این پیش‌بینی امکان لغو شرط را نمی‌پذیرد"
PREDICTION_OPTION_NOT_BET_ON = "شما روی این گزینه شرط نبسته‌اید"
PREDICTION_STATUS_BETS_HEADER = "*شرط‌ها*"
PREDICTION_STATUS_OPTION = "\n\n*{}*. {} \n*مبلغ*: ฿{}"
PREDICTION_STATUS_POTENTIAL_WIN = "\n*برد احتمالی*: ฿{}"
PREDICTION_STATUS_RESULT_LOST = "\n*نتیجه*: " + Emoji.PREDICTION_BET_LOSE + "باخت"
PREDICTION_STATUS_RESULT_LOSS_REFUNDED = " \\(بازگردانده شد\\)"
PREDICTION_STATUS_RESULT_WIN = "\n*نتیجه*: " + Emoji.PREDICTION_BET_WIN + "฿{}"
PREDICTION_STATUS_TOTAL_WIN = "\n\n*مجموع برد*: " + Emoji.PREDICTION_BET_WIN + "฿{}"
PREDICTION_STATUS_NET_WIN = "\n\n*برد خالص*: " + Emoji.PREDICTION_BET_WIN + "฿{}"
PREDICTION_STATUS_TOTAL_LOSS = "\n\n*مجموع باخت*: " + Emoji.PREDICTION_BET_LOSE + "฿{}"
PREDICTION_STATUS_NET_LOSS = "\n\n*باخت خالص*: " + Emoji.PREDICTION_BET_LOSE + "฿{}"
PREDICTION_ALL_BETS_REMOVED_FOR_BOUNTY_RESET = (
    "همه شرط‌ها به دلیل بازنشانی جایزه از این پیش‌بینی حذف شدند"
)
# Prediction Private Chat
PREDICTION_ITEM_TEXT = "{} {}"
PREDICTION_ITEM_TEXT_FILL_IN = "پیش‌بینی"
PREDICTION_ITEM_DETAIL_TEXT = "{}\n\n{}"
PREDICTION_PLACE_BET_TEXT = "{}"
PREDICTION_PLACE_BET_DETAIL_TEXT = (
    "*سوال*: {}\n\n*گزینه*: {}\n\n_لطفاً مبلغی که می‌خواهید شرط ببندید را ارسال کنید_"
)
PREDICTION_PLACE_BET_LIST_OVERVIEW = "روی کدام گزینه می‌خواهید شرط ببندید؟\n{}"
PREDICTION_REMOVE_BET_TEXT = "{}"
PREDICTION_REMOVE_BET_LIST_OVERVIEW = "شرط خود را از کدام گزینه می‌خواهید حذف کنید؟\n{}"
PREDICTION_CREATE_COOLDOWN_ACTIVE = "می‌توانید یک پیش‌بینی در *{}* ایجاد کنید"
PREDICTION_CREATE_REQUEST_POLL = (
    "پیش‌بینی را به‌صورت یک نظرسنجی تلگرامی همراه با سوال و گزینه‌ها ارسال کنید"
)
PREDICTION_CREATE_INVALID_POLL = (
    "نظرسنجی نامعتبر. مطمئن شوید که یک نظرسنجی تلگرامی با یک سوال و حداقل دو گزینه ارسال می‌کنید"
)
PREDICTION_CAN_EDIT_POLL_ONLY_IF_NEW = (
    "فقط در صورتی می‌توانید سوال و گزینه‌ها را ویرایش کنید که پیش‌بینی هنوز"
    " فعال نشده باشد"
)
PREDICTION_CREATE_REQUEST_CLOSE_DATE = (
    "تاریخ بسته شدن پیش‌بینی را ارسال کنید.\n\n" + DATETIME_EXAMPLES
)
PREDICTION_CREATE_INVALID_CLOSE_DATE = (
    "تاریخ بسته شدن نامعتبر. مطمئن شوید که تاریخی معتبر ارسال می‌کنید.\n\n" + DATETIME_EXAMPLES
)
PREDICTION_CREATE_INVALID_CLOSE_DATE_PAST = (
    "تاریخ بسته شدن نامعتبر. مطمئن شوید که تاریخی در آینده ارسال می‌کنید.\n\n" + DATETIME_EXAMPLES
)
PREDICTION_CREATE_REQUEST_CUT_OFF_DATE = (
    "تاریخ قطع شرط‌بندی پیش‌بینی را ارسال کنید.\nهمه شرط‌های ثبت‌شده پس از این زمان حذف و"
    " بازگردانده خواهند شد.\nاین عملیات قابل بازگشت نیست.\nزمان باید بعد از باز شدن پیش‌بینی"
    " و قبل از بسته شدن آن یا هر تاریخ قطع شرط‌بندی قبلی باشد\n\n*زمان باز شدن*: {}\n*زمان بسته"
    " شدن*: {}\n*زمان قطع شرط‌بندی*: {}\n\n" + DATETIME_EXAMPLES_NO_DURATION
)
PREDICTION_CREATE_INVALID_CUT_OFF_DATE = (
    "تاریخ قطع شرط‌بندی نامعتبر. مطمئن شوید که تاریخ و زمانی معتبر بعد از باز شدن پیش‌بینی"
    " و قبل از بسته شدن آن یا هر تاریخ قطع شرط‌بندی قبلی ارسال می‌کنید.\n\n*زمان باز شدن*: {}\n*زمان بسته"
    " شدن*: {}\n*زمان قطع شرط‌بندی*: {}\n\n" + DATETIME_EXAMPLES_NO_DURATION
)
PREDICTION_CUT_OFF_DATE_CONFIRMATION_REQUEST = (
    "آیا مطمئنید که می‌خواهید تاریخ قطع شرط‌بندی را روی *{}* تنظیم کنید؟\n{} شرط با مجموع ฿{}"
    " حذف خواهند شد"
)
PREDICTION_SETTING_CANNOT_BE_CHANGED = "این تنظیم قابل تغییر نیست"
PREDICTION_CREATE_CLOSE_DATE = (
    PREDICTION_CLOSING_DATE
    + "\n_\\(در صورت تنظیم، پیش‌بینی در این تاریخ به‌طور خودکار برای شرط‌های جدید بسته خواهد شد\\)_"
)
PREDICTION_CREATE_CUT_OFF_DATE = (
    "\n"
    + PREDICTION_CUT_OFF_DATE
    + "\n_\\(در صورت تنظیم، همه شرط‌های ثبت‌شده پس از این زمان حذف و بازگردانده خواهند شد\\)_"
)
PREDICTION_CUT_OFF_DATE_HOW_TO_SET = "\n_می‌توانید آن را از منوی ویرایش تنظیم کنید_"
PREDICTION_USER_DISCLAIMER = (
    "\n\n_این پیش‌بینی توسط یک کاربر عادی ایجاد شده و مورد تأیید تیم سیستم جایزه"
    " نیست. قبل از ثبت شرط، مطمئن شوید که به سازنده آن اعتماد دارید._"
)
PREDICTION_DELETE_CONFIRMATION = (
    "آیا مطمئنید که می‌خواهید این پیش‌بینی را حذف کنید؟ این عملیات قابل بازگشت نیست.\nشما"
    " می‌توانید پیش‌بینی دیگری در *{}* ایجاد کنید.\n\nاگر کسی روی این"
    " پیش‌بینی شرط بسته باشد، مبلغ او بازگردانده خواهد شد."
)
PREDICTION_OPEN_CONFIRMATION = (
    "آیا مطمئنید که می‌خواهید این پیش‌بینی را باز کنید؟ پس از این نمی‌توانید سوال یا"
    " گزینه‌ها را تغییر دهید.\n\nاگر پیش‌بینی عمومی باشد، هر کسی در گروه‌های شما می‌تواند"
    " آن را پیدا کند.\nهم‌خدمه‌های شما همیشه می‌توانند آن را پیدا کنند."
)
PREDICTION_CREATE_SUCCESS = "پیش‌بینی با موفقیت ایجاد شد"
PREDICTION_DELETE_SUCCESS = "پیش‌بینی با موفقیت حذف شد"
PREDICTION_OPEN_SUCCESS = "پیش‌بینی اکنون برای شرط‌بندی باز است"
PREDICTION_ALREADY_OPEN = "پیش‌بینی از قبل برای شرط‌بندی باز است"
PREDICTION_ALREADY_CLOSED = "پیش‌بینی از قبل برای شرط‌بندی بسته است"
PREDICTION_CLOSE_CONFIRMATION = (
    "آیا مطمئنید که می‌خواهید این پیش‌بینی را برای شرط‌های جدید ببندید؟\nاین عملیات قابل بازگشت نیست."
)
PREDICTION_CLOSE_SUCCESS = "پیش‌بینی با موفقیت بسته شد"
PREDICTION_INLINE_RESULT_SHARE = "اشتراک‌گذاری پیش‌بینی"
PREDICTION_IN_WRONG_STATUS = "پیش‌بینی در وضعیت نادرست است"
PREDICTION_SEND_TO_GROUP = (
    "می‌توانید این پیش‌بینی را به گروه‌ها یا موضوعاتی که در آن‌ها ادمین هستید ارسال کنید و کاربران"
    " می‌توانند با پاسخ به پیام روی آن شرط ببندند.\nاگر گروهی را پیدا نمی‌کنید، مطمئن شوید که ربات"
    f" عضو آن گروه است و از دستور {CommandName.STATUS.get_formatted()} در"
    " گروه استفاده کنید.\nمی‌توانید فقط یک‌بار به هر گروه یا موضوع ارسال کنید.{}"
)
PREDICTION_SEND_TO_GROUP_NO_GROUPS = "\n\n_گروهی یافت نشد_"
PREDICTION_SEND_TO_GROUP_GROUPS_AVAILABLE = (
    "*\n\nموجود*:{}\n\nشماره گروه را انتخاب کنید \\(نیازی به تأیید نیست\\)"
)
PREDICTION_SEND_TO_GROUP_GROUPS_ALREADY_SENT = "*\n\nقبلاً ارسال شده*:{}"
PREDICTION_SEND_TO_GROUP_GROUPS_ALREADY_SENT_ITEM = "\n•{}"
PREDICTION_SEND_TO_GROUP_GROUPS_AVAILABLE_ITEM = "\n{}. {}"
PREDICTION_SEND_TO_GROUP_NOT_ADMIN = "شما دیگر ادمین نیستید"
PREDICTION_SEND_TO_GROUP_ALREADY_SENT = "این پیش‌بینی قبلاً به این گروه ارسال شده است"
PREDICTION_SET_RESULT = "گزینه‌های صحیح این پیش‌بینی را انتخاب کنید\n\n*{}*\n{}"
PREDICTION_SET_RESULT_CONFIRMATION_REQUEST = (
    "آیا مطمئنید که می‌خواهید نتیجه این پیش‌بینی را تنظیم کنید؟\nشرط‌ها به‌طور متناسب به"
    " برندگان توزیع خواهند شد.\nاین عملیات قابل بازگشت نیست\n\nگزینه‌های صحیح:{}"
)
PREDICTION_SET_RESULT_SUCCESS = "نتیجه پیش‌بینی با موفقیت تنظیم شد"
PREDICTION_SET_RESULT_CONFIRMATION_REQUEST_NO_CORRECT_OPTION = (
    "هیچ گزینه صحیحی تنظیم نشده است، شرط‌ها بازگردانده خواهند شد."
)

# Crew - Private
CREW_SEARCH_ITEM_TEXT = "{} \\(Lv. {}\\)"
CREW_SEARCH_ITEM_TEXT_FILL_IN = "خدمه"
CREW_SEARCH_ITEM_LEGEND_CAN_JOIN = "می‌توان پیوست"
CREW_SEARCH_ITEM_LEGEND_AUTO_ACCEPT_JOIN = "پذیرش خودکار عضویت"
CREW_SEARCH_ITEM_LEGEND_CANNOT_JOIN = "نمی‌توان پیوست"
CREW_SEARCH_ITEM_LEGEND_AVAILABLE_FOR_DAVY_BACK_FIGHT = "برای دیوی بک فایت در دسترس است"
CREW_SEARCH_ITEM_LEGEND_AUTO_ACCEPTS_DAVY_BACK_FIGHT = "پذیرش خودکار دیوی بک فایت"
CREW_SEARCH_FILTER_NAME = "نام خدمه"
CREW_SEARCH_NOT_ALLOWED_TO_VIEW = (
    "اطلاعات خدمه در دسترس نیست.\n\nاگر شما کاپیتان این خدمه هستید، گزینه `اجازه به کاربران"
    " برای یافتن خدمه از طریق جستجو` را در `خدمه-\\>ویرایش` فعال کنید"
)
CREW_SEARCH_JOIN_NOT_ALLOWED = "خدمه اجازه درخواست عضویت از طریق جستجو را نمی‌دهد"
CREW_SEARCH_JOIN_NOT_ENOUGH_BOUNTY = "برای پیوستن به خدمه به جایزه‌ای معادل ฿{} نیاز دارید"
CREW_SEARCH_JOIN_CONFIRMATION_REQUEST = (
    "آیا مطمئنید که می‌خواهید درخواست پیوستن به *{}* را ارسال کنید؟\nشما می‌توانید حداکثر"
    f" {Env.CREW_JOIN_REQUESTS_PER_COOLDOWN.get_int()} درخواست پیوستن به خدمه‌ها هر"
    f" {Env.CREW_JOIN_REQUEST_COOLDOWN_DURATION.get_int()} ساعت ارسال کنید و می‌توانید برای"
    f" پیوستن به همان خدمه هر {Env.CREW_JOIN_REQUEST_COOLDOWN_SAME_CREW_DURATION.get_int()} روز درخواست دهید.\n\nجایزه"
    " فعلی شما با کاپیتان خدمه به اشتراک گذاشته خواهد شد"
)
CREW_SEARCH_JOIN_CONFIRMATION_REQUEST_AUTO_ACCEPT = (
    "\n\n_*درخواست شما به‌طور خودکار پذیرفته خواهد شد*_"
)
CREW_SEARCH_JOIN_SUCCESS = (
    "درخواست پیوستن به *{}* با موفقیت ارسال شد، پس از پذیرفته شدن به شما اطلاع داده خواهد شد"
)
CREW_SEARCH_JOIN_CAPTAIN_REQUEST = (
    "سلام، من {} هستم و می‌خواهم به خدمه شما بپیوندم!\n\nجایزه فعلی: ฿{}"
)
CREW_SEARCH_JOIN_CAPTAIN_ACCEPTED = "{} اکنون عضوی از خدمه شماست!"
CREW_SEARCH_JOIN_CAPTAIN_ACCEPTED_AUTO_ACCEPT = (
    "\n\n_این درخواست به‌طور خودکار پذیرفته شد، برای تغییر این تنظیم [اینجا کلیک کنید]({})_"
)
CREW_SEARCH_JOIN_CAPTAIN_REJECTED = "شما درخواست {} برای پیوستن به خدمه‌تان را رد کردید"
CREW_SEARCH_JOIN_CAPTAIN_ERROR = "خطا هنگام ارسال درخواست به کاپیتان خدمه"
CREW_SEARCH_JOIN_MAXIMUM_REQUESTS_PER_COOLDOWN = "می‌توانید درخواست پیوستن به خدمه دیگری را در {} ارسال کنید"
CREW_SEARCH_JOIN_MAXIMUM_REQUESTS_SAME_CREW_PER_COOLDOWN = (
    "می‌توانید دوباره درخواست پیوستن به این خدمه را در {} ارسال کنید"
)
CREW_SEARCH_UNAUTHORIZED_CANNOT_VIEW_FROM_SEARCH = (
    "اطلاعات این خدمه از طریق جستجو در دسترس نیست.\n\nاگر شما کاپیتان یا معاون اول"
    " این خدمه هستید، گزینه `اجازه به کاربران برای یافتن خدمه از طریق جستجو` را در"
    f" `{PVT_KEY_CREW}-\\>{KEY_MODIFY}` فعال کنید"
)
CREW_USER_NOT_IN_CREW = (
    "شما در هیچ خدمه‌ای نیستید. به دنبال یکی بگردید یا خودتان"
    f" یکی بسازید.\n\nساخت یک خدمه ฿{Env.CREW_CREATE_PRICE.get_belly()} هزینه دارد."
    f"\n\n>همچنین می‌توانید خدمه‌های موجود را در {SUPPORT_GROUP_DEEPLINK} پیدا کنید"
)
CREW_NAME_WITH_LEVEL_DEEPLINK = "[{}]({}) \\(Lv. {}\\)"
CREW_OVERVIEW = (
    "*{}* \\(Lv. *{}*\\)"
    "\n\n_{}_"
    "\n\n*کاپیتان*: {}"
    "{}"  # First Mate
    "\n*تاریخ تشکیل*: {} \\({}\\)"
    "\n*اعضا*: {} \\(حداکثر {}\\)"
    "{}"  # Active abilities count
    "{}"  # Required bounty
    "{}"  # Treasure chest
    "{}"  # Abilities
    "{}"  # No new members allowed
    "{}"  # Davy Back Fight penalty active
)
CREW_OVERVIEW_FIRST_MATE = "\n*معاون اول*: {}"
CREW_OVERVIEW_ACTIVE_ABILITIES_COUNT = "\n*توانایی‌های فعال*: {} \\(حداکثر {}\\)"
CREW_OVERVIEW_TREASURE_CHEST = "\n\n*صندوق گنج*: ฿{}"
CREW_OVERVIEW_ACTIVE_ABILITIES = "\n\n*توانایی‌ها*{}"
CREW_OVERVIEW_REQUIRED_BOUNTY = "\n\n*جایزه مورد نیاز*: ฿{}"

CREW_OVERVIEW_NO_NEW_MEMBERS_ALLOWED = (
    "\n\n_عضو جدید تا جدول امتیازات هفتگی بعدی در {} پذیرفته نمی‌شود_"
)
CREW_OVERVIEW_DAVY_BACK_FIGHT_PENALTY_ACTIVE = (
    f"\n\n_{Emoji.LOG_NEGATIVE}جریمه دیوی بک فایت برای "
    "*{}* آینده فعال است، هیچ عضوی نمی‌تواند خدمه را ترک کند._"
)
CREW_OVERVIEW_DESCRIPTION_NOT_SET = "توضیحاتی تنظیم نشده است"
CREW_MEMBER_ITEM_TEXT = "{}"
CREW_MEMBER_ITEM_ROLE = " \\({}\\)"
# Crew - Member
CREW_MEMBER_ITEM_DETAIL = (
    "*{}*\n\n*جایزه*: ฿{}\n*تاریخ پیوستن*: {} \\({}°\\)"
    "\n*آخرین فعالیت*: {}"
    "\n\nسهم صندوق: ฿{} \\({}°\\)\nپاداش"
    " برترین بازیکن خدمه: {}{}"
)
CREW_MEMBER_ITEM_DETAIL_ARRESTED = f"\n\n{Emoji.LOG_NEGATIVE}بازداشت‌شده \\({{}}\\)"
CREW_MEMBER_ITEM_DETAIL_CONSCRIPTION_END_DATE = "\n\n*تاریخ پایان سربازگیری*: {}"
CREW_MEMBER_ITEM_TEXT_FILL_IN = "عضو خدمه"
CREW_USER_ALREADY_IN_SAME_CREW = "شما از قبل در این خدمه هستید"
CREW_INVITE_TARGET_ALREADY_IN_SAME_CREW = (
    "کاربری که می‌خواهید دعوت کنید از قبل عضو این خدمه است."
)
CREW_USER_ALREADY_IN_CREW = "شما از قبل در یک خدمه هستید"
CREW_JOIN_USER_ALREADY_IN_CREW = (
    "شما از قبل عضو یک خدمه هستید. قبل از پیوستن به خدمه دیگر، خدمه فعلی خود را ترک کنید."
)
CREW_INVITE_TARGET_ALREADY_IN_CREW = "کاربری که می‌خواهید دعوت کنید از قبل عضو یک خدمه است."
CREW_CREATE_USER_NOT_ENOUGH_BOUNTY = (
    f"جایزه ناکافی، تشکیل یک خدمه ฿{Env.CREW_CREATE_PRICE.get_belly()} هزینه دارد"
)
CREW_CANNOT_CREATE_CREW = "می‌توانید یک خدمه در {} بسازید"
CREW_CREATE_REQUEST_NAME = "نام خدمه خود را ارسال کنید"
CREW_CREATE_NAME_ALREADY_EXISTS = "خدمه‌ای با این نام از قبل وجود دارد"
CREW_CREATE_NAME_TOO_LONG = (
    f"نام خدمه نباید بیش از {Env.CREW_NAME_MAX_LENGTH.get_int()} کاراکتر باشد"
)
CREW_CREATE_SUCCESS = (
    "شما اکنون کاپیتان *{}* هستید."
    + f"\n\nبرای شروع جذب اعضا به یک گروه چت بروید!"
)
CREW_EDIT_NAME_SUCCESS = "نام خدمه با موفقیت به‌روزرسانی شد"
CREW_EDIT_REQUEST_DESCRIPTION = (
    f"توضیحات جدید خدمه خود را ارسال کنید \\(حداکثر {Env.CREW_DESCRIPTION_MAX_LENGTH.get_int()}"
    " کاراکتر\\)"
)
CREW_EDIT_DESCRIPTION_TOO_LONG = (
    f"توضیحات خدمه نباید بیش از {Env.CREW_DESCRIPTION_MAX_LENGTH.get_int()} کاراکتر باشد"
)
CREW_EDIT_DESCRIPTION_SUCCESS = "توضیحات خدمه با موفقیت به‌روزرسانی شد"
CREW_EDIT_REQUEST_REQUIRED_BOUNTY = "حداقل جایزه مورد نیاز برای پیوستن به خدمه خود را ارسال کنید"
CREW_EDIT_REQUIRED_BOUNTY_SUCCESS = "جایزه مورد نیاز با موفقیت به‌روزرسانی شد"
CREW_MODIFY = (
    "*نام*: {}"
    "\n\n*توضیحات*: {}"
    "\n\n*جایزه مورد نیاز*: ฿{}"
    "\n\nاجازه به کاربران برای یافتن خدمه از طریق جستجو."
    "\nدر صورت غیرفعال بودن، خدمه در جدول امتیازات جهانی نمایش داده نمی‌شود"
    "\n_{}_"
    "\n\nاجازه به کاربران برای درخواست پیوستن به خدمه از طریق جستجو"
    "\n_{}_"
    "\n\nپذیرش خودکار درخواست‌های پیوستن از طریق جستجو"
    "\n_{}_"
    "\n\nاجازه به کاپیتان‌ها برای به چالش کشیدن خدمه شما به دیوی بک فایت"
    "\n_{}_"
    "\n\nپذیرش خودکار چالش‌های دیوی بک فایت \\(فقط در صورتی که مدت زمان حداقل "
    f"{Env.DAVY_BACK_FIGHT_DEFAULT_DURATION.get()} ساعت باشد\\)."
    "\nدر صورت فعال بودن، می‌توانید انتخاب کنید کدام هم‌خدمه‌ای‌ها به‌طور پیش‌فرض برای شرکت انتخاب شوند، در "
    "صورتی که نتوانید قبل از شروع چالش آن‌ها را به‌صورت دستی انتخاب کنید"
    "\n_{}_"
    "\n\n چه چیزی را می‌خواهید ویرایش کنید؟"
)

CREW_MODIFY_ONLY_CAPTAIN_OR_FIRST_MATE = (
    "فقط کاپیتان یا معاون اول می‌تواند تنظیمات خدمه را ویرایش کند"
)
CREW_EDIT_DAVY_BACK_FIGHT_PRIORITY_SELECT_USER = (
    "اولویت کدام عضو را می‌خواهید تغییر دهید؟"
)
CREW_EDIT_DAVY_BACK_FIGHT_PRIORITY_SELECT_SWAP = (
    "اولویت {} را با کدام عضو می‌خواهید جابه‌جا کنید؟"
)
CREW_EDIT_DAVY_BACK_FIGHT_PRIORITY = "{}\n{}{}"
CREW_EDIT_DAVY_BACK_FIGHT_PRIORITY_EXPLANATION = (
    "\n\n>اولویت، ترتیب پیش‌فرضی که اعضا برای"
    " دیوی بک فایت‌ها انتخاب می‌شوند را مشخص می‌کند.\n>برای مثال، اگر یک چالش دیوی بک فایت با ۳"
    " شرکت‌کننده از هر خدمه دریافت کنید، ۳ عضو اول در لیست بالا به‌طور خودکار"
    " انتخاب خواهند شد.\n>همیشه می‌توانید بازیکنان واقعی را در طول شمارش معکوس"
    f" {Env.DAVY_BACK_FIGHT_START_WAIT_TIME.get()} دقیقه‌ای قبل از شروع چالش تغییر دهید."
)
CREW_ROLE_CAPTAIN = "کاپیتان"
CREW_ROLE_FIRST_MATE = "معاون اول"
CREW_ROLE_CONSCRIPT = "سرباز"

# Crew - Join request
CREW_JOIN_REQUEST_CREW_FULL = "خدمه پر است"
CREW_NOT_FOUND = "خدمه یافت نشد"
CREW_JOIN_REQUEST_CAPTION = (
    "اسم من {} است!!! نمی‌دانم تو کی هستی، اما از تو می‌خواهم!!\nبگذار سوار"
    " کشتی‌ات شوم!!\n\n_فقط [کاپیتان]({}) یا [معاون اول]({}) می‌توانند این درخواست را بپذیرند یا رد کنند_"
)
CREW_JOIN_REQUEST_ACCEPTED = "{} اکنون عضوی از {} است!"
CREW_JOIN_REQUEST_REJECTED = (
    "درخواست [شما](tg://user?id={}) برای پیوستن به *{}* رد شد، اما تسلیم نشوید!!"
)
CREW_JOIN_REQUEST_CREW_CANNOT_ACCEPT_USER = "کاربر نمی‌تواند به این خدمه بپیوندد"
CREW_JOIN_REQUEST_USER_CANNOT_JOIN_CREW = "شما نمی‌توانید به این خدمه بپیوندید"
CREW_USER_CANNOT_JOIN_CREW_UNTIL_RESET = (
    "شما تا جدول امتیازات هفتگی بعدی در {} نمی‌توانید به خدمه‌ای بپیوندید"
)
CREW_JOIN_REQUEST_CREW_CANNOT_ACCEPT_NEW_MEMBERS_UNTIL_NEXT_RESET = (
    "خدمه تا جدول امتیازات هفتگی بعدی در {} نمی‌تواند عضو جدید بپذیرد"
)

# Crew - Invite request
CREW_INVITE_REQUEST_CAPTION = (
    "من {} هستم و این ملاقات باید سرنوشت باشد، {}! \nنظرت درباره زیر و رو کردن دنیا"
    " با من چیه؟"
)
CREW_INVITE_REQUEST_ACCEPTED = "{} اکنون عضوی از {} است!"
CREW_INVITE_REQUEST_REJECTED = "دعوت برای پیوستن به *{}* توسط {} رد شد"

STEP_REQUIRES_TEXT = "لطفاً یک متن معتبر ارسال کنید"
ITEM_NOT_FOUND = (
    "مورد یافت نشد. اگر فکر می‌کنید این یک اشتباه است، لطفاً آن را در "
    f"{SUPPORT_GROUP_DEEPLINK} گزارش دهید"
)
ITEM_NOT_FOUND_NO_CONTACT = "مورد یافت نشد."
ITEM_IN_WRONG_STATUS = "مورد در وضعیت نادرست است"
INLINE_QUERY_ITEM_NOT_FOUND_TITLE = "مورد یافت نشد"
INLINE_QUERY_ITEM_NOT_FOUND_DESCRIPTION = "برای دریافت یک آدرس معتبر، ربات را ری‌استارت کنید"
INLINE_QUERY_ITEM_NOT_FOUND_MESSAGE = "خطا"

# Crew - Leave
CREW_LEAVE_CONFIRMATION = (
    "آیا مطمئنید که می‌خواهید خدمه را ترک کنید؟\nتا جدول امتیازات هفتگی بعدی در {} نمی‌توانید"
    " به خدمه دیگری بپیوندید"
)
CREW_LEAVE_CONFIRMATION_LOCATION_DOWNGRADE = (
    " و موقعیت شما به {} تنزل خواهد یافت \\(موقعیت فعلی: {}\\)"
)
CREW_LEAVE_SUCCESS = "شما خدمه را ترک کردید"

# Crew - Disband
CREW_DISBAND_CONFIRMATION = (
    "آیا مطمئنید که می‌خواهید خدمه را منحل کنید؟\nتا بازنشانی جایزه بعدی در {} نمی‌توانید"
    " خدمه دیگری بسازید"
)
CREW_DISBAND_SUCCESS = "شما خدمه را منحل کردید"
CREW_DISBAND_ACTIVE_DAVY_BACK_FIGHT = (
    "خدمه در طول یک دیوی بک فایت فعال نمی‌تواند منحل شود"
)
CREW_DISBAND_DAVY_BACK_FIGHT_PENALTY = (
    "خدمه در طول دوره جریمه دیوی بک فایت نمی‌تواند منحل شود"
)

# Crew - Remove member
CREW_NOT_SAME = "شما در یک خدمه نیستید"
CREW_REMOVE_MEMBER_CONFIRMATION = (
    "آیا مطمئنید که می‌خواهید {} را از خدمه اخراج کنید؟\nتا جدول امتیازات هفتگی بعدی در {} نمی‌توانید"
    " عضو جدید بپذیرید"
)
CREW_REMOVE_MEMBER_SUCCESS = "{} از خدمه اخراج شد"
CREW_REMOVE_MEMBER_ACTIVE_DAVY_BACK_FIGHT = (
    "در طول یک دیوی بک فایت فعال، اعضا نمی‌توانند حذف شوند یا خدمه را ترک کنند"
)
CREW_REMOVE_MEMBER_DAVY_BACK_FIGHT_PENALTY = (
    "در طول دوره جریمه دیوی بک فایت، اعضا نمی‌توانند حذف شوند یا خدمه را ترک کنند"
)
CREW_REMOVE_MEMBER_CONSCRIPT = "می‌توانید پس از پایان دوره سربازگیری خود در {} خدمه را ترک کنید"

# Crew - Promote to First Mate
CREW_PROMOTE_TO_FIRST_MATE_CREW_ALREADY_HAS_FIRST_MATE = "خدمه از قبل یک معاون اول دارد"
CREW_PROMOTE_TO_FIRST_MATE_CANNOT_PROMOTE_UNTIL_NEXT_LEADERBOARD = (
    "شما اخیراً یک عضو را از معاون اول تنزل داده‌اید. تا جدول امتیازات هفتگی بعدی در {} نمی‌توانید"
    " عضو دیگری را به معاون اول ارتقا دهید"
)
CREW_PROMOTE_CANNOT_PROMOTE_DAVY_BACK_FIGHT = (
    "شما نمی‌توانید در طول یک دیوی بک فایت فعال یا دوره جریمه پس از "
    "یک باخت، عضوی را ارتقا دهید"
)
CREW_FIRST_MATE_PRIVILEGES = (
    "\n• پذیرش اعضای جدید "
    "\n• فعال‌سازی توانایی‌های خدمه"
    "\n• ویرایش تنظیمات خدمه"
    "\n• قابل سربازگیری در دیوی بک فایت‌ها نیست"
)
CREW_PROMOTE_TO_FIRST_MATE_CONFIRMATION = (
    "آیا مطمئنید که می‌خواهید {} را به معاون اول ارتقا دهید؟\nآن‌ها امتیازات زیر را کسب خواهند کرد:"
    + CREW_FIRST_MATE_PRIVILEGES
)
CREW_PROMOTE_TO_FIRST_MATE_SUCCESS = "{} به معاون اول ارتقا یافت"

# Crew - Demote from First Mate
CREW_DEMOTE_FROM_FIRST_MATE_IS_NOT_FIRST_MATE = "{} معاون اول نیست"
CREW_DEMOTE_FROM_FIRST_MATE_CONFIRMATION = (
    "آیا مطمئنید که می‌خواهید {} را از معاون اول تنزل دهید؟\nتا جدول امتیازات هفتگی بعدی در {} نمی‌توانید"
    " عضو دیگری را به معاون اول ارتقا دهید"
)
CREW_DEMOTE_FROM_FIRST_MATE_SUCCESS = "{} از معاون اول تنزل یافت"
POST_BAIL_MEMBER_NOT_ARRESTED_TEMPORARY = "این کاربر محکومیت موقت ندارد"
POST_BAIL_NOT_ENOUGH_BOUNTY = "برای پرداخت وثیقه به ฿{} نیاز دارید.\n\nجایزه فعلی: ฿{}"
POST_BAIL_CONFIRMATION_REQUEST = (
    "آیا مطمئنید که می‌خواهید برای {} وثیقه بپردازید؟"
    "\nبه ازای هر دقیقه باقی‌مانده از محکومیت، "
    f"مبلغ ฿*{Env.IMPEL_DOWN_BAIL_PER_MINUTE.get_belly()}* از شما دریافت خواهد شد"
    "\n\nمجموع وثیقه: ฿*{}*"
)
CREW_POST_BAIL_SUCCESS = "وثیقه با موفقیت پرداخت شد"

# Crew - Promote to Captain
CREW_PROMOTE_TO_CAPTAIN_CANNOT_PROMOTE_NOT_FIRST_MATE = (
    "شما فقط می‌توانید یک معاون اول را به کاپیتان ارتقا دهید"
)
CREW_PROMOTE_TO_CAPTAIN_CANNOT_PROMOTE_UNTIL_NEXT_RESET = (
    "تا بازنشانی جایزه بعدی در {} نمی‌توانید عضوی را به کاپیتان ارتقا دهید"
)
CREW_PROMOTE_TO_CAPTAIN_CONFIRMATION = (
    "آیا مطمئنید که می‌خواهید {} را به کاپیتان ارتقا دهید؟\nشما به معاون"
    f" اول تنزل خواهید یافت.\n\n{Emoji.WARNING_STRONG}توجه: این عملیات قابل بازگشت نیست و شما به‌طور"
    " دائمی مالکیت خدمه خود را از دست خواهید داد مگر اینکه توسط کاپیتان جدید دوباره به"
    " کاپیتان ارتقا یابید"
)
CREW_PROMOTE_TO_CAPTAIN_SUCCESS = "{} به کاپیتان ارتقا یافت"

# Crew abilities
CREW_ABILITIES = (
    "*توانایی‌های خدمه*\n\nتوانایی‌ها اثرات میوه‌های شیطانی را تقلید می‌کنند و به همه"
    " اعضای خدمه گسترش می‌یابند." + "\nهزینه هر توانایی به سطح فعلی خدمه بستگی دارد و"
    f" {Env.CREW_ABILITY_DURATION_DAYS.get_int()} روز طول می‌کشد."
    + "\n{}\n\nهزینه توانایی بعدی: ฿*{}*\nصندوق خدمه: ฿{}"
)
CREW_ABILITY_NO_ABILITIES = "\n_در حال حاضر هیچ توانایی‌ای در این خدمه فعال نیست_"
CREW_ABILITY_ITEM_TEXT = "\n• {}{} \\({}%\\)"
CREW_ABILITY_ITEM_TEXT_DURATION = "\nزمان باقی‌مانده: {}"
CREW_POWERUP_INSUFFICIENT_CREW_CHEST = (
    "صندوق خدمه ناکافی\n\nصندوق خدمه: ฿{}\nهزینه تقویت: ฿{}"
)
CREW_ABILITY_MAX_ABILITIES_REACHED = "حداکثر تعداد توانایی‌های فعال پر شده است"
CREW_ABILITY_ACTIVATE_CHOOSE = (
    "توانایی‌ای که می‌خواهید استفاده کنید را انتخاب کنید، یا برای یک سورپرایز 'تصادفی' را انتخاب کنید. "
    "\n\nاگر توانایی خاصی را انتخاب کنید، همیشه روی "
    f"{Env.CREW_ABILITY_DEFAULT_VALUE_PERCENTAGE.get_int()}% تنظیم خواهد شد."
    "\n\nاگر به‌جای آن تصادفی را انتخاب کنید، یک توانایی کاملاً تصادفی دریافت خواهید کرد و "
    "مقدار آن می‌تواند بین "
    f"{Env.CREW_ABILITY_RANDOM_MIN_VALUE_PERCENTAGE.get_int()}% "
    f"و {Env.CREW_ABILITY_RANDOM_MAX_VALUE_PERCENTAGE.get_int()}% باشد."
)
CREW_ABILITY_ACTIVATE_CHOOSE_RECAP = (
    "\n\n*توانایی*: {}\n*مقدار*: {}\n*مدت*: {} روز\n*هزینه*: ฿{}"
)
CREW_ABILITY_ACTIVATE_CHOOSE_CONFIRMATION_REQUEST = (
    "آیا مطمئنید که می‌خواهید توانایی زیر را فعال کنید؟" + CREW_ABILITY_ACTIVATE_CHOOSE_RECAP
)
CREW_ABILITY_ACTIVATE_SUCCESS = (
    "توانایی با موفقیت فعال شد" + CREW_ABILITY_ACTIVATE_CHOOSE_RECAP
)
CREW_ABILITY_ALREADY_ACTIVATED = (
    "این توانایی از قبل فعال است، لطفاً یکی دیگر را انتخاب کنید."
    "\nهمچنان می‌توان آن را به‌صورت تصادفی به دست آورد."
)

# Crew power-up
CREW_POWERUP = (
    "*سطح*"
    "\nبا ارتقای سطح، خدمه می‌تواند تعداد توانایی‌های مجاز یا ظرفیت اعضا را افزایش دهد"
    " و مالیات بر درآمد اعضا را کاهش دهد."
    "\n\n_*سطح فعلی:*_ {}"
    "\n\n\n*توانایی‌ها*"
    "\nتوانایی‌ها اثرات میوه‌های شیطانی را تقلید می‌کنند و به همه اعضای خدمه گسترش می‌یابند."
    "\n\n_*توانایی‌های فعلی:*_"
    "{}"
    "\n\nفقط کاپیتان یا معاون اول خدمه می‌تواند یک تقویت را فعال کند"
)

# Crew level
CREW_LEVEL_UP_RECAP = "*ارتقا*: +۱ ظرفیت {} \\({}-\\>{}\\)\n*مالیات بر درآمد*: -۱ رده\n*هزینه*: ฿{}"
CREW_LEVEL = (
    "*سطح*"
    "\n\nبا ارتقای سطح، خدمه می‌تواند تعداد توانایی‌های مجاز یا ظرفیت اعضا را افزایش دهد"
    " و مالیات بر درآمد اعضا را کاهش دهد."
    "\nهر سطح قیمت سطح بعدی را دو برابر می‌کند."
    "\n\n*سطح فعلی*: {}"
    "\n*حداکثر اعضا*: {}"
    "\n*حداکثر توانایی‌ها*: {}"
    "\n\n*سطح بعدی*: {}"
    "\n{}"
    "\nصندوق خدمه: ฿{}"
)
CREW_LEVEL_UPGRADE_TYPE_MEMBER = "عضو"
CREW_LEVEL_UPGRADE_TYPE_ABILITY = "توانایی"

CREW_LEVEL_UP_CONFIRMATION_REQUEST = "آیا مطمئنید که می‌خواهید سطح خدمه را ارتقا دهید؟\n\n{}"
CREW_LEVEL_UP_SUCCESS = "سطح خدمه با موفقیت ارتقا یافت\n\n{}"
CREW_DAVY_BACK_FIGHT_LIST_NO_ITEMS = (
    "خدمه هنوز در هیچ دیوی بک فایتی شرکت نکرده است.\nکاپیتان می‌تواند خدمه"
    " دیگری را به چالش بکشد از:"
    f"\n`{CommandName.START.get_non_formatted()}-\\>{PVT_KEY_CREW}-\\>{PVT_KEY_CREW_SEARCH}"
    f"-\\>یک خدمه انتخاب کنید-\\>{PVT_KEY_CREW_DAVY_BACK_FIGHT}`"
)
CREW_DAVY_BACK_FIGHT_ITEM_TEXT = "{} در برابر {}"
CREW_DAVY_BACK_FIGHT_ITEM_TEXT_FILL_IN = "دیوی بک فایت"
CREW_DAVY_BACK_FIGHT_ITEM_DETAIL_TEXT = (
    "*{}*: {}\n\n*تاریخ شروع*: {}\n*تاریخ پایان*: {}\n*بازیکنان*: {}{}\n\n{}{}"
)
CREW_DAVY_BACK_FIGHT_ITEM_DETAIL_CONTRIBUTIONS = (
    "\n\n*مجموع کسب‌شده*: ฿{}\n*مجموع کسب‌شده حریف*: ฿{}\n*برترین بازیکن خدمه*: {} \\(฿{}\\)"
)
CREW_DAVY_BACK_FIGHT_ITEM_DETAIL_PENDING_CHEST = "\n*صندوق منجمد*: ฿{}"
CREW_DAVY_BACK_FIGHT_ITEM_DETAIL_END = "\n\n*پایان جریمه*: {}{}{}"
CREW_DAVY_BACK_FIGHT_ITEM_DETAIL_PENALTY_PAID = "\n*جریمه پرداخت‌شده*: {}"
CREW_DAVY_BACK_FIGHT_ITEM_DETAIL_PENALTY_RECEIVED = "\n*پرداخت جریمه دریافت‌شده*: {}"
CREW_DAVY_BACK_FIGHT_ITEM_DETAIL_CONSCRIPTED_MEMBER = "\n\n*عضو سربازگیری‌شده*: {}"

CREW_DAVY_BACK_FIGHT_REQUEST_ERROR_SAME_CREW = "نمی‌توان خدمه خود را به چالش کشید"
CREW_DAVY_BACK_FIGHT_REQUEST_ERROR_ALREADY_IN_FIGHT = "خدمه از قبل در یک دیوی بک فایت است"
CREW_DAVY_BACK_FIGHT_REQUEST_ERROR_ALREADY_PENDING = (
    "خدمه از قبل یک درخواست دیوی بک فایت در انتظار دارد"
)
CREW_DAVY_BACK_FIGHT_REQUEST_ERROR_IN_PENALTY_PERIOD = (
    "خدمه در دوره جریمه است و نمی‌تواند در دیوی بک فایت شرکت کند"
)
CREW_DAVY_BACK_FIGHT_REQUEST_ERROR_TOO_LATE = (
    "دیوی بک فایت نمی‌تواند کمتر از {} ساعت قبل از بازنشانی جایزه آغاز شود"
)
CREW_DAVY_BACK_FIGHT_REQUEST_ERROR_MINIMUM_PARTICIPANTS = (
    "خدمه باید حداقل {} عضو داشته باشد تا در دیوی بک فایت شرکت کند"
)
CREW_DAVY_BACK_FIGHT_REQUEST_ERROR_OPPONENT_NOT_ALLOWING = (
    "خدمه حریف اجازه درخواست‌های دیوی بک فایت را نمی‌دهد"
)
CREW_DAVY_BACK_FIGHT_PARTICIPANTS_RULES_RECAP = (
    ">تمام جایزه خالص کسب‌شده از چالش‌ها، نبردها و غارت‌ها به سمت کل دستاورد"
    " خدمه محاسبه خواهد شد.\n>- جایزه کسب‌شده از هم‌خدمه‌ای‌های شما محاسبه نمی‌شود\n>- جایزه"
    " کسب‌شده از غیربازیکنان خدمه حریف نصف ارزش‌گذاری می‌شود\n>- نیمی از هر سهم جدید صندوق خدمه"
    " منجمد خواهد شد\n>- بازیکنان خدمه برنده، سهم منجمدشده صندوق را از خدمه حریف"
    " متناسب با سهم خود دریافت خواهند کرد"
)
CREW_DAVY_BACK_FIGHT_RULES_RECAP = (
    ">یک *دیوی بک فایت* رقابتی بین ۲ خدمه است که به مدت معینی"
    f" طول می‌کشد.\n{CREW_DAVY_BACK_FIGHT_PARTICIPANTS_RULES_RECAP}.\n>- خدمه برنده"
    f" {Env.DAVY_BACK_FIGHT_LOSER_CHEST_PERCENTAGE.get()}% از سهم جدید صندوق خدمه بازنده را برای"
    " یک دوره جریمه دریافت خواهد کرد.\n>- خدمه برنده می‌تواند هر عضوی از خدمه حریف که در"
    " چالش شرکت کرده \\(به‌جز کاپیتان و معاون اول\\) را سربازگیری کند، و عضو جدید"
    " نمی‌تواند خدمه را تا پایان دوره جریمه ترک کند\n>در طول دیوی بک فایت و"
    " دوره جریمه احتمالی در صورت باخت، هیچ‌کس نمی‌تواند خدمه را ترک کند."
)
CREW_DAVY_BACK_FIGHT_REQUEST = (
    CREW_DAVY_BACK_FIGHT_RULES_RECAP
    + "\n\n*تعداد شرکت‌کنندگان*: {}\n*مدت*\\(ساعت\\): {}\n*دوره"
    " جریمه*\\(روز\\): {}\n\nآیا مطمئنید که می‌خواهید *{}* را به دیوی بک"
    f" فایت به چالش بکشید؟\nآن‌ها {Env.DAVY_BACK_FIGHT_REQUEST_EXPIRATION_TIME.get()} دقیقه فرصت"
    " خواهند داشت تا بپذیرند یا رد کنند."
)
CREW_DAVY_BACK_FIGHT_REQUEST_AUTO_ACCEPT = (
    "\n\n_*اگر مدت زمان حداقل"
    f" {Env.DAVY_BACK_FIGHT_DEFAULT_DURATION.get()} ساعت باشد، چالش به‌طور خودکار پذیرفته خواهد شد*_"
)
CREW_DAVY_BACK_FIGHT_REQUEST_EDIT_PARTICIPANTS = (
    "چند عضو از هر خدمه در دیوی بک فایت شرکت خواهند کرد؟"
)
CREW_DAVY_BACK_FIGHT_REQUEST_EDIT_DURATION = "دیوی بک فایت چند ساعت طول خواهد کشید؟"
CREW_DAVY_BACK_FIGHT_REQUEST_EDIT_PENALTY = "دوره جریمه چند روز طول خواهد کشید؟"
CREW_DAVY_BACK_FIGHT_REQUEST_SUCCESS = (
    "چالش دیوی بک فایت به *{}* با موفقیت ارسال شد، پس از پذیرفته شدن به شما اطلاع داده خواهد شد"
)
CREW_DAVY_BACK_FIGHT_CAPTAIN_REQUEST = (
    "چالش دیوی بک فایت جدید از {}!"
    "\n\n*تعداد شرکت‌کنندگان*: {}"
    "\n*مدت*\\(ساعت\\): {}"
    "\n*دوره جریمه*\\(روز\\): {}"
    "\n\nشما {} فرصت دارید تا چالش را بپذیرید"
    "\n\n" + CREW_DAVY_BACK_FIGHT_RULES_RECAP
)
CREW_DAVY_BACK_FIGHT_CAPTAIN_ACCEPTED = (
    "دیوی بک فایت در برابر {} پذیرفته شد، در"
    f" {Env.DAVY_BACK_FIGHT_START_WAIT_TIME.get()} دقیقه آغاز خواهد شد.\n\nبرای بازبینی"
    f" و تغییر بازیکنان `{KEY_MANAGE}` را کلیک کنید"
)
CREW_DAVY_BACK_FIGHT_CAPTAIN_REQUEST_AUTO_ACCEPT = (
    "شما یک چالش دیوی بک فایت از {} را پذیرفتید!"
    "\n\n*تعداد شرکت‌کنندگان*: {}"
    "\n*مدت*\\(ساعت\\): {}"
    "\n*دوره جریمه*\\(روز\\): {}"
    f"\n\nچالش در {Env.DAVY_BACK_FIGHT_START_WAIT_TIME.get()} دقیقه آغاز خواهد شد."
    "\n\n_این چالش به‌طور خودکار پذیرفته شد، برای تغییر این تنظیم [اینجا کلیک کنید]({})_"
    f"\n\nبرای بازبینی و تغییر بازیکنان `{KEY_MANAGE}` را کلیک کنید"
    "\n\n" + CREW_DAVY_BACK_FIGHT_RULES_RECAP
)
CREW_DAVY_BACK_FIGHT_CAPTAIN_REJECTED = "دیوی بک فایت در برابر {} رد شد"
CREW_DAVY_BACK_FIGHT_USER_NOT_MEMBER_OF_PARTICIPATING_CREW = (
    "کاربر عضوی از خدمه شرکت‌کننده نیست"
)
CREW_DAVY_BACK_FIGHT_USER_ALREADY_PARTICIPANT = "کاربر از قبل یک شرکت‌کننده است"
CREW_DAVY_BACK_FIGHT_NOT_ENOUGH_MEMBERS = (
    "اعضای کافی برای شرکت در دیوی بک فایت وجود ندارد"
)
CREW_DAVY_BACK_FIGHT_PARTICIPANTS_SELECT_ERROR_ALREADY_STARTED = (
    "دیوی بک فایت از قبل شروع شده است"
)
CREW_DAVY_BACK_FIGHT_PARTICIPANTS_SELECT_ERROR_NOT_ENOUGH_MEMBERS = "عضو اضافه‌ای برای جابه‌جایی وجود ندارد"
CREW_DAVY_BACK_FIGHT_PARTICIPANTS_SELECT = (
    "اعضایی که می‌خواهید در دیوی بک فایت شرکت کنند را انتخاب کنید.\n\nزمان باقی‌مانده: {}"
)
CREW_DAVY_BACK_FIGHT_PARTICIPANTS_SELECT_SWAP = "عضوی که می‌خواهید با آن جابه‌جا کنید را انتخاب کنید"
CREW_DAVY_BACK_FIGHT_PARTICIPANTS = "*هم‌تیمی‌ها*{}\n\n*حریفان*{}"
CREW_DAVY_BACK_FIGHT_PARTICIPANTS_ITEM = "\n{} - ฿{}"
CREW_DAVY_BACK_FIGHT_PARTICIPANTS_ITEM_POTENTIAL_WIN = "\nبرد احتمالی: ฿{}\n"
CREW_DAVY_BACK_FIGHT_PARTICIPANTS_ITEM_WIN = "\nبرد: ฿{}\n"

CREW_DAVY_BACK_FIGHT_PARTICIPANTS_RULES_WITH_TIME = (
    f"\n\n_{CREW_DAVY_BACK_FIGHT_PARTICIPANTS_RULES_RECAP}\n\n*زمان باقی‌مانده*: {{}}_"
)
CREW_DAVY_BACK_FIGHT_WON = (
    f"\n\n_برای *{{}}* آینده، {Env.DAVY_BACK_FIGHT_LOSER_CHEST_PERCENTAGE.get()}% از هر"
    " سهم جدید صندوق خدمه حریف به خدمه شما داده خواهد شد.\nعلاوه بر این، کاپیتان خدمه شما"
    " می‌تواند هر عضوی از خدمه حریف که شرکت کرده \\(به‌جز کاپیتان و"
    " معاون اول\\) را سربازگیری کند، که تا پایان دوره جریمه نمی‌تواند خدمه شما را ترک کند._"
)
CREW_DAVY_BACK_FIGHT_LOST = (
    f"\n\n_برای *{{}}* آینده، {Env.DAVY_BACK_FIGHT_LOSER_CHEST_PERCENTAGE.get()}% از هر"
    " سهم جدید صندوق خدمه به خدمه حریف داده خواهد شد.\nعلاوه بر این، خدمه حریف می‌تواند"
    " هر عضوی از خدمه شما که شرکت کرده \\(به‌جز کاپیتان و معاون اول\\) را سربازگیری کند،"
    " که تا پایان دوره جریمه نمی‌تواند خدمه حریف را ترک کند._"
)
CREW_DAVY_BACK_FIGHT_OPPONENT_CONSCRIPT_ERROR_PENALTY_PERIOD_ENDED = "دوره جریمه به پایان رسیده است"
CREW_DAVY_BACK_FIGHT_OPPONENT_CONSCRIPT_ERROR_ALREADY_CONSCRIPTED = (
    "یک حریف از قبل سربازگیری شده است"
)
CREW_DAVY_BACK_FIGHT_OPPONENT_CONSCRIPT_CHOOSE_CONSCRIPT = (
    "عضوی که می‌خواهید از خدمه حریف سربازگیری کنید را انتخاب کنید.\nآن‌ها باید تا پایان"
    " دوره جریمه در {} در خدمه شما بمانند."
)
CREW_DAVY_BACK_FIGHT_OPPONENT_CONSCRIPT_CHOOSE_CONFIRMATION_REQUEST = (
    "آیا مطمئنید که می‌خواهید {} را از خدمه حریف سربازگیری کنید؟"
)
CREW_DAVY_BACK_FIGHT_OPPONENT_CONSCRIPT_SUCCESS = "{} به خدمه شما سربازگیری شد"

# Bounty Gift
BOUNTY_GIFT_NO_AMOUNT = (
    "باید مبلغ بلی‌ای که می‌خواهید هدیه دهید را مشخص کنید\n\nمثال:"
    f" {CommandName.BOUNTY_GIFT.get_formatted()} 10.000.000"
)
BOUNTY_GIFT_REQUEST = (
    "آیا مطمئنید که می‌خواهید ฿*{}* به {} هدیه دهید؟\n\nمالیات: ฿{} \\({}%\\)\nمجموع: ฿*{}*"
)
BOUNTY_GIFT_CONFIRMED = "شما ฿*{}* به {} هدیه دادید\n\nمالیات: ฿{} \\({}%\\)\nمجموع: ฿*{}*"
BOUNTY_GIFT_CANCELLED = "هدیه لغو شد"
BOUNTY_GIFT_NOT_ENOUGH_BOUNTY = (
    "شما بلی کافی برای هدیه دادن ندارید\n\nبلی موجود: ฿{}\nمبلغ هدیه: ฿*{}*\nمالیات: ฿{}"
    " \\({}%\\)\nمجموع: ฿*{}*\n\nشما می‌توانید تا ฿`{}` هدیه دهید"
)

# Bounty Loan
BOUNTY_LOAN_INVALID_COMMAND = (
    "باید مبلغ وام، مبلغ بازپرداخت و مدت زمان را مشخص کنید\n\nمثال:"
    f" {CommandName.BOUNTY_LOAN.get_formatted()} 100mil 150mil 1day"
)
BOUNTY_LOAN_LOANER = "\nوام‌دهنده: {}"
BOUNTY_LOAN_BORROWER = "\nوام‌گیرنده: {}"
BOUNTY_LOAN_AMOUNT = "\nمبلغ: ฿*{}*"
BOUNTY_LOAN_REPAY_AMOUNT = "\nمبلغ بازپرداخت: ฿*{}*"
BOUNTY_LOAN_AMOUNT_REPAID = "\nمبلغ پرداخت‌شده: ฿*{}*"
BOUNTY_LOAN_AMOUNT_REMAINING = "\nمبلغ باقی‌مانده: ฿*{}*"
BOUNTY_LOAN_AMOUNT_REMAINING_MONOSPACE = "\nمبلغ باقی‌مانده: ฿`{}`"
BOUNTY_LOAN_DATE = "\nتاریخ: *{}*"
BOUNTY_LOAN_DURATION = "\nمدت: *{}*"
BOUNTY_LOAN_DEADLINE_DATE = "\nمهلت: *{}*"
BOUNTY_LOAN_TAX = "\nمالیات: ฿{} \\({}%\\)"
BOUNTY_LOAN_TOTAL = "\nمجموع: ฿*{}*"
BOUNTY_LOAN_STATUS = "\n\nوضعیت: {}*{}*"
BOUNTY_LOAN_CANCELLED = "وام لغو شد"
BOUNTY_LOAN_NOT_ENOUGH_BOUNTY = (
    "شما بلی کافی برای وام گرفتن ندارید\n\nبلی موجود: ฿{}\nمبلغ وام: ฿*{}*\nمالیات: ฿{}"
    " \\({}%\\)\nمجموع: ฿*{}*\n\nشما می‌توانید تا ฿`{}` وام بگیرید"
)
BOUNTY_LOAN_ISSUE_COOLDOWN_ACTIVE = "می‌توانید وامی را در *{}* صادر کنید"
BOUNTY_LOAN_MAX_DURATION_EXCEEDED = (
    f"یک وام نمی‌تواند بیش از {Env.BOUNTY_LOAN_MAX_DURATION_DAYS.get_int()} روز طول بکشد"
)
BOUNTY_LOAN_STATUS_AWAITING_LOANER_CONFIRMATION = "در انتظار تأیید وام‌دهنده"
BOUNTY_LOAN_STATUS_AWAITING_BORROWER_CONFIRMATION = "در انتظار تأیید وام‌گیرنده"
BOUNTY_LOAN_STATUS_ACTIVE = "فعال"
BOUNTY_LOAN_STATUS_REPAID = "بازپرداخت‌شده"
BOUNTY_LOAN_STATUS_EXPIRED = "منقضی‌شده"
BOUNTY_LOAN_STATUS_FORGIVEN = "بخشیده‌شده"
BOUNTY_LOAN_EXPIRED_ACTION_WARNING_PREFIX = "\n\n_در صورتی که وام به‌موقع بازپرداخت نشود، "
BOUNTY_LOAN_EXPIRED_ACTION_SUFFIX = (
    "\nاگر"
    f" {Env.BOUNTY_LOAN_FORGIVENESS_DAYS.get_int()} روز از تاریخ انقضا گذشته باشد و"
    " حداقل دو برابر مبلغ وام بازپرداخت شده باشد، وام به‌طور خودکار بخشیده خواهد شد."
)
BOUNTY_LOAN_EXPIRED_ACTION_PREFIX = "\n\n_از آنجا که وام به‌موقع بازپرداخت نشد، "
BOUNTY_LOAN_EXPIRED_ACTION_LOANER = (
    "{}% از تمام جایزه جدید کسب‌شده توسط {} تا زمان بازپرداخت وام به شما منتقل خواهد شد."
    + BOUNTY_LOAN_EXPIRED_ACTION_SUFFIX
    + "_"
)
BOUNTY_LOAN_EXPIRED_ACTION_BORROWER = (
    "{}% از تمام جایزه جدید کسب‌شده تا زمان بازپرداخت وام به {} منتقل خواهد شد."
    + BOUNTY_LOAN_EXPIRED_ACTION_SUFFIX
    + "_"
)
BOUNTY_LOAN_EXPIRED_ACTION_LOANER_AND_BORROWER = (
    "{}% از تمام جایزه جدید کسب‌شده توسط {} تا زمان بازپرداخت وام به {} منتقل خواهد شد."
    + BOUNTY_LOAN_EXPIRED_ACTION_SUFFIX
    + "_"
)
BOUNTY_LOAN_AUTO_FORGIVEN = (
    "\n\n>این وام به‌طور خودکار بخشیده شد زیرا"
    f" {Env.BOUNTY_LOAN_FORGIVENESS_DAYS.get_int()} روز از تاریخ انقضا گذشته و"
    " حداقل دو برابر مبلغ وام بازپرداخت شده است."
)
BOUNTY_LOAN_REQUEST = (
    "*وام جدید*\n"
    + BOUNTY_LOAN_LOANER
    + BOUNTY_LOAN_BORROWER
    + BOUNTY_LOAN_AMOUNT
    + BOUNTY_LOAN_REPAY_AMOUNT
    + BOUNTY_LOAN_DURATION
    + BOUNTY_LOAN_TAX
    + BOUNTY_LOAN_TOTAL
    + BOUNTY_LOAN_STATUS
    + BOUNTY_LOAN_EXPIRED_ACTION_WARNING_PREFIX
    + BOUNTY_LOAN_EXPIRED_ACTION_LOANER_AND_BORROWER
)
BOUNTY_LOAN_REQUEST_PREDATORY_WARNING = (
    f"\n\n{Emoji.WARNING_STRONG}هشدار، این یک وام مفت‌خورانه با نرخ بهره *{{}}%* است."
)
BOUNTY_LOAN_REQUEST_MANAGE_TEXT = "\n\n" + surround_with_arrows("[مدیریت وام]({})")

# Bounty loan - Private Chat
BOUNTY_LOAN_ITEM_TEXT = "{} ฿{} {} {}"
BOUNTY_LOAN_ITEM_TEXT_FILL_IN = "وام"
BOUNTY_LOAN_ITEM_NOT_ACTIVE = "این وام دیگر فعال نیست"
BOUNTY_LOAN_ITEM_PAY_REQUEST = (
    BOUNTY_LOAN_REPAY_AMOUNT.strip()
    + BOUNTY_LOAN_AMOUNT_REPAID
    + BOUNTY_LOAN_AMOUNT_REMAINING_MONOSPACE
    + "\nجایزه فعلی: ฿`{}`"
    + "\n\n_لطفاً مبلغی که می‌خواهید پرداخت کنید را ارسال کنید \\(برای بازپرداخت حداکثر مجاز توسط"
    " جایزه‌تان \\* ارسال کنید\\)_"
)
BOUNTY_LOAN_ITEM_PAY_CONFIRMATION_REQUEST = "آیا مطمئنید که می‌خواهید ฿*{}* برای این وام پرداخت کنید؟"
BOUNTY_LOAN_ITEM_PAY_SUCCESS = "شما با موفقیت ฿{} برای این وام پرداخت کردید"
BOUNTY_LOAN_ITEM_FORGIVE_CONFIRMATION_REQUEST = (
    BOUNTY_LOAN_REPAY_AMOUNT.strip()
    + BOUNTY_LOAN_AMOUNT_REPAID
    + BOUNTY_LOAN_AMOUNT_REMAINING_MONOSPACE
    + "\n\nآیا مطمئنید که می‌خواهید این وام را ببخشید؟\nنمی‌توانید مبلغ"
    " باقی‌مانده را دریافت کنید"
)
BOUNTY_LOAN_ITEM_FORGIVE_SUCCESS = "شما این وام را بخشیدید"
BOUNTY_LOAN_SOURCE = "\nمنبع: [{}]({})"
BOUNTY_LOAN_SOURCE_USER = "وام"
BOUNTY_LOAN_SOURCE_PLUNDER = "غارت"
BOUNTY_LOAN_SOURCE_IMPEL_DOWN_BAIL = "وثیقه ایمپل دان"

# Notification - Categories
NOTIFICATION_CATEGORY_BOUNTY_GIFT = "هدیه جایزه"
NOTIFICATION_CATEGORY_BOUNTY_LOAN = "وام جایزه"
NOTIFICATION_CATEGORY_CREW = "خدمه"
NOTIFICATION_CATEGORY_DELETED_MESSAGE = "پیام حذف‌شده"
NOTIFICATION_CATEGORY_GAME = "بازی"
NOTIFICATION_CATEGORY_IMPEL_DOWN = "ایمپل دان"
NOTIFICATION_CATEGORY_LOCATION = "موقعیت"
NOTIFICATION_CATEGORY_PREDICTION = "پیش‌بینی"
NOTIFICATION_CATEGORY_DEVIL_FRUIT = "میوه شیطانی"
NOTIFICATION_CATEGORY_WARLORD = "جنگ‌سالار"
NOTIFICATION_CATEGORY_DAVY_BACK_FIGHT = "دیوی بک فایت"
NOTIFICATION_CATEGORY_FIGHT = "نبرد"
NOTIFICATION_CATEGORY_PLUNDER = "غارت"

# Notification - Crew Leave
CREW_LEAVE_NOTIFICATION = "{} خدمه را ترک کرد"
CREW_LEAVE_NOTIFICATION_DESCRIPTION = (
    "در صورتی که بخواهید هنگام ترک کردن یک عضو از خدمه مطلع شوید. \nفقط در صورتی قابل اجراست که کاپیتان یا"
    " معاون اول خدمه باشید."
)
CREW_LEAVE_NOTIFICATION_KEY = "ترک خدمه"
# Notification - Crew Member removed
CREW_MEMBER_REMOVE_NOTIFICATION = "شما از خدمه اخراج شده‌اید"
CREW_MEMBER_REMOVE_NOTIFICATION_DESCRIPTION = (
    "در صورتی که بخواهید هنگام اخراج شدن از خدمه مطلع شوید."
)
CREW_MEMBER_REMOVE_NOTIFICATION_KEY = "اخراج از خدمه"
# Notification - Crew Disband
CREW_DISBAND_NOTIFICATION = "خدمه شما منحل شده است"
CREW_DISBAND_NOTIFICATION_DESCRIPTION = "در صورتی که بخواهید هنگام انحلال خدمه‌تان مطلع شوید."
CREW_DISBAND_NOTIFICATION_KEY = "انحلال خدمه"
# Notification - Crew disband warning
CREW_DISBAND_WARNING_NOTIFICATION = (
    "شما در فصل جایزه فعلی فعالیتی نداشته‌اید."
    "\nدر صورت ادامه عدم فعالیت، خدمه شما در بازنشانی جایزه بعدی در {} منحل خواهد شد"
)
CREW_DISBAND_WARNING_NOTIFICATION_DESCRIPTION = (
    "در صورتی که بخواهید یک هفته قبل از انحلال خدمه‌تان به دلیل عدم فعالیت مطلع شوید."
    "\nفقط در صورتی قابل اجراست که کاپیتان خدمه باشید."
)
CREW_DISBAND_WARNING_NOTIFICATION_KEY = "هشدار انحلال خدمه"
# Notification - Crew ability activated
CREW_ABILITY_ACTIVATED_NOTIFICATION = (
    "توانایی زیر در خدمه شما فعال شده است:\n\n*توانایی*: {}"
    " \\({}%\\)\n*مدت*: {}"
)
CREW_ABILITY_ACTIVATED_NOTIFICATION_DESCRIPTION = (
    "در صورتی که بخواهید هنگام فعال شدن یک توانایی در خدمه‌تان مطلع شوید."
)
CREW_ABILITY_ACTIVATED_NOTIFICATION_KEY = "فعال‌سازی توانایی خدمه"
# Notification - Crew first mate promotion
CREW_FIRST_MATE_PROMOTION_NOTIFICATION = (
    "تبریک می‌گویم! شما به معاون اول خدمه ارتقا یافتید.\n\nامتیازات:"
    + CREW_FIRST_MATE_PRIVILEGES
)
CREW_FIRST_MATE_PROMOTION_NOTIFICATION_DESCRIPTION = (
    "در صورتی که بخواهید هنگام ارتقا یافتن به معاون اول خدمه مطلع شوید."
)
CREW_FIRST_MATE_PROMOTION_NOTIFICATION_KEY = "ارتقا به معاون اول"
# Notification - Crew first mate demotion
CREW_FIRST_MATE_DEMOTION_NOTIFICATION = "شما از معاون اول خدمه تنزل یافتید."
CREW_FIRST_MATE_DEMOTION_NOTIFICATION_DESCRIPTION = (
    "در صورتی که بخواهید هنگام تنزل یافتن از معاون اول خدمه مطلع شوید."
)
CREW_FIRST_MATE_DEMOTION_NOTIFICATION_KEY = "تنزل از معاون اول"
# Notification - Crew Captain promotion
CREW_CAPTAIN_PROMOTION_NOTIFICATION = (
    "تبریک می‌گویم! شما به کاپیتان خدمه ارتقا یافتید"
)
CREW_CAPTAIN_PROMOTION_NOTIFICATION_DESCRIPTION = (
    "در صورتی که بخواهید هنگام ارتقا یافتن به کاپیتان خدمه مطلع شوید."
)
CREW_CAPTAIN_PROMOTION_NOTIFICATION_KEY = "ارتقا به کاپیتان"

# Notification - Crew join request accepted
CREW_JOIN_REQUEST_ACCEPTED_NOTIFICATION = (
    "تبریک می‌گویم! درخواست شما برای پیوستن به *{}* پذیرفته شد"
)
CREW_JOIN_REQUEST_ACCEPTED_NOTIFICATION_DESCRIPTION = (
    "در صورتی که بخواهید هنگام پذیرفته شدن درخواست پیوستن به یک خدمه مطلع شوید."
)
CREW_JOIN_REQUEST_ACCEPTED_NOTIFICATION_KEY = "پذیرش درخواست عضویت"
# Notification - Crew join request rejected
CREW_JOIN_REQUEST_REJECTED_NOTIFICATION = "درخواست شما برای پیوستن به *{}* رد شد"
CREW_JOIN_REQUEST_REJECTED_NOTIFICATION_DESCRIPTION = (
    "در صورتی که بخواهید هنگام رد شدن درخواست پیوستن به یک خدمه مطلع شوید."
)
CREW_JOIN_REQUEST_REJECTED_NOTIFICATION_KEY = "رد درخواست عضویت"
# Notification - Crew conscription start
CREW_CONSCRIPTION_START_NOTIFICATION = (
    "شما به {} سربازگیری شدید.\n\nنمی‌توانید تا *{}* خدمه را ترک کنید."
)
CREW_CONSCRIPTION_START_NOTIFICATION_DESCRIPTION = (
    "در صورتی که بخواهید هنگام سربازگیری شدن به یک خدمه مطلع شوید."
)
CREW_CONSCRIPTION_START_NOTIFICATION_KEY = "شروع سربازگیری"
# Notification - Crew conscription start captain
CREW_CONSCRIPTION_START_CAPTAIN_NOTIFICATION = (
    "{} از خدمه شما به {} سربازگیری شد.\n\nآن‌ها نمی‌توانند تا *{}* خدمه را ترک کنند."
)
CREW_CONSCRIPTION_START_CAPTAIN_NOTIFICATION_DESCRIPTION = (
    "در صورتی که بخواهید هنگام سربازگیری شدن یکی از اعضای خدمه‌تان به خدمه دیگر مطلع شوید."
    "\nفقط در صورتی قابل اجراست که کاپیتان خدمه باشید"
)
CREW_CONSCRIPTION_START_CAPTAIN_NOTIFICATION_KEY = "شروع سربازگیری \\(کاپیتان\\)"
# Notification - Crew conscription end
CREW_CONSCRIPTION_END_NOTIFICATION = (
    "دوره سربازگیری شما نزد {} به پایان رسید، اکنون می‌توانید خدمه را ترک کنید"
)
CREW_CONSCRIPTION_END_NOTIFICATION_DESCRIPTION = (
    "در صورتی که بخواهید هنگام پایان دوره سربازگیری‌تان مطلع شوید."
)
CREW_CONSCRIPTION_END_NOTIFICATION_KEY = "پایان سربازگیری"

# Notification - Davy Back Fight request accepted
DAVY_BACK_FIGHT_REQUEST_ACCEPTED_NOTIFICATION = (
    "{} چالش دیوی بک فایت خدمه شما را پذیرفت، در"
    f" {Env.DAVY_BACK_FIGHT_START_WAIT_TIME.get()} دقیقه آغاز خواهد شد.\n\nبرای بازبینی"
    f" و تغییر بازیکنان `{KEY_MANAGE}` را کلیک کنید"
)
DAVY_BACK_FIGHT_REQUEST_ACCEPTED_NOTIFICATION_DESCRIPTION = (
    "در صورتی که بخواهید هنگام پذیرفته شدن چالش دیوی بک فایت خدمه‌تان مطلع شوید."
    "\nفقط در صورتی قابل اجراست که کاپیتان خدمه باشید"
)
DAVY_BACK_FIGHT_REQUEST_ACCEPTED_NOTIFICATION_KEY = "پذیرش چالش"
# Notification - Davy Back Fight request rejected
CREW_DAVY_BACK_FIGHT_REQUEST_REJECTED_NOTIFICATION = (
    "{} چالش دیوی بک فایت خدمه شما را رد کرد"
)
DAVY_BACK_FIGHT_REQUEST_REJECTED_NOTIFICATION_DESCRIPTION = (
    "در صورتی که بخواهید هنگام رد شدن چالش دیوی بک فایت خدمه‌تان مطلع شوید."
    "\nفقط در صورتی قابل اجراست که کاپیتان خدمه باشید"
)
DAVY_BACK_FIGHT_REQUEST_REJECTED_NOTIFICATION_KEY = "رد چالش"
# Notification - Davy Back Fight start
DAVY_BACK_FIGHT_START_NOTIFICATION = (
    "شما به‌عنوان بازیکن برای یک دیوی بک فایت در برابر {} انتخاب شدید!"
    + CREW_DAVY_BACK_FIGHT_PARTICIPANTS_RULES_WITH_TIME
)
DAVY_BACK_FIGHT_START_NOTIFICATION_DESCRIPTION = (
    "در صورتی که بخواهید هنگام شروع دیوی بک فایتی که در آن بازیکن هستید مطلع شوید"
)
DAVY_BACK_FIGHT_START_NOTIFICATION_KEY = "شروع"
# Notification - Davy Back Fight end
DAVY_BACK_FIGHT_END_NOTIFICATION = ""
DAVY_BACK_FIGHT_END_NOTIFICATION_DESCRIPTION = (
    "در صورتی که بخواهید هنگام پایان دیوی بک فایتی که در آن بازیکن هستید مطلع شوید"
)
DAVY_BACK_FIGHT_END_NOTIFICATION_KEY = "پایان"
DAVY_BACK_FIGHT_END_NOTIFICATION_WON = (
    f"{Emoji.CONFETTI}تبریک می‌گویم، خدمه شما دیوی بک فایت را در برابر "
    "{} برد!\n\nشما ฿*{}* برای سهم"
    " {}% از کل دستاورد به دست آوردید."
    f"{CREW_DAVY_BACK_FIGHT_WON}"
)
DAVY_BACK_FIGHT_END_NOTIFICATION_LOST = (
    f"{Emoji.LOG_NEGATIVE}خدمه شما دیوی بک فایت را در برابر "
    "{} باخت."
    f"{CREW_DAVY_BACK_FIGHT_LOST}"
)

# Notification - Game turn
GAME_TURN_NOTIFICATION = (
    f"نوبت شماست که در {{}} در برابر {{}} بازی کنید.\n\n[{Emoji.RIGHT_ARROW}برای مشاهده"
    f" بازی کلیک کنید{Emoji.LEFT_ARROW}]" + "({}){}"
)
GAME_TURN_NOTIFICATION_DESCRIPTION = (
    "در صورتی که بخواهید هنگام رسیدن نوبت شما در یک بازی، در صورت عدم انجام هیچ اقدامی برای"
    f" {Env.GAME_TURN_NOTIFICATION_TIME_SECONDS.get_int()} ثانیه مطلع شوید"
)
GAME_TURN_NOTIFICATION_KEY = "نوبت بازی"
# Notification - Location
LOCATION_UPDATE_NOTIFICATION = "{}تبریک می‌گویم {}!\nشما اکنون {} {} هستید\n\n{}"
LOCATION_NEXT_LEVEL_REQUIREMENT = "_شرط لازم برای موقعیت بعدی: ฿*{}*_"
LOCATION_CURRENT_LEVEL_MAX = "_شما به حداکثر موقعیت رسیده‌اید_"
LOCATION_UPDATE_NOTIFICATION_DESCRIPTION = "در صورتی که بخواهید هنگام رسیدن به موقعیت جدید مطلع شوید."
LOCATION_UPDATE_NOTIFICATION_KEY = "به‌روزرسانی موقعیت"
# Notification - Impel Down restriction placed
IMPEL_DOWN_RESTRICTION_PLACED_NOTIFICATION = (
    f"{Emoji.DISCIPLINARY_ACTION}*اقدام انضباطی*{Emoji.DISCIPLINARY_ACTION}\n\n*دلیل*:"
    " {}\n\n*محدودیت‌ها*:{}{}{}"
)
IMPEL_DOWN_RESTRICTION_PLACED_NOTIFICATION_BOUNTY_HALVED = "\n- جایزه نصف شد"
IMPEL_DOWN_RESTRICTION_PLACED_NOTIFICATION_BOUNTY_ERASED = "\n- جایزه پاک شد"
IMPEL_DOWN_RESTRICTIONS = (
    "\n• نمی‌توانید جایزه جدیدی کسب کنید"
    "\n• نمی‌توانید در جدول امتیازات ظاهر شوید"
    "\n• نمی‌توانید سایر کاربران را به چالش بکشید یا بازی کنید"
    "\n• نمی‌توانید در نظرسنجی‌ها شرط ببندید"
)
IMPEL_DOWN_RESTRICTION_PLACED_NOTIFICATION_DURATION = "\n\n*مدت*: {}"
IMPEL_DOWN_RESTRICTION_PLACED_NOTIFICATION_DURATION_PERMANENT = "دائمی"
IMPEL_DOWN_RESTRICTION_BAIL_GUIDE = (
    "\n\nشما یا یکی از هم‌خدمه‌ای‌ها می‌توانید وثیقه بپردازید، به قیمت"
    f" ฿*{Env.IMPEL_DOWN_BAIL_PER_MINUTE.get_belly()}* برای هر دقیقه باقی‌مانده از محکومیت شما."
    f" \n\\(`{PVT_KEY_CREW}`-\\>`{PVT_KEY_CREW_MEMBERS}`-\\>"
    f"انتخاب-\\>`{KEY_POST_BAIL}`\\)"
)
IMPEL_DOWN_RESTRICTION_PLACED_NOTIFICATION_DESCRIPTION = (
    "در صورتی که بخواهید هنگام محدود شدن مطلع شوید"
)
IMPEL_DOWN_RESTRICTION_PLACED_NOTIFICATION_KEY = "اعمال محدودیت"
# Notification - Impel Down restriction removed
IMPEL_DOWN_RESTRICTION_REMOVED_NOTIFICATION = "همه محدودیت‌ها برداشته شد"
IMPEL_DOWN_RESTRICTION_REMOVED_NOTIFICATION_DESCRIPTION = (
    "در صورتی که بخواهید هنگام برداشته شدن همه محدودیت‌ها مطلع شوید"
)
IMPEL_DOWN_RESTRICTION_REMOVED_NOTIFICATION_KEY = "رفع محدودیت"
# Notification - Impel Down bail posted
IMPEL_DOWN_BAIL_POSTED_NOTIFICATION = (
    "{} مبلغ *฿{}* پرداخت کرد تا شما را از ایمپل دان آزاد کند \\({} از محکومیت شما باقی مانده بود\\)"
)
IMPEL_DOWN_BAIL_POSTED_NOTIFICATION_DESCRIPTION = "در صورتی که بخواهید هنگام پرداخت وثیقه برای شما مطلع شوید"
IMPEL_DOWN_BAIL_POSTED_NOTIFICATION_KEY = "پرداخت وثیقه"

# Notification - Prediction result
PREDICTION_RESULT_NOTIFICATION = 'شما *{}* ฿{} در پیش‌بینی "*{}*"{}{}{}'
PREDICTION_RESULT_NOTIFICATION_WAGER_REFUNDED = "_\n\n\\(شرط شما بازگردانده شد\\)_"
PREDICTION_RESULT_NOTIFICATION_WAGER_REFUNDED_PARTIAL = "_\n\n\\(مبلغ ฿{} به شما بازگردانده شد\\)_"
PREDICTION_RESULT_NOTIFICATION_WAGER_REFUNDED_NO_CORRECT_OPTIONS = (
    "_\n\n\\(از آنجا که هیچ گزینه صحیحی وجود نداشت، شرط شما بازگردانده شد\\)_"
)
PREDICTION_RESULT_NOTIFICATION_OPTION = "\n{}{}"
PREDICTION_RESULT_NOTIFICATION_OPTION_NO_EMOJI = "\n- {}"
PREDICTION_RESULT_NOTIFICATION_YOUR_OPTION = "\n\n*گزینه شما*: {}"
PREDICTION_RESULT_NOTIFICATION_YOUR_OPTIONS = "\n\n*گزینه‌های شما*: {}"
PREDICTION_RESULT_NOTIFICATION_CORRECT_OPTION = "\n\n*گزینه صحیح*: {}"
PREDICTION_RESULT_NOTIFICATION_CORRECT_OPTIONS = "\n\n*گزینه‌های صحیح*: {}"
PREDICTION_RESULT_NOTIFICATION_DESCRIPTION = (
    "در صورتی که بخواهید از نتیجه پیش‌بینی‌ای که در آن شرکت کرده‌اید مطلع شوید"
)
PREDICTION_RESULT_NOTIFICATION_KEY = "نتیجه پیش‌بینی"
# Notification - Prediction bet invalid
PREDICTION_BET_INVALID_BET_HAS = "شرط"
PREDICTION_BET_INVALID_BETS_HAVE = "شرط‌ها"
PREDICTION_BET_INVALID_NOTIFICATION = (
    'شرط‌های زیر به این دلیل که {} پس از زمان قطع شرط‌بندی \\({}\\) ثبت شده بود از پیش‌بینی'
    ' "*{}*" حذف شد:\n{}'
    + "\n\n_مبلغ ฿{} به شما بازگردانده شد_"
)
PREDICTION_BET_INVALID_NOTIFICATION_OPTION = "\n- {} \\({}\\)"
PREDICTION_BET_INVALID_NOTIFICATION_DESCRIPTION = (
    "در صورتی که بخواهید هنگام حذف شدن شرطی که به این دلیل که پس از زمان قطع شرط‌بندی"
    " ثبت شده بود مطلع شوید"
)
PREDICTION_BET_INVALID_NOTIFICATION_KEY = "حذف شرط پیش‌بینی"
# Notification - Deleted message because of arrest
ABOVE_MESSAGE_DELETED_FROM_CHAT_GROUP = (
    "پیام بالا از گروه چت حذف شد زیرا شما "
)
DELETED_MESSAGE_ARREST_NOTIFICATION = f"{ABOVE_MESSAGE_DELETED_FROM_CHAT_GROUP}بازداشت هستید"
DELETED_MESSAGE_ARREST_NOTIFICATION_DESCRIPTION = (
    "در صورتی که بخواهید هنگام حذف شدن پیامی که در گروه چت ارسال کرده‌اید به دلیل بازداشت بودن"
    " مطلع شوید"
)
DELETED_MESSAGE_ARREST_NOTIFICATION_KEY = "حذف پیام \\(بازداشت\\)"
# Notification - Deleted message because of user is muted
DELETED_MESSAGE_MUTE_NOTIFICATION = f"{ABOVE_MESSAGE_DELETED_FROM_CHAT_GROUP}ساکت شده‌اید"
DELETED_MESSAGE_MUTE_NOTIFICATION_DESCRIPTION = (
    "در صورتی که بخواهید هنگام حذف شدن پیامی که در گروه چت ارسال کرده‌اید به دلیل ساکت بودن مطلع شوید"
)
DELETED_MESSAGE_MUTE_NOTIFICATION_KEY = "حذف پیام \\(سکوت\\)"
# Notification - Deleted message because of user has not reached the required location
DELETED_MESSAGE_LOCATION_NOTIFICATION = (
    f"{ABOVE_MESSAGE_DELETED_FROM_CHAT_GROUP}به موقعیت لازم برای ارسال این نوع پیام"
    " نرسیده‌اید.\n\n*موقعیت شما*: {}\n*موقعیت لازم*: {}"
)
DELETED_MESSAGE_LOCATION_NOTIFICATION_DESCRIPTION = (
    "در صورتی که بخواهید هنگام حذف شدن پیامی که در گروه چت ارسال کرده‌اید به این دلیل که به موقعیت"
    " لازم برای ارسال آن نوع پیام نرسیده‌اید مطلع شوید"
)
DELETED_MESSAGE_LOCATION_NOTIFICATION_KEY = "حذف پیام \\(موقعیت\\)"
# Notification - Bounty Gift
BOUNTY_GIFT_RECEIVED_NOTIFICATION = "شما ฿{} هدیه از {} دریافت کردید"
BOUNTY_GIFT_RECEIVED_NOTIFICATION_DESCRIPTION = "در صورتی که بخواهید هنگام دریافت هدیه جایزه مطلع شوید"
BOUNTY_GIFT_RECEIVED_NOTIFICATION_KEY = "هدیه جایزه"
# Notification - Devil Fruit Awarded
DEVIL_FRUIT_EAT_OR_SELL = (
    "\n\nمی‌توانید آن را بخورید یا در فروشگاه یا یک گروه چت بفروشید"
    f"\\(دستور {CommandName.DEVIL_FRUIT_SELL.get_formatted()} <price\\>\\)"
)
DEVIL_FRUIT_AWARDED_NOTIFICATION = (
    "میوه شیطانی زیر به شما اهدا شد:\n\n*{}*\nدلیل: {}"
    + DEVIL_FRUIT_EAT_OR_SELL
)
DEVIL_FRUIT_AWARDED_NOTIFICATION_DESCRIPTION = (
    "در صورتی که بخواهید هنگام اهدا شدن یک میوه شیطانی مطلع شوید"
)
DEVIL_FRUIT_AWARDED_NOTIFICATION_KEY = "اهدای میوه شیطانی"
# Notification - Devil Fruit Expired
DEVIL_FRUIT_EXPIRED_NOTIFICATION = "میوه شیطانی *{}* شما منقضی شده و لغو گردید"
DEVIL_FRUIT_EXPIRED_NOTIFICATION_DESCRIPTION = "در صورتی که بخواهید هنگام انقضای میوه شیطانی‌تان مطلع شوید"
DEVIL_FRUIT_EXPIRED_NOTIFICATION_KEY = "انقضای میوه شیطانی"
# Notification - Devil Fruit revoke
DEVIL_FRUIT_REVOKE_NOTIFICATION = "میوه شیطانی *{}* شما لغو شد"
DEVIL_FRUIT_REVOKE_NOTIFICATION_DESCRIPTION = "در صورتی که بخواهید هنگام لغو شدن میوه شیطانی‌تان مطلع شوید"
DEVIL_FRUIT_REVOKE_NOTIFICATION_KEY = "لغو میوه شیطانی"
# Notification - Devil Fruit revoke warning
DEVIL_FRUIT_REVOKE_WARNING_NOTIFICATION = (
    "شما در آخرین"
    f" {Env.DEVIL_FRUIT_MAINTAIN_MIN_LATEST_LEADERBOARD_APPEARANCE.get_int() - 1}"
    " [جدول امتیازات جهانی]({}) ظاهر نشده‌اید."
    "\nاگر در جدول امتیازات بعدی نیز ظاهر نشوید، میوه شیطانی *{}* شما لغو خواهد شد."
)
DEVIL_FRUIT_REVOKE_WARNING_NOTIFICATION_DESCRIPTION = (
    "در صورتی که بخواهید یک هفته قبل از لغو میوه شیطانی که خورده‌اید به دلیل عدم ظاهر شدن"
    " در"
    f" {Env.DEVIL_FRUIT_MAINTAIN_MIN_LATEST_LEADERBOARD_APPEARANCE.get()} جدول امتیازات متوالی مطلع شوید"
)
DEVIL_FRUIT_REVOKE_WARNING_NOTIFICATION_KEY = "هشدار لغو میوه شیطانی"
# Notification - Devil Fruit Sold
DEVIL_FRUIT_SOLD_NOTIFICATION = (
    "میوه شیطانی شما خریداری شد!\n\n*نام*: {}\n*قیمت*: ฿{}\n*خریدار*: {}"
)
DEVIL_FRUIT_SOLD_NOTIFICATION_DESCRIPTION = "در صورتی که بخواهید هنگام فروخته شدن میوه شیطانی‌تان مطلع شوید"
DEVIL_FRUIT_SOLD_NOTIFICATION_KEY = "فروش میوه شیطانی"
# Notification - Bounty Loan
BOUNTY_LOAN_NOTIFICATION_GO_TO_ITEM_BUTTON_TEXT = "رفتن به وام"
# Notification - Bounty Loan Payment
BOUNTY_LOAN_PAYMENT_NOTIFICATION = "شما پرداختی به مبلغ ฿{} از {} برای وام خود دریافت کردید"
BOUNTY_LOAN_PAYMENT_NOTIFICATION_DESCRIPTION = (
    "در صورتی که بخواهید هنگام دریافت پرداختی برای وام خود مطلع شوید"
)
BOUNTY_LOAN_PAYMENT_NOTIFICATION_KEY = "پرداخت وام"
# Notification - Bounty Loan Forgiven
BOUNTY_LOAN_FORGIVEN_NOTIFICATION = "وام ฿{} شما از {} بخشیده شد"
BOUNTY_LOAN_FORGIVEN_NOTIFICATION_DESCRIPTION = "در صورتی که بخواهید هنگام بخشیده شدن وامتان مطلع شوید"
BOUNTY_LOAN_FORGIVEN_NOTIFICATION_KEY = "بخشش وام"
# Notification - Bounty Loan Expired
BOUNTY_LOAN_EXPIRED_NOTIFICATION = (
    "وام ฿{} شما از {} منقضی شد."
    + BOUNTY_LOAN_EXPIRED_ACTION_PREFIX
    + BOUNTY_LOAN_EXPIRED_ACTION_BORROWER
)
BOUNTY_LOAN_EXPIRED_NOTIFICATION_DESCRIPTION = "در صورتی که بخواهید هنگام انقضای وامتان مطلع شوید"
BOUNTY_LOAN_EXPIRED_NOTIFICATION_KEY = "انقضای وام"
# Notification - Warlord appointment
WARLORD_APPOINTMENT_NOTIFICATION = (
    "تبریک می‌گویم، شما به‌عنوان جنگ‌سالار منصوب شدید!\n\n*لقب*:"
    " {}\n*مدت*: {}\n*دلیل*: {}\n\n*امتیازات*\n•"
    f" {Env.PIRATE_KING_TRANSACTION_TAX_DISCOUNT.get_int()}% تخفیف مالیات هدیه‌ها و"
    " وام‌ها\n• مصونیت از لغو میوه شیطانی به دلیل عدم ظاهر شدن در آخرین"
    f" {Env.DEVIL_FRUIT_MAINTAIN_MIN_LATEST_LEADERBOARD_APPEARANCE.get_int()} جدول امتیازات\n•"
    " مشاهده وضعیت رتبه‌های پایین‌تر \\(امپراتور و پایین‌تر\\)\n• پوستر جایزه"
    " سفارشی جنگ‌سالار\n• مشاهده کاربران دنیای جدید"
    " در گزارش‌ها\n\n_شما به‌طور انحصاری با رتبه جنگ‌سالار در جدول امتیازات هفتگی"
    " ظاهر خواهید شد \\(فقط برای جدول امتیازات جهانی\\)_"
)
WARLORD_APPOINTMENT_NOTIFICATION_DESCRIPTION = (
    "در صورتی که بخواهید هنگام انتصاب به‌عنوان جنگ‌سالار مطلع شوید"
)
WARLORD_APPOINTMENT_NOTIFICATION_KEY = "انتصاب جنگ‌سالار"
# Notification - Warlord revocation
WARLORD_REVOCATION_NOTIFICATION = "عنوان جنگ‌سالاری شما لغو شد\n\n*دلیل*: {}"
WARLORD_REVOCATION_NOTIFICATION_DESCRIPTION = (
    "در صورتی که بخواهید هنگام لغو عنوان جنگ‌سالاری‌تان مطلع شوید"
)
WARLORD_REVOCATION_NOTIFICATION_KEY = "لغو جنگ‌سالاری"

# Notification - Legendary Pirate appointment
LEGENDARY_PIRATE_APPOINTMENT_NOTIFICATION = (
    "تبریک می‌گویم، شما به‌عنوان دزد دریایی افسانه‌ای منصوب شدید!\n\n*لقب*: {}\n\n"
    "*مدت*: {}\n\n*دلیل*: {}\n\n*امتیازات*\n• مصونیت کامل از تمام خسارت‌های"
    " مرتبط با نبرد\n• معافیت از مالیات جایزه و مالیات بر درآمد\n• وضعیت دائمی دریابان\n•"
    " مصونیت از لغو میوه شیطانی"
)
LEGENDARY_PIRATE_APPOINTMENT_NOTIFICATION_PERMANENT_FOOTER = (
    "\n\n_شما اکنون یک دزد دریایی افسانه‌ای دائمی هستید و همیشه در تمام جدول‌های"
    " امتیازات جهانی ظاهر خواهید شد_"
)
LEGENDARY_PIRATE_APPOINTMENT_NOTIFICATION_DESCRIPTION = (
    "در صورتی که بخواهید هنگام انتصاب به‌عنوان دزد دریایی افسانه‌ای مطلع شوید"
)
LEGENDARY_PIRATE_APPOINTMENT_NOTIFICATION_KEY = "انتصاب دزد دریایی افسانه‌ای"
LEGENDARY_PIRATE_REVOCATION_NOTIFICATION = (
    "عنوان دزد دریایی افسانه‌ای شما لغو شد\n\n*دلیل*: {}"
)
LEGENDARY_PIRATE_REVOCATION_NOTIFICATION_DESCRIPTION = (
    "در صورتی که بخواهید هنگام لغو عنوان دزد دریایی افسانه‌ای‌تان مطلع شوید"
)
LEGENDARY_PIRATE_REVOCATION_NOTIFICATION_KEY = "لغو دزد دریایی افسانه‌ای"
NOTIFICATION_CATEGORY_LEGENDARY_PIRATE = "دزد دریایی افسانه‌ای"

# Notification - Fight attack
FIGHT_ATTACK_NOTIFICATION = "شما {0} در نبردی در برابر {1}{2}\n\nمبلغ {3}: ฿*{4}*"
FIGHT_ATTACK_NOTIFICATION_DESCRIPTION = "در صورتی که بخواهید هنگام نبرد کردن بازیکن دیگری با شما مطلع شوید"
FIGHT_ATTACK_NOTIFICATION_KEY = "حمله نبرد"
FIGHT_ATTACK_CAN_REVENGE = (
    "\n\n>می‌توانید این نبرد را برای *{}* آینده از"
    " گزارش نبرد، بدون توجه به هرگونه زمان انتظار یا مصونیت حریف، انتقام بگیرید."
)
FIGHT_ATTACK_CANNOT_REVENGE = (
    "\n\n>از آنجا که این حمله در پاسخ به [نبرد]({}) قبلی شما بود، قابل انتقام‌گیری نیست"
)

# Notification - Plunder attack
PLUNDER_ATTACK_NOTIFICATION = ""
PLUNDER_ATTACK_NOTIFICATION_WON = (
    "شما {} را در حالی که سعی داشت شما را غارت کند شکست دادید"
    + Emoji.CONFETTI
    + "\n\nمبلغ برده‌شده \\(وام\\): ฿*{}*"
)
PLUNDER_ATTACK_NOTIFICATION_LOST = (
    "شما توسط {} غارت شدید" + Emoji.LOSER + "\n\nمبلغ از دست رفته: ฿*{}*"
)
PLUNDER_ATTACK_NOTIFICATION_DESCRIPTION = (
    "در صورتی که بخواهید هنگام غارت شدن توسط بازیکن دیگری مطلع شوید"
)
PLUNDER_ATTACK_NOTIFICATION_KEY = "حمله غارت"
PLUNDER_ATTACK_CAN_REVENGE = (
    "\n\n>می‌توانید این غارت را برای *{}* آینده از"
    " گزارش غارت، بدون توجه به هرگونه زمان انتظار یا مصونیت حریف، انتقام بگیرید."
)
PLUNDER_ATTACK_CANNOT_REVENGE = (
    "\n\n>از آنجا که این حمله در پاسخ به [غارت]({}) قبلی شما بود، قابل انتقام‌گیری نیست"
)

# Notification - Game Outcome
GAME_OUTCOME_NOTIFICATION = "{0}شما در چالش *{3}* در برابر {4}، ฿*{2}* {1}"
GAME_OUTCOME_NOTIFICATION_TIME_TERMINOLOGY = "{}\n\n{}"
GAME_OUTCOME_NOTIFICATION_DRAW = (
    "چالش *{}* در برابر {} با نتیجه مساوی به پایان رسید." "\nشرط شما \\(฿*{}*\\) بازگردانده شد"
)
GAME_OUTCOME_NOTIFICATION_DESCRIPTION = (
    "در صورتی که بخواهید از نتیجه یک بازی مطلع شوید \\(فقط جهانی\\)"
)
GAME_OUTCOME_NOTIFICATION_KEY = "نتیجه بازی"

# List
LIST_OVERVIEW = (
    "انتخاب کنید" + " {} *{}* را از لیست زیر\n{}"
)  # In the chunk to avoid IDE recognizing it as SQL
LIST_OVERVIEW_NO_ITEMS = "{} یافت نشد"
LIST_ITEM_TEXT = "\n*{}*. {}"
LIST_FOOTER = "\n\n_نمایش {}-{} از {} مورد_"
LEGEND = "راهنما"
LIST_EMOJI_LEGEND = "\n\n>*راهنما*{}"
LIST_EMOJI_LEGEND_ITEM = "\n>{} {} \\({}\\)"
LIST_FILTER_SEND_PART_OF_STRING = "\n\n>_بخشی از {} را ارسال کنید تا جستجو محدود شود_"
LIST_FILTER_ACTIVE_FILTERS = "\n\n_*فیلترهای فعال*:{}_"
LIST_FILTER_ITEM = "\n• {}"
LIST_FILTER_ITEM_CONTAINS = "{} شامل '{}' است"
LIST_FILTER_ONLY = "فقط *{}*"
NAVIGATION_LIMIT_REACHED = "به محدودیت رسیدید"

# Logs
LOG_ITEM_DETAIL_GENERIC_OUTCOME_TEXT = "{} *{}*"
LOG_ITEM_DETAIL_GENERIC_OUTCOME_TEXT_NO_BOLD = "{} {}"
LOG_ITEM_DETAIL_OUTCOME_TEXT = "{}شما *{}*"
LOG_ITEM_DETAIL_OUTCOME_BELLY_TEXT = "{}شما {} ฿*{}*"
LOG_ITEM_DETAIL_STATUS_TEXT = "*وضعیت*: {}"
LOG_ITEM_DETAIL_GO_TO_MESSAGE = (
    f"\n\n{Emoji.RIGHT_ARROW}[رفتن به پیام]("
    + "{}"
    + f"){Emoji.LEFT_ARROW}"
    + "\n_\\(ممکن است پیام دیگر در دسترس نباشد\\)_"
)
LOG_ITEM_DETAIL_NO_PERMISSION = "شما مجاز به مشاهده این مورد نیستید"
LOG_STATS_TEXT = "*آمار {}*\n\n{}"
LOG_STATS_NOT_ENOUGH_DATA = "داده کافی برای تولید آمار این گزارش وجود ندارد"

# Logs - Fight
FIGHT_LOG_KEY = "نبردها"
FIGHT_LOG_ITEM_DETAIL_TEXT_FILL_IN = "نبرد"
FIGHT_LOG_ITEM_TEXT = "{} در برابر {} \\(฿{}\\)"
FIGHT_LOG_ITEM_DETAIL_TEXT = "*{}*: {}\n*تاریخ*: {}\n*احتمال برد*: {}%\n\n{}{}"
FIGHT_LOG_STATS_TEXT = (
    "*مجموع نبردها*: {}\n*بردها*: {} \\({}%\\)\n*باخت‌ها*: {} \\({}%\\)\n*بلی برده‌شده*: ฿{}\n*بلی"
    " از دست رفته*: ฿{}\n*بیشترین بلی برده‌شده*: [฿{} \\({}\\)]({})\n*بیشترین بلی از دست رفته*: [฿{} \\({}\\)]({})\n*بیشترین"
    " کاربر نبردشده*: {} \\({}x\\)"
)
FIGHT_LOG_ITEM_DETAIL_TEXT_REVENGED = "\n\n>این نبرد [انتقام گرفته شده]({}) است"
FIGHT_LOG_ITEM_DETAIL_TEXT_IN_RESPONSE = (
    "\n\n>این نبرد در انتقام از یک [حمله]({}) قبلی بود"
)

# Logs . Plunder
PLUNDER_LOG_KEY = "غارت‌ها"
PLUNDER_LOG_ITEM_DETAIL_TEXT_FILL_IN = "غارت"
PLUNDER_LOG_ITEM_TEXT = "{} در برابر {} \\(฿{}\\)"
PLUNDER_LOG_ITEM_DETAIL_TEXT = "*{}*: {}\n*تاریخ*: {}\n*احتمال برد*: {}%\n\n{}{}"
PLUNDER_LOG_ITEM_DETAIL_SENTENCE_DURATION = "\n\n*محکومیت ایمپل دان*: {}"
PLUNDER_LOG_STATS_TEXT = (
    "*مجموع غارت‌ها*: {}"
    "\n*بردها*: {} \\({}%\\)"
    "\n*باخت‌ها*: {} \\({}%\\)"
    "\n*بلی دزدیده‌شده*: ฿{}"
    "\n*بلی از دست رفته*: ฿{}"
    "\n*بیشترین بلی دزدیده‌شده*: [฿{} \\({}\\)]({})"
    "\n*بیشترین بلی از دست رفته*: [฿{} \\({}\\)]({})"
    "\n*بیشترین محکومیت ایمپل دان*: [{}]({})"
    "\n*بیشترین کاربر غارت‌شده*: {} \\({}x\\)"
)
PLUNDER_LOG_ITEM_DETAIL_TEXT_REVENGED = "\n\n>این غارت [انتقام گرفته شده]({}) است"
PLUNDER_LOG_ITEM_DETAIL_TEXT_IN_RESPONSE = (
    "\n\n>این غارت در انتقام از یک [حمله]({}) قبلی بود"
)
PLUNDER_LOG_ITEM_DETAIL_TEXT_WON_LOAN = "شما ฿*{}* به دست آوردید \\(از طریق یک [وام]({}) بازپرداخت خواهد شد\\)"
PLUNDER_LOG_ITEM_DETAIL_TEXT_WON_IMMUNE = (
    "شما چیزی به دست نیاوردید \\(حریف در برابر از دست دادن جایزه مصون بود\\)"
)

# Logs - DocQ
DOC_Q_GAME_LOG_KEY = "داک کیو"
DOC_Q_GAME_LOG_ITEM_DETAIL_TEXT_FILL_IN = "بازی داک کیو"
DOC_Q_GAME_LOG_ITEM_TEXT = "{} ฿{}"
DOC_Q_GAME_LOG_ITEM_DETAIL_TEXT = "*تاریخ*: {}\n*سیب درست*: {}°\n\n{}{}"
DOC_Q_GAME_LOG_STATS_TEXT = (  # Logs - Game
    "*مجموع احضارها*: {}\n*بردها*: {} \\({}%\\)\n*باخت‌ها*: {} \\({}%\\)\n*بلی برده‌شده*: ฿{}\n*بلی"
    " از دست رفته*: ฿{}\n*بیشترین بلی برده‌شده*: [฿{}]({})\n*بیشترین بلی از دست رفته*: [฿{}]({})\n"
)

GAME_LOG_KEY = "چالش‌ها"
GAME_LOG_ITEM_DETAIL_TEXT_FILL_IN = "چالش"
GAME_LOG_ITEM_TEXT = "{} در برابر {} \\(฿{}\\)"
GAME_LOG_ITEM_DETAIL_TEXT = "*{}*: {}\n*بازی*: {}\n*تاریخ*: {}\n*شرط*: ฿{}\n\n{}{}"
GAME_LOG_STATS_TEXT = (
    "*مجموع چالش‌ها*: {}\n*بردها*: {} \\({}%\\)\n*باخت‌ها*: {} \\({}%\\)\n*مساوی‌ها*: {}"
    " \\({}%\\)\n*بلی برده‌شده*: ฿{}\n*بلی از دست رفته*: ฿{}\n*بیشترین بلی برده‌شده*: [฿{} \\({}\\)]({})\n*بیشترین"
    " بلی از دست رفته*: [฿{} \\({}\\)]({})\n*بیشترین کاربر به‌چالش‌کشیده‌شده*: {} \\({}x\\)\n*بیشترین بازی انجام‌شده*:"
    " {} \\({}x\\)"
)
# Logs - Bounty Gift
BOUNTY_GIFT_LOG_KEY = "هدیه‌های جایزه"
BOUNTY_GIFT_LOG_ITEM_DETAIL_TEXT_FILL_IN = "هدیه جایزه"
BOUNTY_GIFT_LOG_ITEM_TEXT = "{} ฿{} {} {}"
BOUNTY_GIFT_LOG_ITEM_DETAIL_TAX_TEXT = "\n*مالیات*: ฿{} \\({}%\\)\n*مجموع*: ฿{}"
BOUNTY_GIFT_LOG_ITEM_DETAIL_TEXT = (
    f"*{{}}*: {{}}\n*تاریخ*: {{}}\n*مبلغ*: ฿{{}}{{}}{LOG_ITEM_DETAIL_GO_TO_MESSAGE}"
)
BOUNTY_GIFT_LOG_STATS_TEXT = (
    "*مجموع هدیه‌ها*: {}\n*مجموع اهدا شده*: ฿{}\n*مجموع دریافت‌شده*: ฿{}\n*بیشترین مقدار اهدایی*: [฿{}"
    " \\({}\\)]({})\n*بیشترین مقدار دریافتی*: [฿{} \\({}\\)]({})\n*بیشترین دریافت‌کننده*: {} \\(฿{}\\)\n*بیشترین"
    " اهداکننده*: {} \\(฿{}\\)"
)
BOUNTY_GIFT_LOG_LEGEND_SENT = "ارسال‌شده"
BOUNTY_GIFT_LOG_LEGEND_RECEIVED = "دریافت‌شده"

# Logs - Legendary Pirate
LEGENDARY_PIRATE_LOG_KEY = "دزدان دریایی افسانه‌ای"
LEGENDARY_PIRATE_LOG_ITEM_DETAIL_TEXT_FILL_IN = "دزد دریایی افسانه‌ای"
LEGENDARY_PIRATE_LOG_ITEM_TEXT = "{}"
LEGENDARY_PIRATE_LOG_ITEM_DETAIL_TEXT = "*{}*\nلقب: {}\n\n*دلیل*: {}"

# Logs - Warlord
WARLORD_LOG_KEY = "جنگ‌سالاران"
WARLORD_LOG_ITEM_DETAIL_TEXT_FILL_IN = "جنگ‌سالار"
WARLORD_LOG_ITEM_TEXT = "{}"
WARLORD_LOG_ITEM_DETAIL_TEXT = "*{}*\nلقب: {}\n\n*دلیل*: {}"

# Logs - New World Pirate
NEW_WORLD_PIRATE_LOG_KEY = "دزدان دریایی دنیای جدید"
NEW_WORLD_PIRATE_LOG_ITEM_DETAIL_TEXT_FILL_IN = "دزد دریایی دنیای جدید"
NEW_WORLD_PIRATE_LOG_ITEM_TEXT = "{} \\(฿{}\\)"
NEW_WORLD_PIRATE_LOG_ITEM_DETAIL_CREW_TEXT = "\n*خدمه*: {}"
NEW_WORLD_PIRATE_LOG_ITEM_DETAIL_TEXT = "*{}*\n\n*جایزه*: ฿{}\n*موقعیت*: {}{}"

# Logs - Leaderboard Rank
LEADERBOARD_RANK_LOG_KEY = "رتبه‌های جدول امتیازات جهانی"
LEADERBOARD_RANK_LOG_ITEM_DETAIL_TEXT_FILL_IN = "رتبه جدول امتیازات جهانی"
LEADERBOARD_RANK_LOG_ITEM_TEXT = "هفته {} از {} - {}"
LEADERBOARD_RANK_LOG_ITEM_DETAIL_TEXT = (
    "*هفته {} از {}*\n\n*جایگاه*: {}°\n*رتبه*: {}\n*جایزه*: ฿{}"
)
LEADERBOARD_RANK_LOG_STATS_TEXT = (
    "*مجموع حضورها*: {}\n*حضور به‌عنوان پادشاه دزدان دریایی*: {} \\({}%\\)\n*حضور به‌عنوان"
    " امپراتور*: {} \\({}%\\)\n*حضور به‌عنوان معاون اول*: {} \\({}%\\)\n*حضور به‌عنوان"
    " سوپرنوا*: {} \\({}%\\)\n*حضور به‌عنوان جنگ‌سالار*: {} \\({}%\\)\n*بالاترین رتبه*: [{}"
    " \\({}°\\)]({})\n*بیشترین جایزه*: [฿{} \\({}°\\)]({})"
)

# Logs - Income tax event
INCOME_TAX_EVENT_LOG_KEY = "جزئیات مالیات"
INCOME_TAX_EVENT_LOG_ITEM_DETAIL_TEXT_FILL_IN = "جزئیات مالیات بر درآمد"
INCOME_TAX_EVENT_LOG_ITEM_TEXT = "{} \\(฿{}\\)"
INCOME_TAX_EVENT_LOG_ITEM_DETAIL_TEXT = (
    "*رویداد*: [{}]({})\n*تاریخ*: {}\n*درآمد*: ฿{}\n*سود خالص*: "
    + Emoji.LOG_POSITIVE
    + "฿{}\n*مجموع مالیات*: "
    + Emoji.LOG_NEGATIVE
    + "฿{} \\({}%\\){}{}\n\n\n*جزئیات*{}"
)
INCOME_TAX_EVENT_LOG_ITEM_DETAIL_TEXT_DEDUCTION = "\n\n*کسورات*"
INCOME_TAX_EVENT_LOG_ITEM_DETAIL_TEXT_DEDUCTION_ITEM = "\n{}: {}%"
INCOME_TAX_EVENT_LOG_ITEM_DETAIL_TEXT_CONTRIBUTION = "\n\n*مشارکت‌ها* \\(از مالیات\\)"
INCOME_TAX_EVENT_LOG_ITEM_DETAIL_TEXT_CONTRIBUTION_ITEM = "\n{}: ฿{} \\({}%\\)"

INCOME_TAX_EVENT_LOG_ITEM_DETAIL_TEXT_BREAKDOWN_ITEM = (
    "\n\nمبلغ: ฿{}\nسود: ฿{}\nمالیات: ฿{} \\({}%\\)"
)

SILENCE_ACTIVE = (
    "یک میدان عایق صدا فعال شده است، فقط کسانی که اجازه دارند می‌توانند صحبت کنند."
    f"\nاز {CommandName.SILENCE_END.get_formatted()} برای اجازه دادن دوباره به همه برای صحبت کردن استفاده کنید."
)
SILENCE_END = "میدان عایق صدا لغو شد، همه می‌توانند دوباره صحبت کنند"
SILENCE_NOT_ACTIVE = "میدان عایق صدا فعال نیست"
SPEAK = "به {} اجازه صحبت کردن داده شد"

# Devil Fruit
DEVIL_FRUIT_CATEGORY_DESCRIPTION_ZOAN = "زوآن"
DEVIL_FRUIT_CATEGORY_DESCRIPTION_ANCIENT_ZOAN = "زوآن باستانی"
DEVIL_FRUIT_CATEGORY_DESCRIPTION_MYTHICAL_ZOAN = "زوآن اساطیری"
DEVIL_FRUIT_CATEGORY_DESCRIPTION_SMILE = "اسمایل"
DEVIL_FRUIT_STATUS_DESCRIPTION_NEW = "جدید"
DEVIL_FRUIT_STATUS_DESCRIPTION_COMPLETED = "تکمیل‌شده"
DEVIL_FRUIT_STATUS_DESCRIPTION_ENABLED = "فعال"
DEVIL_FRUIT_STATUS_DESCRIPTION_SCHEDULED = "زمان‌بندی‌شده"
DEVIL_FRUIT_STATUS_DESCRIPTION_RELEASED = "منتشرشده"
DEVIL_FRUIT_STATUS_DESCRIPTION_COLLECTED = "جمع‌آوری‌شده"
DEVIL_FRUIT_STATUS_DESCRIPTION_EATEN = "خورده‌شده"
DEVIL_FRUIT_ABILITY_TEXT = "\n\n*توانایی‌ها*"
DEVIL_FRUIT_ABILITY_TEXT_LINE = "\n{}{} \\({}{}%\\)"
DEVIL_FRUIT_ABILITY_UNKNOWN = "\nناشناخته"
DEVIL_FRUIT_ABILITY_DEFECTIVE_SMILE = f"\n{Emoji.LOG_NEGATIVE}اسمایل معیوب، هیچ توانایی‌ای اعطا نشد"
# Devil Fruit - Private Chat
DEVIL_FRUIT_ITEM_TEXT = "{}"
DEVIL_FRUIT_ITEM_TEXT_FILL_IN = "میوه شیطانی"
DEVIL_FRUIT_ITEM_DETAIL_TEXT = "*{}*\nدسته: {}{}{}{}"
DEVIL_FRUIT_EXPIRATION_EXPLANATION = (
    "\n>اگر میوه شیطانی قبل از انقضا خورده نشود لغو خواهد شد"
)
DEVIL_FRUIT_SMILE_EXPIRATION_EXPLANATION = (
    f"\n>اسمایل‌ها {Env.DEVIL_FRUIT_SMILE_DEFECTIVE_PERCENTAGE.get_int()}% احتمال دارد"
    " معیوب باشند \\(بدون توانایی اعطایی\\) و مدت توانایی‌های آن‌ها به‌طور تصادفی هنگام خورده شدن"
    f" تعیین می‌شود، حداکثر {Env.DEVIL_FRUIT_SMILE_MAX_DAYS.get()} روز"
)
DEVIL_FRUIT_ITEM_DETAIL_TEXT_EXPIRING_DATE = "\n\nانقضا: {}"
DEVIL_FRUIT_ITEM_DETAIL_TEXT_SELL_COMMAND = (
    "\n\nمی‌توانید این میوه شیطانی را در فروشگاه یا یک گروه چت بفروشید"
    f"\\(دستور {CommandName.DEVIL_FRUIT_SELL.get_formatted()} <price\\>\\)"
)
DEVIL_FRUIT_LIST_NO_ITEMS = "شما هیچ میوه شیطانی‌ای ندارید"
DEVIL_FRUIT_NOT_OWNER = "شما مالک این میوه شیطانی نیستید"
DEVIL_FRUIT_EAT_USER_ALREADY_ATE = "شما قبلاً یک میوه شیطانی خورده‌اید"
DEVIL_FRUIT_EAT_CONFIRMATION_REQUEST = (
    "آیا مطمئنید که می‌خواهید {} را بخورید؟{}\n\nتا زمانی که آن را دور نیندازید نمی‌توانید"
    " میوه شیطانی دیگری بخورید"
)
DEVIL_FRUIT_EAT_CONFIRMATION_REQUEST_ABILITIES = "\nشما توانایی‌های زیر را کسب خواهید کرد:\n{}"
DEVIL_FRUIT_EAT_CONFIRMATION_CONFIRMED = (
    "شما {} را خوردید و توانایی‌های زیر را کسب کردید:\n{}"
)
DEVIL_FRUIT_DISCARD_DEFECTIVE_SMILE = "نمی‌توانید یک اسمایل معیوب را دور بیندازید، تا انقضای آن صبر کنید"
DEVIL_FRUIT_DISCARD_CONFIRMATION_REQUEST = (
    "آیا مطمئنید که می‌خواهید {} را دور بیندازید؟\n\nآن را از دست خواهید داد و می‌توانید با پیدا کردن یا"
    " معامله دوباره آن را به دست آورید"
)
DEVIL_FRUIT_DISCARD_CONFIRMATION_CONFIRMED = "شما {} را دور انداختید"
DEVIL_FRUIT_RELEASE_MESSAGE_INFO = (
    "تبریک می‌گویم {}، شما یک میوه شیطانی پیدا کردید!\n\nنام: *{}*\nدسته: {}{}"
    + DEVIL_FRUIT_EXPIRATION_EXPLANATION
    + DEVIL_FRUIT_EAT_OR_SELL
)

DEVIL_FRUIT_SELL_NO_AMOUNT = (
    "باید مبلغ بلی‌ای که می‌خواهید میوه شیطانی را بفروشید مشخص کنید\n\nمثال:"
    f" {CommandName.DEVIL_FRUIT_SELL.get_formatted()} 10.000.000"
)
DEVIL_FRUIT_SELL_NO_FRUITS = (
    "شما هیچ میوه شیطانی‌ای برای فروش ندارید \\(فقط میوه‌های شیطانی جمع‌آوری‌شده و خورده‌نشده"
    " قابل فروش هستند\\)"
)
DEVIL_FRUIT_SELL_SELECT_FRUIT = (
    "میوه شیطانی‌ای که می‌خواهید بفروشید را انتخاب کنید\n\n>وقتی این دستور در پاسخ به یک"
    " کاربر استفاده شود، فقط او امکان خرید میوه شیطانی را خواهد داشت"
    f"\n\n{Emoji.WARNING}میوه"
    " شیطانی در فروشگاه جهانی برای فروش لیست نخواهد شد."
    "\nاگر می‌خواهید همه بازیکنان آن را ببینند، آن را از اینجا برای فروش بگذارید:"
    f"\n`{CommandName.START.get_non_formatted()}-\\>{PVT_KEY_DEVIL_FRUIT}-\\>انتخاب"
    f"-\\>{PVT_KEY_DEVIL_FRUIT_DETAIL_SELL}`"
)
DEVIL_FRUIT_SELL_NO_LONGER_OWN = "{} دیگر مالک این میوه شیطانی نیست"
DEVIL_FRUIT_SELL_NO_LONGER_SELLABLE = "این میوه شیطانی دیگر قابل فروش نیست"
DEVIL_FRUIT_SELL_BUY = "{} میوه شیطانی زیر را برای فروش گذاشته است:\n\n{}\n\n*قیمت*: ฿{}{}"
DEVIL_FRUIT_SELL_BUY_ONLY_BY_USER_ADDENDUM = "\n\n_فقط {} می‌تواند این میوه شیطانی را بخرد_"
DEVIL_FRUIT_SELL_BUY_NOT_ENOUGH_BELLY = "شما بلی کافی برای خرید این میوه شیطانی ندارید"
DEVIL_FRUIT_SELL_BUY_CANNOT_BUY_OWN = "شما نمی‌توانید میوه شیطانی خودتان را بخرید"
DEVIL_FRUIT_SELL_BUY_SUCCESS = (
    "{} میوه شیطانی زیر را از {} خریداری کردید\n\n{}\n\n*قیمت*: ฿{}"
)
DEVIL_FRUIT_DETAIL_SELL = "لطفاً مبلغی که می‌خواهید میوه شیطانی را بفروشید ارسال کنید"
DEVIL_FRUIT_DETAIL_SELL_AVERAGE_PRICE = ".\n\nمیانگین قیمت فروش: ฿{}"
DEVIL_FRUIT_DETAIL_SELL_CONFIRMATION_REQUEST = (
    "آیا مطمئنید که می‌خواهید *{}* را با قیمت ฿{} برای فروش بگذارید؟\n\nهنگامی که "
    "کسی آن را بخرد به شما اطلاع داده خواهد شد"
)
DEVIL_FRUIT_DETAIL_SELL_CONFIRMATION_CONFIRMED = (
    "این میوه شیطانی اکنون برای خرید توسط سایر کاربران در فروشگاه در دسترس است."
    "\n\n*نام*: {}"
    "\n*قیمت*: ฿{}"
    f"\n\nبرای بازبینی یا لغو `{PVT_KEY_DEVIL_FRUIT_VIEW_IN_SHOP}` را کلیک کنید"
)
DEVIL_FRUIT_DETAIL_SELL_ALREADY_FOR_SALE = (
    "این میوه شیطانی از قبل در فروشگاه برای فروش گذاشته شده است، لطفاً ابتدا آن را حذف کنید"
)
# Devil Fruit Shop
DEVIL_FRUIT_SHOP_ITEM_TEXT = "{}\nقیمت: ฿{}"
DEVIL_FRUIT_SHOP_ITEM_TEXT_FILL_IN = "میوه شیطانی"
DEVIL_FRUIT_SHOP_ITEM_DETAIL_TEXT = "{}\n\n*فروشنده*: {}\n*قیمت*: ฿{}"
DEVIL_FRUIT_SHOP_LIST_NO_ITEMS = (
    "در حال حاضر هیچ *میوه شیطانی*‌ای برای فروش وجود ندارد، لطفاً بعداً دوباره سر بزنید.\n\nهر"
    " میوه شیطانی برای فروش را در پیام جایزه روزانه خود، با استفاده از دستور"
    f" {CommandName.DAILY_REWARD.get_formatted()} در یک گروه چت، خواهید دید."
)
DEVIL_FRUIT_SHOP_ITEM_DETAIL_REMOVE_CONFIRMATION = (
    "آیا مطمئنید که می‌خواهید این میوه شیطانی را از فروشگاه حذف کنید؟\nمی‌توانید دوباره آن را"
    " برای فروش بگذارید."
)
DEVIL_FRUIT_SHOP_ITEM_DETAIL_REMOVE_SUCCESS = "میوه شیطانی از فروشگاه حذف شد"
DEVIL_FRUIT_SHOP_ITEM_DETAIL_BUY_CONFIRMATION_REVOKE = (
    "\n\n>اگر آن را ظرف {} نخورید، لغو خواهد شد"
)
DEVIL_FRUIT_SHOP_ITEM_DETAIL_BUY_CONFIRMATION = (
    "آیا مطمئنید که می‌خواهید میوه شیطانی زیر را بخرید؟\n\n*نام*: {}\n*قیمت*: ฿{}"
    + DEVIL_FRUIT_SHOP_ITEM_DETAIL_BUY_CONFIRMATION_REVOKE
)

# Admin chat error messages
NO_DEVIL_FRUIT_TO_SCHEDULE = "هیچ میوه شیطانی {} برای زمان‌بندی انتشار وجود ندارد"

THANKS_FOR_ADDING_TO_GROUP = "ممنون که من را به گروهتان اضافه کردید!\n" + JOIN_SUPPORT_GROUP + "\n\n"

INCOME_TAX_EVENT_BOUNTY_LOAN = "وام جایزه"
INCOME_TAX_EVENT_DEVIL_FRUIT_SELL = "فروش میوه شیطانی"
INCOME_TAX_EVENT_PREDICTION = "پیش‌بینی"

INCOME_TAX_DEDUCTION_TYPE_ADMIN = "ادمین"
INCOME_TAX_DEDUCTION_TYPE_CREW_ABILITY = "توانایی خدمه"
INCOME_TAX_DEDUCTION_TYPE_DEVIL_FRUIT = "میوه شیطانی"
INCOME_TAX_DEDUCTION_TYPE_LEGENDARY_PIRATE = "دزد دریایی افسانه‌ای"

INCOME_TAX_CONTRIBUTION_TYPE_CREW_CHEST = "صندوق خدمه"

FEATURE_BOUNTY_GIFT = "هدیه جایزه"
FEATURE_CHALLENGE = "چالش"
FEATURE_CREW = "خدمه"
FEATURE_DEVIL_FRUIT_APPEARANCE = "ظهور میوه شیطانی"
FEATURE_DOC_Q = "داک کیو"
FEATURE_FIGHT = "نبرد"
FEATURE_LEADERBOARD = "جدول امتیازات"
FEATURE_MESSAGE_FILTER = "فیلتر پیام"
FEATURE_PREDICTION = "پیش‌بینی"
FEATURE_SILENCE = "سکوت"
FEATURE_STATUS = "وضعیت"
FEATURE_DEVIL_FRUIT_SELL = "فروش میوه شیطانی"
FEATURE_BOUNTY_LOAN = "وام جایزه"
FEATURE_PLUNDER = "غارت"
FEATURE_DAILY_REWARD = "جایزه روزانه"

# Ability
ABILITY_TYPE_DOC_Q_COOLDOWN_DURATION = "زمان انتظار داک کیو"
ABILITY_TYPE_GAME_COOLDOWN_DURATION = "زمان انتظار چالش"
ABILITY_TYPE_FIGHT_COOLDOWN_DURATION = "زمان انتظار نبرد"
ABILITY_TYPE_FIGHT_IMMUNITY_DURATION = "مصونیت نبرد"
ABILITY_TYPE_FIGHT_DEFENSE_BOOST = "تقویت دفاع نبرد"
ABILITY_TYPE_PREDICTION_WAGER_REFUND = "حداکثر بازگشت وجه شرط پیش‌بینی"
ABILITY_TYPE_GIFT_LOAN_TAX = "مالیات هدیه و وام"
ABILITY_TYPE_INCOME_TAX = "مالیات بر درآمد"
ABILITY_TYPE_PLUNDER_COOLDOWN_DURATION = "زمان انتظار غارت"
ABILITY_TYPE_PLUNDER_IMMUNITY_DURATION = "مصونیت غارت"
ABILITY_TYPE_PLUNDER_SENTENCE_DURATION = "مدت محکومیت غارت"
ABILITY_TYPE_FIGHT_SCOUT_FEE = "هزینه شناسایی نبرد"
ABILITY_TYPE_PLUNDER_SCOUT_FEE = "هزینه شناسایی غارت"
ABILITY_TYPE_GAME_GLOBAL_ACCEPT_COOLDOWN_DURATION = "زمان انتظار پذیرش چالش جهانی"

PLUNDER_CANNOT_PLUNDER_USER = "شما نمی‌توانید این کاربر را غارت کنید"
PLUNDER_USER_IN_COOLDOWN = "زمان انتظار غارت فعال است. می‌توانید دوباره در *{}* غارت کنید"
PLUNDER_CONFIRMATION_REQUEST = (
    "{} آیا مطمئنید که می‌خواهید از {} بدزدید؟\n"
    "\nاگر موفق شوید، ฿*{}* به دست خواهید آورد."
    "\nاگر دستگیر شوید، ฿*{}* بدهکار خواهید شد و به مدت *{}* در ایمپل دان زندانی خواهید شد!"
    + "\n\nاحتمال موفقیت: *{}%*\nجایزه فعلی: ฿*{}*\nجایزه نهایی در صورت برد:"
    " ฿*{}*\n\nاگر"
    " ببازید، وامی برای پرداخت جریمه ایجاد خواهد شد"
)
PLUNDER_WIN = (
    "{} با موفقیت {} را غارت کردید، بهتر است قبل از اینکه متوجه شود فرار کنید!\n\n" + GAME_WIN_STATUS
)
PLUNDER_LOSE = (
    "{} هنگام تلاش برای غارت {} دستگیر شدید و شما را به نیروی دریایی تحویل داده‌اند."
    "\nشما به مدت *{}* در ایمپل دان زندانی خواهید شد، دفعه بعد شانس بهتری داشته باشید!"
    + IMPEL_DOWN_RESTRICTION_BAIL_GUIDE
    + "\n\nشما اکنون یک [وام ฿*{}*]({}) نزد {} دارید"
)
PLUNDER_LOSE_IMMUNE = (
    "{} هنگام تلاش برای غارت {} دستگیر شدید، اما وضعیت دزد دریایی افسانه‌ای شما را از"
    " هرگونه جریمه محافظت کرد."
)
PLUNDER_LOSE_SENTENCE_REASON = "غارت ناموفق در برابر {}"
PLUNDER_REVENGE_TOO_LATE = (
    "فقط در صورتی می‌توانید انتقام یک غارت را بگیرید که کمتر از {} از زمان حمله گذشته باشد.\n\nزمان"
    " سپری‌شده: {}"
)
PLUNDER_REVENGE_ALREADY_REVENGED = "این غارت قبلاً انتقام گرفته شده است\n\n[مشاهده انتقام]({})"

DAILY_REWARD_ALREADY_COLLECTED = "جایزه بعدی شما در *{}* در دسترس خواهد بود{}"
DAILY_REWARD = (
    f"{Emoji.LOG_POSITIVE}جایزه: ฿*{{}}*" f"\n\n>*جزئیات*" f"\n>جایزه پایه: ฿*{{}}*{{}}"
)
DAILY_REWARD_GROUP_MESSAGE = (
    "خوش برگشتی {}، این هم جایزه روزانه امروزت!\n\n{}"
    "\n>\n>*پشتکار*"
    "\n>پشتکار فعلی: *{} {}*"
    "\n>جایزه بعدی در: *{} {}*"
    f"\n>_به ازای هر {Env.DAILY_REWARD_STREAK_DAYS.get_int()} روز متوالی که جایزه روزانه را دریافت کنید،"
    " یک جایزه ویژه دریافت خواهید کرد!_"
)
DAILY_REWARD_BONUS = "\n>\n>• {}: *+{}%* \\(฿{}\\)\n>_{}_"
DAILY_REWARD_BONUS_LIMITATION_LOCATION_PARADISE = (
    "\n>هیچ جایزه اضافه‌ای به دلیل بودن در پارادایس در حالی که جایزه کافی برای دنیای جدید"
    " دارید \\(฿{}\\) در دسترس نیست"
)
DAILY_REWARD_BONUS_LIMITATION_LOCATION_NEW_WORLD = (
    "\n>هیچ جایزه اضافه‌ای به دلیل داشتن بیش از ฿{} و بودن در آخرین موقعیت دنیای جدید در دسترس نیست"
)
DAILY_REWARD_BONUS_LIMITATION_ARRESTED = "\n>هیچ جایزه اضافه‌ای به دلیل بازداشت بودن در دسترس نیست"
DAILY_REWARD_NEXT = "\n>\n>جایزه بعدی در *{}* در دسترس خواهد بود||"
DAILY_REWARD_NEXT_SPLIT = (
    "\n>\n>جایزه روزانه به {} بخش تقسیم شده است، جایزه بعدی در *{}* در دسترس خواهد بود||"
)
DAILY_REWARD_BONUS_DESCRIPTION_STREAK = "پشتکار"
DAILY_REWARD_BONUS_DESCRIPTION_STREAK_EXPLANATION = (
    f"+{Env.DAILY_REWARD_BONUS_BASE_STREAK.get_int()}% به ازای هر روز متوالی که جایزه را دریافت"
    " می‌کنید \\({}\\)"
)
DAILY_REWARD_BONUS_DESCRIPTION_LOCATION = "موقعیت"
DAILY_REWARD_BONUS_DESCRIPTION_LOCATION_EXPLANATION = (
    f"+{Env.DAILY_REWARD_BONUS_BASE_LOCATION.get_int()}% \\* سطح موقعیت فعلی \\({{}}\\)"
)
DAILY_REWARD_BONUS_DESCRIPTION_CREW_LEVEL = "سطح خدمه"
DAILY_REWARD_BONUS_DESCRIPTION_CREW_LEVEL_EXPLANATION = (
    f"+{Env.DAILY_REWARD_BONUS_BASE_CREW_LEVEL.get_int()}% \\* سطح خدمه \\({{}}\\)"
)
DAILY_REWARD_BONUS_DESCRIPTION_CREW_MVP = "برترین بازیکن خدمه"
DAILY_REWARD_BONUS_DESCRIPTION_CREW_MVP_EXPLANATION = (
    "اگر جایزه شما بیشتر از میانگین جایزه خدمه‌تان باشد"
)

DAILY_REWARD_DEVIL_FRUIT_SHOP = "\n\n>*فروشگاه میوه شیطانی*{}||"
DAILY_REWARD_DEVIL_FRUIT_SHOP_ITEM = "\n>•[{} - ฿{}]({})"
DAILY_REWARD_GLOBAL_CHALLENGE = "\n\n>*چالش‌های جهانی*{}||"
GLOBAL_CHALLENGE_ITEM = "\n>{}"
DAILY_REWARD_PRIZE_REQUEST = (
    "{}\nمی‌توانید جایزه پیشنهادی را بپذیرید یا"
    " شانس خود را برای جایزه بهتر امتحان کنید.\n\nجایزه پیشنهادی: ฿*{}*\n\nدر صورتی که شانس"
    " خود را امتحان کنید، ممکن است به دست آورید:\n• بلی تصادفی بین ฿*{}* و"
    f" ฿*{{}}* \\({Env.DAILY_REWARD_PRIZE_BELLY_PERCENTAGE.get_int()}% احتمال\\)\n• یک میوه شیطانی"
    f" اسمایل \\({Env.DAILY_REWARD_PRIZE_SMILE_PERCENTAGE.get_int()}% احتمال\\)"
)
DAILY_REWARD_PRIZE_REQUEST_FROM_STREAK = (
    "تبریک می‌گویم {} بابت حفظ پشتکار خود در"
    f" {Env.DAILY_REWARD_STREAK_DAYS.get_int()} روز گذشته!"
)
DAILY_REWARD_PRIZE_REQUEST_FIRST_TIME = "تبریک می‌گویم {} بابت دریافت اولین جایزه‌تان!"
DAILY_REWARD_PRIZE_CONFIRM = (
    Emoji.CONFETTI
    + "تبریک می‌گویم {}، شما جایزه زیر را به دست آوردید:\n\n{}\n\n\n_پشتکار"
    f" خود را برای {Env.DAILY_REWARD_STREAK_DAYS.get_int()} روز آینده حفظ کنید تا جایزه"
    " دیگری دریافت کنید!_"
)
DAILY_REWARD_PRIZE_CONFIRM_BELLY = "مقدار بلی: ฿*{}*"

AUTO_DELETE_SET = (
    "پیام‌های ربات پس از چند دقیقه باید از چت حذف شوند؟"
    "\n\nتنظیم فعلی: *{}*"
)

# Owner broadcast - gcast/pcast
BROADCAST_REPLY_REQUIRED = "لطفاً به پیامی که می‌خواهید همگانی ارسال کنید پاسخ دهید."
BROADCAST_GROUPS_PROGRESS = f"{Emoji.HOURGLASS}در حال ارسال پیام به همه گروه‌ها..."
BROADCAST_PLAYERS_PROGRESS = f"{Emoji.HOURGLASS}در حال ارسال پیام به همه بازیکنان..."
BROADCAST_GROUPS_STATISTICS = (
    "*مجموع گروه‌ها*: {}\n*موفق*: {}\n*ناموفق*: {}"
)
BROADCAST_PLAYERS_STATISTICS = (
    "*مجموع بازیکنان*: {}\n*موفق*: {}\n*ناموفق*: {}"
)
BROADCAST_PIN_STATISTICS = "\n\n*آمار سنجاق کردن*\n\n*با موفقیت سنجاق شد*: {}\n*سنجاق ناموفق*: {}"
BROADCAST_GROUPS_COMPLETED = (
    f"{Emoji.ACCEPT}ارسال همگانی به گروه‌ها تکمیل شد.\n\n*آمار ارسال همگانی*\n\n{{}}{{}}"
)
BROADCAST_PLAYERS_COMPLETED = (
    f"{Emoji.ACCEPT}ارسال همگانی به بازیکنان تکمیل شد.\n\n*آمار ارسال همگانی*\n\n{{}}{{}}"
)
