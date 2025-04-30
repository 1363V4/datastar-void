from quart import Quart, session, render_template, request
from datastar_py.quart import make_datastar_response
from datastar_py.sse import ServerSentEventGenerator as SSE
from faker import Faker
import asyncio
import redis.asyncio as redis
import json
import random
import time
import uuid


# CONFIG

app = Quart(__name__)
app.secret_key = 'a_secret_key'

fake = Faker()

# REDIS STUFF

@app.before_serving
async def start_redis():
    global redis_client
    redis_client = redis.Redis(host="localhost", port=6379, db=1, decode_responses=True)

@app.after_serving
async def close_redis():
    await redis_client.close()

# APP STUFF

@app.before_request
async def before_request():
    if not session.get('user_id'): 
        session['user_id'] = fake.name()

@app.route('/')
async def index():
    return await render_template('void.html')

@app.route('/void')
async def void():
    # pubsub = redis_client.pubsub()
    # await pubsub.subscribe('main')
    
    async def event():
        while True:
            try:
                # await pubsub.get_message()
                keys = await redis_client.keys('msg-*')
                if keys:
                    html = '<div id="messages">'
                    for key in keys:
                        data = await redis_client.get(key)
                        ttl = await redis_client.ttl(key)
                        if data and ttl:
                            opacity = ttl / 10
                            payload = json.loads(data)
                            html += f'''
                            <div
                            id="{key}"
                            class="message"
                            style="
                                opacity:{opacity};
                                top:{payload['y']}%;
                                left:{payload['x']}%;
                                background:{payload['color']};
                            "
                            >
                            {payload['message']}
                            </div>'''
                    html += '</div>'
                    yield SSE.merge_fragments(fragments=[html])
                else:
                    await asyncio.sleep(.2)
            except asyncio.CancelledError:
                # await pubsub.unsubscribe('main')
                break
                
    return await make_datastar_response(event())

@app.post("/message")
async def post_message():
    message = (await request.form).get('message')
    if not message:
        return "No message", 200
        
    payload = {
        "message": message,
        "color": f"#{random.randint(0, 0xFFFFFF):06x}",
        "x": round(10 + random.random() * 80, 2),
        "y": round(5 + random.random() * 80, 2),
    }
    
    msg_id = str(time.time()).replace(".", "-")
    await redis_client.set(f"msg-{msg_id}", json.dumps(payload), ex=10)
    # await redis_client.publish('main', msg_id)
    
    return "", 200

if __name__ == '__main__':
    app.run(debug=True)
