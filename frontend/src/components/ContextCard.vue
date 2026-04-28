<script>
export default {
  data() {
    return {
      collapse: true
    }
  },
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
        <h3>{{ card.name }}</h3>
        <button @click="collapse = !collapse">{{ collapse ? 'Edit' : 'Collapse' }}</button>
        <div v-if="!collapse">
          <h4>Name</h4>
          <input type="text" v-model="card.name" />
          <h4>Content</h4>
          <textarea v-model="card.content" />
          <h4>Keywords (comma-separated)</h4>
          <input type="text" v-model="card.keywords" />
          <button class="btn btn-danger" @click="$emit('remove')">Delete Card</button>
        </div>
    </div>
</template>

<style scoped>
.context-card {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.context-card > div {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.context-card textarea {
  min-height: 120px;
}
.context-card h4 {
  margin: 3px 0 3px;
}
.context-card button {
  margin-bottom: 10px;
}
.context-card .btn-danger {
  background: #ff4d4d;
}
</style>