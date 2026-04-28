<script>
export default {
  name: 'SettingsMenu',
  props: {
    main_model: String,
    mem_model: String,
    use_local: Boolean,
    show_local_toggle: Boolean,
    show_token_use: Boolean,
    top_p: Number,
    temperature: Number,
    max_tokens: Number,
    context_length: Number
  },
  data() {
    return {
      temp_context_length: this.context_length
    }
  },
  methods: {
    setContextLength(new_length) {
      let num = Number(new_length)

      // Handle invalid input
      if (isNaN(num)) {
        num = this.context_length || 4000 // fallback
      } else {
        // Clamp to 1-32000
        num = Math.min(Math.max(num, 1), 32000)
      }
      this.$emit('update:context_length', num)
    }
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
    topPVal: {
      get() { return this.top_p },
      set(v) {
        let num = Number(v)

        // Handle invalid input
        if (isNaN(num)) {
          num = this.top_p || 0.9 // fallback
        } else {
          // Clamp to 0-1
          num = Math.min(Math.max(num, 0), 1)
        }
        this.$emit('update:top_p', num)
      }
    },
    temperatureVal: {
      get() { return this.temperature },
      set(v) {
        let num = Number(v)

        // Handle invalid input
        if (isNaN(num)) {
          num = this.temperature || 0.8 // fallback
        } else {
          // Clamp to 0-2
          num = Math.min(Math.max(num, 0), 2)
        }
        this.$emit('update:temperature', num)
      }
    },
    maxTokensVal: {
      get() { return this.max_tokens },
      set(v) {
        let num = Number(v)

        // Handle invalid input
        if (isNaN(num)) {
          num = this.max_tokens || 200 // fallback
        } else {
          // Clamp to 10-1000
          num = Math.min(Math.max(num, 10), 1000)
        }
        this.$emit('update:max_tokens', num)
      }
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
      <input 
        v-model.number="temp_context_length"
        type="number" 
        max="32000" 
        min="1"
        placeholder="4000"
      />
      <button @click="setContextLength(temp_context_length)">Set Limit</button>
      <span title="Changing the limit will automatically save and reload any loaded story.">
        ⓘ
      </span>
    </div>
    
    <div>
      <label>Top P: </label>
      <input v-model.number="topPVal" 
      type="number" 
      step="0.1" 
      min="0" 
      max="1"
      placeholder="0.9" />
    </div>

    <div>
      <label>Temperature: </label>
      <input v-model.number="temperatureVal" 
      type="number" 
      step="0.1" 
      min="0" 
      max="2"
      placeholder="0.8" />
    </div>

    <div>
      <label>Maximum Generated Tokens: </label>
      <input v-model.number="maxTokensVal" 
      type="number" 
      min="10"
      max="1000"
      placeholder="200" />
    </div>

    <div>
      <label>Show API Call Token Usage: </label>
      <input v-model="tokenVal" type="checkbox" />
    </div>
  </div>
</template>

<style scoped>
.settings-menu {
  border: 1px solid #aa3bff;
  border-radius: 5px;
  padding: 15px;
  background: #1a1a2e;
}
</style>