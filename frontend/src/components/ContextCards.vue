<script>
import ContextCard from './ContextCard.vue';

export default {
  data() {
    return {
      cards: [],
      name: '',
      content: '',
      keywords: ''
    }
  },
  components: { ContextCard },
  methods: {
    // Add card with id, name, content, and keywords (comma separated)
    addCard() {
      this.cards.push({
        id: Date.now(),
        name: this.name,
        content: this.content,
        keywords: this.keywords.split(',').map(k => k.trim())
      });
      this.name = '';
      this.content = '';
      this.keywords = '';
    },
    // Get matching context cards based on keywords in recent story content
    getMatchingContextCards(text) {
      const lower_text = text.toLowerCase();
      const matching = [];

      for (const card of this.cards) {
        // Check if any keyword is in the text
        for (const keyword of card.keywords) {
          if (lower_text.includes(keyword.trim().toLowerCase())) {
            matching.push(card.content);
            break; // Only add card once even if multiple keywords match
          }
        }

        // To avoid adding too much context, stop if we have 5 matching cards
        if (matching.length >= 5) {
          break;
        }
      }

      if (matching.length === 0) return '';
      
      // Format matching cards into a string to be included in the prompt
      let cardText = '';
      for (const card of matching) {
        cardText += '- ' + card + '\n';
      }
      return cardText;
    },
    removeCard(id) {
      this.cards = this.cards.filter(card => card.id !== id);
    }
  }
}
</script>

<template>
  <div class="context-cards">
    <h2>Add New Card</h2>
    <div class="context-card">
        <h4>Name</h4>
        <input type="text" v-model="name" />
        <h4>Content</h4>
        <textarea v-model="content" />
        <h4>Keywords (comma-separated)</h4>
        <input type="text" v-model="keywords" />

        <button @click="addCard">Add Card</button>
    </div>
    <div class="context-card">
    <h3>Existing Cards</h3>
    <h4>
      Cards with keywords matching recent story content will be included as context in story generation.
      Cards will automatically be saved when edited.
    </h4>
    </div>
    <ContextCard
      v-for="card in cards"
      :key="card.id"
      :card="card"
      @remove="removeCard(card.id)"
    />
  </div>
</template>

<style scoped>
.context-cards {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.context-cards > div {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.context-card {
  border: 1px solid #aa3bff;
  border-radius: 5px;
  padding: 5px;
  background: #1a1a2e;
  color: #fff;
}
.context-card h4 {
  margin: 3px 0 3px;
}
.context-card textarea {
  min-height: 120px;
}
.context-card button {
  margin-bottom: 10px;
}
</style>