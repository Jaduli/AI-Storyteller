<script>
import StoryEditor from './components/StoryEditor.vue';

export default {
  components: { StoryEditor },
  data() {
    return {
      model: ''
    }
  }
}
</script>

<template>
  <div>
    <h1>AI Storyteller</h1>
    <div id="model-input">
      <input
        type="text"
        v-model="model"
        placeholder="llama-3.1-8b-instant"
      />
    </div>
    <StoryEditor :model="model" />
  </div>
</template>

<style>

</style>