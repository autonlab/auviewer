<template>
    <div>
        <b-form-group class="add-style">
            <label style="font-weight: 500">{{fieldInfo.name}}</label>
            <br/>
            <b-form-radio-group
              v-if="fieldInfo && fieldInfo.type === 'categorical'"
              v-model="inputValue"
              :options="fieldInfo.options"
              :name="fieldInfo.id"
              button-variant="outline-primary"
              buttons
              :required="fieldInfo.required"></b-form-radio-group>
            <b-form-textarea
              v-else-if="fieldInfo && fieldInfo.type === 'text'"
              v-model="inputValue"
              :name="fieldInfo.id"
              :required="fieldInfo.required"
              ></b-form-textarea>
        </b-form-group>
    </div>
</template>

<script lang="ts">
import { Component, Vue, Watch, Prop } from 'vue-property-decorator';
import { AnnotationField, AnnotationFormInput, AnnotationFieldType, AnnotationSelectionType, CategoryOption } from '@/types';
import $ from 'jquery';

@Component({
    components: {}
})
export default class AnnotationFieldComponent extends Vue {
    /* DATA */
    // public type: AnnotationFieldType;
    // public content: Array<AnnotationFieldType>;
    @Prop() readonly fieldInfo: AnnotationFormInput | undefined;
    @Prop([String, Number]) readonly value: string | number | undefined;

    get inputValue() {
        return this.value;
    }
    set inputValue(val: any) {
        this.$emit('input', val);
    }

    /* LIFECYCLE HOOKS */
    mounted() {}


    get projectID(): number {
        const curPath: string = window.location.href;
        let el = $(this.$el);
        let project_id: number = parseInt(curPath.split("=")[1][0]);
        return project_id
    }


}
</script>

<style scoped>
fieldset {
    /* added this to align fields properly */
    padding: unset;
}
</style>