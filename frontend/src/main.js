import { createPinia } from 'pinia';
import { createApp } from 'vue';
import App from './App.vue';
import './assets/index.css';

const app = createApp(App);
const pinia = createPinia();

app.use(pinia);
app.mount('#app');
