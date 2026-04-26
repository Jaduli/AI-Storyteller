<script>
import StoryEditor from './components/StoryEditor.vue';
import SettingsMenu from './components/SettingsMenu.vue';

export default {
  components: { StoryEditor, SettingsMenu },
  data() {
    return {
      // Default settings
      // Main model used for story continuation
      main_model: 'llama-3.1-8b-instant', // Free model on Groq
      // Memory model used for memory and summary generation
      mem_model: 'llama-3.1-8b-instant',
      // If true, memory and summary are generated with local AI
      use_local: true, 
      // If true, show total tokens used for all AI API calls
      show_token_use: false,
      // Context length affects the length of recent story
      // used as context in story generation (in tokens)
      context_length: 1000,
      show_settings: false
    }
  }
}
</script>

<template>
  <div>
    <h1>AI Storyteller</h1>
    <StoryEditor class="story-editor"
      :main_model="main_model"
      :mem_model="mem_model"
      :use_local="use_local"
      :show_token_use="show_token_use"
      :context_length="context_length"
    />
    <button @click="show_settings = !show_settings">
      {{ show_settings ? 'Hide Settings' : 'Show Settings' }}
    </button>
    <SettingsMenu 
      v-if="show_settings"
      
      :main_model="main_model"
      :mem_model="mem_model"
      :use_local="use_local"
      :show_token_use="show_token_use"
      :context_length="context_length"

      @update:main_model="main_model = $event"
      @update:mem_model="mem_model = $event"
      @update:use_local="use_local = $event"
      @update:show_token_use="show_token_use = $event"
      @update:context_length="context_length = $event"
    />
  </div>
</template>

<style>
.story-editor {
  margin-top: 20px;
}
</style>