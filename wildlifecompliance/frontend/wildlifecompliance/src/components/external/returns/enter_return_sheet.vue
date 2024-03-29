<template>
<div class="panel panel-default">
    <div class="panel-heading">
        <h3 class="panel-title">{{ sheetTitle }}
            <a class="panelClicker" :href="'#'+pdBody" data-toggle="collapse"  data-parent="#userInfo" expanded="true" :aria-controls="pdBody">
                <span class="glyphicon glyphicon-chevron-up pull-right "></span>
            </a>
        </h3>
    </div>
    <div class="panel-body panel-collapse in" :id="pdBody">
        <div class="col-sm-12">
            <div class="row">
                <div class="col-md-6">
                    <div class="form-group">
                        <label for="">Species Available:</label>
                        <select required v-if="returns.species" class="form-control" ref="species_selector" name="species_selector" id="species_selector">
                          <option v-if="Object.values(returns.species_saved).length === 0" value="" disabled selected></option>
                          <option class="change-species" v-for="(specie, s_idx) in returns.species_list" :value="s_idx" :selected="s_idx === specie_selection" :species_id="s_idx" v-bind:key="`specie_${s_idx}`" >{{specie}}</option>
                        </select>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="form-group" v-if="!readonly" >
                        <button class="btn btn-primary pull-right" @click.prevent="addSheetRow()" name="sheet_entry">New Entry</button>
                    </div>
                </div>
            </div>
            <div class="row">
                <div class="col-md-12">
                    <div class="form-group">
                        <label for="">Species already added for this Return:</label>
                        <div v-show="true" v-for="(specie, a_idx) in returns.species_saved" v-bind:key="`selected_${a_idx}`" >
                          <span v-if='a_idx === returns.species'>&nbsp;&nbsp;&nbsp;{{specie}}</span>
                          <button v-else class="btn btn-link" :name="`specie_link_${a_idx}`" @click.prevent="getSheetSpecies(a_idx)" >{{specie}}</button>
                        </div>
                    </div>
                </div>
            </div>
            <div class="row">
                <div class="col-md-6">
                    <div class="form-group">
                        <label for="">Activity Type:</label>
                        <select ref="activity_filter_selector" name="activity_filter_selector" class="form-control" v-model="filterActivityType">
                            <option value="All">All</option>
                            <option v-for="(sa, sa_idx) in sheet_activity_type" :value="sa['label']" v-bind:key="`sa_type_${sa_idx}`">{{sa['label']}}</option>
                        </select>
                    </div>
                </div>
            </div>
            <div class = "row">
                <div class="col-lg-12">
                    <datatable ref="return_datatable" :id="datatable_id" :dtOptions="sheet_options" :dtHeaders="sheet_headers"/>
                </div>
            </div>
            <!-- End of Sheet Return -->
        </div>
    </div>
    <SheetEntry ref="sheet_entry"></SheetEntry>
</div>
</template>

<script>
import datatable from '@/utils/vue/datatable.vue'
import utils from '@/components/external/utils'
import $ from 'jquery'
import Vue from 'vue'
import Returns from '../../returns_form.vue'
import { mapActions, mapGetters } from 'vuex'
import CommsLogs from '@common-components/comms_logs.vue'
import SheetEntry from './enter_return_sheet_entry.vue'
import {
  api_endpoints,
  helpers
}
from '@/utils/hooks'
import '@/scss/forms/return_sheet.scss';
export default {
  name: 'externalReturnSheet',
  props: {
     url:{
        type: String,
        required: false
     }
  },
  data() {
    var vm = this; // keep and use created ViewModel context with table.
    return {
        pdBody: 'pdBody' + vm._uid,
        datatable_id: 'return-datatable',
        form: null,
        filterActivityType: 'All',
        readonly: false,
        isModalOpen: false,
        sheetTitle: null,
        specie_selection: '',
        sheet_total: 0,
        sheet_activity_type: [],
        sheet_headers:["order","Entry Date","Activity","Date","Qty","Total","Action","Supplier","Comments"],
        sheet_options:{
            language: {
                processing: "<i class='fa fa-4x fa-spinner fa-spin'></i>"
            },
            responsive: true,
            ajax: {
                url: helpers.add_endpoint_json(api_endpoints.returns,'sheet_details'),
                dataSrc: '',
                type: 'GET',
                data: function(_data) {
                  _data.return_id = vm.returns.id
                  _data.species_id = vm.returns.sheet_species
                  return _data;
                },
            },
            columnDefs: [
              { visible: false, targets: [0, 7, 8] } // hide order column.
            ],
            columns: [
              { data: "date" },
              { data: "date",
                className: "pay-row-icon",
                mRender: function(data, type, full) {
                   let _date = new Date(parseInt(full.date));
                   return _date.toLocaleString("en-GB")
                }
              },
              { data: "activity",
                mRender: function(data, type, full) {
                   return vm.returns.sheet_activity_list[data]['label']
                }
              },
              { data: "doa" },
              { data: "qty" },
              { data: "total" },
              { data: "transfer",
                mRender: function(data, type, full) {
                   if (full.activity && (vm.returns.can_current_user_edit || vm.returns.user_in_officers)
                                && !vm.isTrue(vm.returns.sheet_activity_list[full.activity]['auto'])
                                && (full.transfer === 'Notified' || full.transfer === '')) {
                      var column = `<a class="edit-row" data-rowid=\"__ROWID__\">Edit</a><br/>`;
                      column = column.replace(/__ROWID__/g, full.rowId);
                      return column;
                   }
                   if (full.activity && (full.transfer === 'Accepted' || full.transfer === 'Declined')) {
                      return full.transfer;
                   }
                   if (full.activity && vm.is_external
                                && (vm.isTrue(vm.returns.sheet_activity_list[full.activity]['auto'])
                                && full.transfer === 'Notified')) {
                      var accept = `<a class="accept-row" data-rowid=\"__ROWID__\">Accept</a> or `;
                      accept = accept.replace(/__ROWID__/g, full.rowId);
                      var decline = `<a class="decline-row" data-rowid=\"__ROWID__\">Decline</a><br/>`;
                      decline = decline.replace(/__ROWID__/g, full.rowId);
                      return accept + decline;
                   } else {
                      return "";
                   }
                }
              },
              { data: "supplier"},
              { data: "comment"},
            ],
            order: [0, 'desc'],
            rowCallback: function (row, data){
                $(row).addClass('payRecordRow');
            },
            drawCallback: function() {
              if ((vm.specie_selection === '' || null) && Object.values(vm.returns.species_saved).length === 0) {
                vm.specie_selection = document.getElementById("species_selector").options[document.getElementById("species_selector").selectedIndex].textContent;
              } else {
                vm.specie_selection = vm.species_list[vm.returns.sheet_species]
              }
              vm.sheetTitle = vm.specie_selection
            },
            footerCallback: function(row, data, start, end, display) {
              var api = this.api(), data;
              vm.sheet_total = api.column(5).data()[0]
            },
            processing: true,
            ordering: true,
            rowId: function(_data) {
              return _data.rowId
            },
            initComplete: function () {
              if (vm.$refs.return_datatable.vmDataTable.ajax.json().length > 0) {
                // cache initial load.
                vm.species_cache[vm.returns.sheet_species] = vm.$refs.return_datatable.vmDataTable.ajax.json()
              }
              // Populate activity list from the data in the table
              var activityColumn = vm.$refs.return_datatable.vmDataTable.columns(2);
              activityColumn.data().unique().sort().each( function ( d, j ) {
                let activityTitles = [];
                $.each(d,(index,a) => {
                  a != null && activityTitles.indexOf(vm.returns.sheet_activity_list[a])<0 ? activityTitles.push(vm.returns.sheet_activity_list[a]): '';
                })
                vm.sheet_activity_type = activityTitles;
              });
            }
        }
    }
  },
  components:{
    SheetEntry,
    datatable,
    Returns,
  },
  // watch:{
  //   filterActivityType: function(value){
  //     let table = this.$refs.return_datatable.vmDataTable
  //     value = value != 'All' ? value : ''
  //     table.column(2).search(value).draw();
  //   },
  // },
  computed: {
     ...mapGetters([
        'isReturnsLoaded',
        'returns',
        'species_list',
        'species_cache',
        'is_external',
        'species_transfer',
    ]),
  },
  methods: {
    ...mapActions([
        'setReturns',
        'setReturnsSpecies',
        'setSpeciesCache',
    ]),
    isTrue: function(_value) {
      return (_value === 'true');
    },
    intVal: function(_value) {
      return typeof _value === 'string' ?
          _value.replace(/[\$,]/g, '')*1 :
          typeof _value === 'number' ?
          _value : 0;
    },
    addSheetRow: function () {
      if (document.getElementById("species_selector").value === '' || null) {
        swal(
          'Select Specie',
          'Please select a specie before adding a new entry.',
          'error'
        )
      } else {
        const self = this;
        var rows = self.$refs.return_datatable.vmDataTable
        self.$refs.sheet_entry.entryActivity = Object.keys(self.returns.sheet_activity_list)[0];
        if (rows.data().length<1) {
          for (const [key, value] of Object.entries(self.returns.sheet_activity_list)) {
            self.$refs.sheet_entry.entryActivity = key === 'stock' ? key :  self.$refs.sheet_entry.entryActivity
          }
          // self.$refs.sheet_entry.entryActivity = Object.keys(self.returns.sheet_activity_list);
        }
        self.$refs.sheet_entry.isAddEntry = true;
        self.$refs.sheet_entry.return_table = rows;
        self.$refs.sheet_entry.row_of_data = rows;
        self.$refs.sheet_entry.activityList = self.returns.sheet_activity_list;
        self.$refs.sheet_entry.speciesType = self.returns.sheet_species
        self.$refs.sheet_entry.entrySpecies = self.sheetTitle;
        self.$refs.sheet_entry.entryTotal = self.sheet_total;
        self.$refs.sheet_entry.currentStock = self.sheet_total;
        self.$refs.sheet_entry.initialQty = '0';
        self.$refs.sheet_entry.entryQty = '0';      // for editing purposes.
        self.$refs.sheet_entry.entryComment = '';
        self.$refs.sheet_entry.entryLicence = '';
        self.$refs.sheet_entry.entryDateTime = '';
        self.$refs.sheet_entry.entryActivityDate = '';
        self.$refs.sheet_entry.entrySupplier = '';
        self.$refs.sheet_entry.isSubmitable = true;
        self.$refs.sheet_entry.isModalOpen = true;
      }
    },
    addEventListeners: function(){
      let vm = this;

      vm.$refs.return_datatable.vmDataTable.on('click','.edit-row', function(e) {
        e.preventDefault();
        vm.$refs.sheet_entry.isChangeEntry = true;
        vm.$refs.sheet_entry.activityList = vm.returns.sheet_activity_list;
        vm.$refs.sheet_entry.speciesType = vm.returns.sheet_species;
        vm.$refs.sheet_entry.return_table = vm.$refs.return_datatable.vmDataTable
        vm.$refs.sheet_entry.row_of_data = vm.$refs.return_datatable.vmDataTable.row('#'+$(this).attr('data-rowid'));
        vm.$refs.sheet_entry.entrySpecies = vm.sheetTitle;
        vm.$refs.sheet_entry.entryDateTime = vm.$refs.sheet_entry.row_of_data.data().date;
        vm.$refs.sheet_entry.entryActivity = vm.$refs.sheet_entry.row_of_data.data().activity;
        vm.$refs.sheet_entry.entryActivityDate = vm.$refs.sheet_entry.row_of_data.data().doa;
        vm.$refs.sheet_entry.entryQty = vm.$refs.sheet_entry.row_of_data.data().qty;
        vm.$refs.sheet_entry.initialQty = vm.$refs.sheet_entry.row_of_data.data().qty;
        vm.$refs.sheet_entry.entryTotal = vm.$refs.sheet_entry.row_of_data.data().total;
        vm.$refs.sheet_entry.currentStock = vm.$refs.sheet_entry.row_of_data.data().total;
        vm.$refs.sheet_entry.entryComment = vm.$refs.sheet_entry.row_of_data.data().comment;
        vm.$refs.sheet_entry.entryLicence = vm.$refs.sheet_entry.row_of_data.data().licence;
        vm.$refs.sheet_entry.entryTransfer = vm.$refs.sheet_entry.row_of_data.data().transfer;
        vm.$refs.sheet_entry.entrySupplier = vm.$refs.sheet_entry.row_of_data.data().supplier;

        vm.species_cache[vm.returns.sheet_species] = vm.$refs.return_datatable.vmDataTable.data();

        vm.$refs.sheet_entry.isSubmitable = true;
        vm.$refs.sheet_entry.isModalOpen = true;
        vm.$refs.sheet_entry.errors = false;
      });

      vm.$refs.return_datatable.vmDataTable.on('click','.accept-row', function(e) {
        e.preventDefault();
        var selected = vm.$refs.return_datatable.vmDataTable.row('#'+$(this).attr('data-rowid'));
        var rows = vm.$refs.return_datatable.vmDataTable.data();
        for (let i=0; i<rows.length; i++) {
          if (vm.intVal(rows[i].date)>=vm.intVal(selected.data().date)){ //activity is after accepted
            rows[i].total = vm.intVal(rows[i].total) + vm.intVal(selected.data().qty)
          }
          if (vm.intVal(rows[i].date)==vm.intVal(selected.data().date)) {
            rows[i].transfer = 'Accepted'

            let transfer = {}  //{speciesID: {this.entryDateTime: row_data},}
            if (vm.returns.sheet_species in vm.species_transfer){
              transfer = vm.species_transfer[vm.returns.sheet_species]
            }
            transfer[rows[i].date] = Object.assign({}, rows[i]);
            transfer[rows[i].date].species_id = vm.returns.sheet_species
            vm.species_transfer[vm.returns.sheet_species] = transfer
          }
        }
        vm.species_cache[vm.returns.sheet_species] = vm.$refs.return_datatable.vmDataTable.data();
        vm.$refs.return_datatable.vmDataTable.clear().draw();
        vm.$refs.return_datatable.vmDataTable.rows.add(vm.species_cache[vm.returns.sheet_species]);
        vm.$refs.return_datatable.vmDataTable.draw();
      });

      vm.$refs.return_datatable.vmDataTable.on('click','.decline-row', function(e) {
        e.preventDefault();
        var selected = vm.$refs.return_datatable.vmDataTable.row('#'+$(this).attr('data-rowid'));
        var rows = vm.$refs.return_datatable.vmDataTable.data();
        for (let i=0; i<rows.length; i++) {
          if (vm.intVal(rows[i].date)==vm.intVal(selected.data().date)) {
            rows[i].transfer = 'Declined'

            let transfer = {}  //{speciesID: {this.entryDateTime: row_data},}
            if (vm.returns.sheet_species in vm.species_transfer){
              transfer = vm.species_transfer[vm.returns.sheet_species]
            }
            transfer[rows[i].date] = Object.assign({}, rows[i]);
            transfer[rows[i].date].species_id = vm.returns.sheet_species
            vm.species_transfer[vm.returns.sheet_species] = transfer
          }
        }
        vm.species_cache[vm.returns.sheet_species] = vm.$refs.return_datatable.vmDataTable.data();
        vm.$refs.return_datatable.vmDataTable.clear().draw();
        vm.$refs.return_datatable.vmDataTable.rows.add(vm.species_cache[vm.returns.sheet_species]);
        vm.$refs.return_datatable.vmDataTable.draw();
      });

      // payment row listener
      vm.$refs.return_datatable.vmDataTable.on('click', 'tr.payRecordRow', function(e) {
          // If a link is clicked, ignore
          if($(e.target).is('a')){
              return;
          }
          // Generate child row for application
          // Get licence row data
          var tr = $(this);
          var row = vm.$refs.return_datatable.vmDataTable.row(tr);
          var row_data = row.data()
          var return_id = row_data.id;
          // var current_application = row_data.current_application
          // var licence_category_id = current_application.category_id ? current_application.category_id : "";
          // var proxy_id = current_application.proxy_applicant ? current_application.proxy_applicant.id : "";
          // var org_id = current_application.org_applicant ? current_application.org_applicant.id : "";

          if (row.child.isShown()) {
              // This row is already open - close it
              row.child.hide();
              tr.removeClass('shown');
          }
          else {
              // Open this row (the format() function would return the data to be shown)
              var child_row = ''
              // Generate rows for each activity
              var activity_rows = ''
              // Generate html for child row
              child_row += `
                  <table class="table table-bordered child-row-table">
                      `;
              child_row += 
                      `<tr>
                          <td class="width_15pc"><strong>Name of Supplier/Recipient:&nbsp;</strong></td>
                          <td>${row.data()['supplier']}</td>
                      </tr>`;

              child_row += 
                      `<tr>
                          <td class="width_15pc"><strong>Keeper, Import or Export <br/> Licence number:&nbsp;</strong></td>
                          <td>${row.data()['licence']}</td>
                      </tr>`;

              child_row += 
                      `<tr>
                          <td class="width_15pc"><strong>Comments:&nbsp;</strong></td>
                          <td>${row.data()['comment']}</td>
                      </tr>`;

              child_row += `</table>`
              // child_row += `
              //     <table class="table table-striped table-bordered child-row-table">
              //         <tr>
              //             <td class="width_15pc"><strong>Invoice:&nbsp;</strong></td>
              //             <td>1233412244</td>
              //         </tr>
              //     </table>`;
              // Show child row, dark-row className CSS applied from application.scss
              row.child(
                  child_row
                  , 'dark-row').show();
              tr.addClass('shown');
          }
      });

      // // Instantiate Form Actions
      // $('form').on('click', '.change-species', function(e) {
      //   e.preventDefault();
      //   let selected_id = $(this).attr('species_id');
      //   if (vm.species_cache[vm.returns.sheet_species]==null
      //                   && vm.$refs.return_datatable.vmDataTable.ajax.json().length>0) {
      //       // cache currently displayed species json
      //       vm.species_cache[vm.returns.sheet_species] = vm.$refs.return_datatable.vmDataTable.ajax.json()
      //   }
      //   vm.returns.sheet_species = selected_id;
      //   if (vm.species_cache[selected_id] != null) {
      //       // species json previously loaded from ajax
      //       vm.$refs.return_datatable.vmDataTable.clear().draw();
      //       vm.$refs.return_datatable.vmDataTable.rows.add(vm.species_cache[selected_id]);
      //       vm.$refs.return_datatable.vmDataTable.draw();
      //   } else {
      //       // load species json from ajax
      //       vm.$refs.return_datatable.vmDataTable.clear().draw();
      //       vm.$refs.return_datatable.vmDataTable
      //               .ajax.url = helpers.add_endpoint_json(api_endpoints.returns,'sheet_details');
      //       vm.$refs.return_datatable.vmDataTable.ajax.reload();
      //   };
      // });

      vm.setSpeciesSelector();
      vm.setActivityFilterSelector();
    },      // end of eventListener()
    setFilterActivityType: function(value){
      let table = this.$refs.return_datatable.vmDataTable
      value = value != 'All' ? value : ''
      table.column(2).search(value).draw();
    },
    getSheetSpecies: function(selected_species) {
      const self = this
      self.setSheetSpecies(selected_species)
      self.returns.species = selected_species
      $(self.$refs.species_selector).val(selected_species);
      $(self.$refs.species_selector).trigger('change');
    },
    setSheetSpecies: function(selected_species) {
      let vm = this;
      let selected_id = selected_species;
      if (vm.species_cache[vm.returns.sheet_species]==null
                      && vm.$refs.return_datatable.vmDataTable.ajax.json().length>0) {
          // cache currently displayed species json
          vm.species_cache[vm.returns.sheet_species] = vm.$refs.return_datatable.vmDataTable.ajax.json()
      }
      vm.returns.sheet_species = selected_id;
      if (vm.species_cache[selected_id] != null) {
          // species json previously loaded from ajax
          vm.$refs.return_datatable.vmDataTable.clear().draw();
          vm.$refs.return_datatable.vmDataTable.rows.add(vm.species_cache[selected_id]);
          vm.$refs.return_datatable.vmDataTable.draw();
      } else {
          // load species json from ajax
          vm.$refs.return_datatable.vmDataTable.clear().draw();
          vm.$refs.return_datatable.vmDataTable
                  .ajax.url = helpers.add_endpoint_json(api_endpoints.returns,'sheet_details');
          vm.$refs.return_datatable.vmDataTable.ajax.reload();
      };
    },
    setSpeciesSelector: function () {
        let vm = this;

        $(vm.$refs.species_selector).select2({
            "theme": "bootstrap",
            minimumInputLength: 2,
            placeholder:"Select Species...",
        }).
        on("select2:select",function (e) {
            e.stopImmediatePropagation();
            e.preventDefault();
            var selected = $(e.currentTarget);
            var selected_species = selected.val();
            vm.setSheetSpecies(selected_species)
        });
    },
    setActivityFilterSelector: function () {
        let vm = this;

        $(vm.$refs.activity_filter_selector).select2({
            "theme": "bootstrap",
            // placeholder:"Select Species..."
        }).
        on("select2:select",function (e) {
            var selected = $(e.currentTarget);
            var filter = selected.val();
            vm.setFilterActivityType(filter)
        });
    },
  },
  created: function(){
     this.form = document.forms.enter_return_sheet;
     this.readonly = !(this.is_external || this.returns.user_in_officers) || !this.returns.is_draft
     this.select_species_list = this.species_list;
  },
  mounted: function(){
    var vm = this;
    this.$nextTick(() => {
        vm.addEventListeners();
    });
  },
};
</script>
