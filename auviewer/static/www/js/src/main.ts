import Vue from 'vue';
import AnnotationModal from './components/AnnotationModal.vue';
import VueObserveVisibility from 'vue-observe-visibility';
import { BootstrapVue, BootstrapVueIcons } from 'bootstrap-vue';

import router from './router'
import store from './store'
import 'bootstrap/dist/css/bootstrap.css'
import 'bootstrap-vue/dist/bootstrap-vue.css'
import './quasar'

Vue.use(BootstrapVue)
Vue.use(BootstrapVueIcons)
Vue.use(VueObserveVisibility)

Vue.config.productionTip = false;
Vue.component('annotationmodalvue', AnnotationModal);
const vueApp = new Vue({
  router,
  store
}).$mount('#vueapp');
