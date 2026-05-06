//Due to conflicting jquery instances, we cannot have a global jquery or jquery-ui setup
//We have it here instead, to be used in components as needed


import $ from 'jquery'

window.$ = $
window.jQuery = $

import 'jquery-ui-dist/jquery-ui'

export default $