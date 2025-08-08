import App from './App.vue';
import 'vant/es/toast/style';

import { ViteSSG } from 'vite-ssg';
import 'vant/lib/index.css';
import { routes } from 'vue-router/auto-routes';
import { Notify, Uploader } from 'vant';

export const createApp = ViteSSG(
  App,
  {
    routes,
    base: '/chameleon/'
  },
  ({ app }) => {
    app.use(Notify);
    app.use(Uploader)
  }
);
