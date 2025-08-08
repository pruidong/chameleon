import { defineConfig, loadEnv } from 'vite';
import Vue from '@vitejs/plugin-vue';
import Components from 'unplugin-vue-components/vite';
import { VantResolver } from '@vant/auto-import-resolver';
import VueRouter from 'unplugin-vue-router/vite';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd());
  const { VITE_BASE_URL } = env;
  console.log(VITE_BASE_URL);
  return {
    base: VITE_BASE_URL, // ./ VITE_BASE_URL
    plugins: [
      VueRouter({
        base: VITE_BASE_URL,
        extensions: ['.vue', '.md'],
        dts: 'src/typed-router.d.ts',
        prefix: VITE_BASE_URL,
      }),
      Vue(),
      Components({
        // allow auto load markdown components under `./src/components/`
        extensions: ['vue', 'md'],
        // allow auto import and register components used in markdown
        include: [/\.vue$/, /\.vue\?vue/, /\.md$/],
        resolvers: [VantResolver()
        ],
        dts: 'src/components.d.ts'
      })
    ],
    resolve: {
      alias: {
        // '@': resolve(__dirname, './src'),
        "@": fileURLToPath(new URL("./src", import.meta.url)),
        '~/': `${path.resolve(__dirname, 'src')}/`,
        '@assets/': `${path.resolve(__dirname, 'src')}/assets`
      }
    },
    server: {
      port: 4200
    }
  };
});
