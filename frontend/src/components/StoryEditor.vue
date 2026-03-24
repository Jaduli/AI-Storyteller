<script>
export default {
  props: {
    model: { type: String, default: '' }
  },
  data() {
    return {
      content: '',
      summary: '',
      status_message: '',
      action_counter: 0
    }
  },
  methods: {
    async continueStory() {
      try {
        this.status_message = 'Continuing story...';
        const res = await fetch('http://localhost:5000/api/continue', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            content: this.content,
            summary: this.summary,
            model: this.model
          })
        });
        const data = await res.json();

        if (data.error) {
          this.status_message = 'Error: ' + data.error;
          return;
        }

        this.content = this.content + ' ' + (data.continued_content || '');
        this.status_message = '';
        this.action_counter++;
        if (this.action_counter >= 5) {
          await this.summarizeStory();
          this.action_counter = 0; // reset counter
        }
      } catch (err) {
        this.status_message = 'Error continuing story: ' + err.error;
      }
    },
    async summarizeStory() {
      try {
        const res = await fetch('http://localhost:5000/api/summarize', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            content: this.content
          })
        });
        const data = await res.json();

        if (data.error) {
          this.status_message = 'Error: ' + data.error;
          return;
        }

        this.summary = data.summary || '';
      } catch (err) {
        this.status_message = 'Error summarizing story: ' + err.error;
      }
    }
  }
}
</script>

<template>
  <div class="container">
    <textarea v-model="content" 
    rows="15" 
    cols="80" 
    placeholder="Paste or write story text here"></textarea>
    <div>
      <button @click="continueStory">Continue Story</button>
    </div>
    <p>{{ status_message}}</p>
  </div>
  <div class="container">
    <h3>Summary</h3>
    <textarea v-model="summary" 
    rows="5" 
    cols="80" 
    placeholder="Summary will appear here. Summary will be used as context in story generation.">
    </textarea>
  </div>
</template>

<style>

</style>