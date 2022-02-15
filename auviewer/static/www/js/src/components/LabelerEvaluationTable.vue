<template>
  <b-table small striped hover v-bind:items="labelerInformation" :fields="fieldFormatting"></b-table>
</template>

<script lang="ts">
import { Component, Prop, Vue } from 'vue-property-decorator';
import { LabelerEvaluativeStats } from '@/types';


@Component
export default class LabelerEvaluationTable extends Vue {
  @Prop() labelerInformation!: Array<LabelerEvaluativeStats>;

  fieldFormatting: Array<Object> = [
          { key: 'labeler',
            sortable: false,
            isRowHeader: true},
          {
            key: 'polarity',
            sortable: false},
          {
            key: 'coverage',
            sortable: true,},
          {
            key: 'overlaps',
            sortable: true,},
          {
            key: 'conflicts',
            sortable: true,},
          {
            key: 'experimental_accuracy',
            sortable: true,},
    ];
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped lang="scss">
h3 {
  margin: 40px 0 0;
}
ul {
  list-style-type: nonefrom '@/ty
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
