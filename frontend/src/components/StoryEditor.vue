<script>
export default {
  name: 'StoryEditor',
  props: {
    main_model: String,
    mem_model: String,
    use_local: Boolean,
    show_token_use: Boolean,
    context_length: Number
  },
  data() {
    return {
      // Random story ID for storing memories in database
      story_id: crypto.getRandomValues(new Uint32Array(1))[0],
      // Components
      instructions: '', // Special instructions for the AI to use
      content: '',
      summary: '',
      plot_essentials: '',
      sent_context: '', // Full context sent for story generation
      status_message: '',
      // Values
      filename: '',
      active_tab: 'editor',
      is_loading: false,
      active_requests: 0,
      memory_cursor: 0,
      summary_cursor: 0,
      // Editable content displayed in story editor
      story_editor_content: '',
    }
  },
  methods: {
    // Helper function to trim text to approximate token length
    trimToTokenApprox(text, max_tokens) {
      // Approximate to 4 characters per token (may vary based on language and content)
      const approx_chars_per_token = 4;
      const max_chars = max_tokens * approx_chars_per_token;

      return text.slice(-max_chars);
    },
    // Helper function to trim past content for memory creation
    trimToPastContent(text, max_tokens) {
      const approx_chars_per_token = 4;
      const max_chars = max_tokens * approx_chars_per_token;

      const cutoff_index = Math.max(0, text.length - max_chars);

      const memory_content = text.slice(this.memory_cursor, cutoff_index);

      // Only create memory if there's enough content to memorize
      if (memory_content.length < 4000) return '';

      // Move memory cursor forward to cutoff index for next memory
      this.memory_cursor = cutoff_index;

      return memory_content;
    },
    trimToSummaryContent(text, max_tokens) {
      const approx_chars_per_token = 4;
      const max_chars = max_tokens * approx_chars_per_token;

      const cutoff_index = Math.max(0, text.length - max_chars + 1000); // Add some buffer to prevent losing content before next summary

      const new_content = text.slice(this.summary_cursor, cutoff_index);

      // Only summarize if there's enough new content to summarize
      if (new_content.length < 2000) return '';

      // Move summary cursor forward to cutoff index for next summary
      this.summary_cursor = cutoff_index;

      return new_content;
    },
    // Main function to continue the story with the backend API
    async continueStory() {
      // Basic validation to ensure there's enough content to continue
      if (!this.content || this.content.trim().length < 20) {
        this.status_message = 'Error: Please enter enough story content to continue.';
        return;
      }
      try {
        this.status_message = 'Continuing story...';
        this.active_requests++;

        const context = 'Plot Essentials:\n' + this.plot_essentials + '\n\nSummary:\n' + this.summary;
        const recent_story = this.trimToTokenApprox(this.content, this.context_length);

        const full_context = context + '\n\nRecent Story:\n' + recent_story;

        const res = await fetch('/api/continue', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            story_id: this.story_id,
            content: full_context,
            model: this.main_model,
            instructions: this.instructions
          })
        });
        const data = await res.json();

        if (data.error) {
          this.status_message = 'Error continuing story: ' + data.error;
          return;
        }

        this.content = this.content + '\n\n' + (data.continued_content || '');
        
        // Display full context used in API call
        if (data.full_context) {
          this.sent_context = data.full_context;
        }
        
        // Scroll to bottom to show new content
        this.$nextTick(() => {
          const el = this.$refs.storyBox;
          el.scrollTop = el.scrollHeight;
        });

        this.status_message = '';

        if (this.show_token_use && data.tokens_total) {
          this.status_message = 'Total tokens used for continue action: ' + data.tokens_total
        }
        // Automatically summarize (only happens once enough content is generated)
        await this.summarizeStory();

        // Automatically save story and turn past context into a memory if file name is set
        if (this.filename.trim() != '') {
          await this.saveStory();
          await this.createMemory();
        } else {
          this.status_message = 'Please set file name to save and memorize story.'
        }
      } catch (err) {
        this.status_message = 'Error continuing story: ' + (err.message || err);
      } finally {
        this.active_requests--;
      }
    },
    // Function to summarize the story with the backend API
    async summarizeStory() {
      const new_content = this.trimToSummaryContent(this.content, this.context_length);

      if (new_content.trim() === '') {
        return;
      }

      try {
        this.status_message = 'Summarizing story, please wait...'
        this.active_requests++;

        const recent_story = this.trimToTokenApprox(this.content, this.context_length);
        const full_context = 'Current Summary:\n' + this.summary + '\n\nNew Story Content:\n' + recent_story;

        const res = await fetch('/api/summarize', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            content: full_context,
            model: this.mem_model,
            local: this.use_local
          })
        });
        const data = await res.json();

        if (data.error) {
          this.status_message = 'Error summarizing story: ' + data.error;
          return;
        }
        this.summary = data.summary || '';
        this.status_message = '';

        if (this.show_token_use && data.tokens_total) {
          this.status_message = 'Total tokens used for summary action: ' + data.tokens_total
        }
      } catch (err) {
        this.status_message = 'Error summarizing story: ' + (err.message || err);
      } finally {
        this.active_requests--;
      }
    },
    // Function to create a memory with the backend API
    async createMemory() {
      if (!this.content || this.content.trim().length < 50) {
        return;
      }
      // Use past story content for new memory
      const content = this.trimToPastContent(this.content, this.context_length / 2);

      if (content.trim() === '') return;
      try {
        this.active_requests++;
        this.status_message = 'Creating a new memory, please wait...'
        
        const res = await fetch('/api/memorize', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            story_id: this.story_id,
            content: 'Past Story:\n' + content,
            model: this.mem_model,
            local: this.use_local
          })
        });
        const data = await res.json();

        if (data.error) {
          this.status_message = 'Error creating memory: ' + data.error;
          return;
        }

        this.status_message = '';

        if (this.show_token_use && data.tokens_total) {
          this.status_message = 'Total tokens used for memory action: ' + data.tokens_total
        }
      } catch (err) {
        this.status_message = 'Error creating memory: ' + (err.message || err);
      } finally {
        this.active_requests--;
      }
    },
    // Function to save the story to the backend API
    async saveStory() {
      if (!this.filename) {
        this.status_message = 'Please enter a filename to save the story.';
        return;
      }
      try {
        this.active_requests++;

        // Ensure filename ends with .json
        const filename = this.filename.endsWith('.json') ? this.filename : this.filename + '.json';
        const res = await fetch('/api/save', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            filename,
            story_id: this.story_id,
            instructions: this.instructions,
            content: this.content,
            summary: this.summary,
            plot_essentials: this.plot_essentials,
            memory_cursor: this.memory_cursor,
            summary_cursor: this.summary_cursor
          })
        });
        const data = await res.json();

        if (data.error) {
          this.status_message = 'Error saving story: ' + data.error;
          return;
        }
      } catch (err) {
        this.status_message = 'Error saving story: ' + (err.message || err);
      } finally {
        this.active_requests--;
      }
    },
    // Function to load the story from backend API
    async loadStory() {
      if (!this.filename) {
        this.status_message = 'Please enter a filename to load the story.';
        return;
      }
      try {
        this.active_requests++;
        this.status_message = 'Loading story...';

        const filename = this.filename.endsWith('.json') ? this.filename : this.filename + '.json';
        const res = await fetch('/api/load?filename=' + encodeURIComponent(filename));
        const data = await res.json();

        this.story_id = data.story_id || crypto.getRandomValues(new Uint32Array(1))[0];
        this.instructions = data.instructions || '';
        this.content = data.content || '';
        this.summary = data.summary || '';
        this.plot_essentials = data.plot_essentials || '';
        this.memory_cursor = data.memory_cursor || 0;
        this.summary_cursor = data.summary_cursor || 0;

        if (data.error) {
          this.status_message = 'Back end: ' + data.error + ' New story created.';
          return;
        }
        // Scroll to bottom after loading story
        this.$nextTick(() => {
          const el = this.$refs.storyBox;
          el.scrollTop = el.scrollHeight;
        });

        this.status_message = 'Story loaded successfully.';
      } catch (err) {
        this.status_message = 'Error loading story: ' + (err.message || err);
      } finally {
        this.active_requests--;
      }
    },
    // Update content from story_editor_content after user edit/input
    onEditorInput(e) {
      const start = this.displayStart;
      const new_text = e.target.value;

      this.story_editor_content = new_text;
      this.content = this.content.slice(0, start) + new_text;
    }
  },
  computed: {
    // Set state to loading if any active request is in process
    isLoading() {
      return this.active_requests > 0;
    },
    // Calculate where to start displaying content in editor based on context length
    displayStart() {
      const approx_chars_per_token = 4;
      const max_chars = this.context_length * approx_chars_per_token;

      return Math.max(0, this.content.length - max_chars);
    }
  },
  watch: {
    // Update story_editor_content when content changes
    content() {
      const start = this.displayStart;
      this.story_editor_content = this.content.slice(start);
    }
  }
}
</script>

<template>
  <div class="tab-header">
  <button 
    :class="{ active: active_tab === 'instructions' }"
    @click="active_tab = 'instructions'"
  >
    Instructions
  </button>

  <button 
    :class="{ active: active_tab === 'editor' }"
    @click="active_tab = 'editor'"
  >
    Editor
  </button>

  <button 
    :class="{ active: active_tab === 'summary' }"
    @click="active_tab = 'summary'"
  >
    Summary
  </button>

  <button 
    :class="{ active: active_tab === 'essentials' }"
    @click="active_tab = 'essentials'"
  >
    Essentials
  </button>

  <button 
    :class="{ active: active_tab === 'context' }"
    @click="active_tab = 'context'"
  >
    Context
  </button>
  </div>

  <div class="tab-content">
    <div class="container" v-show="active_tab === 'instructions'">
      <h2>Generation Instructions</h2>
      <textarea 
      v-model="instructions" 
      rows="15" 
      cols="80" 
      placeholder="Additional story generation instructions can be added here.">
      </textarea>
    </div>

    <div class="container" v-show="active_tab === 'editor'">
      <h2>Story Editor</h2>
      <textarea 
      ref="storyBox"
      v-model="story_editor_content" 
      @input="onEditorInput"
      rows="15" 
      cols="80" 
      placeholder="Paste or write story text here"></textarea>
      <div>
        <button @click="continueStory" :disabled="isLoading">Continue Story</button>
      </div>
    </div>

    <div class="container" v-show="active_tab === 'summary'">
      <h2>Summary</h2>
      <textarea v-model="summary" 
      rows="15" 
      cols="80" 
      placeholder="Summary will appear here. Summary will be used as context in story generation.">
      </textarea>
    </div>

    <div class="container" v-show="active_tab === 'essentials'">
      <h2>Plot Essentials</h2>
      <textarea v-model="plot_essentials" 
      rows="15" 
      cols="80" 
      placeholder="Key plot points, character details, or world-building elements. This will be used as context in story generation.">
      </textarea>
    </div>

    <div class="container" v-show="active_tab === 'context'">
      <h2>Sent Context</h2>
      <textarea v-model="sent_context" 
      rows="15" 
      cols="80" 
      placeholder="Context sent to story generation will show up here."
      readonly>
      </textarea>
    </div>
  </div>
  <p class="status">{{ status_message}}</p>
  <div class="container">
    <h2>Story File Name</h2>
    <input v-model="filename" placeholder="Enter file name" />
    <button @click="loadStory" :disabled="isLoading">Load Story</button>
  </div>
</template>

<style scoped>
.status {
  height: 30px;
  background: #08060d;
  padding: 5px;
}

textarea {
  resize: none;
}

.tab-content {
  position: relative;
  min-height: 285px;
  padding: 10px;
  padding-top: 10px;
}

.tab-content .container {
  position: absolute;
  width: 100%;
  top: 0;
  left: 0;
}
.tab-header button {
  padding: 8px 16px;
  border: none;
  background: #08060d;
  cursor: pointer;
}

.tab-header button.active {
  background: #aa3bff;
  color: white;
  font-weight: bold;
}
</style>