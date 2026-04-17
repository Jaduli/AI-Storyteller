# AI-Storyteller

RUNNING INSTRUCTIONS

Docker is required to run the app: https://www.docker.com/products/docker-desktop/.

With Docker running, navigate to "AI-Storyteller" folder in your terminal and run "docker-compose up --build" to start the app.

Add your API key and URL to backend/.env. The API key is ONLY used for API calls to your selected AI. 

Example AI, GroqCloud:
https://console.groq.com/home
API URL: https://api.groq.com/openai/v1/chat/completions


GENERATION INSRUCTIONS

Once you have the app running, begin a story by writing in the editor or load a previous story with its file name. Click on 'Continue Story' for the AI to continue from where the story left off. The AI uses summary and recent story as context based on set context length. Story summary can be edited in the Summary-menu.

Generation model and context length can be edited in the Settings-menu. The story can also be set to auto-save (requires filename set) and to auto-summarize after set amount of story continue-actions.

The story can be saved any time. Note that saving overrides the previous file. Saved files can be found in backend/files.

Default prompts for story/summary generation can be found in backend/default_prompts.py file.


PROJECT INFORMATION

Technologies used
- Docker for containerization
- Backend: Python + Flask
- Frontend: Vue + Nginx
- Local AI: Ollama (currently unused in story generation)


AI USAGE INFORMATION
This program has been made in VSCode with GitHub Copilot(free version for TUNI students) tuned on. Model used is GPT-5 mini. Copilot has helped with debugging problematic code and generating useful functions such as for trimming text. AI has NOT been used in the overall structure, project idea, or technology selection.

Prompts for story generation (in backend/default_prompts.py) have been improved with the help of ChatGPT-5.