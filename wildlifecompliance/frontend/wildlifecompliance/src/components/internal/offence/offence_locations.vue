<template lang="html">
    <div class="">
        <div id="map-filter">
            <div>
                <label class="">Sanction Outcome Types</label>
                <select class="form-control" v-model="filterSanctionOutcomeType">
                    <option v-for="option in sanction_outcome_type_choices" :value="option.id" v-bind:key="option.id">
                        {{ option.display }}
                    </option>
                </select>
            </div>
            <div>
                <label class="">Offence Status</label>
                <select class="form-control" v-model="filterStatus">
                    <option v-for="option in status_choices" :value="option.id" v-bind:key="option.id">
                        {{ option.display }}
                    </option>
                </select>
            </div>
            <div>
                <label class="">Date From</label>
                <div class="input-group date" ref="lodgementDateFromPicker">
                    <input type="text" class="form-control" placeholder="DD/MM/YYYY" v-model="filterDateFrom" />
                    <span class="input-group-addon">
                        <span class="glyphicon glyphicon-calendar"></span>
                    </span>
                </div>
            </div>
            <div>
                <label class="">Date To</label>
                <div class="input-group date" ref="lodgementDateToPicker">
                    <input type="text" class="form-control" placeholder="DD/MM/YYYY" v-model="filterDateTo" />
                    <span class="input-group-addon">
                        <span class="glyphicon glyphicon-calendar"></span>
                    </span>
                </div>
            </div>
        </div>

        <div id="map-wrapper">
            <div id="search-box">
                <input id="search-input" />
            </div>
            <div id="mapLeaf"> </div>
            <div id="basemap-button">
                <img id="basemap_sat" src="../../../assets/img/satellite_icon.jpg" @click="setBaseLayer('sat')" />
                <img id="basemap_osm" src="../../../assets/img/map_icon.png" @click="setBaseLayer('osm')" />
            </div>
            <div id="cursor-location">
                <div v-if="cursor_location">
                    <span id="cursor-location-lat">{{ cursor_location.lat.toFixed(5) }}, {{ cursor_location.lng.toFixed(5) }}</span>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import L from 'leaflet';
import 'leaflet.markercluster';  /* This should be imported after leaflet */
import 'leaflet.locatecontrol';
import Awesomplete from 'awesomplete';
import { api_endpoints, helpers, cache_helper } from '@/utils/hooks'
import { mapState, mapGetters, mapActions, mapMutations } from "vuex";
import Vue from "vue";
import 'leaflet/dist/leaflet.css';
import 'leaflet.markercluster/dist/MarkerCluster.css';
import 'leaflet.markercluster/dist/MarkerCluster.Default.css';
import 'leaflet.locatecontrol/dist/L.Control.Locate.min.css'
import 'bootstrap/dist/css/bootstrap.css';
import 'awesomplete/awesomplete.css';

L.TileLayer.WMTS = L.TileLayer.extend({
    defaultWmtsParams: {
        service: 'WMTS',
        request: 'GetTile',
        version: '1.0.0',
        layers: '',
        styles: '',
        tilematrixSet: '',
        format: 'image/jpeg'
    },

    initialize: function (url, options) { // (String, Object)
        this._url = url;
        var wmtsParams = L.extend({}, this.defaultWmtsParams);
        var tileSize = options.tileSize || this.options.tileSize;
        if (options.detectRetina && L.Browser.retina) {
            wmtsParams.width = wmtsParams.height = tileSize * 2;
        } else {
            wmtsParams.width = wmtsParams.height = tileSize;
        }
        for (var i in options) {
            // all keys that are not TileLayer options go to WMTS params
            if (!this.options.hasOwnProperty(i) && i!="matrixIds") {
                wmtsParams[i] = options[i];
            }
        }
        this.wmtsParams = wmtsParams;
        this.matrixIds = options.matrixIds||this.getDefaultMatrix();
        L.setOptions(this, options);
    },

    onAdd: function (map) {
        this._crs = this.options.crs || map.options.crs;
        L.TileLayer.prototype.onAdd.call(this, map);
    },

    getTileUrl: function (coords) { // (Point, Number) -> String
        var tileSize = this.options.tileSize;
        var nwPoint = coords.multiplyBy(tileSize);
        nwPoint.x+=1;
        nwPoint.y-=1;
        var sePoint = nwPoint.add(new L.Point(tileSize, tileSize));
        var zoom = this._tileZoom;
        var nw = this._crs.project(this._map.unproject(nwPoint, zoom));
        var se = this._crs.project(this._map.unproject(sePoint, zoom));
        var tilewidth = se.x-nw.x;
        //zoom = this._map.getZoom();
        var ident = this.matrixIds[zoom].identifier;
        var tilematrix = this.wmtsParams.tilematrixSet + ":" + ident;
        var X0 = this.matrixIds[zoom].topLeftCorner.lng;
        var Y0 = this.matrixIds[zoom].topLeftCorner.lat;
        var tilecol=Math.floor((nw.x-X0)/tilewidth);
        var tilerow=-Math.floor((nw.y-Y0)/tilewidth);
        var url = L.Util.template(this._url, {s: this._getSubdomain(coords)});
        return url + L.Util.getParamString(this.wmtsParams, url) + "&tilematrix=" + tilematrix + "&tilerow=" + tilerow +"&tilecol=" + tilecol;
    },

    setParams: function (params, noRedraw) {
        L.extend(this.wmtsParams, params);
        if (!noRedraw) {
            this.redraw();
        }
        return this;
    },

    getDefaultMatrix : function () {
        /**
         * the matrix3857 represents the projection
         * for in the IGN WMTS for the google coordinates.
         */
        var matrixIds3857 = new Array(22);
        for (var i= 0; i<22; i++) {
            matrixIds3857[i]= {
                identifier    : "" + i,
                topLeftCorner : new L.LatLng(20037508.3428,-20037508.3428)
            };
        }
        return matrixIds3857;
    }
});
L.tileLayer.wmts = function (url, options) {
    return new L.TileLayer.WMTS(url, options);
};

/* To make default marker work with webpack */
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
    iconUrl: require('leaflet/dist/images/marker-icon.png'),
    shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});
/********************************************/

module.exports = {
    data: function(){
        let vm = this;
        vm.layers = [];
        vm.mcg = L.markerClusterGroup();
        vm.datetime_pattern = /^\d{2}\/\d{2}\/\d{4}$/gi;
        vm.ajax_for_location = null;

        return {
            mapboxAccessToken: null,
            map: null,
            tileLayer: null, // Base layer (Open street map)
            tileLayerSat: null, // Base layer (satelllite)
            popup: null,
            opt_url : helpers.add_endpoint_json(api_endpoints.offence, "optimised"),

            /*
             * Filers:
             * value of the "value" attribute of the option is stored.
             * The value of this is used queryset.filter() in the backend.
             */
            filterStatus: 'all',
            filterDateFrom: '',
            filterDateTo: '',
            filterSanctionOutcomeType: 'all',

            status_choices: [],
            sanction_outcome_type_choices: [],
            cursor_location: null,
        }
    },
    created: async function() {
        let temp_token = await this.retrieveMapboxAccessToken();
        this.mapboxAccessToken = temp_token.access_token;

        let returned_status_choices = await cache_helper.getSetCacheList('Offence_StatusChoices', '/api/offence/status_choices');
        Object.assign(this.status_choices, returned_status_choices);
        this.status_choices.splice(0, 0, {id: 'all', display: 'All'});

        let returned_choices = await cache_helper.getSetCacheList('SanctionOutcome_TypeChoices', '/api/sanction_outcome/types');
        Object.assign(this.sanction_outcome_type_choices, returned_choices);
        this.sanction_outcome_type_choices.splice(0, 0, {id: 'all', display: 'All'});

    },
    mounted(){
        let vm = this;
        vm.initMap();
        vm.loadLocations();
        vm.initAwesomplete();
        vm.$nextTick(() => {
            vm.addEventListeners();
        });
    },
    watch: {
        filterStatus: function () {
            this.loadLocations();
        },
        filterSanctionOutcomeType: function(){
            this.loadLocations();
        },
        filterDateFrom: function(){
            if (!this.filterDateFrom){
                /* When empty string */
                this.loadLocations();
            } else {
                let result = this.datetime_pattern.exec(this.filterDateFrom);
                if (result){
                    /* When date is set */
                    this.loadLocations();
                }
            }
        },
        filterDateTo: function(){
            if (!this.filterDateTo){
                /* When empty string */
                this.loadLocations();
            } else {
                let result = this.datetime_pattern.exec(this.filterDateTo);
                if (result){
                    /* When date is set */
                    this.loadLocations();
                }
            }
        }
    },
    computed: {
    },
    methods: {
        addEventListeners: function () {
            let vm = this;
            let el_fr = $(vm.$refs.lodgementDateFromPicker);
            let el_to = $(vm.$refs.lodgementDateToPicker);

            // Date "From" field
            el_fr.datetimepicker({ format: 'DD/MM/YYYY', maxDate: moment().millisecond(0).second(0).minute(0).hour(0), showClear: true });
            el_fr.on('dp.change', function (e) {
                if (el_fr.data('DateTimePicker').date()) {
                    vm.filterDateFrom = e.date.format('DD/MM/YYYY');
                    el_to.data('DateTimePicker').minDate(e.date);
                } else if (el_fr.data('date') === "") {
                    vm.filterDateFrom = "";
                }
            });

            // Date "To" field
            el_to.datetimepicker({ format: 'DD/MM/YYYY', maxDate: moment().millisecond(0).second(0).minute(0).hour(0), showClear: true });
            el_to.on('dp.change', function (e) {
                if (el_to.data('DateTimePicker').date()) {
                    vm.filterDateTo = e.date.format('DD/MM/YYYY');
                    el_fr.data('DateTimePicker').maxDate(e.date);
                } else if (el_to.data('date') === "") {
                    vm.filterDateTo = "";
                }
            });
        },
        initAwesomplete: function(){
            var self = this;
            var element_search = document.getElementById('search-input');
            this.awe = new Awesomplete(element_search);
            $(element_search).on('keyup', function(ev){
                var keyCode = ev.keyCode || ev.which;
                if ((48 <= keyCode && keyCode <= 90)||(96 <= keyCode && keyCode <= 105)){
                    self.search(ev.target.value);
                    return false;
                }
            }).on('awesomplete-selectcomplete', function(ev){
                ev.preventDefault();
                ev.stopPropagation();
                /* User selected one of the search results */
                for (var i=0; i<self.suggest_list.length; i++){
                    if (self.suggest_list[i].value == ev.target.value){
                        var latlng = {lat: self.suggest_list[i].feature.geometry.coordinates[1], lng: self.suggest_list[i].feature.geometry.coordinates[0]};
                        //self.map.setView(latlng, 13);
                        self.map.flyTo(latlng, 13,{
                            animate: true,
                            duration: 1.5
                        });
                    }
                }
                return false;
            });
        },
        search: function(place){
            var self = this;

            var latlng = this.map.getCenter();
            $.ajax({
                url: api_endpoints.geocoding_address_search + encodeURIComponent(place)+'.json?'+ $.param({
                    access_token: self.mapboxAccessToken,
                    country: 'au',
                    limit: 10,
                    proximity: ''+latlng.lng+','+latlng.lat,
                    bbox: '112.920934,-35.191991,129.0019283,-11.9662455',
                    types: 'region,postcode,district,place,locality,neighborhood,address,poi'
                }),
                dataType: 'json',
                success: function(data, status, xhr) {
                    self.suggest_list = [];  // Clear the list first
                    if (data.features && data.features.length > 0){
                        for (var i = 0; i < data.features.length; i++){
                            self.suggest_list.push({ label: data.features[i].place_name,
                                                     value: data.features[i].place_name,
                                                     feature: data.features[i]
                                                     });
                        }
                    }

                    self.awe.list = self.suggest_list;
                    self.awe.evaluate();
                }
            });
        },
        setBaseLayer: function(selected_layer_name){
            if (selected_layer_name == 'sat') {
                this.map.removeLayer(this.tileLayer);
                this.map.addLayer(this.tileLayerSat);
                $('#basemap_sat').hide();
                $('#basemap_osm').show();
            }
            else {
                this.map.removeLayer(this.tileLayerSat);
                this.map.addLayer(this.tileLayer);
                $('#basemap_osm').hide();
                $('#basemap_sat').show();
            }
        },
        onClick(e){
            console.log(e.latlng.toString());
        },
        onMouseMove: function(e){
            this.cursor_location = this.map.mouseEventToLatLng(e.originalEvent);
        },
        onMouseOut: function(e){
            this.cursor_location = null;
        },
        initMap(){
            console.log('Start initMap()');

            this.map = L.map('mapLeaf').setView([-24.9505, 122.8605], 5);
            this.tileLayer = L.tileLayer(
                'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
                {
                    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>, contributiors',
                }
            );

            this.tileLayerSat = L.tileLayer.wmts(
                'https://kmi.dpaw.wa.gov.au/geoserver/gwc/service/wmts',
                {
                    layer: 'public:mapbox-satellite',
                    tilematrixSet: 'mercator',
                    format: 'image/png',
                }
            );

            this.popup = L.popup();
            this.map.on('click', this.onClick).on('mousemove', this.onMouseMove).on('mouseout', this.onMouseOut);
            this.setBaseLayer('osm');
            this.addOtherLayers();
            this.map.addLayer(this.mcg);
            L.control.locate().addTo(this.map);
        },
        addOtherLayers(){
            var overlayMaps = {};

            this.$http.get('/api/map_layers/').then(response => {
                let layers = response.body.results;
                for (var i = 0; i < layers.length; i++){
                    let l = L.tileLayer.wmts(
                        'https://kmi.dpaw.wa.gov.au/geoserver/gwc/service/wmts',
                        {
                            layer: layers[i].layer_name.trim(),
                            tilematrixSet: 'mercator',
                            format: 'image/png',
                        }
                    );
                    overlayMaps[layers[i].display_name] = l;
                }
                L.control.layers(null, overlayMaps, {position: 'topleft'}).addTo(this.map);
            });
        },
        loadLocations(){
            let vm = this;

            /* Cancel all the previous requests */
            if (vm.ajax_for_location != null){
                vm.ajax_for_location.abort();
                vm.ajax_for_location = null;
            }
            let myData = {
                "status": vm.filterStatus,
                "date_from" : vm.filterDateFrom,
                "date_to" : vm.filterDateTo,
                "sanction_outcome_type": vm.filterSanctionOutcomeType,
            };

            vm.ajax_for_location = $.ajax({
                type: 'GET',
                data: myData,
                url: vm.opt_url,
                success: function(data){
                    vm.addMarkers(data);
                },
                error: function (e){
                    console.log(e);
                }
            });
        },
        addMarkers(offences){
            let self = this;
            self.mcg.clearLayers();

            if (offences && offences.length > 0){
                for (var i = 0; i < offences.length; i++){
                    if(offences[i].location){
                        let offence = offences[i];
                        let coords = offence.location.geometry.coordinates;

                        /* Select a marker file, according to the classification */
                        let filename = 'marker-gray-locked.svg';
                        if (offence.status){
                            if (offence.status == 'open'){
                                filename = 'marker-green-locked.svg';
                            } else if (offence.status == 'discarded'){
                                filename = 'marker-blue-locked.svg';
                            } else if (offence.status == 'closing'){
                                filename = 'marker-orange-locked.svg';
                            } else if (offence.status == 'closed'){
                                filename = 'marker-red-locked.svg';
                            }
                        }

                        /* create marker */
                        let myIcon = L.icon({
                            iconUrl: require('../../../assets/' + filename),
                            shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
                            shadowSize: [41, 41],
                            shadowAnchor: [12, 41],
                            iconSize: [32, 32],
                            iconAnchor: [16, 32],
                            popupAnchor: [0, -20]
                        });
                        let myMarker = L.marker([coords[1], coords[0]], {icon: myIcon});
                        let myPopup = L.popup();
                        myMarker.bindPopup(myPopup);
                        self.mcg.addLayer(myMarker);

                        /* dynamically construct content of the popup */
                        myMarker.on('click', (ev)=>{
                            let popup = ev.target.getPopup();
                            self.$http.get('/api/offence/' + offence.id).then(response => {
                                let offence = response.body;
                                popup.setContent(self.construct_content(offence, coords));
                            });
                        })
                    }
                }
            }
        },
        construct_content: function (offence, coords){
            console.log('offence clicked');
            console.log(offence);
            let offenders_str = ''
            for (let i=0; i<offence.offenders.length; i++) {
                let offender = offence.offenders[i].person;
                if (offender){
                    offenders_str += `<div>${offender.full_name}</div>`
                }
            }
            let status_str = offence.status?offence.status.name:''
            let identifier_str = offence.identifier?offence.identifier:''

            let content = '<div class="popup-title-main">' + offence.lodgement_number + '</div>';

            content += '<div class="popup-title">Identifier</div>'
                    + '<div class="popup-address">'
                    + identifier_str
                    + '</div>'

            content += '<div class="popup-title">Offender(s)</div>'
                    + '<div class="popup-address">'
                    + offenders_str
                    + '</div>'

            content += '<div class="popup-title">Status</div>'
                    + '<div class="popup-address">'
                    + status_str
                    + '</div>'

            if (offence.location.properties.street){
                let str_street = offence.location.properties.street?offence.location.properties.street:''
                let str_town_suburb = offence.location.properties.town_suburt?offence.location.properties.town_suburt:''
                let str_state = offence.location.properties.state?offence.location.properties.state:''
                let str_postcode = offence.location.properties.postcode?offence.location.properties.postcode:''
                content += '<div class="popup-title">Address</div>'
                + '<div class="popup-address">'
                + str_street + '<br />'
                + str_town_suburb + '<br />'
                + str_state + '<br />'
                + str_postcode
                + '</div>'

            } else {
                content += '<div class="popup-title">Details</div>'
                + '<div class="popup-address">'
                + offence.location.properties.details.substring(0, 10)
                + '</div>'
            }

            content += '<div class="popup-link">'
                + offence.user_action
                + '</div>';

            return content;
        }
    },
}
</script>

<style lang="css">
#map-wrapper {
    position: relative;
}
#mapLeaf {
    position: relative;
    height: 800px;
    margin-bottom: 50px;
}
#search-box {
    z-index: 1000;
    position: absolute;
    top: 10px;
    left: 50px;
}
#search-input {
    z-index: 1000;
    width: 300px;
    padding: 5px;
    -moz-border-radius: 5px;
    -webkit-border-radius: 5px;
    border-radius: 5px;
}
#basemap-button {
    position: absolute;
    top: 10px;
    right: 10px;
    z-index: 400;
    -moz-box-shadow: 3px 3px 3px #777;
    -webkit-box-shadow: 3px 3px 3px #777;
    box-shadow: 3px 3px 3px #777;
    -moz-filter: brightness(1.0);
    -webkit-filter: brightness(1.0);
    filter: brightness(1.0);
    border: 2px white solid;
}
#basemap_sat,#basemap_osm {
    /* border-radius: 5px; */
}
#basemap-button:hover {
    cursor: pointer;
    -moz-filter: brightness(0.9);
    -webkit-filter: brightness(0.9);
    filter: brightness(0.9);
}
#basemap-button:active {
    top: 11px;
    right: 9px;
    -moz-box-shadow: 2px 2px 2px #555;
    -webkit-box-shadow: 2px 2px 2px #555;
    box-shadow: 2px 2px 2px #555;
    -moz-filter: brightness(0.8);
    -webkit-filter: brightness(0.8);
    filter: brightness(0.8);
}
.popup-title {
    padding: 5px 5px 5px 10px;
    background: darkgray;
    font-size: 1.3em;
    font-weight: bold;
    color: white;
}
.popup-title-main {
    color: gray;
    font-size: 1.3em;
    font-weight: bold;
    padding: 5px 5px 5px 10px;
}
.popup-coords {
    padding: 0 0 10px 0;
}
.popup-address {
    padding: 10px;
}
.popup-link {
    text-align: center;
    font-size: 1.2em;
    padding: 10px;
}
.leaflet-popup-content {
    margin: 0px !important;
}
.leaflet-popup-content-wrapper {
    padding: 0px !important;
}
#map-filter{
    display: flex;
    justify-content: space-evenly;
    padding: 10px;
}
#cursor-location {
    position: absolute;
    bottom: 0px;
    color: white;
    background-color: rgba(37, 45, 51, 0.6);
    z-index: 1100;
    font-size: 0.9em;
    padding: 5px;
}
</style>
