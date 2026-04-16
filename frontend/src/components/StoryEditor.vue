<script>
export default {
  name: 'StoryEditor',
  props: {
    model: String,
    context_length: Number,
    auto_save: Boolean,
    auto_summarize: Boolean,
    summarize_after_actions: Number,
    save_after_actions: Number
  },
  data() {
    return {
      content: '',
      summary: '',
      status_message: '',
      save_action_counter: 0,
      summarize_action_counter: 0,
      filename: '',
      show_summary: false
    }
  },
  methods: {
    trimToTokenApprox(text, maxTokens) {
      // Approximate characters per token
      const approxCharsPerToken = 4;
      const maxChars = maxTokens * approxCharsPerToken;

      return text.slice(-maxChars);
    },
    async continueStory() {
      try {
        // Trim content to last context_length for better performance
        const recent_story = this.trimToTokenApprox(this.content, this.context_length);

        this.status_message = 'Continuing story...';
        const res = await fetch('http://localhost:5000/api/continue', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            content: recent_story,
            summary: this.summary,
            model: this.model
          })
        });
        const data = await res.json();

        if (data.error) {
          this.status_message = 'Error continuing story: ' + data.error;
          return;
        }

        this.content = this.content + '\n\n' + (data.continued_content || '');
        
        // Scroll to bottom to show new content
        this.$nextTick(() => {
          const el = this.$refs.storyBox;
          el.scrollTop = el.scrollHeight;
        });

        this.status_message = '';

        // Automatically summarize after a set number of continue actions
        if (this.auto_summarize) {
          this.summarize_action_counter++; 

          if  (this.summarize_action_counter >= this.summarize_after_actions) {
            await this.summarizeStory();
            this.summarize_action_counter = 0; // reset counter
          }
        }
        // Automatically save story after a set number of continue actions
        if (this.auto_save) {
          this.save_action_counter++;
         
          if (this.save_action_counter >= this.save_after_actions) {
            await this.saveStory();
            this.save_action_counter = 0; // reset counter
          }
        }
      } catch (err) {
        this.status_message = 'Error continuing story: ' + err.error;
      }
    },
    async summarizeStory() {
      this.status_message = 'Summarizing story...';
      try {
        // Trim content to last context_length words
        const words = this.content.split(/\s+/);
        const recent_story = words.slice(-this.context_length).join(' ');

        const res = await fetch('http://localhost:5000/api/summarize', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            content: recent_story,
            summary: this.summary
          })
        });
        const data = await res.json();

        if (data.error) {
          this.status_message = 'Error summarizing story: ' + data.error;
          return;
        }
        this.summary = data.summary || '';
        this.status_message = 'Story summarized.';
      } catch (err) {
        this.status_message = 'Error summarizing story: ' + err.error;
      }
    },
    async saveStory() {
      if (!this.filename) {
        this.status_message = 'Please enter a filename to save the story.';
        return;
      }
      this.status_message = 'Saving story...';
      try {
        // Ensure filename ends with .json
        const filename = this.filename.endsWith('.json') ? this.filename : this.filename + '.json';
        const res = await fetch('http://localhost:5000/api/save', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            filename,
            content: this.content,
            summary: this.summary
          })
        });
        const data = await res.json();

        if (data.error) {
          this.status_message = 'Error saving story: ' + data.error;
          return;
        }
        this.status_message = data.message || 'Story saved.';
      } catch (err) {
        this.status_message = 'Error saving story: ' + err.error;
      }
    },
    async loadStory() {
      if (!this.filename) {
        this.status_message = 'Please enter a filename to load the story.';
        return;
      }
      this.status_message = 'Loading story...';
      try {
        const filename = this.filename.endsWith('.json') ? this.filename : this.filename + '.json';
        const res = await fetch('http://localhost:5000/api/load?filename=' + encodeURIComponent(filename));
        const data = await res.json();

        if (data.error) {
          this.status_message = 'Error loading story: ' + data.error;
          return;
        }
        this.content = data.content || '';
        this.summary = data.summary || '';
        this.status_message = 'Story loaded.';
      } catch (err) {
        this.status_message = 'Error loading story: ' + err.error;
      }
    }
  }
}
</script>

<template>
  <div class="container">
    <h2>Story Editor</h2>
    <textarea 
    ref="storyBox"
    v-model="content" 
    rows="15" 
    cols="80" 
    placeholder="Paste or write story text here"></textarea>
    <div>
      <button @click="continueStory">Continue Story</button>
    </div>
    <p>{{ status_message}}</p>
  </div>
  <div class="container">
    <h2>Load/Save Story</h2>
    <input v-model="filename" placeholder="Enter filename" />
    <button @click="loadStory">Load Story</button>
    <button @click="saveStory">Save Story</button>
  </div>
  <button @click="show_summary = !show_summary">
    {{ show_summary ? 'Hide Summary' : 'Show Summary' }}
  </button>
  <div class="container" v-if="show_summary">
    <h3>Summary</h3>
    <textarea v-model="summary" 
    rows="5" 
    cols="80" 
    placeholder="Summary will appear here. Summary will be used as context in story generation.">
    </textarea>
    <div>
      <button @click="summarizeStory">Summarize Story</button>
    </div>
  </div>
</template>

<style scoped>

</style>