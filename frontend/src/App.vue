<script>
export default {
  data() {
    return {
      content: '',
      filename: 'filename.txt',
      status: ''
    }
  },
  methods: {
    async loadFile() {
      try {
        const res = await fetch(`http://localhost:5000/api/load?filename=${this.filename}`)
        const data = await res.json()
        this.content = data.content
        this.status = 'File loaded successfully'
      } catch (err) {
        this.status = 'Error loading file'
      }
    },
    async saveFile() {
      try {
        const res = await fetch('http://localhost:5000/api/save', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            filename: this.filename,
            content: this.content
          })
        })
        const data = await res.json()
        this.status = data.message
      } catch (err) {
        this.status = 'Error saving file'
      }
    }
  }
}
</script>

<template>
  <div class="container">
    <h1>Simple Text Editor</h1>
    <textarea v-model="content" rows="20" cols="80"></textarea>

    <div class="buttons">
      <input v-model="filename" placeholder="filename.txt" />
      <button @click="loadFile">Load</button>
      <button @click="saveFile">Save</button>
    </div>

    <p>{{ status }}</p>
  </div>
</template>

<style>
.container {
  font-family: Arial;
  padding: 20px;
}
textarea {
  width: 100%;
  margin-bottom: 10px;
}
.buttons {
  margin-bottom: 10px;
}
button {
  margin-left: 5px;
}
</style>