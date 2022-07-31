<template>
  <div ref="dygraph-mount-point">

  </div>
</template>

<script lang="ts">
import { Component, Prop, Vue } from 'vue-property-decorator';
import { dygraphs } from 'dygraphs';

@Component
export default class DygraphWrapper extends Vue {
  @Prop() data!: dygraphs.Data;

  dg: any | null = null;

  mounted() {
    console.log(this.$refs['dygraph-mount-point'])
    this._instantiate()
  }

  _instantiate() {
    // this.dg = new dygraphs.Dygraph(
      // this.$refs['dygraph-mount-point'],
      // this.$props.data,
      // colors: ['#5253FF'],
		// dateWindow: timeWindow,
      // drawPoints: true,
      // labels: [series.labels[0], series.labels[3]],
      // legend: 'follow',
      // ylabel: this.getSeriesToRenderY(),
      // valueRange: yAxisRange//[yAxisRange[0], 160]
    // )
  }

}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped lang="scss">
h3 {
  margin: 40px 0 0;
}
ul {
  list-style-type: none;
  padding: 0;
}
li {
  display: inline-block;
  margin: 0 10px;
}
a {
  color: #42b983;
}
</style>
