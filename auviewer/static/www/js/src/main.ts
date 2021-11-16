import Vue from 'vue'
import SupervisorEvaluation from './views/SupervisorEvaluation.vue'
import router from './router'
import store from './store'
import { BootstrapVue, BootstrapVueIcons } from 'bootstrap-vue'

import 'bootstrap/dist/css/bootstrap.css'
import 'bootstrap-vue/dist/bootstrap-vue.css'

Vue.use(BootstrapVue)
Vue.use(BootstrapVueIcons)

Vue.config.productionTip = false
Vue.component('vuea', SupervisorEvaluation);
const vueApp = new Vue({
  router,
  store
}).$mount('#vueapp');
// console.log('hello');
// @ts-ignore
// window.Vue = require('vue');
// new Vue({
//   router,
//   store,
//   render: h => h(App)
// }).$mount('#app')
