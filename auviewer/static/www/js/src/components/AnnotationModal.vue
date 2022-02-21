<template>
<div v-observe-visibility="onVisible">
  <b-form  @submit="onSubmit" >
      <b-form-group
        id="input-group-1"
        class="add-style"
      >
      <label style="font-weight: 500">Annotation ID</label>
        <b-form-input
          id="input-1"
          v-model="annotationID"
          readonly
        ></b-form-input>
      </b-form-group>
      <b-form-group
        id="input-group-2"
        class="add-style"
      >
      <label style="font-weight: 500">File</label>
        <b-form-input
          id="input-2"
          v-model="annotationFile"
          readonly
        ></b-form-input>
      </b-form-group>
      <b-form-group
        id="input-group-3"
        class="add-style"
      >
      <label style="font-weight: 500">Series</label>
        <b-form-input
          id="input-3"
          v-model="annotationSeries"
          readonly
        ></b-form-input>
      </b-form-group>
      <div v-for="(annotationFieldInput, index) in annotationFormInputs"
          :key="index"
          >
          <annotation-field-component
            v-model="annotationResult[annotationFieldInput.id]"
            :field-info="annotationFieldInput">
          </annotation-field-component>
      </div>
      <b-form-row class="mb-2">
        <div class="col">
        <b-form-group
          id="input-group-4"
          class="add-style"
          >
      <label style="font-weight: 500">Start time</label>
        <b-input-group>
          <b-form-input
            id="input-4"
            v-model="startDateText"
            type="date"
            ></b-form-input>
        </b-input-group>
        </b-form-group>
        <b-form-group
          id="input-group-6"
          >
        <b-input-group>
          <b-form-input
            id="input-6"
            v-model="startTimeText"
            type="time"
            step=".001"
            ></b-form-input>
        </b-input-group>
        </b-form-group>

        </div>
        <div class="col">

        <b-form-group
          id="input-group-5"
          class="add-style"
          >
      <label style="font-weight: 500">End time</label>
        <b-input-group>
          <b-form-input
            id="input-5"
            v-model="endDateText"
            type="date"
            ></b-form-input>
        </b-input-group>
        </b-form-group>
        <b-form-group
          id="input-group-7"
          >
        <b-input-group>
          <b-form-input
            id="input-7"
            v-model="endTimeText"
            type="time"
            step=".001"
            ></b-form-input>
        </b-input-group>
        </b-form-group>
        </div>
      </b-form-row>
      <b-form-row>
        <b-button class="mr-auto" @click="onDelete" type="button" variant="danger">Delete</b-button>
    
        <b-button type="submit" variant="primary">Submit</b-button>
        <b-button @click="onCancel" type="button" data-dismiss="modal" variant="secondary">Cancel</b-button>
				<!-- <button type="button" class="btn btn-danger mr-auto deleteButton">Delete</button>
				<button type="button" class="btn btn-secondary cancelButton" data-dismiss="modal">Cancel</button>
				<button type="button" class="btn btn-primary saveButton">Save</button> -->
      </b-form-row>
  </b-form>
<!-- <q-form
  @submit="onSubmit"
  class="q-pa-xl"
  >
  <div class="row justify-evenly">
    <q-input outlined class="q-gutter-sm col" color="primary" label-color="primary" v-model="form.annotation_id" label="Annotation ID" stack-label readonly />
    <q-input outlined class="q-gutter-sm col" color="primary" label-color="primary" v-model="form.annotation_file" label="File" stack-label readonly />
    <q-input outlined class="q-gutter-sm col" color="primary" label-color="primary" v-model="form.annotation_series" label="Series" stack-label readonly />
  </div>

  <div v-for="(annotationFieldInput, index) in categoricalButtonInputs"
       :key="index"
       >
        <q-btn-toggle
          v-model="annotationResult[annotationFieldInput.id]"
          spread
          no-caps
          toggle-color="primary"
          color="white"
          text-color="primary"
          :options="annotationFieldInput.options"
          />
  </div>
  <div class="row justify-evenly">
    <div class="col-5">
      <q-input color="primary" label-color="primary" readonly v-model="startDateText" label="Start Time">
        <template v-slot:append>
          <q-icon name="event" />
        </template>
      </q-input>
      <q-input color="primary" label-color="primary" readonly v-model="startTimeText" label="Start Time">
        <template v-slot:append>
          <q-icon name="schedule" />
        </template>
      </q-input>
    </div>
    <div class="col-5">
      <q-input color="primary" label-color="primary" readonly v-model="endDateText" label="End Time">
        <template v-slot:append>
          <q-icon name="event" />
        </template>
      </q-input>
      <q-input color="primary" label-color="primary" readonly v-model="endTimeText" label="End Time">
        <template v-slot:append>
          <q-icon name="schedule"/>
        </template>
      </q-input>
    </div>
  </div>
  <div class="row justify-evenly">
    <q-btn class="q-gutter-sm col-5" label="Submit" type="submit" color="primary"/>
    <q-btn class="q-gutter-sm col-5" label="Reset" type="reset" color="primary" />
  </div>

   <div 
       v-for="categoricalRadioField in categoricalRadioFields"
       :key="categoricalRadioField.id"
       class="q-gutter-y-md">
        <q-radio
          spread
          no-caps
          toggle-color="primary"
          color="white"
          text-color="primary"
          :options="categoricalRadioFields"
          />
  </div> 
</q-form> -->
</div>
</template>

<script lang="ts">
// import * as bootstrap from 'bootstrap';
// import * as toastr from 'toastr';
// import $ from 'jquery';
import { Annotation, AnnotationField, AnnotationFormInput, AnnotationFieldType, AnnotationSelectionType, CategoryOption } from '@/types';
import AnnotationFieldComponent from '@/components/AnnotationFieldComponent.vue';
import { Component, Vue, Watch } from 'vue-property-decorator';
import  Fetcher from '@/utils/fetcher';

//@ts-ignore
@Component({
  components: {
    AnnotationFieldComponent,
  }
})
export default class AnnotationModal extends Vue {
    /* DATA */
    public annotationResult: { [key:string]: string } = {};
    public annotationFormInputs: Array<AnnotationFormInput> = new Array<AnnotationFormInput>();
    public annotationID: number = -1;
    public inAnnotation: boolean = false;
    public annotationFile?: string = '';
    public annotationSeries?: string = '';
    public startDateText?: string = '';
    public startTimeText?: string = '';
    public endDateText?: string = '';
    public endTimeText?: string = '';
    private start?: Date;
    private end?: Date;
    /* LIFECYCLE HOOKS */
    mounted() {
      // this.populateFormModel(this.annotationFields);
      //@ts-ignore
      toastr.options.timeOut = 6000;
      //@ts-ignore
      toastr.options.positionClass = "toast-bottom-center";
      //@ts-ignore
      toastr.options.showMethod = 'slideDown';
      //@ts-ignore
      toastr.options.hideMethod = 'slideUp';
      //@ts-ignore
      toastr.options.preventDuplicates = true;
    }

    getHTML5DateTimeStringsFromDate(d: Date) {
      // @ts-ignore Date string
      let ds = d.getFullYear().toString() + '-' + (d.getMonth()+1).toString().padStart(2, '0') + '-' + d.getDate().toString().padStart(2, '0');

      // @ts-ignore Time string
      let tstr: any = d.getHours().toString().padStart(2, '0') + ':' + d.getMinutes().toString().padStart(2, '0') + ':' + d.getSeconds().toString().padStart(2, '0') + '.' + d.getMilliseconds().toString().padStart(3, 0);

      // Return them in array
      return [ds, tstr];
    }

    onVisible(isVisible: any, entry: any) {
      if (isVisible) {
        this.clearFormValues();
        // this.inAnnotation = true;
        if (this.annotationID < 0) {
          console.log(this.getAnnotationFields());
          this.populateFormModel(this.getAnnotationFields());
        }
        // @ts-ignore
        // let curAnnotationIdx = globalStateManager.currentProject.assignmentsManager.currentTargetAssignmentSet.currentTargetAssignmentIndex;
        // let curAnnotation = globalStateManager.currentAnnotation;
        // @ts-ignore
        let curAnnotation = globalStateManager.currentAnnotation;
        // let curAnnotation = globalStateManager.currentProject.assignmentsManager.currentTargetAssignmentSet.members[curAnnotationIdx];
        this.annotationID = curAnnotation.id;
        this.annotationFile = curAnnotation.filename;
        this.annotationSeries = curAnnotation.series;
        // this.start = new Date(curAnnotation.begin * 1000);
        // this.end = new Date(curAnnotation.end * 1000);
        this.start = curAnnotation.getStartDate();
        this.end = curAnnotation.getEndDate();
        if (!this.start || !this.end) {
          return;
        }
        let [startDate, startTime] = this.getHTML5DateTimeStringsFromDate(this.start);
        let [endDate, endTime] = this.getHTML5DateTimeStringsFromDate(this.end);
        this.startDateText = startDate;
        this.startTimeText = startTime;
        this.endDateText = endDate;
        this.endTimeText = endTime;
        this.populateFormValues(curAnnotation);
      }
      else {
        // //@ts-ignore
        // globalStateManager.currentFile.triggerRedraw();
        // if (this.inAnnotation) {
        this.onCancel(null);
        // }
        // this.clearFormValues();
      }
    }

    constructLabelFromForm() {
      return JSON.stringify(this.annotationResult);
    }

    onSubmit(event: any) {
      event.preventDefault();
      // this.inAnnotation = false;
      //@ts-ignore
      // globalStateManager.currentAnnotation.save();
      if (!(this.annotationID && this.annotationFile && this.annotationSeries && this.start && this.end)) {
        return;
      }

      let formedLabel = this.constructLabelFromForm();

      // populate annotation from form and annotationresult
      let populatedAnnotation: Annotation = {
        project_id: this.projectID,
        //@ts-ignore
        file_id: globalStateManager.currentFile.id,
        left: Math.floor(this.start.getTime() / 1000),
        right: Math.floor(this.end.getTime() / 1000),
        series_id: this.annotationSeries,
        label: formedLabel,
      };
      this.createOrUpdate(populatedAnnotation);
      // this.clearFormValues();
      // return true;
    }

    onCancel(event: any) {
      if (event) {
        event.preventDefault();
      }
      // this.inAnnotation = false;
      this.hideModal();
      //@ts-ignore
      globalStateManager.currentAnnotation && globalStateManager.currentAnnotation.cancel();
      // //@ts-ignore
      // toastr.warning("Canceled annotation");
    }

    onDelete(event: any) {
      event.preventDefault();
      // this.inAnnotation = false;
      // //@ts-ignore
      // globalStateManager.currentAnnotation.delete();

      //@ts-ignore
      let t = globalStateManager.currentAnnotation;
      if (t.type !== 'annotation') {
        //@ts-ignore
        toastr.warning("You may only delete a pre-existing annotation, and this isn't one.");
        return;
      }
        
      let self = this;
      //@ts-ignore
      globalStateManager.currentAnnotation.delete(function (data) {
        if (data.hasOwnProperty('success') && data['success'] === true) {
          self.clearFormValues();
          //@ts-ignore
          toastr.success("Successfully deleted.");
          //@ts-ignore
          globalStateManager.currentAnnotation.parentSet.deleteMember(globalStateManager.currentAnnotation);
          //@ts-ignore
          globalStateManager.currentAnnotation.hideDialog();
        } else {
          //@ts-ignore
          toastr.warning("There was an error while trying to delete this annotation.");
        }
      });
    }

    @Watch('annotationResult')
    onAnnotationChange(oldVal: any, newVal: any) {
      console.log(oldVal, newVal);
    }

    populateFormModel(annotationfields: Array<AnnotationField>) {
      // this.annotationResult = {};
      for (let annotationField of annotationfields) {
        if (annotationField.type == AnnotationFieldType.Categorical) {
          if (! annotationField.classes) {
            continue;
          }
          Vue.set(this.annotationResult, annotationField.id, "");
          // button selection or radio selection
          let currentCategories = new Array<CategoryOption>();
          for (let category of annotationField.classes) {
            currentCategories.push({
              text: category,
              value: category 
            } as CategoryOption);
          }
          this.annotationFormInputs.push({
            id: annotationField.id,
            name: annotationField.label,
            type: annotationField.type,
            selection_type: annotationField.selection_type,
            options: currentCategories
          } as AnnotationFormInput);
        } else if (annotationField.type == AnnotationFieldType.Text) {
          Vue.set(this.annotationResult, annotationField.id, "");
          this.annotationFormInputs.push({
            id: annotationField.id,
            name: annotationField.label,
            type: annotationField.type
          } as AnnotationFormInput);
        } else if (annotationField.type == AnnotationFieldType.Numeric) {
          Vue.set(this.annotationResult, annotationField.id, "");
          this.annotationFormInputs.push({
            id: annotationField.id,
            name: annotationField.label,
            type: annotationField.type
          } as AnnotationFormInput);
        }
      }
    }

    populateFormValues(annotation: Annotation) {
      if (!annotation['label']) {
        return;
      }
      if ((typeof annotation['label']) === 'string') {
        annotation['label'] = JSON.parse(annotation['label']);
      }
      for (const [field_id, value] of Object.entries(annotation['label'])) {
        if (field_id in this.annotationResult) {
          //@ts-ignore
          this.annotationResult[field_id] = value;
          // Vue.set(this.annotationResult, field_id, value);
        }
      }
    }

    clearFormValues() {
      for (const [field_id, value] of Object.entries(this.annotationResult)) {
        this.annotationResult[field_id] = "";
      }

    }

    createOrUpdate(annotation: Annotation) {
      //@ts-ignore
      let gsm = globalStateManager;

      //@ts-ignore
      if (globalStateManager.currentAnnotation.type === 'unsaved_annotation')
      {
        let self = this;
        Fetcher.createAnnotation(annotation.project_id, annotation.file_id, annotation.left, annotation.right, annotation.series_id, annotation.label, annotation.pattern_id, (data: any) => {
          if (data.hasOwnProperty('success') && data.success === true) {
            //@ts-ignore
            let gsm = globalStateManager;

            let t = gsm.currentAnnotation;
            // $('#annotationModal').modal('toggle');
            self.hideModal();

            // Update type to 'annotation'
            t.type = 'annotation';
            t.id = data.id;

            // If this was an annotation of a pattern, report it to the
            // assignments manager (in case the pattern is an assignment).
            if (t.pattern_id != null) {
              gsm.currentProject.assignmentsManager.annotationCreatedForPattern(t.related.parentSet.id, t.related.id, this);
            }
            //@ts-ignore
            toastr.success('Successfully created annotation ' + data.id.toString());
            //update currentAnnotation state so local data reflects backend data
            gsm.currentAnnotation.begin = annotation.left;
            gsm.currentAnnotation.end = annotation.right;
            gsm.currentAnnotation.label = annotation.label;
          } else {
            //@ts-ignore
            toastr.warning('Something went wrong, failed to create annotation');
          }

          //@ts-ignore
          globalStateManager.currentFile.triggerRedraw();
        });

      }
      //@ts-ignore
      else if (globalStateManager.currentAnnotation.type === 'annotation') 
      {
        let self = this;
        //@ts-ignore
        Fetcher.updateAnnotation(this.annotationID, globalStateManager.currentFile.parentProject.id, globalStateManager.currentFile.id, annotation.left, annotation.right, annotation.series_id, annotation.label, (data: any) => {
          if (data.hasOwnProperty('success') && data.success === true) {
            self.hideModal()
            // //@ts-ignore
            // $('#annotationModal').modal('toggle');

            //@ts-ignore
            toastr.success('Successfully updated.');
            //update currentAnnotation state so local data reflects backend data
            gsm.currentAnnotation.begin = annotation.left;
            gsm.currentAnnotation.end = annotation.right;
            gsm.currentAnnotation.label = annotation.label;
          } else {
            //@ts-ignore
            toastr.warning('Something went wrong, failed to update annotation.');
          }

          //@ts-ignore
          globalStateManager.currentFile.triggerRedraw();

        });
      }
    }

    hideModal() {
      //@ts-ignore
      let modal = $('#annotationModal');
      //@ts-ignore
      modal.removeData('callingAnnotation');
      //@ts-ignore
      modal.modal('hide');
    }

    get projectID(): number {
        //@ts-ignore
        let project_id: number = globalStateManager.currentProject.id;
        return project_id
    }

    getAnnotationFields(): Array<AnnotationField> {
      let fields: Array<AnnotationField> = [];
      //@ts-ignore
      for (let [name, value]: Array<any> of Object.entries(templateSystem['project_templates'][this.projectID]['project_template']['annotations'])) {
        if (name !== '_default') {
          //@ts-ignore
          for (let [idx, fieldObj] of Object.entries(value.fields)) {
          //@ts-ignore
            fields.push(fieldObj); 
          }
        }
      }
      return fields;
    }

}
</script>

<style scoped>
fieldset {
/* added this to align fields properly */
  padding: unset;
}

.btn {
  margin: 10px;
}
</style>