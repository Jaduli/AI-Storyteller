<script>
export default {
  props: {
    card: {
      type: Object,
      required: true
    }
  },
  emits: ['remove'],
  computed: {
    keywordsString: {
      get() {
        return Array.isArray(this.card.keywords) ? this.card.keywords.join(', ') : this.card.keywords;
      },
      set(value) {
        this.card.keywords = value.split(',').map(k => k.trim());
      }
    }
  }
}
</script>

<template>
    <div class="context-card">
        <h3>Name</h3>
        <input type="text" v-model="card.name" />
        <h4>Content</h4>
        <textarea v-model="card.content" />
        <h4>Keywords</h4>
        <input type="text" v-model="card.keywords" />
        <button @click="$emit('remove')">Remove</button>
    </div>
</template>

<style scoped>
/* Styling generated with Copilot */
.context-card {
  border: 1px solid #aa3bff;
  border-radius: 5px;
  padding: 15px;
  background: #1a1a2e;
}

.context-card h3 {
  margin-top: 0;
  color: #aa3bff;
}

.context-card h4 {
  margin: 10px 0 5px 0;
  color: #ccc;
}

.context-card input,
.context-card textarea {
  width: 100%;
  padding: 8px;
  margin-bottom: 10px;
  background: #0f0f1e;
  color: #fff;
  border: 1px solid #444;
  border-radius: 3px;
  font-family: inherit;
  box-sizing: border-box;
}

.context-card input:focus,
.context-card textarea:focus {
  outline: none;
  border-color: #aa3bff;
  box-shadow: 0 0 5px rgba(170, 59, 255, 0.3);
}

.context-card button {
  background: #aa3bff;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 3px;
  cursor: pointer;
  font-weight: bold;
}

.context-card button:hover {
  background: #9a2bef;
}

.context-card textarea {
  resize: vertical;
  min-height: 80px;
}
</style>