import ollama
from pathlib import Path

print("MENDVERSE AI Vision Test")

image_path = input("Enter your image path: ").strip().strip('"')

if not Path(image_path).is_file():
    print("ERROR: Image not found.")
else:
    try:
        print("\nAnalyzing your photograph...")

        response = ollama.chat(
            model="qwen2.5vl:3b",
            messages=[
                {
                    "role": "user",
                    "content": """
                    You are the MENDVERSE repair intelligence assistant.

                    Examine this photograph and provide:

                    1. Object identification
                    2. Visible damage or defects
                    3. Possible causes (clearly mark uncertainty)
                    4. Possible repair options
                    5. Reuse or upcycling ideas
                    6. Responsible recycling or recovery options
                    7. Safety precautions

                    Do not claim to identify hidden internal damage.
                    Do not present guesses as confirmed facts.
                    """,
                    "images": [image_path]
                }
            ]
        )

        print("\n===== MENDVERSE AI RESULT =====\n")
        print(response.message.content)

    except Exception as error:
        print("\nERROR:", error)