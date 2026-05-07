<script>
import ContextCards from './ContextCards.vue';

// Approximate to 4 characters per token for simple tokens-to-chars conversion.
// Real token amount may vary based on language and content.
const APPROX_CHARS_PER_TOKEN = 4;

export default {
  name: 'StoryEditor',
  components: {
    ContextCards
  },
  emits: ['loading-changed'],
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
      // Random story ID for storing memories in database.
      // Uses 32 bits (additional checks to prevent collision
      // may be required if used on a larger scale).
      story_id: crypto.getRandomValues(new Uint32Array(1))[0],
      // Components
      instructions: '', // Special instructions for the AI to use
      content: '',
      summary: '',
      story_essentials: '',
      sent_context: '', // Full context sent for story generation
      status_message: '',
      // Values
      filename: '',
      active_tab: 'editor',
      active_requests: 0,
      memory_cursor: 0,
      summary_cursor: 0,
      // Recent story content (i.e. content within the context window) 
      // is displayed in the editor
      story_editor_content: '',
    }
  },
  methods: {
    setActiveTab(tab) {
      this.active_tab = tab;
    },
    // Extract past content between cursor and beginning of recent content,
    // i.e. content that has fallen out of the context window. Overlap with recent  
    // story can be added and is used in summarization to avoid losing context 
    // between summary actions.
    extractPastContent(cursor, overlap = 0) {
      const recent_story_window = this.context_length * APPROX_CHARS_PER_TOKEN;

      let cutoff_index = this.content.length - recent_story_window;

      // Overlap with recent content (default: no overlap)
      cutoff_index += overlap;

      // Ensure cutoff is not negative (e.g. when content length is less than context window allows)
      cutoff_index = Math.max(0, cutoff_index)

      // Past content window is between cursor and cutoff index
      const past_content = this.content.slice(cursor, cutoff_index);

      return {past_content, cutoff_index};
    },
    // Syncronize content with story editor, e.g. to include user edits before saving
    syncContentWithEditor() {
      const start = this.displayStart;

      // Avoid unnecessary assignment if contents match
      if (this.story_editor_content !== this.content.slice(start)) {
        this.content = this.content.slice(0, start) + this.story_editor_content;
      }
    },
    // Main function to continue the story with backend API
    async continueStory() {
      const recent_story = this.story_editor_content

      // Basic validation to ensure there's enough content to continue from
      if (!recent_story || recent_story.trim().length < 20) {
        this.status_message = 'Error: Please enter enough story content to continue.';
        return;
      }
      try {
        this.active_requests++;
        this.status_message = 'Continuing story...';

        // Sync content with editor for any user edits before continuing story
        this.syncContentWithEditor();

        // Get relevant context cards based on found keywords in recent story
        const context_cards = this.$refs.contextCards.getMatchingContextCards(recent_story);

        // Use POST for continue action
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
            story_essentials: this.story_essentials,
            context_cards: context_cards,
            recent_story: recent_story,
            top_p: this.top_p || 0.9,
            temperature: this.temperature || 0.8,
            max_tokens: this.max_tokens || 200
          })
        });
        const data = await res.json();

        if (data.error) {
          this.status_message = 'Backend error continuing story: ' + data.error;
          return;
        }

        const continued_content = data.continued_content || '';

        // Append continued content to story with proper spacing (\n\n + new content)
        // Count existing newlines at end of text
        const matching_count = recent_story.match(/\n*$/)[0].length;

        // Add 0-2 newlines based on existing count. This ensures \n\n in case of
        // 0-2 existing newlines but does not remove newlines above the limit.
        const newline_count = Math.max(0, 2 - matching_count);

        this.content += '\n'.repeat(newline_count) + continued_content;
        
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
        // Automatically summarize (only happens if enough content is past the recent story context window)
        await this.summarizeStory();

        // Automatically turn past context into a memory and save the story if filename is set
        if (this.filename && this.filename.trim() !== '') {
          await this.createMemory();
          await this.saveStory();
        } else {
          this.status_message = 'Please set filename to save and memorize story.'
        }
      }catch (err) {
        this.status_message = 'Error continuing story: ' + (err.message || err);
      } finally {
        this.active_requests--;
      }
    },
    // Function to summarize the story with backend API
    async summarizeStory() {
      // Minimum past content length (in characters) to create a new summary.
      // default: 4000
      const minimum_length_chars = 4000;
      // Use half of minimum length as overlap with recent story.
      // This prevents context that falls out of recent content window
      // from being lost between summary actions.
      const overlap = minimum_length_chars / 2;

      const {past_content, cutoff_index} = 
              this.extractPastContent(this.summary_cursor, minimum_length_chars, overlap);

      // Return if there is not enough content to summarize
      if (past_content.length < minimum_length_chars) {
        return;
      }
      try {
        this.active_requests++;
        this.status_message = 'Summarizing story, please wait...'

        const full_context = 'Current Summary:\n' + this.summary + 
                             '\n\nNew Story Content:\n' + past_content;
        
        // Use POST for summary action
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
          this.status_message = 'Backend error summarizing story: ' + data.error;
          return;
        }
        if (!data.summary || data.summary.trim() === '') {
          this.status_message = 'Error: Summary action returned empty content.';
          return;
        }

        this.summary = data.summary;
        this.status_message = '';
        
        // Move summary cursor forward to cutoff index for next summary action
        this.summary_cursor = cutoff_index;

        if (this.show_token_use && data.tokens_total) {
          this.status_message = 'Total tokens used for summary action: ' + data.tokens_total
        }
      } catch (err) {
        this.status_message = 'Error summarizing story: ' + (err.message || err);
      } finally {
        this.active_requests--;
      }
    },
    // Function to create a memory with backend API
    async createMemory() {
      // Minimum past content length to create a new memory.
      // default: 7000
      const minimum_length_chars = 7000;

      // Use past story content for new memory (without overlap with recent story)
      const {past_content, cutoff_index} = this.extractPastContent(this.memory_cursor, 7000);

      // Return if there is not enough content to memorize
      if (past_content.length < minimum_length_chars) {
        return;
      }
      try {
        this.active_requests++;
        this.status_message = 'Creating a new memory, please wait...'
        
        // Use POST for memory action
        const res = await fetch('/api/memorize', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            story_id: this.story_id,
            content: 'Past Story Content:\n' + past_content,
            model: this.mem_model,
            local: this.use_local
          })
        });
        const data = await res.json();

        if (data.error) {
          this.status_message = 'Backend error creating memory: ' + data.error;
          return;
        }
        this.status_message = '';

        // Move memory cursor forward to cutoff index for next memory creation
        this.memory_cursor = cutoff_index;

        if (this.show_token_use && data.tokens_total) {
          this.status_message = 'Total tokens used for memory action: ' + data.tokens_total
        }
      } catch (err) {
        this.status_message = 'Error creating memory: ' + (err.message || err);
      } finally {
        this.active_requests--;
      }
    },
    // Function to save the story to backend API
    async saveStory(sync = true) {
      if (!this.filename || this.filename.trim() === '') {
        this.status_message = 'Please enter a filename to save the story.';
        return;
      }
      try {
        this.active_requests++;
        // Only change status message if this is the only active request to
        // avoid confusion with other actions.
        if (this.active_requests === 1) {
          this.status_message = 'Saving story...';
        }

        if (sync) {
          // Sync content with story editor before saving
          this.syncContentWithEditor();
        }

        // Ensure filename ends with .json
        const filename = this.filename.endsWith('.json') ? this.filename : this.filename + '.json';
        
        const context_cards = this.$refs.contextCards.cards || [];

        // Use POST to save story
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
            story_essentials: this.story_essentials,
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
        if (this.active_requests === 1 && data.message) {
          this.status_message = 'Success: ' + data.message;
        }
      } catch (err) {
        this.status_message = 'Error saving story: ' + (err.message || err);
      } finally {
        this.active_requests--;
      }
    },
    // Function to load the story from backend API.
    // If file is not found or filename is empty/invalid, creates a new story instead.
    async loadStory() {
      try {
        this.active_requests++;
        this.status_message = 'Loading story...';

        let data = {};
      
        // Fetch file content if filename is set
        if (this.filename && this.filename.trim() !== '') {
          // Ensure filename ends with .json
          const filename = this.filename.endsWith('.json') ? this.filename : this.filename + '.json';

          // Use GET to load story (default method for fetch).
          // Encode filename to prevent issues with URL special characters such as '&' and '='.
          const res = await fetch('/api/load?filename=' + encodeURIComponent(filename));
          data = await res.json();
        }

        // Set values, default to new story
        this.story_id = data.story_id || crypto.getRandomValues(new Uint32Array(1))[0];
        this.instructions = data.instructions || '';
        this.content = data.content || '';
        this.summary = data.summary || '';
        this.story_essentials = data.story_essentials || '';
        this.memory_cursor = data.memory_cursor || 0;
        this.summary_cursor = data.summary_cursor || 0;
        this.$refs.contextCards.cards = data.context_cards || [];

        if (data.error) {
          this.status_message = 'Backend: ' + data.error + ' New story created.';
          return;
        }
        else if (!this.filename || this.filename.trim() === '') {
          this.status_message = 'Filename not set. New story created.'
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
    // requests which could cause issues. Also disables 'Set Limit' button in settings 
    // menu when loading.
    isLoading() {
      return this.active_requests > 0;
    },
    // Calculate where to start displaying content in editor based on context length.
    // This prevents editing already memorized or summarized content and makes textEditor
    // more responsive by not rendering the entire story in the editor.
    displayStart() {
      const max_chars = this.context_length * APPROX_CHARS_PER_TOKEN;

      return Math.max(0, this.content.length - max_chars);
    }
  },
  watch: {
    // Update story_editor_content when content changes, e.g. when continuing or loading story
    content() {
      const start = this.displayStart;
      this.story_editor_content = this.content.slice(start);
    },
    // Emit loading change events so parent can disable settings controls when requests are active
    isLoading(value) {
      this.$emit('loading-changed', value);
    },
    // Watch for changes in context_length to ensure that content isn't lost when changing 
    // context window size and that the story editor properly reflects the new context window.
    context_length(new_val, old_val) {
      // Prevent unnecessary triggers
      if (new_val === old_val) return;

      try {
        const old_max_chars = old_val * APPROX_CHARS_PER_TOKEN;
        const old_start = Math.max(0, this.content.length - old_max_chars);

        // Sync content with editor using old start to avoid losing user edits
        if (this.story_editor_content !== this.content.slice(old_start)) {
          this.content = this.content.slice(0, old_start) + this.story_editor_content;
        }

        // Sync editor to display story content with new context length
        const new_start = this.displayStart;
        this.story_editor_content = this.content.slice(new_start);

        this.status_message = 'Limit set. Editor updated with new token limit.';
      } catch (err) {
        this.status_message = 'Error setting token limit: ' + (err.message || err);
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
      <h2>Story Essentials</h2>
      <textarea v-model="story_essentials" 
      rows="12" 
      cols="80" 
      placeholder="Key plot points, character details, or world-building elements. This will always be used as context in story generation.">
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
      placeholder="Context sent to story generation will appear here."
      readonly>
      </textarea>
      <div class="tab-footer-space"></div>
    </div>
  </div>
  <p class="status">{{ status_message }}</p>
  <div class="container">
    <h2>Story File Name</h2>
    <input v-model="filename" placeholder="Enter filename" />
    <button @click="loadStory" :disabled="isLoading">Load Story</button>
    <button @click="saveStory" :disabled="isLoading">Save Story</button>
  </div>
</template>

<style scoped>
.status {
  height: 30px;
  background: #0f0f1e;
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