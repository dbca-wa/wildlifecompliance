// vue.config.js
const { defineConfig } = require('@vue/cli-service');
const path = require('path');
const webpack = require('webpack');
const MomentLocalesPlugin = require('moment-locales-webpack-plugin');
const port = process.env.PORT ? parseInt(process.env.PORT) : 9052;

module.exports = defineConfig({
    runtimeCompiler: true,
    outputDir: path.resolve(__dirname, '../../static/wildlifecompliance_vue'),
    publicPath: '/static/wildlifecompliance_vue/',
    filenameHashing: false,
    chainWebpack: (config) => {
        config.resolve.alias.set("vue", "@vue/compat");
        config.module
            .rule("vue")
            .use("vue-loader")
            .tap((options) => {
            return { ...options, compilerOptions: { compatConfig: { MODE: 2 } } };
        });
        config.resolve.alias.set(
            '@',
            path.resolve(__dirname, 'src')
        );
        config.resolve.alias.set(
            '@vue-utils',
            path.resolve(__dirname, 'src/utils/vue')
        );
        config.resolve.alias.set(
            '@common-components',
            path.resolve(__dirname, 'src/components/common/')
        );
        config.resolve.alias.set(
            '@internal-components',
            path.resolve(__dirname, 'src/components/internal/')
        );
        config.resolve.alias.set(
            '@external-components',
            path.resolve(__dirname, 'src/components/external/')
        );
        config.resolve.alias.set(
            'easing',
            path.resolve(__dirname, 'jquery.easing/jquery.easing.js')
        );
        config.resolve.alias.set(
            '@static-root',
            path.resolve(__dirname, '../../../staticfiles_wc/')
        );
    },
    configureWebpack: {
        devtool: 'source-map',
        resolve: {
            fallback: {
                buffer: require.resolve('buffer/'),
            },
        },
        plugins: [
            new webpack.ProvidePlugin({
                $: 'jquery',
                jQuery: 'jquery',
                moment: 'moment',
                swal: 'sweetalert2',
                _: 'lodash',
            }),
            new MomentLocalesPlugin(),
            new webpack.ProvidePlugin({
                Buffer: ['buffer', 'Buffer'],
            }),
            new webpack.DefinePlugin({
                __VUE_PROD_HYDRATION_MISMATCH_DETAILS__: 'false',
            }),
        ],
        devServer: {
            host: '0.0.0.0',
            allowedHosts: 'all',
            devMiddleware: {
                //index: true,
                writeToDisk: true,
            },
            headers: {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers':
                    'Origin, X-Requested-With, Content-Type, Accept',
            },
            client: {
                webSocketURL: 'ws://0.0.0.0:' + port + '/ws',
            },
        },
        module: {
            rules: [
                /* config.module.rule('images') */
                {
                    test: /\.(png|jpe?g|gif|webp|avif)(\?.*)?$/,
                    type: 'asset/resource',
                    generator: {
                        filename: 'img/[name][ext]',
                    },
                },
                /* config.module.rule('fonts') */
                {
                    test: /\.(woff2?|eot|ttf|otf)(\?.*)?$/i,
                    type: 'asset/resource',
                    generator: {
                        filename: 'fonts/[name][ext]',
                    },
                },
            ],
        },
        performance: {
            hints: false,
        },
    },
});