module.exports = {
  runtimeCompiler: true,
  outputDir: './vueDist',
  lintOnSave: false,
  productionSourceMap: false,
  filenameHashing: false,
  css: {
    extract: {
      filename: '[name].css'
    }
  },
  configureWebpack: {
    optimization: {
      splitChunks: false
    },
    output: {
      filename: '[name].js'
    },
    resolve: {
      alias: {
        'vue$': 'vue/dist/vue.esm.js'
      }
    }
  },
}