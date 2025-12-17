<template lang="html">
     <div>
          <label :id="id" :required="isRequired" class="fw-bold"> {{ label }} </label>

          <template v-if="help_text">
              <HelpText :help_text="help_text" />
          </template>

          <template v-if="help_text_url">
              <HelpTextUrl :help_text_url="help_text_url" />
          </template>

          <!--<CommentBlock :name="name" :label="label" :field_data="getDeficiencyField" />-->

          <div class="grid-container">
              <div class="col-sm-3 form-group" v-if="headers">
                  <div class="grid-item row">
                      
                      <div class="col-sm-1 grid-column" v-for="header in headers" >
                                  <input disabled="true"
                                         type="text"
                                         class="form-control grid-element"
                                         :value="header.label"
                                  />
                          </div>
                      
                  </div>
                  
                  <div class="grid-item row" v-for ="(field, row_no) in field_data" >
                          
                          <div class="col-sm-1 grid-column" id="field.name" v-for="(title,key) in field"
                              :name="`${name}::${key}`" :key="`f_${key}`" >
                                  <input :disabled="readonly"
                                         type="text"
                                         :id="key + '::' + row_no"
                                         class="form-control grid-element"
                                         :name="name + '::' + key"
                                         :required="isRequired"
                                         :v-model="field_data[row_no][key].value"
                                         :value="field_data[row_no][key].value"
                                         @input="update($event,key,row_no)"
                                  />
                          </div>
                          <div class="col-sm-1">
                            <button class="btn btn-danger btn-md" @click.prevent="removeRow(row_no)" ><i class="bi bi-trash"></i></button>
                          </div>
                </div>
              </div>
          </div>
          <div >
             <button class="btn btn-primary btn-md" @click.prevent="addRow()" >Add Row</button>
          </div>
     </div>
</template>
<script>
import HelpText from './help_text.vue'
import HelpTextUrl from './help_text_url.vue'
import CommentBlock from './comment_block.vue';
const GridBlock = {
  /* Example schema config
     Note: Each grid-item requires a unique name ie.'Table-Name::location'.
     {
      "type": "grid",
      "headers": "{'label': 'LOCATION','name': 'location', 'type': 'string','required': 'true'}",
      "name": "table-name",
      "label": "Grid format of Table Data"
      "data" : "{'key': 'value'}"
     }
  */
  props: ['field_data','headers','name', 'label', 'id', 'help_text', 'help_text_url', 'readonly', 'isRequired'],
  components: {HelpText, HelpTextUrl, CommentBlock},
  data: function() {
    return {
      show_add_row: false,
    }
  },
  computed: {
    //TODO determine if this is needed
    /*getDeficiencyField: function(){
      var def = this.field_data[0][this.name + '-deficiency-field']
      if (def==null){
        return {'deficiency-value': null}
      }
      return this.field_data[0][this.name + '-deficiency-field']
    },*/
    showAddRow: function(){
      return this.show_add_row
    },
  },
  mounted: function() {
    if (this.field_data.length > 0) {
      for (const i in this.field_data[0]) {
        if (this.field_data[0][i].error === undefined) {
          this.field_data[0][i].error = "";
        }
      }
    }
  },
  methods: {
    update: function($event,key,index) {
      this.field_data[index][key].value = $event.target.value;
    },
    addRow: function(e) {
      const self = this;
      let fieldObj = Object.assign({}, this.field_data[0]);
      // schema data type on each field is validated - error value required.
      for(let key in fieldObj) {
        fieldObj[key] = {'value':'', 'error':''};
      };
      self.field_data.push(fieldObj);
    },
    removeRow: function(row_num) {
      const self = this;
      if (self.field_data.length > 1) {
        self.field_data.splice(row_num,1);
      } else {
        let fieldObj = Object.assign({}, this.field_data[0]);
        for(let key in fieldObj) {
          fieldObj[key] = {'value':'', 'error':''};
        };
        self.field_data[0] = fieldObj;
      }
    },
    setDateValue: function(value, row, name, readonly) {
      const self = this;
      if (value !== '') {
         self.field_data[row][name].value = value;
         self.value = value;
      }
      self.show_add_row = !readonly
      return self.field_data[row][name].value;
    },
  },
}

export default GridBlock;
</script>

<style lang="css">
    input {
        box-shadow:none;
    }
    .grid-container {
        display: grid;
        width: 100%;
        height: 300px;
        border: 1px solid #ffffff;
        grid-template-columns: [labels] 5120px;
        grid-template-rows: auto;
        overflow: scroll;
        background-color: #ffffff;
    }
    .grid-container > label {
        grid-column: labels;
        grid-row: auto;
    }
    .grid-item {
        grid-column: 1 / 1;
        grid-row: 1 / 1;
        border: 1px solid #ffffff;
        margin: auto;    
    }
    .grid-column {
        padding: 1px !important;
    }
    .grid-element {
        margin: 1px !important;
    }

</style>






