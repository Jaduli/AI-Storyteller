<script>
import StoryEditor from './components/StoryEditor.vue';
import SettingsMenu from './components/SettingsMenu.vue';

export default {
  components: { StoryEditor, SettingsMenu },
  data() {
    return {
      // Default settings //

      // Main model used for story continuation.
      main_model: 'llama-3.1-8b-instant', // Free model on Groq
      // Memory model used for memory and summary generation.
      mem_model: 'llama-3.1-8b-instant',
      // If true, memory and summary are generated with local AI.
      use_local: false, 
      // Shows/hides toggle depending on mode (local AI (=GPU mode)/no local AI).
      // Only shown if local AI is available, otherwise use_local is always false.
      show_local_toggle: false, 
      // If true, show total tokens used for all AI API calls (including local).
      show_token_use: false,
      // Context length affects the length of recent story
      // used as context in story generation (in tokens).
      context_length: 4000,
      // Top P and temperature control randomness in the AI output.
      // Higher values mean more randomness and creativity, lower values improve 
      // consistency with story context (e.g. story essentials and memories).
      top_p: 0.9,
      temperature: 0.8,
      // Max tokens controls the length of returned content in story generation.
      max_tokens: 200,
      show_settings: false,
      config_ready: false
    }
  },
  methods: {
    async loadConfig(delay = 2000) {
      while (!this.config_ready) {
        try {
          const res = await fetch('/api/config');

          if (!res.ok) {
            throw new Error(`HTTP ${res.status}`);
          }

          const data = await res.json();

          // If local AI is enabled, show toggle and set use_local to true by default
          this.show_local_toggle = data.local_ai_enabled;
          this.use_local = data.local_ai_enabled;
          
          // Load default models from backend .env if provided
          this.main_model = data.main_model || this.main_model;
          this.mem_model = data.mem_model || this.mem_model;

          this.config_ready = true;
        } catch (err) {
          console.error('Failed to load backend configuration, retrying...', err);
          await this.wait(delay);
        }
      }
    },
    wait(ms) {
      return new Promise(resolve => setTimeout(resolve, ms));
    }
  },
  async mounted() {
    // Load backend config. Wait 2 seconds before retry.
    this.loadConfig(2000);
  }
}
</script>

<template>
  <!-- App is loaded only after backend config is ready -->
  <div v-if="config_ready" class="app-container">
    <h1>AI Storyteller</h1>
    <StoryEditor class="story-editor"
      :main_model="main_model"
      :mem_model="mem_model"
      :use_local="use_local"
      :show_token_use="show_token_use"
      :context_length="context_length"
      :top_p="top_p"
      :temperature="temperature"
      :max_tokens="max_tokens"
    />
    <button @click="show_settings = !show_settings">
      {{ show_settings ? 'Hide Settings' : 'Show Settings' }}
    </button>
    <SettingsMenu
      v-if="show_settings"
      
      :main_model="main_model"
      :mem_model="mem_model"
      :show_local_toggle="show_local_toggle"
      :use_local="use_local"
      :show_token_use="show_token_use"
      :context_length="context_length"
      :top_p="top_p"
      :temperature="temperature"
      :max_tokens="max_tokens"

      @update:main_model="main_model = $event"
      @update:mem_model="mem_model = $event"
      @update:use_local="use_local = $event"
      @update:show_token_use="show_token_use = $event"
      @update:context_length="context_length = $event"
      @update:top_p="top_p = $event"
      @update:temperature="temperature = $event"
      @update:max_tokens="max_tokens = $event"
    />
  </div>
  <div v-else>
    <p>Loading backend configuration, please wait...</p>
  </div>
</template>

<style>
.story-editor {
  margin-top: 20px;
}
input, textarea {
  resize: none;
  padding: 8px;
  background: #0f0f1e;
  color: #fff;
  border: 1px solid #444;
  border-radius: 3px;
  font-family: inherit;
  box-sizing: border-box;
}

textarea {
  font-family: 'Merriweather', 'Georgia', serif;
  width: 100%;
  margin-bottom: 10px;
}

input:focus,
textarea:focus {
  outline: none;
  border-color: #aa3bff;
  box-shadow: 0 0 5px rgba(170, 59, 255, 0.3);
}

button {
  background: #aa3bff;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 3px;
  cursor: pointer;
  font-weight: bold;
  margin: 5px;
}

.container {
  border: 1px solid #0f0f1e;
  border-radius: 5px;
  padding: 15px;
  background: #1a1a2e;
}
</style>