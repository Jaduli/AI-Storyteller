<script>
export default {
  name: 'SettingsMenu',
  props: {
    main_model: String,
    mem_model: String,
    use_local: Boolean,
    show_local_toggle: Boolean,
    show_token_use: Boolean,
    context_length: Number
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
    tokenVal: {
      get() { return this.show_token_use },
      set(v) { this.$emit('update:show_token_use', v) }
    },
    contextLengthVal: {
      get() { return this.context_length },
      set(v) { this.$emit('update:context_length', v) }
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

    <div v-if="show_local_toggle">
      <label>Use Local AI: </label>
      <input v-model="localVal" type="checkbox" />
    </div>

    <div v-if="!use_local">
      <label>Memorize/Summarize Model Name: </label>
      <input v-model="memModelVal" 
      type="text" 
      placeholder="llama-3.1-8b-instant"
      />
    </div>

    <div>
      <label>Recent Story Token Limit: </label>
      <input v-model.number="contextLengthVal" type="number" />
    </div>

    <div>
      <label>Show API Call Token Usage: </label>
      <input v-model="tokenVal" type="checkbox" />
    </div>
  </div>
</template>

<style scoped>
</style>