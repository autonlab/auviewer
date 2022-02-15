<template>
<b-container fluid style="padding-left: 0px">
    <b-row >
        <b-col cols="5">
            <b-card>
            <b-card-body>
                <div v-if="labelerInformation">
                    <labeler-evaluation-table
                        v-bind:labelerInformation="labelerInformation"
                        />
                </div>
                <div v-else>
                    <div style="margin: 0 auto" class="sk-chase">
                        <div class="sk-chase-dot"></div>
                        <div class="sk-chase-dot"></div>
                        <div class="sk-chase-dot"></div>
                        <div class="sk-chase-dot"></div>
                        <div class="sk-chase-dot"></div>
                        <div class="sk-chase-dot"></div>
                    </div>
                    <div style="margin: 0 auto">
                        Loading labeler aggregate stats...
                    </div>

                </div>
            </b-card-body>
            </b-card>
        </b-col>
        <b-col cols="7">

        </b-col>
    </b-row>
    <b-row>
        <b-col>
        <b-card>
        <b-card-body>
        <div v-if="possibleLabelers && possibleLabels">
            <b-form inline>
                <!-- <b-input-group prepend="" -->
                    Show me what &nbsp;
                <label class="sr-only" for="inline-form-select-labeler">My Labeler</label>
                    <b-form-select id="inline-form-select-labeler"
                        v-model="form.labelerSelection"
                        :options="computedPossibleLabelers"
                        required />
                  &nbsp; labels as &nbsp;
                <label class="sr-only" for="inline-form-select-label">My Label</label>
                    <b-form-select id="inline-form-select-label"
                        v-model="form.labelSelection"
                        :options="computedPossibleLabels"
                        required />
            </b-form>
        </div>
        </b-card-body>
        </b-card>
        </b-col>

    </b-row>
</b-container>
</template>

<script lang="ts">
import { Component, Vue, Watch } from 'vue-property-decorator';
import  LabelerEvaluationTable  from '@/components/LabelerEvaluationTable.vue';
import  Fetcher from '@/utils/fetcher';
import $ from 'jquery';
// import * as GlobalAppConfig from '@/../config.js';
// import * as RequestHandler from '@/../classes/requesthandler.js';
import { LabelerEvaluativeStats } from '@/types';

@Component({
  components: {
    LabelerEvaluationTable,
  }
})
export default class SupervisorEvaluation extends Vue {
    /* DATA */
    public labelerInformation: Array<LabelerEvaluativeStats> | null = null;
    public possibleLabelers: Array<string> | null = null;
    public possibleLabels: Array<string> | null = null;
    public form: any = {
        'labelerSelection': null,
        'labelSelection': null
    };

    /* COMPUTED */
    get computedPossibleLabelers() {
        let result = new Array<string>();
        if (this.possibleLabelers) {
            return result.concat(this.possibleLabelers);
        }
    }
    get computedPossibleLabels() {
        if (! this.possibleLabels) {
            return null;
        }
        let labelsCopy: Array<string> | null;
        if (this.form['labelerSelection'] === 'LabelModel')
        {
            labelsCopy = [...this.possibleLabels];
            labelsCopy.splice(labelsCopy.indexOf('ABSTAIN'), 1);
        }
        else
        {
            labelsCopy = this.possibleLabels
        }
        let result = new Array<string>();
        if (labelsCopy) {
            return result.concat(labelsCopy);
        }
    }

    /* LIFECYCLE HOOKS */
    mounted() {
        let self: SupervisorEvaluation = this;
        Fetcher.requestPossibleLabelers(this.projectID, function(data: any) {
            self.possibleLabelers = data.possible_labelers;
        });
        Fetcher.requestPossibleLabels(this.projectID, function(data: any) {
            self.possibleLabels = data.possible_labels;
        });
        // fetch and populate labelingFunctions
        Fetcher.requestInitialEvaluatorPayload( this.projectID, function(data: any): void {
            if (data.lfInfo) {
                let lfInfo: JSON = JSON.parse(data.lfInfo)
                let lfs: Array<string> = data.lfs;
                let labelingFunctions: Array<any> = [];
                for (let lfname of lfs) {
                    labelingFunctions.push({'labeler': lfname});
                }

                for (const [metric, values] of Object.entries(lfInfo)) {
                    console.log(metric);
                    for (let i: number = 0; i < lfs.length; i++) {
                        let value = values[i];
                        if (typeof values[i] === 'number') {
                            value = (value*100).toFixed(1);
                        }
                        labelingFunctions[i][metric.toLowerCase()] = value;
                    }
                }
                self.labelerInformation = labelingFunctions as Array<LabelerEvaluativeStats>;
            }
        });
    }

    get projectID(): number {
        const curPath : string = window.location.href;
        let el = $(this.$el);
        let project_id : number = parseInt(curPath.split("=")[1][0]);
        return project_id
    }

}
</script>

<style scoped>

</style>