<script>
export default {
  name: 'SettingsMenu',
  props: {
    main_model: String,
    mem_model: String,
    use_local: Boolean,
    context_length: Number,
    auto_save: Boolean,
    auto_summarize: Boolean,
    summarize_after_actions: Number,
    save_after_actions: Number
  },
  computed: {
    // Create computed properties with getters and setters to emit value updates
    mainModelVal: {
      get() {
        return this.main_model
      },
      set(v) {
        // Default to 'llama-3.1-8b-instant' if input is empty
        const value = v && v.trim() !== '' ? v : 'llama-3.1-8b-instant'
        this.$emit('update:main_model', value)
      }
    },
    memModelVal: {
      get() {
        return this.mem_model
      },
      set(v) {
        // Default to 'llama-3.1-8b-instant' if input is empty
        const value = v && v.trim() !== '' ? v : 'llama-3.1-8b-instant'
        this.$emit('update:mem_model', value)
      }
    },
    localVal: {
      get() { return this.use_local },
      set(v) { this.$emit('update:use_local', v) }
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
      <label>Main Model Name: </label>
      <input v-model="mainModelVal" 
      type="text" 
      placeholder="llama-3.1-8b-instant"
      />
    </div>

    <div>
      <label>Memorize/Summarize Model Name: </label>
      <input v-model="memModelVal" 
      type="text" 
      placeholder="llama-3.1-8b-instant"
      />
    </div>

    <div>
      <label>Use Local AI: </label>
      <input v-model="localVal" type="checkbox" />
    </div>

    <div>
      <label>Context Length: </label>
      <input v-model.number="contextLengthVal" type="number" />
    </div>

    <div>
      <label>Auto-Save: </label>
      <input v-model="autoSaveVal" type="checkbox" />
    </div>

    <div v-if="autoSaveVal">
      <label>Save After Actions: </label>
      <input v-model.number="saveAfterActionsVal" type="number" />
    </div>

    <div>
      <label>Auto-Summarize: </label>
      <input v-model="autoSummarizeVal" type="checkbox" />
    </div>

    <div v-if="autoSummarizeVal">
      <label>Summarize After Actions: </label>
      <input v-model.number="summarizeAfterActionsVal" type="number" />
    </div>
  </div>
</template>

<style scoped>
</style>