# AI-Storyteller

RUNNING INSTRUCTIONS

Docker is required to run the app: https://www.docker.com/products/docker-desktop/.

With Docker running, navigate to "AI-Storyteller" folder in your terminal and run `docker-compose up --build` to start the app without local AI (all AI use is done with the external AI API). 

If you have an NVIDIA GPU with at least 8 GB of VRAM, you can run the app with a local AI for summary and memory actions with the command `docker compose -f docker-compose.yml -f docker-compose.gpu.yml up --build`. Running the AI locally will reduce cloud API rate limits and cost.

NOTE! The full container takes about 25-35 GB to run, mainly due to Docker images and a local AI model (only installed if run on GPU mode). First time set up may take 20+ minutes to compose depending on selected mode and your internet connection.

Add your cloud AI API key and URL in a .env file in the root folder. The API key is ONLY used for API calls to your selected AI. You can also add a default model for external API calls.

Example AI, GroqCloud:
https://console.groq.com/home
Provides a free model: llama-3.1-8b-instant (rate limits apply).
API URL: https://api.groq.com/openai/v1/chat/completions

Best price/quality AI, DeepSeek:
https://platform.deepseek.com/
Model name & Pricing can be found here:
https://api-docs.deepseek.com/quick_start/pricing
API URL: https://api.deepseek.com/chat/completions

The container can be stopped with CTRL+C in the terminal. Once set up, the container can be started and stopped through the Docker Desktop app.


GENERATION INSRUCTIONS

Once you have the app running, begin a story by writing in the editor or load a previous story with its file name. Click on 'Continue Story' for the AI to continue the story from where it left off. The AI uses all of summary and plot essentials, relevant context cards, and up to two most recent + two most relevant memories for context. Length of recent story used in context can be adjusted in the Settings-menu (has no effect on other context fields). You may enable a setting to display total tokens used in each API call. Context sent in a continue-action can be seen in the Sent Context-tab.

Additional story generation instructions, such as storytelling style or content restrictions, can be written in the Instructions tab. Default prompts for story, memory, and summary generation can be found in backend/default_prompts.py file. By default, there are no safeguards for generated content beyond the model's and API's own guardrails. Be mindful that the AI may provide mature or disturbing content if prompted to do so. For this reason, it should not be used by minors without adult supervision.

The story is saved automatically after every continue action. It can also be saved manually with the save button. One backup save is created for each file, which can be accessed with file name {story_name}_backup. Saved files and their backups can be found in backend/files. Memories are saved in a database which can be found in backend/data/memory.db. Memories can be viewed and edited with an SQL compatible database editor, e.g DBeaver (https://dbeaver.io/).


PROJECT INFORMATION

Technologies used
- Docker for containerization
- Backend: Python + Flask + SQLite + FAISS
- Frontend: Vue + Nginx
- Local AI: Ollama (current model: llama3:8b)

Story files are saved as JSON. Memories are kept in a SQLite database. FAISS (Facebook AI Similarity Search, https://faiss.ai/index.html) is used to fetch memories relevant to current story context from the database.

Inspiration for this project has been gained from similar AI storytellers such as AI Dungeon (https://aidungeon.com/) and NovelAI (https://novelai.net/). 


AI USAGE INFORMATION

This program has been made in VSCode with GitHub Copilot (free version for TUNI students) tuned on. Model used is GPT-5 mini. Copilot has helped with debugging problematic code and generating useful functions such as for trimming text. AI has NOT been used in the overall structure, project idea, or technology selection.

Prompts for story generation (in backend/default_prompts.py) have been improved with the help of ChatGPT-5. As FAISS is a new technology for me, ChatGPT-5 has also been used to help generate and understand code found in backend/database.py.