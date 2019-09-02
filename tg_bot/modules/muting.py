import html
from typing import Optional, List

from telegram import Message, Chat, Update, Bot, User
from telegram.error import BadRequest
from telegram.ext import CommandHandler, Filters
from telegram.ext.dispatcher import run_async
from telegram.utils.helpers import mention_html

from tg_bot import dispatcher, LOGGER
from tg_bot.modules.helper_funcs.chat_status import bot_admin, user_admin, is_user_admin, can_restrict
from tg_bot.modules.helper_funcs.extraction import extract_user, extract_user_and_text
from tg_bot.modules.helper_funcs.string_handling import extract_time
from tg_bot.modules.log_channel import loggable


@run_async
@bot_admin
@user_admin
@loggable
def mute(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text("ഒന്നുകിൽ നിശബ്ദമാക്കുന്നതിന് നിങ്ങൾ എനിക്ക് ഒരാളെം നൽകേണ്ടതുണ്ട്, അല്ലെങ്കിൽ നിശബ്ദമാക്കാൻ ആർക്കെങ്കിലും മറുപടി നൽകണം..")
        return ""

    if user_id == bot.id:
        message.reply_text("I'm not muting myself!")
        return ""

    member = chat.get_member(int(user_id))

    if member:
        if is_user_admin(chat, user_id, member=member):
            message.reply_text("Afraid I can't stop an admin from talking!")

        elif member.can_send_messages is None or member.can_send_messages:
            bot.restrict_chat_member(chat.id, user_id, can_send_messages=False)
            message.reply_text("👍🏻 ലവന്റെ വായടച്ചിട്ടുണ്ട്! 🤐")
            return "<b>{}:</b>" \
                   "\n#MUTE" \
                   "\n<b>Admin:</b> {}" \
                   "\n<b>User:</b> {}".format(html.escape(chat.title),
                                              mention_html(user.id, user.first_name),
                                              mention_html(member.user.id, member.user.first_name))

        else:
            message.reply_text("മിണ്ടാതിരിക്കടേ :rage:!")
    else:
        message.reply_text("അളിയാ അയാൾ ഇവിടെ ഇല്ല:cry:")

    return ""


@run_async
@bot_admin
@user_admin
@loggable
def unmute(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text("ഒന്നുകിൽ നിങ്ങൾ ശബ്‌ദമുള്ളതാക്കാൻ എനിക്ക് ഒരു ഉപയോക്തൃനാമം നൽകേണ്ടതുണ്ട്, അല്ലെങ്കിൽ നിശബ്ദമാക്കുന്നതിന് മറ്റൊരാൾക്ക് മറുപടി നൽകണം..")
        return ""

    member = chat.get_member(int(user_id))

    if member.status != 'kicked' and member.status != 'left':
        if member.can_send_messages and member.can_send_media_messages \
                and member.can_send_other_messages and member.can_add_web_page_previews:
            message.reply_text("ഇനി അയാൾക്ക് വാ തുറക്കാം :+1:.")
        else:
            bot.restrict_chat_member(chat.id, int(user_id),
                                     can_send_messages=True,
                                     can_send_media_messages=True,
                                     can_send_other_messages=True,
                                     can_add_web_page_previews=True)
            message.reply_text("Unmuted!")
            return "<b>{}:</b>" \
                   "\n#UNMUTE" \
                   "\n<b>Admin:</b> {}" \
                   "\n<b>User:</b> {}".format(html.escape(chat.title),
                                              mention_html(user.id, user.first_name),
                                              mention_html(member.user.id, member.user.first_name))
    else:
        message.reply_text("This user isn't even in the chat, unmuting them won't make them talk more than they "
                           "already do!")

    return ""


@run_async
@bot_admin
@can_restrict
@user_admin
@loggable
def temp_mute(bot: Bot, update: Update, args: List[str]) -> str:
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    message = update.effective_message  # type: Optional[Message]

    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("You don't seem to be referring to a user.")
        return ""

    try:
        member = chat.get_member(user_id)
    except BadRequest as excp:
        if excp.message == "User not found":
            message.reply_text("I can't seem to find this user")
            return ""
        else:
            raise

    if is_user_admin(chat, user_id, member):
        message.reply_text("I really wish I could mute admins...")
        return ""

    if user_id == bot.id:
        message.reply_text("I'm not gonna MUTE myself, are you crazy?")
        return ""

    if not reason:
        message.reply_text("You haven't specified a time to mute this user for!")
        return ""

    split_reason = reason.split(None, 1)

    time_val = split_reason[0].lower()
    if len(split_reason) > 1:
        reason = split_reason[1]
    else:
        reason = ""

    mutetime = extract_time(message, time_val)

    if not mutetime:
        return ""

    log = "<b>{}:</b>" \
          "\n#TEMP MUTED" \
          "\n<b>Admin:</b> {}" \
          "\n<b>User:</b> {}" \
          "\n<b>Time:</b> {}".format(html.escape(chat.title), mention_html(user.id, user.first_name),
                                     mention_html(member.user.id, member.user.first_name), time_val)
    if reason:
        log += "\n<b>Reason:</b> {}".format(reason)

    try:
        if member.can_send_messages is None or member.can_send_messages:
            bot.restrict_chat_member(chat.id, user_id, until_date=mutetime, can_send_messages=False)
            message.reply_text("കുറച്ചുനേരം മിണ്ടാതിരിക്ക്! 😠 Muted for {}!".format(time_val))
            return log
        else:
            message.reply_text("This user is already muted.")

    except BadRequest as excp:
        if excp.message == "Reply message not found":
            # Do not reply
            message.reply_text("കുറച്ചുനേരം മിണ്ടാതിരിക്ക്! 😠 Muted for {}!".format(time_val), quote=False)
            return log
        else:
            LOGGER.warning(update)
            LOGGER.exception("ERROR muting user %s in chat %s (%s) due to %s", user_id, chat.title, chat.id,
                             excp.message)
            message.reply_text("Well damn, I can't mute that user.")

    return ""


__help__ = """
*Admin only:*
 - /mute <userhandle>: ഒരു ഉപയോക്താവിനെ നിശബ്ദമാക്കുന്നു. ഉപയോക്താവിനുള്ള മറുപടി നിശബ്ദമാക്കി ഒരു മറുപടിയായി ഉപയോഗിക്കാനും കഴിയും.
 - /tmute <userhandle> x(m/h/d):x സമയത്തേക്ക് ഒരു ഉപയോക്താവിനെ നിശബ്ദമാക്കുന്നു. (ഹാൻഡിൽ വഴി അല്ലെങ്കിൽ മറുപടി വഴി). m = മിനിറ്റ്, h = മണിക്കൂർ, d = ദിവസം.
 - /unmute <userhandle>: ഒരു ഉപയോക്താവിനെ നിശബ്ദമാക്കുന്നു. ഉപയോക്താവിനുള്ള മറുപടി നിശബ്ദമാക്കി ഒരു മറുപടിയായി ഉപയോഗിക്കാനും കഴിയും.
"""

__mod_name__ = "mute"

MUTE_HANDLER = CommandHandler("mute", mute, pass_args=True, filters=Filters.group)
UNMUTE_HANDLER = CommandHandler("unmute", unmute, pass_args=True, filters=Filters.group)
TEMPMUTE_HANDLER = CommandHandler(["tmute", "tempmute"], temp_mute, pass_args=True, filters=Filters.group)

dispatcher.add_handler(MUTE_HANDLER)
dispatcher.add_handler(UNMUTE_HANDLER)
dispatcher.add_handler(TEMPMUTE_HANDLER)
