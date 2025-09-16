import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import path from 'path';
import vueDevTools from 'vite-plugin-vue-devtools';
import svgLoader from 'vite-svg-loader';

const applicationNameShort = 'wildlifecompliance';
const port = process.env.PORT ? parseInt(process.env.PORT) : 9052;
const host = process.env.HOST || '0.0.0.0';

export default defineConfig(({ mode }) => {
    const isProduction = mode === 'production';

    return {
        base: `/static/${applicationNameShort}_vue/`,  //Base public path when served in development or production.
        server: {
            host: host,
            port: port,
            strictPort: true,
            open: false,
            headers: {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers':
                    'Origin, X-Requested-With, Content-Type, Accept',
            },
            origin: `http://localhost:${port}`,
            hmr: {
                protocol: 'ws',
                host: 'localhost',
                port: port,
            },
        },
        plugins: [
            vueDevTools(),
            vue(),
            svgLoader({
                defaultImport: 'url',
            }),
        ],
        resolve: {
            alias: {
                // vue: 'vue/dist/vue.esm-bundler.js',
                //'vue': '@vue/compat',
                '@': path.resolve(__dirname, './src'),
                '@common-components': path.resolve(__dirname, './src/components/common/'),
                '@vue-utils': path.resolve(__dirname, './src/utils/vue/')
            },
        },
        define: {
            'process.env': {}
        },
        build: {
            manifest: 'manifest.json',
            commonjsOptions: { transformMixedEsModules: true },
            root: path.resolve(__dirname, './src'),
            outDir: path.resolve(
                __dirname,
                `../../static/${applicationNameShort}_vue`
            ),
            sourcemap: true,
            rollupOptions: {
                input: {
                    main: path.resolve(__dirname, 'src/main.js'),
                },
            },
            exclude: ['jquery', 'bootstrap'],
            emptyOutDir: true,
        },
    };
});