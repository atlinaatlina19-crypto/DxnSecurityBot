import os
from threading import Thread
from flask import Flask

app = Flask('')


@app.route('/')
def home():
  return "Bot is alive!"


def run():
  app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))


def keep_alive():
  t = Thread(target=run)
  t.daemon = True
  t.start()


# تشغيل خادم الويب قبل تشغيل البوت
keep_alive()

# ضع سطر تشغيل البوت الخاص بك هنا في الأسفل:
client.run(MTU2MjExMjMzMjI3OTA1NDQxOA.Gzhn3T.VkoKW_msRjLgCwEq9JVQfqE6huC1NkuOgAmSwA)
