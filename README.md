# AI-Storyteller

RUNNING INSTRUCTIONS

Docker is required to run the app: https://www.docker.com/products/docker-desktop/.

With Docker running, navigate to "AI-Storyteller" folder in your terminal and run "docker-compose up --build" to start the app. NOTE! The full container takes about 30-35 GB to run, mainly due to AI models and Docker images. First time set up may take 20+ minutes to compose depending on your internet connection.

Add your cloud AI API key and URL to backend/.env. The API key is ONLY used for API calls to your selected AI. 

Example AI, GroqCloud:
https://console.groq.com/home
API URL: https://api.groq.com/openai/v1/chat/completions


GENERATION INSRUCTIONS

Once you have the app running, begin a story by writing in the editor or load a previous story with its file name. Click on 'Continue Story' for the AI to continue the story from where it left off. The AI uses all of summary and plot essentials and up to two most relevant memories for context. Length of recent story used in context can be adjusted in the settings-menu. You may enable a setting to display total tokens used in each API call.

Additional story generation instructions can be in the Instructions tab. Default prompts for story/summary generation can be found in backend/default_prompts.py file. Full contex sent to the AI in a continue action can be seen in the Context tab.

NOTE! Running summary and memory generation with local AI requires an NVIDIA GPU with at least 8 GB of VRAM.

The story is saved after every continue action. Saved files can be found in backend/files. Memories in the database are tracked by using Story IDs.


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

Prompts for story generation (in backend/default_prompts.py) have been improved with the help of ChatGPT-5. As Faiss is a new technology for me, ChatGPT-5 has also been used to help generate and understand code found in backend/database.py.