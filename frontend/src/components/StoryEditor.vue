<script>
import ContextCards from './ContextCards.vue';

export default {
  name: 'StoryEditor',
  components: {
    ContextCards
  },
  emits: ['tab-changed'],
  props: {
    main_model: String,
    mem_model: String,
    use_local: Boolean,
    show_token_use: Boolean,
    context_length: Number,
    top_p: Number,
    temperature: Number,
    max_tokens: Number
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
      active_requests: 0,
      memory_cursor: 0,
      summary_cursor: 0,
      // Editable content displayed in story editor
      story_editor_content: '',
    }
  },
  methods: {
    setActiveTab(tab) {
      this.active_tab = tab;
    },
    // Trim text to approximate token length
    trimToTokenApprox(text) {
      // Approximate to 4 characters per token (may vary based on language and content)
      const approx_chars_per_token = 4;
      const max_chars = (this.context_length || 4000) * approx_chars_per_token;

      return text.slice(-max_chars);
    },
    // Trim past content for memory creation.
    // Minimum length determines how much content is needed for creating a new memory.
    trimToPastContent(minimum_length_chars = 7000) {
      const approx_chars_per_token = 4;

      // Trim so that recent story won't be included in memory creation
      const recent_story_chars = (this.context_length || 4000) * approx_chars_per_token;

      const cutoff_index = Math.max(0, this.content.length - recent_story_chars);
      
      // Window is content between memory cursor and story content that has fallen 
      // out of context window.
      const memory_content = this.content.slice(this.memory_cursor, cutoff_index);

      // Only create new memory if there's enough content to memorize
      if (memory_content.length < minimum_length_chars) return '';

      // Move memory cursor forward to cutoff index for next memory
      this.memory_cursor = cutoff_index;

      return memory_content;
    },
    // Trim past content for summary creation
    trimToSummaryContent(minimum_length_chars = 4000) {
      const approx_chars_per_token = 4;

      const recent_story_chars = (this.context_length || 4000) * approx_chars_per_token;

      // Overlap with recent content to avoid losing context when content
      // falls out of context window between summary actions.
      const overlap = minimum_length_chars / 2;

      const cutoff_index = Math.max(0, this.content.length - recent_story_chars + overlap);

      const new_content = this.content.slice(this.summary_cursor, cutoff_index);

      // Only summarize if there's enough new content to summarize
      if (new_content.length < minimum_length_chars) return '';

      // Move summary cursor forward to cutoff index for next summary
      this.summary_cursor = cutoff_index;

      return new_content;
    },
    // Main function to continue the story with the backend API
    async continueStory() {
      let start = this.displayStart;

      // Sync content with story editor
      if (this.story_editor_content !== this.content.slice(start)) {
        this.content = this.content.slice(0, start) + this.story_editor_content;
      }

      // Basic validation to ensure there's enough content to continue
      if (!this.story_editor_content || this.story_editor_content.trim().length < 20) {
        this.status_message = 'Error: Please enter enough story content to continue.';
        return;
      }
      try {
        this.active_requests++;
        this.status_message = 'Continuing story...';

        const recent_story = this.trimToTokenApprox(this.content);

        // Get relevant context cards based on found keywords in recent story
        const context_cards = this.$refs.contextCards.getMatchingContextCards(recent_story);

        const res = await fetch('/api/continue', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            model: this.main_model,
            story_id: this.story_id,
            instructions: this.instructions,
            summary: this.summary,
            plot_essentials: this.plot_essentials,
            context_cards: context_cards,
            recent_story: recent_story,
            top_p: this.top_p || 0.9,
            temperature: this.temperature || 0.8,
            max_tokens: this.max_tokens || 200
          })
        });
        const data = await res.json();

        if (data.error) {
          this.status_message = 'Error continuing story: ' + data.error;
          return;
        }

        const continued_content = data.continued_content || '';

        // Append continued content to story with proper spacing
        if (recent_story.slice(-1) != '\n') {
          this.content += ('\n\n' + continued_content);
        } else {
          this.content += continued_content;
        }

        // Sync story editor content with new content
        start = this.displayStart;
        this.story_editor_content = this.content.slice(start);
        
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
          await this.createMemory();
          await this.saveStory();
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
      // Use past story content (+some overlap with recent content) for summary
      const past_content = this.trimToSummaryContent();

      if (past_content.trim() === '') {
        return;
      }

      try {
        this.active_requests++;
        this.status_message = 'Summarizing story, please wait...'

        const full_context = 'Current Summary:\n' + this.summary + '\n\nNew Story Content:\n' + past_content;

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
        console.log('Summary created with content:\n' + past_content);

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
      const past_content = this.trimToPastContent();

      if (past_content.trim() === '') return;
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
            content: 'Past Story:\n' + past_content,
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
        console.log('Memory created with content:\n' + past_content);

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
    async saveStory(sync = true) {
      if (!this.filename) {
        this.status_message = 'Please enter a filename to save the story.';
        return;
      }
      if (sync) {
        // Sync content with story editor before saving
        const start = this.displayStart;

        if (this.story_editor_content !== this.content.slice(start)) {
          this.content = this.content.slice(0, start) + this.story_editor_content;
        }
      }

      try {
        this.active_requests++;

        // Ensure filename ends with .json
        const filename = this.filename.endsWith('.json') ? this.filename : this.filename + '.json';
        
        const context_cards = this.$refs.contextCards.cards || [];

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
            summary_cursor: this.summary_cursor,
            context_cards: context_cards
          })
        });
        const data = await res.json();

        if (data.error) {
          this.status_message = 'Error saving story: ' + data.error;
          return;
        }
        // Only show success message if this is the only active request to avoid confusion with other actions
        if (this.active_requests === 1 && data.message) {
          this.status_message = 'Success: ' + data.message;
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
        this.$refs.contextCards.cards = data.context_cards || [];
        
        // Initialize story editor content based on current content length
        const start = this.displayStart;
        this.story_editor_content = this.content.slice(start);

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
    }
  },
  computed: {
    // App state counts as loading if any active request is in process.
    // This disables continue, save, and load buttons to prevent multiple simultaneous 
    // requests which can cause issues.
    isLoading() {
      return this.active_requests > 0;
    },
    // Calculate where to start displaying content in editor based on context length.
    // This prevents editing already memorized or summarized content and makes textEditor
    // more responsive by not rendering the entire story in the editor.
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
    },
    // Watch for changes in context_length to trigger save and reload of story before 
    // applying new context window. This is to ensure that content isn't lost when changing 
    // context window size and that the story editor properly reflects the new context window.
    async context_length(new_val, old_val) {
      // Prevent unnecessary triggers
      if (new_val === old_val) return;

      while (this.isLoading) {
        // Wait for any active requests to finish before handling context length change
        await new Promise(resolve => setTimeout(resolve, 500));
      }
      try {
        const approx = 4;
        const old_max_chars = old_val * approx;
        const old_start = Math.max(0, this.content.length - old_max_chars);

        // Sync using old start
        if (this.story_editor_content !== this.content.slice(old_start)) {
          this.content = this.content.slice(0, old_start) + this.story_editor_content;
        }

        // Save and reload story to apply new context window and update 
        // story editor content based on new display start point
        if (this.filename.trim() !== '') {
          await this.saveStory(false); // Don't sync to new start before saving
          await this.loadStory();
          this.status_message = 'Story saved and reloaded with new context window.';
        }
        else {
          this.status_message = 'Limit set successfully.';
        }
      } catch (err) {
        this.status_message = 'Error handling context resize: ' + (err.message || err);
      }
    }
  }
}
</script>

<template>
  <div class="tab-header">
  <button 
    :class="{ active: active_tab === 'instructions' }"
    @click="setActiveTab('instructions')"
  >
    Instructions
  </button>

  <button 
    :class="{ active: active_tab === 'editor' }"
    @click="setActiveTab('editor')"
  >
    Editor
  </button>

  <button 
    :class="{ active: active_tab === 'summary' }"
    @click="setActiveTab('summary')"
  >
    Summary
  </button>

  <button 
    :class="{ active: active_tab === 'essentials' }"
    @click="setActiveTab('essentials')"
  >
    Essentials
  </button>

  <button 
    :class="{ active: active_tab === 'context_cards' }"
    @click="setActiveTab('context_cards')"
  >
    Context Cards
  </button>

  <button 
    :class="{ active: active_tab === 'sent_context' }"
    @click="setActiveTab('sent_context')"
  >
    Sent Context
  </button>
  </div>

  <div class="tab-content">
    <div class="container" v-show="active_tab === 'instructions'">
      <h2>Storytelling Instructions</h2>
      <textarea 
      v-model="instructions" 
      rows="12" 
      cols="80" 
      placeholder="Additional story generation instructions can be added here.">
      </textarea>
      <div class="tab-footer-space"></div>
    </div>

    <div class="container" v-show="active_tab === 'editor'">
      <h2>Story Editor</h2>
      <textarea 
      ref="storyBox"
      v-model="story_editor_content" 
      rows="12" 
      cols="80" 
      placeholder="Paste or write story text here."></textarea>
      <div>
        <button @click="continueStory" :disabled="isLoading">Continue Story</button>
      </div>
    </div>

    <div class="container" v-show="active_tab === 'summary'">
      <h2>Story Summary</h2>
      <textarea v-model="summary" 
      rows="12" 
      cols="80" 
      placeholder="Summary will appear here. Summary will be used as context in story generation.">
      </textarea>
      <div class="tab-footer-space"></div>
    </div>

    <div class="container" v-show="active_tab === 'essentials'">
      <h2>Plot Essentials</h2>
      <textarea v-model="plot_essentials" 
      rows="12" 
      cols="80" 
      placeholder="Key plot points, character details, or world-building elements. This will be used as context in story generation.">
      </textarea>
      <div class="tab-footer-space"></div>
    </div>

    <div class="container" v-show="active_tab === 'context_cards'">
      <ContextCards ref="contextCards" />
    </div>

    <div class="container" v-show="active_tab === 'sent_context'">
      <h2>Sent Context</h2>
      <textarea v-model="sent_context" 
      rows="12" 
      cols="80" 
      placeholder="Context sent to story generation will show up here."
      readonly>
      </textarea>
      <div class="tab-footer-space"></div>
    </div>
  </div>
  <p class="status">{{ status_message}}</p>
  <div class="container">
    <h2>Story File Name</h2>
    <input v-model="filename" placeholder="Enter file name" />
    <button @click="loadStory" :disabled="isLoading">Load Story</button>
    <button @click="saveStory" :disabled="isLoading">Save Story</button>
  </div>
</template>

<style scoped>
.status {
  height: 30px;
  background: #08060d;
  padding: 5px;
  margin-bottom: 15px;
}

.tab-content {
  position: relative;
  min-height: 285px;
  padding: 10px;
  padding-top: 10px;
}

.tab-header button {
  background: #1a1a2e;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 3px;
  cursor: pointer;
  font-weight: bold;
  margin: 0px;
}
.tab-header button:hover {
  background: #aa3bff;
}
.tab-header button.active {
  background: #9a2bef;
  color: white;
  font-weight: bold;
}

/* Reserve space for Continue button */
.tab-footer-space {
  height: 42px;
}
</style>