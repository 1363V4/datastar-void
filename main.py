from quart import Quart, session, render_template, request
from datastar_py.quart import make_datastar_response
from datastar_py.sse import ServerSentEventGenerator as SSE

from faker import Faker

import asyncio
import redis.asyncio as redis
import json
import random
import time


# CONFIG

app = Quart(__name__)
app.secret_key = 'a_secret_key'

fake = Faker()

# REDIS STUFF

@app.before_serving
async def start_redis():
    global redis
    redis = redis.Redis(
        host="localhost",
        port=6379,
        db=0,
        encoding="utf-8",
        decode_responses=True,
    )

@app.after_serving
async def close_redis():
    await redis.close()

# APP STUFF

@app.before_request
async def before_request():
    if not session.get('user_id'): 
        user_id = fake.name()
        session['user_id'] = user_id

@app.route('/')
async def index():
    return await render_template('index.html')

@app.route('/void')
async def void():
    user_id = session.get('user_id')

    pubsub = redis.pubsub()
    await pubsub.subscribe('main')
    async def event(generator):
        while True:
            try:
                ping = await pubsub.get_message()
                messages = await redis.lindex("messages", 0)
                html = '''
                <div id="messages">
                '''
                for message in messages:
                    payload = json.loads(message)
                    html += f'''
                    <div
                    class="message"
                    style="
                        position:absolute;
                        top:{payload.y}%;
                        left:{payload.x}%;
                        background:{payload.color};
                    "
                    </div>'''
                yield SSE.merge_fragments(fragments=[html], use_view_transition=True)
            except asyncio.CancelledError:
                pubsub.unsubscribe('main')
                break
    return await make_datastar_response(event)

@app.post("/message")
async def post_message():
    message = (await request.form).get('message')
    if not message:
        return 200
    color = f"#{random.randint(0, 0xFFFFFF):06x}"
    x = round(random.random() * 100, 2)
    y = round(random.random() * 100, 2)
    payload = {
        "message": message,
        "color": color,
        "x": x,
        "y": y,
    }
    await redis.lpush("messages", json.dumps(payload))
    return 200

if __name__ == '__main__':
    app.run(debug=True)
