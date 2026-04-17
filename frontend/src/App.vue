<script>
import StoryEditor from './components/StoryEditor.vue';
import SettingsMenu from './components/SettingsMenu.vue';

export default {
  components: { StoryEditor, SettingsMenu },
  data() {
    return {
      // Default settings
      model: 'llama-3.1-8b-instant', // Free model on Groq
      context_length: 300,
      auto_save: false,
      auto_summarize: true,
      summarize_after_actions: 3,
      save_after_actions: 5,
      show_settings: false
    }
  }
}
</script>

<template>
  <div>
    <h1>AI Storyteller</h1>
    <StoryEditor class="story-editor"
      :model="model"
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
      
      :model="model"
      :context_length="context_length"
      :auto_save="auto_save"
      :auto_summarize="auto_summarize"
      :summarize_after_actions="summarize_after_actions"
      :save_after_actions="save_after_actions"

      @update:model="model = $event"
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