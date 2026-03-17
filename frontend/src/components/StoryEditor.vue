<script>
export default {
  props: {
    model: { type: String, default: '' }
  },
  data() {
    return {
      content: '',
      status_message: ''
    }
  },
  methods: {
    async continueStory() {
      try {
        const res = await fetch('http://localhost:5000/api/continue', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            content: this.content,
            model: this.model
          })
        });
        const data = await res.json();

        this.content = this.content + '\n\n' + (data.continued_content || '');
      } catch (err) {
        this.status_message = 'Error continuing story: ' + err.error;
      }
    }
  }
}
</script>

<template>
  <div class="container">
    <textarea v-model="content" rows="6" cols="80" placeholder="Paste or write story text here"></textarea>
    <div>
      <button @click="continueStory">Continue Story</button>
    </div>
    <p>{{ status_message }}</p>
  </div>
</template>

<style>

</style>