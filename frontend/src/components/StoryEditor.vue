<script>
export default {
  name: 'StoryEditor',
  props: {
    main_model: String,
    mem_model: String,
    use_local: Boolean,
    context_length: Number
  },
  data() {
    return {
      // Random story ID for storing memories in database
      story_id: crypto.getRandomValues(new Uint32Array(1))[0],
      // Components
      instructions: '',
      content: '',
      summary: '',
      plot_essentials: '',
      sent_context: '', // Context sent for story generation
      memories: '',
      status_message: '',
      // Values
      filename: '',
      active_tab: 'editor',
      memory_cursor: 0,
      summary_cursor: 0
    }
  },
  methods: {
    // Helper function to trim text to approximate token length
    trimToTokenApprox(text, maxTokens) {
      // Approximate to 4 characters per token (may vary based on language and content)
      const approxCharsPerToken = 4;
      const maxChars = maxTokens * approxCharsPerToken;

      return text.slice(-maxChars);
    },
    // Helper function to trim past content for memory creation
    trimToPastContent(text, maxTokens) {
      const approxCharsPerToken = 4;
      const maxChars = maxTokens * approxCharsPerToken;

      const cutoffIndex = Math.max(0, text.length - maxChars);

      const newOldContent = text.slice(this.memory_cursor, cutoffIndex);

      // Only create memory if there's enough new content
      if (newOldContent.length < 4000) return '';

      this.memory_cursor = cutoffIndex;

      return newOldContent;
    },
    trimToSummaryContent(text, maxTokens) {
      const approxCharsPerToken = 4;
      const maxChars = maxTokens * approxCharsPerToken;

      const cutoffIndex = Math.max(0, text.length - maxChars);

      const newContent = text.slice(this.summary_cursor, cutoffIndex);

      // Only summarize if enough new content
      if (newContent.length < 2000) return '';

      this.summary_cursor = cutoffIndex;

      return newContent;
    },
    // Main function to continue the story with the backend API
    async continueStory() {
      // Basic validation to ensure there's enough content to continue
      if (!this.content || this.content.trim().length < 20) {
        this.status_message = 'Error: Please enter enough story content to continue.';
        return;
      }
      this.status_message = 'Continuing story...';
      try {
        const context = 'Plot Essentials:\n' + this.plot_essentials + '\n\nSummary:\n' + this.summary;
        const recent_story = this.trimToTokenApprox(this.content, this.context_length);

        const full_context = context + '\n\nRecent Story:\n' + recent_story;

        const res = await fetch('http://localhost:5000/api/continue', {
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
        this.sent_context = full_context;
        
        // Scroll to bottom to show new content
        this.$nextTick(() => {
          const el = this.$refs.storyBox;
          el.scrollTop = el.scrollHeight;
        });

        this.status_message = '';

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
        this.status_message = 'Error continuing story: ' + err.error;
      }
    },
    // Function to summarize the story with the backend API
    async summarizeStory() {
      const newContent = this.trimToSummaryContent(this.content, this.context_length);

      if (newContent.trim() === '') {
        return;
      }

      const full_context = 'Current Summary:\n' + this.summary + '\n\nNew Story Content:\n' 
                            + newContent;
      try {
        this.status_message = 'Summarizing story, please wait...'
        const recent_story = this.trimToTokenApprox(this.content, this.context_length);
        const full_context = 'Summary:\n' + this.summary + '\n\nRecent Story:\n' + recent_story;

        const res = await fetch('http://localhost:5000/api/summarize', {
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
      } catch (err) {
        this.status_message = 'Error summarizing story: ' + err.error;
      }
    },
    // Function to create a memory with the backend API
    async createMemory() {
      if (!this.content || this.content.trim().length < 50) {
        return;
      }
      try {
        this.status_message = 'Creating a new memory, please wait...'
        // Use past story content for new memory
        const content = this.trimToPastContent(this.content, this.context_length / 2);

        if (content.trim() == '') return;

        const res = await fetch('http://localhost:5000/api/memorize', {
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
        this.memories += 'Created Memory:\n';
        this.memories += data.memory || '';
        this.memories += '\n\n';

        this.status_message = '';
      } catch (err) {
        this.status_message = 'Error creating memory: ' + err.error;
      }
    },
    // Function to save the story to the backend API
    async saveStory() {
      if (!this.filename) {
        this.status_message = 'Please enter a filename to save the story.';
        return;
      }
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
        this.status_message = 'Error saving story: ' + err.error;
      }
    },
    // Function to load the story from backend API
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
        this.story_id = data.story_id || crypto.getRandomValues(new Uint32Array(1))[0];
        this.instructions = data.instructions || '';
        this.content = data.content || '';
        this.summary = data.summary || '';
        this.plot_essentials = data.plot_essentials || '';
        this.memory_cursor = data.memory_cursor || 0;
        this.summary_cursor = data.summary_cursor || 0;

        this.status_message = 'Story loaded successfully.';
      } catch (err) {
        this.status_message = 'Error loading story: ' + err.error;
      }
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
    :class="{ active: active_tab === 'memories' }"
    @click="active_tab = 'memories'"
  >
    Memories
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
      ref="storyBox"
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
      v-model="content" 
      rows="15" 
      cols="80" 
      placeholder="Paste or write story text here"></textarea>
      <div>
        <button @click="continueStory">Continue Story</button>
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

    <div class="container" v-show="active_tab === 'memories'">
      <h2>Created Memories</h2>
      <textarea v-model="memories" 
      rows="15" 
      cols="80" 
      placeholder="New memories will show up here."
      readonly>
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
    <input v-model="filename" placeholder="Enter filename" />
    <button @click="loadStory">Load Story</button>
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