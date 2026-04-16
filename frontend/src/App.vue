<script>
import StoryEditor from './components/StoryEditor.vue';
import SettingsMenu from './components/SettingsMenu.vue';

export default {
  components: { StoryEditor, SettingsMenu },
  data() {
    return {
      // Default settings
      model: 'llama-3.1-8b-instant',
      context_length: 300,
      auto_save: false,
      auto_summarize: true,
      summarize_after_actions: 3,
      save_after_actions: 5
    }
  }
}
</script>

<template>
  <div>
    <h1>AI Storyteller</h1>
    <SettingsMenu
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
    <StoryEditor
      :model="model"
      :context_length="context_length"
      :auto_save="auto_save"
      :auto_summarize="auto_summarize"
      :summarize_after_actions="summarize_after_actions"
      :save_after_actions="save_after_actions"
    />
  </div>
</template>

<style>

</style>