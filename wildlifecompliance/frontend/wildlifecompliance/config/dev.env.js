var merge = require('webpack-merge')
var prodEnv = require('./prod.env')

module.exports = merge(prodEnv, {
  NODE_ENV: '"development"',
  WEBPACK_HOST: '"localhost:9052"',
  PORT: '"9052"'
})
