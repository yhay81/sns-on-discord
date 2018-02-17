import sqlite3
import discord
import ConfigParser

client = discord.Client()
conn = sqlite3.connect("tweet.db")


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    conn.execute("CREATE TABLE IF NOT EXISTS follower(followed_id integer, follower_id integer)")
    conn.execute("CREATE INDEX IF NOT EXISTS follower_user_id_index on follower(followed_id)")
    conn.commit()


@client.event
async def on_server_join(server):
    return await tw_man(server.default_channel)


@client.event
async def on_message(message):
    if message.content.startswith('!'):
        if message.content.startswith('!つぶやきくん'):
            return await tw_man(message.channel)
        if message.content.startswith('!follow'):
            return await tw_follow(message)
        if message.content.startswith('!unfollow'):
            return await tw_unfollow(message)
        if message.content.startswith('!showfollows'):
            return await tw_showfollows(message)
        if message.content.startswith('!showfollowers'):
            return await tw_showfollowers(message)
        if message.content.startswith('!allunfollow'):
            return await tw_allunfollow(message)
    if not message.server and not message.author.id == client.user.id and not message.content.startswith('!'):
        return await tw_tweet(message)


# CREATE TABLE follower(followed_id integer, follower_id integer);
#  create index follower_user_id_index on follower(followed_id);

async def tw_man(channel):
    return await client.send_message(
        channel,
        """つぶやきくんと個人チャットで何か喋るとフォロワーに公開されるよ！
              
使えるコマンド(コマンドはつぶやかれません):
ヘルプをみる: !つぶやきくん
フォローする: !follow [@フォローしたい人] [@フォローしたい人2(オプション)] ...
フォローをやめる: !unfollow [@フォロー外したい人] [@フォロー外したい人2(オプション)] ...
フォロー一覧をみる: !showfollows
フォロワー一覧をみる: !showfollowers
つぶやきくんをやめる: !allunfollow
"""
    )


async def tw_tweet(message):
    content = "{}\n{}".format(message.author.mention, message.content)
    print(content)
    for follower in conn.execute(
            "SELECT follower_id FROM follower WHERE followed_id=?", (message.author.id,)).fetchall():
        await client.send_message(discord.utils.get(client.get_all_members(), id=str(follower[0])), content)
    return


async def tw_follow(message):
    for mention in message.mentions:
        if conn.execute("SELECT * FROM follower WHERE followed_id=? and follower_id=?",
                        (mention.id, message.author.id)).fetchone():
            return await client.send_message(message.author, "{}さんはもうすでにフォローしています。".format(mention.mention))
        else:
            conn.execute("insert into follower values( ?, ? )",
                         [mention.id, message.author.id])
            conn.commit()
            return await client.send_message(message.author, "{}さんをフォローしました。".format(mention.mention))


async def tw_unfollow(message):
    for mention in message.mentions:
        if conn.execute("SELECT * FROM follower WHERE followed_id=? and follower_id=?",
                        (mention.id, message.author.id)).fetchone():
            conn.execute("delete from follower where followed_id=? and follower_id=?",
                         (mention.id, message.author.id))
            conn.commit()
            return await client.send_message(message.author, "{}さんのフォローを解除しました。".format(mention.mention))
        else:
            return await client.send_message(message.author, "{}さんはフォローしていません。".format(mention.mention))


async def tw_allunfollow(message):
    if conn.execute("SELECT * FROM follower WHERE follower_id=?", (message.author.id)).fetchone():
        conn.execute("delete from follower where follower_id=?",
                     (message.author.id))
        conn.commit()
        return await client.send_message(message.author, "全てのフォローを解除しました。")
    else:
        return await client.send_message(message.author, "あなたは誰もフォローしていません。")


async def tw_showfollows(message):
    count = int(conn.execute("SELECT count(0) FROM follower WHERE follower_id=?",
                             (message.author.id,)).fetchone()[0])
    if count == 0:
        return await client.send_message(
            message.author,
            "{}さんは誰もフォローしていません。\nコマンド:!follow [@フォローしたい人]\nで誰かをフォローしてみましょう。".format(message.author.mention))
    follows = conn.execute(
        "SELECT followed_id FROM follower WHERE follower_id=?", (message.author.id,)).fetchall()
    return await client.send_message(
        message.author, "{}さんのフォロー一覧({}):\n{}".format(message.author.mention, count, "- " + "\n- ".join(
            "<@{}>".format(follow[0]) for follow in follows)))


async def tw_showfollowers(message):
    count = int(conn.execute("SELECT count(0) FROM follower WHERE followed_id=?",
                             (message.author.id,)).fetchone()[0])
    if count == 0:
        return await client.send_message(message.author, "{}さんは誰にもフォローされていません。".format(message.author.mention))
    followers = conn.execute(
        "SELECT follower_id FROM follower WHERE followed_id=?", (message.author.id,)).fetchall()
    return await client.send_message(
        message.author, "{}さんのフォロワー一覧({}):\n{}".format(message.author.mention, count, "- " + "\n- ".join(
            "<@{}>".format(follower[0]) for follower in followers)))


if __name__ == '__main__':
    config = ConfigParser.ConfigParser()
    config.read('setting.ini')
    client.run(config.get('client', 'secret'))
