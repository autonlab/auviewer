<template>
  <div>
    <b-table striped hover :items="items"></b-table>
  </div>
</template>

<script>
  export default {
    props: {
        averageFeatureStats
    },

    data() {
      return {
        items: this.averageFeatureStats
      }
    }
  }
</script>