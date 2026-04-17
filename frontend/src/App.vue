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
      context_length: 3000,
      auto_save: true,
      save_after_actions: 1,
      auto_summarize: true,
      summarize_after_actions: 3,
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
      :context_length="context_length"
      :auto_save="auto_save"
      :auto_summarize="auto_summarize"
      :summarize_after_actions="summarize_after_actions"
      :save_after_actions="save_after_actions"
    />
    <button @click="show_settings = !show_settings">
      {{ show_settings ? 'Hide Settings' : 'Show Settings' }}
    </button>
    <SettingsMenu 
      v-if="show_settings"
      
      :main_model="main_model"
      :mem_model="mem_model"
      :use_local="use_local"
      :context_length="context_length"
      :auto_save="auto_save"
      :auto_summarize="auto_summarize"
      :summarize_after_actions="summarize_after_actions"
      :save_after_actions="save_after_actions"

      @update:main_model="main_model = $event"
      @update:mem_model="mem_model = $event"
      @update:use_local="use_local = $event"
      @update:context_length="context_length = $event"
      @update:auto_save="auto_save = $event"
      @update:auto_summarize="auto_summarize = $event"
      @update:summarize_after_actions="summarize_after_actions = $event"
      @update:save_after_actions="save_after_actions = $event"
    />
  </div>
</template>

<style>
.story-editor {
  margin-top: 20px;
}
</style>