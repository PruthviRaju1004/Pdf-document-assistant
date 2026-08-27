import os
import json
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()
client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

tools = [
    {
        "name": "get_weather",
        "description": "Get the current weather for a city",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "The city name"}
            },
            "required": ["city"]
        }
    }
]

def get_weather(city: str) -> str:
    # Fake implementation, just to prove the loop works.
    # A real one would call a weather API here.
    return f"It's 72°F and sunny in {city}."

messages = [{"role": "user", "content": "What's the weather like in Boston?"}]

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=500,
    tools=tools,
    messages=messages,
)

print("First response stop_reason:", response.stop_reason)

if response.stop_reason == "tool_use":
    tool_use_block = next(b for b in response.content if b.type == "tool_use")
    print("Claude wants to call:", tool_use_block.name, "with", tool_use_block.input)

    tool_result = get_weather(**tool_use_block.input)
    print("Real function returned:", tool_result)

    messages.append({"role": "assistant", "content": response.content})
    messages.append({
        "role": "user",
        "content": [
            {
                "type": "tool_result",
                "tool_use_id": tool_use_block.id,
                "content": tool_result,
            }
        ]
    })

    final_response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        tools=tools,
        messages=messages,
    )

    print("\nFinal answer:", final_response.content[0].text)