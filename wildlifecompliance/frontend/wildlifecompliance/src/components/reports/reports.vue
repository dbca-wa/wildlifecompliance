<template lang="html">
  <div class="container">
    <div id="report-form">
        <form  method="get" id="payments-form" action="/ledger/payments/api/report">
            <div class="well">
                <div class="row">
                    <div class="col-md-12">
                        <h3 style="margin-bottom:20px;">Payments Reports</h3>
                            <div class="row" v-show="!region">
                                <div class="col-md-6">
                                    <div class="form-group">
                                      <label for="">Start Date</label>
                                      <div class="input-group date"  id="accountsDateStartPicker">
                                          <input type="date" class="form-control" name="start" placeholder="DD/MM/YYYY" required >
                                          <span class="input-group-addon">
                                              <span class="glyphicon glyphicon-calendar"></span>
                                          </span>
                                      </div>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="form-group">
                                      <label for="">End Date</label>
                                      <div class="input-group date" id="accountsDateEndPicker">
                                          <input type="date" class="form-control" name="end"  placeholder="DD/MM/YYYY" required>
                                          <span class="input-group-addon">
                                              <span class="glyphicon glyphicon-calendar"></span>
                                          </span>
                                      </div>
                                    </div>
                                </div>
                            </div>
                            <div class="row" style="margin-top:20px;">
                                <div class="col-md-6">
                                    <div class="form-group">
                                      <label for="">Bank Start Date</label>
                                      <div class="input-group date" id="flatDateStartPicker">
                                          <input type="date" class="form-control" name="banked_start"  placeholder="DD/MM/YYYY" required>
                                          <span class="input-group-addon">
                                              <span class="glyphicon glyphicon-calendar"></span>
                                          </span>
                                      </div>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="form-group">
                                      <label for="">Bank End Date</label>
                                      <div class="input-group date" id="flatDateEndPicker">
                                          <input type="date" class="form-control" name="banked_end"  placeholder="DD/MM/YYYY" required>
                                          <span class="input-group-addon">
                                              <span class="glyphicon glyphicon-calendar"></span>
                                          </span>
                                      </div>
                                    </div>
                                </div>

                            </div>
                            <div class="row">
                                <div class="col-sm-6">
                                    <button @click.prevent="generateByAccount()" class="btn btn-primary pull-left" >Generate Report By Accounts</button>
                                </div>
                                <div class="col-sm-6 clearfix">
                                  <button @click.prevent="generateFlatReport()" class="btn btn-primary pull-left" >Generate Report Flat</button>
                                </div>
                            </div>
                    </div>
                </div>
            </div>
        </form>
        <form ref="oracle_form">
            <div class="well well-sm">
                <div class="row">
                    <div class="col-lg-12">
                        <div class="col-lg-12">
                            <h3 style="margin-bottom:20px;">Oracle Job</h3>
                        </div>
                        <div class="row">
                            <div class="col-lg-12">
                                <div class="col-sm-6">
                                    <div class="form-group">
                                      <label for="">Date</label>
                                      <div class="input-group date" ref="oracleDatePicker">
                                          <input type="text" class="form-control" name="oracle_date"  placeholder="DD/MM/YYYY" required>
                                          <span class="input-group-addon">
                                              <span class="glyphicon glyphicon-calendar"></span>
                                          </span>
                                      </div>
                                    </div>
                                    <div class="form-group">
                                        <button @click.prevent="runOracleJob()" class="btn btn-primary pull-left" >Run Job</button>
                                    </div>
                                </div>
                                <div class="col-sm-6">
                                    <div class="checkbox">
                                      <label><input v-model="oracle_override" type="checkbox" value="">Override closed period check</label>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </form>
    </div>
  </div>
</template>

<script>
//import {$,swal,bus,datetimepicker,api_endpoints,helpers,Moment,validate} from "@/utils/hooks.js"
import {api_endpoints,helpers,fetch} from "@/utils/hooks.js"
export default {
    name:"reports",
    data:function () {
        let vm = this;
        return {
            form:null,
            refund_form:null,
            oracle_form: null,
            oracleDatePicker: null,
            booking_settlements_form: null,
            bookings_form: null,
            bookingSettlementsDatePicker: null,
            bookingsDatePicker: null,
            accountsDateStartPicker:null,
            accountsDateEndPicker:null,
            flatDateStartPicker:null,
            flatDateEndPicker:null,
            refundsStartPicker:null,
            refundsEndPicker:null,
            datepickerOptions:{
                format: 'DD/MM/YYYY',
                showClear:true,
                useCurrent:false
            },
            regions:[],
            region:'',
            district:'',
            selected_region:{
                code:'',
                name:'',
                districts:[]
            },
            oracle_override: false,
        };
    },
    watch:{
        region: function () {
            let vm =this;
            vm.district = '';
            if (vm.region) {
                vm.selected_region = vm.regions.find(r => (r.name == vm.region));
            }else{
                vm.selected_region={
                    code:'',
                    name:'',
                    districts:[]
                }
            }
        }
    },
    methods:{
        addEventListeners:function () {
            let vm = this;
            vm.form = $('#payments-form');
            vm.refund_form = $('#refund_form');
            vm.oracle_form = $(vm.$refs.oracle_form);
            vm.booking_settlements_form = $(vm.$refs.booking_settlements_form);
            vm.bookings_form = $(vm.$refs.bookings_form);
            vm.addFormValidations();
            vm.fetchRegions();
        },
        runOracleJob(){
            let vm = this;
            
            if (vm.oracle_form.valid()){
                let data = vm.oracleDatePicker.data("DateTimePicker").date().format('DD/MM/YYYY');
                let override = vm.oracle_override ? 'true': 'false';
                let request = fetch.fetchUrl('/api/oracle_job?date='+data+'&override='+override).then((response) => {
                    swal.fire({
                        type: 'success',
                        title: 'Job Success', 
                        text: 'The oracle job was completed successfully', 
                    })
                }).catch((error) => {
                    swal.fire({
                        type: 'error',
                        title: 'Oracle Job Error', 
                        text: helpers.apiVueResourceError(error), 
                    })
                })
            }
        },
        fetchRegions:function () {
            let vm = this;
            $.get('/api/regions?format=json',function (data) {
                vm.regions = data;
            });
        },
        generateFlatReport:function () {
            let vm = this;
            var values = vm.generateValues();
            if (values) {
                values.flat = false;
                vm.getReport(values);
            }
        },
        generateValues:function () {
            console.log('generateValues');
            let vm = this;
            if(vm.form.valid()){
                var values = {
                    "system":"S566",
                    "start":(vm.region) ? vm.flatDateStartPicker.data("DateTimePicker").date().set({hour:0,minute:0,second:0,millisecond:0}).format('YYYY-MM-DD H:mm:ss'):vm.accountsDateStartPicker.data("DateTimePicker").date().set({hour:0,minute:0,second:0,millisecond:0}).format('YYYY-MM-DD H:mm:ss'),
                    "end":(vm.region) ? vm.flatDateEndPicker.data("DateTimePicker").date().set({hour:23,minute:59,second:59,millisecond:0}).format('YYYY-MM-DD H:mm:ss'):vm.accountsDateEndPicker.data("DateTimePicker").date().set({hour:23,minute:59,second:59,millisecond:0}).format('YYYY-MM-DD H:mm:ss'),
                    "banked_start":vm.flatDateStartPicker.data("DateTimePicker").date().set({hour:0,minute:0,second:0,millisecond:0}).format('YYYY-MM-DD H:mm:ss'),
                    "banked_end":vm.flatDateEndPicker.data("DateTimePicker").date().set({hour:23,minute:59,second:59,millisecond:0}).format('YYYY-MM-DD H:mm:ss'),
                };
                //if(vm.region){
                //    values.region = vm.region;
                //    if (vm.district) {
                //        values.district = vm.district;
                //    }
                //}
                return values;
            }
            return false;
        },
        generateByAccount:function () {
            console.log('generateByAccount');
            let vm = this;
            var values = vm.generateValues();
            if (values) {
                values.items = true;
                vm.getReport(values);
            }

        },
        generateRefundReport:function () {
            let vm =this;

            if (vm.refund_form.valid()) {
                var values = {
                    "start": vm.refundsStartPicker.data("DateTimePicker").date().format('DD/MM/YYYY'),
                    "end" :vm.refundsEndPicker.data("DateTimePicker").date().format('DD/MM/YYYY'),
                }
                var url = api_endpoints.booking_refunds +"?"+ $.param(values);
                window.location.assign(url);
            }else{
                console.log("invalid form");
            }

        },
        getReport:function (values) {
            console.log('getReport');
            let vm = this;
            //var url = "/ledger/payments/api/report?"+$.param(values);
            var url = "/ledger/payments/api/report?"+$.param(values);
            window.location.assign(url);
        },
        addFormValidations: function() {
            let vm =this;
            vm.form.validate({
                rules: {
                    start: {
                        required:function(){
                            return vm.region.length == 0;
                        }
                    },
                    end: {
                        required:function(){
                            return vm.region.length == 0;
                        }
                    },
                    banked_start: "required",
                    banked_end: "required",
                },
                messages: {
                    start: "Field is required",
                    end: "Field is required",
                    banked_end: "Field is required",
                    banked_start: "Field is required",
                },
                showErrors:function(errorMap, errorList) {
                    $.each(this.validElements(), function(index, element) {
                        var $element = $(element);

                        $element.attr("data-original-title", "").parents('.form-group').removeClass('has-error');
                    });

                    // destroy tooltips on valid elements
                    $("." + this.settings.validClass).tooltip("destroy");

                    // add or update tooltips
                    for (var i = 0; i < errorList.length; i++) {
                        var error = errorList[i];
                        $(error.element)
                            .tooltip({
                                trigger: "focus"
                            })
                            .attr("data-original-title", error.message)
                            .parents('.form-group').addClass('has-error');
                    }
                }
            });
            vm.refund_form.validate({
                rules: {
                    refund_start_date: {
                        required:function(){
                            return vm.region.length == 0;
                        }
                    },
                    refund_end_date: {
                        required:function(){
                            return vm.region.length == 0;
                        }
                    }
                },
                messages: {
                    refund_start_date: "Field is required",
                    refund_end_date: "Field is required",
                },
                showErrors:function(errorMap, errorList) {
                    $.each(this.validElements(), function(index, element) {
                        var $element = $(element);

                        $element.attr("data-original-title", "").parents('.form-group').removeClass('has-error');
                    });

                    // destroy tooltips on valid elements
                    $("." + this.settings.validClass).tooltip("destroy");

                    // add or update tooltips
                    for (var i = 0; i < errorList.length; i++) {
                        var error = errorList[i];
                        $(error.element)
                            .tooltip({
                                trigger: "focus"
                            })
                            .attr("data-original-title", error.message)
                            .parents('.form-group').addClass('has-error');
                    }
                }
            });
            vm.oracle_form.validate({
                rules: {
                    oracle_date:'required', 
                },
                messages: {
                    oracle_date: "Field is required",
                },
                showErrors:function(errorMap, errorList) {
                    $.each(this.validElements(), function(index, element) {
                        var $element = $(element);

                        $element.attr("data-original-title", "").parents('.form-group').removeClass('has-error');
                    });

                    // destroy tooltips on valid elements
                    $("." + this.settings.validClass).tooltip("destroy");

                    // add or update tooltips
                    for (var i = 0; i < errorList.length; i++) {
                        var error = errorList[i];
                        $(error.element)
                            .tooltip({
                                trigger: "focus"
                            })
                            .attr("data-original-title", error.message)
                            .parents('.form-group').addClass('has-error');
                    }
                }
            });
            vm.booking_settlements_form.validate({
                rules: {
                    booking_settlement_date:'required', 
                },
                messages: {
                    booking_settlement_date: "Field is required",
                },
                showErrors:function(errorMap, errorList) {
                    $.each(this.validElements(), function(index, element) {
                        var $element = $(element);

                        $element.attr("data-original-title", "").parents('.form-group').removeClass('has-error');
                    });

                    // destroy tooltips on valid elements
                    $("." + this.settings.validClass).tooltip("destroy");

                    // add or update tooltips
                    for (var i = 0; i < errorList.length; i++) {
                        var error = errorList[i];
                        $(error.element)
                            .tooltip({
                                trigger: "focus"
                            })
                            .attr("data-original-title", error.message)
                            .parents('.form-group').addClass('has-error');
                    }
                }
            });
            vm.bookings_form.validate({
                rules: {
                    bookings_date:'required', 
                },
                messages: {
                    bookings_date: "Field is required",
                },
                showErrors:function(errorMap, errorList) {
                    $.each(this.validElements(), function(index, element) {
                        var $element = $(element);

                        $element.attr("data-original-title", "").parents('.form-group').removeClass('has-error');
                    });

                    // destroy tooltips on valid elements
                    $("." + this.settings.validClass).tooltip("destroy");

                    // add or update tooltips
                    for (var i = 0; i < errorList.length; i++) {
                        var error = errorList[i];
                        $(error.element)
                            .tooltip({
                                trigger: "focus"
                            })
                            .attr("data-original-title", error.message)
                            .parents('.form-group').addClass('has-error');
                    }
                }
            });
        },
    },
    mounted:function () {
        let vm = this;
        vm.addEventListeners();
    }
}

</script>

<style lang="css">
</style>
