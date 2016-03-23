#!/usr/bin/env python
"""telegram bot to send youtube rss-feeds"""

import telegram
import feedparser
import json
import psycopg2
import psycopg2.extras

with open('config.json', 'r') as f:
    config = json.load(f)

pg = config['db']['pg_conn']
tg_bot = config['telegram']['bot']

bot = telegram.Bot(token=tg_bot['token'])

conn = psycopg2.connect(
    "host=%s port=%s dbname=%s user=%s password=%s"
    % (pg['host'], pg['port'], pg['dbname'], pg['user'], pg['pass']),
    cursor_factory=psycopg2.extras.DictCursor)

cur = conn.cursor()
cur_upd = conn.cursor()

cur.execute("""
    select id, ch_name, ch_id
    from channels_settings
    where active
            """)
for channel in cur:
    r = feedparser.parse("%s%s" % (
        config['url']['youtube'], channel['ch_id']
    ))
    for e in r.entries:
        cur_upd.execute("""
            insert into feeds_send(
                channel_id, entry_id, published, title, link
            ) values (%s, %s, %s, %s, %s)
            on conflict (entry_id) do nothing
                    """, (channel['id'], e.id, e.published, e.title, e.link))
        conn.commit()

cur_feeds = conn.cursor()
cur_feeds.execute("""
    select cs.ch_name, fs.id, fs.link
        , to_char(fs.published, 'dd.mm.yy hh24:mi') dt
    from feeds_send fs
        join channels_settings as cs on cs.id = fs.channel_id
    where sent is null
        and cs.active = true
    order by fs.published asc
    limit %s
                  """ % (tg_bot['send_feeds_limit'], ))

for feed in cur_feeds:
    msg = "%s\n%s" % (feed['dt'], feed['link'])
    for chat_id in config['telegram']['chat_ids']:
        bot.sendMessage(
            chat_id=chat_id,
            text=msg,
            parse_mode=telegram.ParseMode.MARKDOWN,
            disable_web_page_preview=False)

    cur_upd.execute("""
        update feeds_send
        set sent = now()
        where id = %s
                    """ % feed['id'])
    conn.commit()

cur_feeds.close()
cur_upd.close()
cur.close()

conn.close()
