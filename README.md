# AI-Storyteller

APPLICATION FEATURES

- Continue a story with an AI model of your choosing. You may start off with anything in any genre, in any point of view (including second person view).
- Add custom story context with Story Essentials (always included in prompt) and Context Cards (only included when relevant to story).
- Add custom instructions to be used in story generation (e.g. storytelling style, point of view, content restrictions).
- Edit generated story content in any way (within the context window).
- Story memories and summary will be created and used automatically as the story progresses.
- Save and load stories. The story autosaves after every continuation, and one backup save is generated for each story.
- Edit generation settings such as model, temperature, and recent story token limit.
- See total tokens used in each API call.
- Support is included for running a local AI that can be used for summary and memory creation (requires compatible GPU).


RUNNING INSTRUCTIONS

Docker is required to run the app: https://www.docker.com/products/docker-desktop/.

With Docker running, navigate to "AI-Storyteller" folder in your terminal and run `docker compose up --build` to build and run the app without local AI (=> all AI use is done with an external AI API). 

When running, the app can be accessed at http://localhost:5173/.

If you have an NVIDIA GPU with at least 8 GB of VRAM and compatible drivers, you can run the app with a local AI for summary and memory actions (GPU mode). To use local AI, build and run the app with `docker compose -f docker-compose.yml -f docker-compose.gpu.yml up --build`. Running the AI locally will reduce cloud API rate limits and cost. Local story continuation is not supported as competent storytelling should be done with a large (20B+ parameter) model. Smaller models struggle with consistency and creativity and have limited use cases.

NOTE! The full container takes about 25-35 GB to run, mainly due to Docker images and the local AI model (only installed on GPU mode). First time set up may take 20+ minutes to compose depending on selected mode and your internet connection.

Add your cloud AI API key and URL in a .env file in the root folder. The API key is ONLY used for API calls to your selected provider. You can also add default models for external API calls in the .env file.

Example AI, GroqCloud:
https://console.groq.com/home
API URL: https://api.groq.com/openai/v1/chat/completions
Groq provides a free model: llama-3.1-8b-instant (rate limits apply, use less context, recommended only for testing purposes).

Best quality/price AI, DeepSeek:
https://platform.deepseek.com/
API URL: https://api.deepseek.com/chat/completions
Model name & Pricing can be found here:
https://api-docs.deepseek.com/quick_start/pricing

The container can be stopped with CTRL+C in the terminal. Once built, the container can also be run directly through the Docker Desktop app. After startup, the site will load only once it reaches a connection to the backend. If the site refuses to load, check that containers are up and have finished loading.


GENERATION INSRUCTIONS

Once you have the app running, begin a story by writing in the editor or load a previous story with its filename. Click on 'Continue Story' for the AI to continue the story from where it left off. The AI uses all of summary and story essentials, up to five relevant context cards, and up to two most recent + two most relevant past memories for context. Length of recent story used as context can be adjusted in the 'Settings'-menu (has no effect on other context fields). You may enable a setting to display total tokens used in each API call. The full prompt & system instructions used in story generation can be seen in the 'Sent Context' tab. For more detailed explanations on how each component works, read chapter 2.4 of ProjectDocumentation.pdf.

The application includes a simple example scenario which can be accessed with the file name 'example' or 'example.json'. After a successful story continuation, you can look through 'Sent Context' tab to see how different context fields are included in story generation.

Additional story generation instructions, such as storytelling style or content restrictions, can be written in the Instructions tab. Default prompts for story, memory, and summary generation can be found in backend/default_prompts.py file.

The story is saved automatically after every Continue action. It can also be saved manually with the Save button. One backup save is created for each file, which can be accessed with the filename {filename}_backup.json. Saved files and their backups can be found in backend/files. 

Past memories for each story are saved in a database which can be found in backend/data/memory.db. Memories can be viewed and edited with an SQL compatible database editor, e.g DBeaver (https://dbeaver.io/). As summaries and memories are generated with AI, hallucination or metatext may be included in the output. For this reason, manual context editing may be required for lower token usage and better story consistency.


PROJECT INFORMATION

Technologies used
- Docker for containerization
- Backend: Python + Flask + SQLite + FAISS
- Frontend: Vue.js + Nginx
- Local AI: Ollama (current model: llama3.1:8b)

Story files are saved as JSON. Memories are kept in a SQLite database. FAISS (Facebook AI Similarity Search, https://faiss.ai/index.html) is used to fetch memories relevant to current story context from the database.

Inspiration for this project has been gained from similar AI storytellers such as AI Dungeon (https://aidungeon.com/) and NovelAI (https://novelai.net/).

For more detailed project information, read ProjectDocumentation.pdf.


USAGE RIGHTS & SAFETY NOTICE

You are free to use and edit the program for personal use. Commercial use is not allowed. You are personally responsible for any content you create with the application.

By default, there are no restrictions in place for content generation beyond the model's and API provider's own guardrails. The AI can generate text content that could be considered dangerous, mature, or distressing, especially if prompted to do so. For this reason, the application should never be used by minors without adult supervision.


AI USAGE INFORMATION

The application has been made in VSCode with GitHub Copilot (free version for TUNI students) tuned on. Model used is GPT-5 mini. Copilot has helped with commenting, debugging, autocompletion, CSS, and generating useful functions such as for trimming text. AI has NOT been used in the overall structure, project idea, or technology selection.

Prompts for story generation (in backend/default_prompts.py) have been improved with the help of ChatGPT-5. As FAISS is a new technology for me, ChatGPT-5 has also been used to help generate and understand code found in backend/database.py.
