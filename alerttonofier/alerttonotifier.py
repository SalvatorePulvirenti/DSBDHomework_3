#!/usr/bin/env python
# pylint: disable=unused-argument
# This program is dedicated to the public domain under the CC0 license.

"""
Simple Bot to send timed Telegram messages.

This Bot uses the Application class to handle the bot and the JobQueue to send
timed messages.

First, a few handler functions are defined. Then, those functions are passed to
the Application and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Basic Alarm Bot example, sends a message after a set time.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.

Note:
To use the JobQueue, you must install PTB via
`pip install "python-telegram-bot[job-queue]"`
"""
from confluent_kafka import Consumer
import logging
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import os

BOOTSTRAP_SERVERS = os.getenv("BOOTSTRAP_SERVERS", "localhost:29092")
GROUP_ID = os.getenv("GROUP_ID", "consumer-group")

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Define a few command handlers. These usually take the two arguments update and
# context.
# Best practice would be to replace context with an underscore,
# since context is an unused local variable.
# This being an example and not having context present confusing beginners,
# we decided to have it present as context.

config_kafka={
        'bootstrap.servers': "kafka:9092", #BOOTSTRAP_SERVERS,
        'group.id': GROUP_ID,
        'auto.offset.reset': 'earliest',
        'enable.auto.commit': True
}


consumer = Consumer(config_kafka)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends explanation on how to use the bot."""
    global userid
    userid=update.message.from_user.id
    await update.message.reply_text("Hi! Use /set <seconds> to set a timer")


async def alarm(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the alarm message."""
    msg=consumer.poll(1.0)
    if msg is None:
       highvalue="None"
    else:
       if msg.error():
       	 highvalue="Errore: {errore}".format(errore= msg.error())
       else:
         data=msg.value().decode('utf-8')
         data_j = json.loads(msg.value().decode('utf-8'))

#         highvalue=msg.value().decode('utf-8')
         job = context.job
         ticker=data_j['ticker']
         alarm=data_j['alarm']   
         id=data_j['id']
         if id == userid:
            await context.bot.send_message(job.chat_id, text=f"Beep! {job.data} seconds are over and ticker={ticker} Alarm={alarm} data={data}!")


def remove_job_if_exists(name: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


async def set_timer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add a job to the queue."""
    chat_id = update.effective_message.chat_id
    user=update.message.from_user.id
    username=update.message.from_user.first_name
    
    try:
        # args[0] should contain the time for the timer in seconds
        due = float(context.args[0])
        if due < 0:
            await update.effective_message.reply_text("Sorry we can not go back to future!")

        job_removed = remove_job_if_exists(str(chat_id), context)
        context.job_queue.run_repeating(alarm, due, chat_id=chat_id, name=str(chat_id), data=due)
#        context.job_queue.run_once(alarm, due, chat_id=chat_id, name=str(chat_id), data=due)
        print(user,type(user))
        text = "Dear {user} Timer successfully set!".format(user=user)
        if job_removed:
            text += " Old one was removed."
        await update.effective_message.reply_text(text)

    except (IndexError, ValueError):
        await update.effective_message.reply_text("Usage: /set <seconds>")


async def unset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Remove the job if the user changed their mind."""
    chat_id = update.message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)
    text = "Timer successfully cancelled!" if job_removed else "You have no active timer."
    await update.message.reply_text(text)


def main() -> None:
    """Run bot."""
    tonotif = 'to-notifier'  # Destination topic for output statistics
    consumer.subscribe(['to-notifier'])

    # Create the Application and pass it your bot's token.
    application = Application.builder().token("7707366922:AAHb79k2LJ-LDTCasynkK1Cr7p1mxvNtlXM").build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler(["start", "help"], start))
    application.add_handler(CommandHandler("set", set_timer))
    application.add_handler(CommandHandler("unset", unset))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    print("ciao")

if __name__ == "__main__":
    main()
