# Datastar Void: Message Into The Void

A minimalist **"message into the void"** application built with **Datastar** and **Quart**, demonstrating two distinct approaches to real-time messaging: **TTL-based expiration** and **pub/sub broadcasting**. This project showcases Datastar's reactive patterns, long-lived SSE connections, and dynamic DOM manipulation in an animated interface.

[Quart](https://quart.palletsprojects.com/en/latest/index.html) is an asyncio reimplementation of the popular Flask microframework API.

## Overview

This application allows users to "scream into the void" by sending messages that appear as floating text on screen. Messages automatically fade away over time. The project demonstrates two different real-time architectures:

1. **TTL Implementation** (`/void`): Messages stored in Redis with time-to-live, fetched periodically
2. **Pub/Sub Implementation** (`/void2`): Messages broadcast instantly via Redis pub/sub

Both showcase different Datastar SSE patterns while maintaining the same user experience.

## Project Structure

```
datastar-void/
├── main.py               # Main Quart application with dual implementations
├── templates/
│   └── void.html         # Single-page interface with form and message area
├── static/
│   └── css/
│       └── main.css      # Animated gradient background and message styling
├── datastar_py/          # Local Datastar Python integration
└── pyproject.toml        # Project dependencies
```

## Technology Stack

- **Backend**: Quart (async Python) with Redis for message storage and pub/sub
- **Frontend**: Datastar for reactive UI with long-lived SSE connections
- **Communication**: Server-Sent Events & pub/sub
- **Styling**: CSS animations with dynamic positioning and opacity transitions
- **Message Generation**: Faker for automatic user identification

## Features

### ✨ **Ephemeral Messaging**

- Messages appear as floating bubbles with random colors and positions
- Automatic fade-out over 10 seconds
- No permanent storage - truly into the void

### 🎨 **Dynamic Visual Effects**

- Animated gradient background
- Random message positioning (10-90% of screen)
- Random hex colors for each message
- Smooth opacity transitions

### ⚡ **Real-Time Updates**

- Long-lived SSE connections for instant message appearance
- Two implementation patterns: polling vs. pub/sub
- Automatic user identification with Faker

## Datastar Integration & Features

### 1. Reactive Form Submission

**Zero-JavaScript Form Handling**:

```html
<form data-on-submit="@post('/message2', {contentType: 'form'})">
  <input name="message" placeholder="Scream into the void..." />
</form>
```

**Server-Side Processing**:

```python
@app.post("/message2")
async def post_message2():
    message = (await request.form).get('message')
    if not message:
        return "No message", 200

    payload = {
        "message": message,
        "color": f"#{random.randint(0, 0xFFFFFF):06x}",
        "x": round(10 + random.random() * 80, 2),
        "y": round(5 + random.random() * 80, 2),
    }

    await redis_client.publish('main', json.dumps(payload))
    return "", 200
```

**Key Features**:

- **`data-on-submit`**: Automatic form submission without page reload
- **Content-Type Control**: `{contentType: 'form'}` for proper form encoding
- **Dynamic Message Properties**: Server generates random colors and positions
- **Instant Broadcasting**: Redis pub/sub for immediate message distribution

### 2. Long-Lived SSE Connection with Auto-Load

**Connection Initialization**:

```html
<div id="messages" data-on-load="@get('/void2')"></div>
```

**Server-Side SSE Stream**:

```python
@app.route('/void2')
async def void2():
    pubsub = redis_client.pubsub()
    await pubsub.subscribe('main')
    async def event():
        while True:
            try:
                ping = await pubsub.get_message()
                if ping and ping['type'] == "message":
                    payload = json.loads(ping['data'])
                    html = f'''
                    <div
                    class="message2"
                    style="
                        top:{payload['y']}%;
                        left:{payload['x']}%;
                        background:{payload['color']};
                    "
                    >
                    {payload['message']}
                    </div>'''
                    yield SSE.merge_fragments(
                        fragments=[html],
                        selector="#messages",
                        merge_mode="prepend"
                        )
            except asyncio.CancelledError:
                await pubsub.unsubscribe('main')
                break

    return await make_datastar_response(event())
```

**Advanced Features**:

- **`data-on-load`**: Automatic SSE connection when page loads
- **Persistent Connection**: Single connection handles all real-time updates
- **Redis Pub/Sub Integration**: Instant message broadcasting across clients
- **Dynamic CSS Injection**: Server-generated inline styles for positioning
- **Graceful Cleanup**: Automatic unsubscribe on connection close

### 3. Advanced Fragment Targeting with Merge Modes

**Prepend Mode for Message History**:

```python
yield SSE.merge_fragments(
    fragments=[html],
    selector="#messages",
    merge_mode="prepend"
)
```

**DOM Structure Management**:

```html
<div id="messages">
  <!-- New messages prepended here -->
  <div class="message2">Latest message</div>
  <div class="message2">Previous message</div>
  <div class="message2">Older message</div>
</div>
```

**Benefits**:

- **Selective Updates**: Target specific DOM elements with `selector`
- **Content Ordering**: `prepend` mode maintains chronological order
- **Performance**: Merges message container into DOM without changing anything else on the page
- **CSS Integration**: Works seamlessly with CSS animations

### 4. TTL-Based Implementation (Alternative Pattern)

**Polling-Based Message Retrieval**:

```python
@app.route('/void')
async def void():
    async def event():
        while True:
            try:
                keys = await redis_client.keys('msg-*')
                if keys:
                    html = '<div id="messages">'
                    for key in keys:
                        data = await redis_client.get(key)
                        ttl = await redis_client.ttl(key)
                        if data and ttl:
                            opacity = ttl / 10  # Fade based on remaining TTL
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
            except asyncio.CancelledError:
                break
    return await make_datastar_response(event())
```

**TTL Message Storage**:

```python
@app.post("/message")
async def post_message():
    message = (await request.form).get('message')
    # ... generate payload ...

    msg_id = str(time.time()).replace(".", "-")
    await redis_client.set(f"msg-{msg_id}", json.dumps(payload), ex=10)  # 10 second expiry

    return "", 200
```

**Pattern Comparison**:

| Feature               | TTL Implementation        | Pub/Sub Implementation |
| --------------------- | ------------------------- | ---------------------- |
| **Message Retrieval** | Periodic polling          | Real-time broadcasting |
| **Fade Effect**       | Server-calculated opacity | CSS animation          |

### 5. Automatic User Session Management

**Seamless User Identification**:

```python
@app.before_request
async def before_request():
    if not session.get('user_id'):
        session['user_id'] = fake.name()
        # useful if we want the same user to always have the same color
```

**Benefits**:

- **No Registration**: Automatic user assignment using Faker
- **Session Persistence**: Maintains user identity across requests

### 6. Event-Driven Real-Time Updates

```python
# Pub/Sub pattern for instant updates
await redis_client.publish('main', json.dumps(payload))

# SSE stream responds to Redis messages
ping = await pubsub.get_message()
if ping and ping['type'] == "message":
    yield SSE.merge_fragments(fragments=[html])
```

### 7. Server-Driven Styling

```python
# Server generates CSS properties
html = f'''
<div style="
    top:{payload['y']}%;
    left:{payload['x']}%;
    background:{payload['color']};
">
{payload['message']}
</div>'''
```

### 8. Form-to-SSE Integration

```html
<!-- Form submission triggers real-time update -->
<form data-on-submit="@post('/message2', {contentType: 'form'})">
  <!-- SSE connection receives the update -->
  <div id="messages" data-on-load="@get('/void2')">
</form>
```

## CSS Animation Integration

### Dynamic Message Positioning

**Server-Generated Coordinates**:

```python
payload = {
    "message": message,
    "color": f"#{random.randint(0, 0xFFFFFF):06x}",
    "x": round(10 + random.random() * 80, 2),  # 10-90% width
    "y": round(5 + random.random() * 80, 2),   # 5-85% height
}
```

**CSS Positioning and Animation**:

```css
.message2 {
  position: absolute;
  transform: translate(-50%, -50%);
  padding: 0.5rem 1rem;
  border-radius: 0.25rem;
  color: #fff;
  font-weight: bold;
  pointer-events: none;
  animation: fadeout 10s linear forwards;
}

@keyframes fadeout {
  from {
    opacity: 1;
  }
  to {
    opacity: 0;
  }
}
```

### Animated Background

**Dynamic Gradient Animation**:

```css
body {
  background: linear-gradient(135deg, var(--bg-primary), var(--bg-secondary));
  background-size: 200% 200%;
  animation: animateBackground 10s ease infinite;
}

@keyframes animateBackground {
  50% {
    background-position: 100% 100%;
  }
}
```

## Running the Application

### Prerequisites

- Redis server
- uv package manager

### Setup

1. **Start Redis**:

```bash
redis-server
```

2. **Install dependencies**:

```bash
uv sync
```

3. **Run the application**:

```bash
uv run main.py
```

4. **Open your browser**: Navigate to `http://localhost:5000`

### Usage

1. **Type a message** in the input field
2. **Press Enter** or click submit
3. **Watch your message** appear as a colorful bubble
4. **Messages automatically fade** over 10 seconds
5. **Open multiple tabs** to see real-time messaging between sessions

## Key Datastar Patterns

### Declarative Form

```html
data-on-submit="@post('/message2', {contentType: 'form'})"
```

### Auto-Loading SSE Connections

```html
data-on-load="@get('/void2')"
```

### Targeted Fragment Updates

```python
yield SSE.merge_fragments(
    fragments=[html],
    selector="#messages",
    merge_mode="prepend"
)
```

### Long-Lived Event Streams

```python
async def event():
    while True:
        ping = await pubsub.get_message()
        yield SSE.merge_fragments(fragments=[html])
```

## Why This Architecture Matters

This project demonstrates that **beautiful, real-time user experiences** can be achieved with minimal complexity. By combining:

- **Datastar's declarative approach**: No complex JavaScript framework needed
- **Quart's async capabilities**: High-performance, scalable server architecture
- **Redis pub/sub**: Instant message broadcasting across clients
- **CSS animations**: Smooth, browser-optimized visual effects

We achieve:

- ✅ **Instant real-time updates** without polling overhead
- ✅ **Beautiful animations** with server-driven positioning & timing
- ✅ **Developer-friendly** patterns that are easy to understand and extend
- ✅ **Zero JavaScript complexity** while maintaining rich interactivity

**The Result**: A delightful experience that showcases Datastar's real-time capabilities in a beautifully simple application.
