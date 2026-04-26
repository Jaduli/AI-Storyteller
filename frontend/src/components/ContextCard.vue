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
        <h3>{{ card.name }}</h3>
        <input type="text" v-model="card.name" placeholder="Card name" />
        <h4>Content</h4>
        <textarea v-model="card.content" placeholder="Card content" />
        <h4>Keywords</h4>
        <input type="text" v-model="keywordsString" placeholder="Comma-separated keywords" />
        <button @click="$emit('remove')">Remove</button>
    </div>
</template>