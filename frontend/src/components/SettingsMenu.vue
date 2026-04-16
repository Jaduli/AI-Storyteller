<script>
export default {
  name: 'SettingsMenu',
  props: {
    model: String,
    context_length: Number,
    auto_save: Boolean,
    auto_summarize: Boolean,
    summarize_after_actions: Number,
    save_after_actions: Number
  },
  computed: {
    // Create computed properties with getters and setters to emit value updates
    modelVal: {
      get() { return this.model },
      set(v) { this.$emit('update:model', v) }
    },
    contextLengthVal: {
      get() { return this.context_length },
      set(v) { this.$emit('update:context_length', v) }
    },
    autoSaveVal: {
      get() { return this.auto_save },
      set(v) { this.$emit('update:auto_save', v) }
    },
    autoSummarizeVal: {
      get() { return this.auto_summarize },
      set(v) { this.$emit('update:auto_summarize', v) }
    },
    summarizeAfterActionsVal: {
      get() { return this.summarize_after_actions },
      set(v) { this.$emit('update:summarize_after_actions', v) }
    },
    saveAfterActionsVal: {
      get() { return this.save_after_actions },
      set(v) { this.$emit('update:save_after_actions', v) }
    }
  }
}
</script>

<template>
  <div class="settings-menu">
    <h2>Settings</h2>

    <div>
      <label>Model Name:</label>
      <input v-model="modelVal" 
      type="text" 
      placeholder="Default: llama-3.1-8b-instant"
      />
    </div>

    <div>
      <label>Context Length:</label>
      <input v-model.number="contextLengthVal" type="number" />
    </div>

    <div>
      <label>Auto-Save:</label>
      <input v-model="autoSaveVal" type="checkbox" />
    </div>

    <div v-if="autoSaveVal">
      <label>Save After Actions:</label>
      <input v-model.number="saveAfterActionsVal" type="number" />
    </div>

    <div>
      <label>Auto-Summarize:</label>
      <input v-model="autoSummarizeVal" type="checkbox" />
    </div>

    <div v-if="autoSummarizeVal">
      <label>Summarize After Actions:</label>
      <input v-model.number="summarizeAfterActionsVal" type="number" />
    </div>
  </div>
</template>

<style scoped>
</style>